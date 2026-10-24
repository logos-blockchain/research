//! Baseline: the deprecated Logos DA pipeline (spec 148) with the kzgrs primitives.
//! Rows of K=1024 31-byte chunks interpolated over the K-domain, committed with KZG,
//! RS-extended to N=2048 columns, one FK20 proof per column for the combined polynomial.
use std::time::Instant;

use ark_bls12_381::{Bls12_381, Fr};
use ark_poly::{EvaluationDomain as _, GeneralEvaluationDomain, univariate::DensePolynomial};
use ark_poly_commit::kzg10::KZG10;
use kzgrs::{
    bdfg_proving::{compute_combined_polynomial, generate_row_commitments_hash, verify_column},
    fk20::fk20_batch_generate_elements_proofs,
    common::bytes_to_polynomial_unchecked,
    fk20::Toeplitz1Cache,
    kzg::commit_polynomial,
    rs::encode,
    verification_key_proving_key, Commitment, Evaluations, Polynomial,
};
use rand::{RngCore as _, SeedableRng as _};

const K: usize = 1024;
const N: usize = 2 * K;
const CHUNK: usize = 31;

fn median(v: &mut [f64]) -> f64 {
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    v[v.len() / 2]
}

fn main() {
    let mut rng = rand::rngs::StdRng::seed_from_u64(1987);
    let t = Instant::now();
    let pk = KZG10::<Bls12_381, DensePolynomial<Fr>>::setup(N, true, &mut rng).unwrap();
    let vk = verification_key_proving_key(&pk);
    let cache = Toeplitz1Cache::with_size(&pk, N);
    eprintln!("setup (SRS of {N} + FK20 cache): {:.1} s", t.elapsed().as_secs_f64());
    let coeff_domain = GeneralEvaluationDomain::<Fr>::new(K).unwrap();
    let encode_domain = GeneralEvaluationDomain::<Fr>::new(N).unwrap();

    let blob_kib: Vec<usize> = std::env::args().skip(1).filter_map(|a| a.parse().ok()).collect();
    let blob_kib = if blob_kib.is_empty() { vec![256, 1024, 4096] } else { blob_kib };
    println!("kzg-da baseline: K={K} N={N}, BLS12-381, 31-byte chunks, FK20 column proofs");
    println!("{:>8} {:>5} | {:>9} {:>8} {:>9} {:>9} | {:>9} | {:>7} {:>8}",
        "blob", "rows", "commit_ms", "rs_ms", "fk20_ms", "enc_ms", "node_us", "col_B", "coms_KiB");
    for kib in blob_kib {
        let rows = kib * 1024 / (CHUNK * K);
        let mut data = vec![0u8; rows * K * CHUNK];
        rng.fill_bytes(&mut data);
        let reps = 3;
        let mut tc = Vec::new(); let mut tr = Vec::new(); let mut tf = Vec::new(); let mut te = Vec::new();
        let mut last: Option<(Vec<Commitment>, Vec<Evaluations>, Vec<kzgrs::Proof>)> = None;
        for _ in 0..reps {
            let t0 = Instant::now();
            let polys: Vec<(Evaluations, Polynomial)> = data
                .chunks(K * CHUNK)
                .map(|row| bytes_to_polynomial_unchecked::<CHUNK>(row, coeff_domain))
                .collect();
            let commitments: Vec<Commitment> = polys.iter().map(|(_, p)| commit_polynomial(p, &pk).unwrap()).collect();
            let t1 = Instant::now();
            let extended: Vec<Evaluations> = polys.iter().map(|(_, p)| encode(p, encode_domain)).collect();
            let t2 = Instant::now();
            let hash = generate_row_commitments_hash(&commitments);
            let combined = compute_combined_polynomial(&extended, &hash, encode_domain).interpolate();
            // degree < K: pad the coefficient vector to N so FK20 opens all N columns
            let mut coeffs = combined.coeffs;
            coeffs.resize(N, Fr::from(0u64));
            let padded = DensePolynomial { coeffs };
            let proofs = fk20_batch_generate_elements_proofs(&padded, &pk, Some(&cache));
            let t3 = Instant::now();
            tc.push((t1 - t0).as_secs_f64() * 1e3);
            tr.push((t2 - t1).as_secs_f64() * 1e3);
            tf.push((t3 - t2).as_secs_f64() * 1e3);
            te.push((t3 - t0).as_secs_f64() * 1e3);
            last = Some((commitments, extended, proofs));
        }
        let (commitments, extended, proofs) = last.unwrap();
        assert_eq!(proofs.len(), N);
        // per-column verification (DA node / light client)
        let iters = 100;
        let t = Instant::now();
        for i in 0..iters {
            let j = (1337 + i * 97) % N;
            let column: Vec<Fr> = extended.iter().map(|e| e.evals[j]).collect();
            assert!(verify_column(j, &column, &commitments, &proofs[j], encode_domain, &vk));
        }
        let node_us = t.elapsed().as_secs_f64() * 1e6 / iters as f64;
        println!("{:>6}Ki {:>5} | {:>9.1} {:>8.1} {:>9.1} {:>9.1} | {:>9.1} | {:>7} {:>8}",
            kib, rows, median(&mut tc), median(&mut tr), median(&mut tf), median(&mut te),
            node_us, rows * CHUNK, rows * 48 / 1024);
    }
}
