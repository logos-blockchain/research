//! Prototype of the hash-based DA encoding proposed in analysis-pq-statistical-da.md §6:
//! rows RS-extended (rate 1/2) over Goldilocks, Merkle root over the 2k columns (BLAKE2b-256),
//! Fiat–Shamir challenge h in F_{p^2}, published check row c_j = Σ_i h^i · data_i^j.
use std::time::Instant;

use blake2::digest::consts::U32;
use blake2::{Blake2b, Digest};
use p3_dft::{Radix2DitParallel, TwoAdicSubgroupDft};
use p3_field::integers::QuotientMap;
use p3_field::{Field, PrimeCharacteristicRing, PrimeField64};
use p3_goldilocks::Goldilocks;
use p3_matrix::dense::RowMajorMatrix;
use p3_matrix::Matrix;
use rand::{Rng, SeedableRng};

type F = Goldilocks;
type H = Blake2b<U32>;
type Hash = [u8; 32];

const K: usize = 1024; // original columns
const N: usize = 2 * K; // extended columns = subnetworks

fn hash_bytes(b: &[u8]) -> Hash {
    let mut h = H::new();
    h.update(b);
    h.finalize().into()
}
fn hash_pair(a: &Hash, b: &Hash) -> Hash {
    let mut h = H::new();
    h.update(a);
    h.update(b);
    h.finalize().into()
}

/// Quadratic extension element (a0 + a1·x) kept as two base coordinates, so that
/// ext × base multiplications stay two base multiplications.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Ext(F, F);
impl Ext {
    // x^2 = 7 is Goldilocks' binomial extension (p3-goldilocks: W = 7).
    const W: u64 = 7;
    fn mul(self, o: Ext) -> Ext {
        let w = F::from_int(Self::W);
        Ext(self.0 * o.0 + w * self.1 * o.1, self.0 * o.1 + self.1 * o.0)
    }
}

struct Encoded {
    /// extended matrix, column-major: columns[j] holds the ℓ chunks of column j
    columns: Vec<Vec<F>>,
    leaves: Vec<Hash>,
    tree: Vec<Vec<Hash>>, // level 0 = leaves … last = [root]
    root: Hash,
    h: Ext,
    check_row: Vec<Ext>, // length N
}

fn column_bytes(col: &[F]) -> Vec<u8> {
    let mut v = Vec::with_capacity(col.len() * 8);
    for x in col {
        v.extend_from_slice(&x.as_canonical_u64().to_le_bytes());
    }
    v
}

fn merkle(leaves: &[Hash]) -> (Vec<Vec<Hash>>, Hash) {
    let mut levels = vec![leaves.to_vec()];
    while levels.last().unwrap().len() > 1 {
        let prev = levels.last().unwrap();
        let next: Vec<Hash> = prev.chunks(2).map(|p| hash_pair(&p[0], &p[1])).collect();
        levels.push(next);
    }
    let root = levels.last().unwrap()[0];
    (levels, root)
}

fn merkle_path(tree: &[Vec<Hash>], mut j: usize) -> Vec<Hash> {
    let mut path = Vec::new();
    for level in tree.iter().take(tree.len() - 1) {
        path.push(level[j ^ 1]);
        j >>= 1;
    }
    path
}

fn merkle_verify(root: &Hash, mut j: usize, leaf: Hash, path: &[Hash]) -> bool {
    let mut acc = leaf;
    for sib in path {
        acc = if j & 1 == 0 { hash_pair(&acc, sib) } else { hash_pair(sib, &acc) };
        j >>= 1;
    }
    &acc == root
}

fn challenge(root: &Hash) -> Ext {
    let d = hash_bytes(&[b"DA_V2".as_slice(), root].concat());
    let a = u64::from_le_bytes(d[0..8].try_into().unwrap());
    let b = u64::from_le_bytes(d[8..16].try_into().unwrap());
    Ext(F::from_int(a), F::from_int(b))
}

fn powers(h: Ext, n: usize) -> Vec<Ext> {
    let mut p = Vec::with_capacity(n);
    let mut acc = Ext(F::ONE, F::ZERO);
    for _ in 0..n {
        p.push(acc);
        acc = acc.mul(h);
    }
    p
}

/// c_j = Σ_i h^i · data_i^j, as two base-field accumulations.
fn rlc(col: &[F], hp: &[Ext]) -> Ext {
    let mut c0 = F::ZERO;
    let mut c1 = F::ZERO;
    for (x, p) in col.iter().zip(hp) {
        c0 += p.0 * *x;
        c1 += p.1 * *x;
    }
    Ext(c0, c1)
}

struct Timings {
    lde: f64,
    hashing: f64,
    merkle: f64,
    check_row: f64,
}

fn encode(rows: usize, data: &[F], dft: &Radix2DitParallel<F>) -> (Encoded, Timings) {
    // data: rows × K, row-major. The DFT works column-wise on a matrix, so we lay the
    // matrix out as K (evaluation index) × rows, i.e. transpose: mat[i][r] = data[r][i].
    let t = Instant::now();
    let mut vals = vec![F::ZERO; K * rows];
    for r in 0..rows {
        for i in 0..K {
            vals[i * rows + r] = data[r * K + i];
        }
    }
    let mat = RowMajorMatrix::new(vals, rows);
    let ext = dft.lde_batch(mat, 1).to_row_major_matrix(); // N × rows
    debug_assert_eq!(ext.height(), N);
    let columns: Vec<Vec<F>> = (0..N).map(|j| ext.row_slice(j).unwrap().to_vec()).collect();
    let lde = t.elapsed().as_secs_f64();

    let t = Instant::now();
    let leaves: Vec<Hash> = columns.iter().map(|c| hash_bytes(&column_bytes(c))).collect();
    let hashing = t.elapsed().as_secs_f64();

    let t = Instant::now();
    let (tree, root) = merkle(&leaves);
    let merkle_t = t.elapsed().as_secs_f64();

    let t = Instant::now();
    let h = challenge(&root);
    let hp = powers(h, rows);
    let check_row: Vec<Ext> = columns.iter().map(|c| rlc(c, &hp)).collect();
    let check_row_t = t.elapsed().as_secs_f64();

    (
        Encoded { columns, leaves, tree, root, h, check_row },
        Timings { lde, hashing, merkle: merkle_t, check_row: check_row_t },
    )
}

/// Once per blob: the check row must be an RS codeword of rate 1/2, i.e. both
/// coordinate vectors interpolate to degree < K on the size-N subgroup.
fn check_row_is_codeword(check_row: &[Ext], dft: &Radix2DitParallel<F>) -> bool {
    let mut vals = Vec::with_capacity(2 * N);
    for c in check_row {
        vals.push(c.0);
        vals.push(c.1);
    }
    let coeffs = dft.idft_batch(RowMajorMatrix::new(vals, 2));
    (K..N).all(|i| coeffs.row_slice(i).unwrap().iter().all(|x| *x == F::ZERO))
}

/// Per column, DA node or light client.
fn verify_column(enc: &Encoded, j: usize, path: &[Hash], hp: &[Ext]) -> bool {
    let leaf = hash_bytes(&column_bytes(&enc.columns[j]));
    merkle_verify(&enc.root, j, leaf, path) && rlc(&enc.columns[j], hp) == enc.check_row[j]
}

fn median(v: &mut [f64]) -> f64 {
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    v[v.len() / 2]
}

fn main() {
    let dft = Radix2DitParallel::<F>::default();
    let mut rng = rand::rngs::StdRng::seed_from_u64(7);
    let blob_kib: Vec<usize> = std::env::args().skip(1).map(|a| a.parse().unwrap()).collect();
    let blob_kib = if blob_kib.is_empty() { vec![256, 1024, 4096] } else { blob_kib };
    println!("hash-da prototype: K={K} N={N}, Goldilocks, BLAKE2b-256, F_p^2 challenge");
    println!("{:>8} {:>5} | {:>8} {:>8} {:>8} {:>8} {:>8} | {:>9} {:>9} {:>9} | {:>7} {:>8}",
        "blob", "rows", "lde_ms", "hash_ms", "mrkl_ms", "crow_ms", "enc_ms",
        "node_us", "lc_col_us", "lc_blob_ms", "col_B", "crow_KiB");
    for kib in blob_kib {
        let rows = kib * 1024 / (8 * K);
        let data: Vec<F> = (0..rows * K).map(|_| F::from_int(rng.gen::<u64>())).collect();
        let reps = 5;
        let mut te = Vec::new(); let mut tl = Vec::new(); let mut th = Vec::new();
        let mut tm = Vec::new(); let mut tc = Vec::new();
        let mut enc = None;
        for _ in 0..reps {
            let t = Instant::now();
            let (e, ti) = encode(rows, &data, &dft);
            te.push(t.elapsed().as_secs_f64() * 1e3);
            tl.push(ti.lde * 1e3); th.push(ti.hashing * 1e3); tm.push(ti.merkle * 1e3); tc.push(ti.check_row * 1e3);
            enc = Some(e);
        }
        let enc = enc.unwrap();
        let hp = powers(enc.h, rows);
        // sanity
        assert!(check_row_is_codeword(&enc.check_row, &dft));
        let j = 1337;
        let path = merkle_path(&enc.tree, j);
        assert!(verify_column(&enc, j, &path, &hp));
        let mut bad = enc.columns[j].clone(); bad[3] += F::ONE;
        assert!(rlc(&bad, &hp) != enc.check_row[j]);
        // DA node / light-client per column (includes recomputing the leaf hash)
        let iters = 2000;
        let t = Instant::now();
        for i in 0..iters {
            let jj = (j + i * 97) % N;
            let p = merkle_path(&enc.tree, jj);
            assert!(verify_column(&enc, jj, &p, &hp));
        }
        let node_us = t.elapsed().as_secs_f64() * 1e6 / iters as f64;
        // light client once per blob: recompute h, powers, check-row codeword test
        let mut tb = Vec::new();
        for _ in 0..reps {
            let t = Instant::now();
            let h2 = challenge(&enc.root);
            let _hp2 = powers(h2, rows);
            assert!(check_row_is_codeword(&enc.check_row, &dft));
            tb.push(t.elapsed().as_secs_f64() * 1e3);
        }
        let col_bytes = rows * 8;
        let crow_kib = N * 16 / 1024;
        println!("{:>6}Ki {:>5} | {:>8.2} {:>8.2} {:>8.2} {:>8.2} {:>8.2} | {:>9.1} {:>9.1} {:>9.2} | {:>7} {:>8}",
            kib, rows, median(&mut tl), median(&mut th), median(&mut tm), median(&mut tc), median(&mut te),
            node_us, node_us, median(&mut tb), col_bytes, crow_kib);
        let _ = &enc.leaves;
    }
}
