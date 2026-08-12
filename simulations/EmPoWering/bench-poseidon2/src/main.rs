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

    // ---- v0.5.6 (PR #3305): the blend candidate is ONE 3-input hash with a DST ----
    //     pow_ticket = zkhash(BLEND_POW_V1, pol_epoch_nonce, pow_nonce)
    // digest(3) = absorb x3 + pad = 4 permutations; the (dst, nonce_e) prefix is
    // constant per epoch, so an optimising miner precomputes 2 of them.
    let dst = Fr::from(0x424c454e445f504fu64); // stand-in for BLEND_POW_V1

    let t_blend_naive = bench("blend candidate v0.5.6, naive (4 perms)", 300_000, |i| {
        Poseidon2Hasher::digest(&[dst, nonce, Fr::from(i)])
    });
    let mut s_pre = [Fr::ZERO; 3];
    s_pre[0] += dst; permute(&mut s_pre);
    s_pre[0] += nonce; permute(&mut s_pre);
    let t_blend_opt = bench("blend candidate v0.5.6, prefix precomputed (2)", 500_000, |i| {
        let mut s = s_pre;
        s[0] += Fr::from(i); permute(&mut s);
        s[0] += Fr::ONE; permute(&mut s);
        s[0]
    });

    // ---- the reward candidate keeps its key: derive pk, then 3-input ticket ----
    //     pk = zkhash(KDF, sk); ticket = zkhash(nonce_e, block_hash, pk)  (no DST)
    let bh = Fr::from(0xb10cb10cu64);
    let t_reward_naive = bench("reward candidate, naive (kdf + ticket = 7 perms)", 200_000, |i| {
        let pk = Poseidon2Hasher::digest(&[kdf_tag, Fr::from(i)]);
        Poseidon2Hasher::digest(&[nonce, bh, pk])
    });
    let mut s_kdf2 = [Fr::ZERO; 3];
    s_kdf2[0] += kdf_tag; permute(&mut s_kdf2);
    let mut s_tk = [Fr::ZERO; 3];
    s_tk[0] += nonce; permute(&mut s_tk);
    s_tk[0] += bh; permute(&mut s_tk);
    let t_reward_opt = bench("reward candidate, prefixes precomputed (4 perms)", 300_000, |i| {
        let mut s = s_kdf2;
        s[0] += Fr::from(i); permute(&mut s);
        s[0] += Fr::ONE; permute(&mut s);
        let pk = s[0];
        let mut s2 = s_tk;
        s2[0] += pk; permute(&mut s2);
        s2[0] += Fr::ONE; permute(&mut s2);
        s2[0]
    });

    println!("\n  v0.5.6 blend: naive {:.1} perms, opt {:.1};  reward: naive {:.1}, opt {:.1}",
             t_blend_naive / t_perm, t_blend_opt / t_perm,
             t_reward_naive / t_perm, t_reward_opt / t_perm);
    println!("\n  Blend threshold cost (naive basis), seconds per solution on ONE core:\n");
    println!("  {:>6} {:>18} {:>12} {:>12}", "k", "candidates", "naive", "optimised");
    println!("  {}", "-".repeat(54));
    for k in [21u32, 22, 23, 24, 25] {
        let n = 2f64.powi(k as i32);
        let fmt = |s: f64| if s < 120.0 { format!("{s:.1} s") } else { format!("{:.1} min", s / 60.0) };
        println!("  {:>6} {:>18.0} {:>12} {:>12}",
                 format!("2^{k}"), n, fmt(n * t_blend_naive), fmt(n * t_blend_opt));
    }
}
