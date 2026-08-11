// Measures the cost of one EmPoWering proof-of-work candidate.
//
// A candidate is (proof-of-quota.md:204-205):
//     pow_public_key = zkhash(b"KDF", pow_sk)
//     pow_ticket     = zkhash(pol_epoch_nonce, pow_public_key)
//
// zkhash is Poseidon2 over BN254 with a rate-2 sponge. The tree's Digest::digest
// absorbs every input AND a padding element, so a two-input hash is THREE
// permutations, not one. Naive: 6 permutations per candidate. An optimising miner
// precomputes the state after the constant first input of each hash (the "KDF" tag,
// and the epoch nonce, which is fixed for the epoch), leaving 4.
use ark_bn254::Fr;
use ark_ff::{AdditiveGroup, Field};
use logos_blockchain_poseidon2::{Digest, Poseidon2Bn254Hasher as Poseidon2Hasher};
use std::time::Instant;

type Params = jf_poseidon2::constants::bn254::Poseidon2ParamsBn3;
use logos_blockchain_poseidon2::Poseidon2Bn254;
use jf_poseidon2::Poseidon2 as _;

#[inline(always)]
fn permute(state: &mut [Fr; 3]) {
    Poseidon2Bn254::permute_mut::<Params, 3>(state);
}

fn bench<F: FnMut(u64) -> Fr>(label: &str, iters: u64, mut f: F) -> f64 {
    let t0 = Instant::now();
    let mut acc = Fr::ZERO;
    for i in 0..iters {
        acc += f(i);
    }
    let secs = t0.elapsed().as_secs_f64();
    std::hint::black_box(acc);
    let per = secs / iters as f64;
    println!("  {label:<44} {:>10.0} ns   {:>12.0} /s", per * 1e9, 1.0 / per);
    per
}

fn main() {
    let nonce = Fr::from(0x9e3779b97f4a7c15u64);
    let kdf_tag = Fr::from(0x4b4446u64); // b"KDF" as a field element

    println!("Poseidon2 / BN254, t=3 -- single core, release build\n");

    let t_perm = bench("one permutation", 2_000_000, |_| {
        let mut s = [Fr::ONE, Fr::ZERO, Fr::ZERO];
        permute(&mut s);
        s[0]
    });

    let t_digest2 = bench("zkhash of 2 inputs (Digest::digest)", 500_000, |i| {
        Poseidon2Hasher::digest(&[kdf_tag, Fr::from(i)])
    });

    let t_naive = bench("candidate, naive (2 x digest = 6 perms)", 200_000, |i| {
        let pk = Poseidon2Hasher::digest(&[kdf_tag, Fr::from(i)]);
        Poseidon2Hasher::digest(&[nonce, pk])
    });

    // Optimised: precompute the state after absorbing each hash's constant first
    // input, then per candidate do (absorb + pad) twice = 4 permutations.
    let mut s_kdf = [Fr::ZERO; 3];
    s_kdf[0] += kdf_tag;
    permute(&mut s_kdf);
    let mut s_nonce = [Fr::ZERO; 3];
    s_nonce[0] += nonce;
    permute(&mut s_nonce);

    let t_opt = bench("candidate, precomputed prefixes (4 perms)", 300_000, |i| {
        let mut s = s_kdf;
        s[0] += Fr::from(i);
        permute(&mut s);
        s[0] += Fr::ONE;
        permute(&mut s);
        let pk = s[0];
        let mut s2 = s_nonce;
        s2[0] += pk;
        permute(&mut s2);
        s2[0] += Fr::ONE;
        permute(&mut s2);
        s2[0]
    });

    println!("\n  permutations per candidate: naive {:.1}, optimised {:.1}",
             t_naive / t_perm, t_opt / t_perm);
    println!("  candidates/second, one core: naive {:>12.0}   optimised {:>12.0}",
             1.0 / t_naive, 1.0 / t_opt);

    // What the difficulty exponents cost, using the optimised (adversary) rate.
    println!("\n  Seconds per solution on ONE core, at target = p / 2^k:\n");
    println!("  {:>6} {:>18} {:>14} {:>14}", "k", "candidates", "naive", "optimised");
    println!("  {}", "-".repeat(56));
    for k in [20u32, 22, 24, 26, 28] {
        let n = 2f64.powi(k as i32);
        let fmt = |s: f64| if s < 120.0 { format!("{s:.1} s") }
                           else if s < 7200.0 { format!("{:.1} min", s / 60.0) }
                           else { format!("{:.1} h", s / 3600.0) };
        println!("  {:>6} {:>18.0} {:>14} {:>14}",
                 format!("2^{k}"), n, fmt(n * t_naive), fmt(n * t_opt));
    }
}
