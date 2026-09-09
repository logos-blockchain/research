// Measures the cost of one EmPoWering proof-of-work candidate against the real
// logos-blockchain-poseidon2 crate, for the two tickets as the specification
// defines them since 2026-09-09 (logos-lips PR 400):
//
//   Blend admission (proof-of-quota.md):
//       pow_ticket = zkhash(pow_nonce, pol_epoch_nonce)
//   Reward claim (bedrock-v1.1-mantle-specification.md, CLAIM_POW_REWARD):
//       public_key = zkhash(b"KDF", secret_key)
//       ticket     = zkhash(public_key, block_hash, epoch_nonce)
//
// zkhash is Poseidon2 over BN254 with a rate-2 sponge. Digest::digest absorbs
// every input AND a padding element, so a two-input hash is three permutations
// and a three-input hash four. Both tickets absorb the searched input first, so
// no sponge state carries across candidates: a Blend candidate is a full
// three-permutation evaluation whatever the miner does. The only prefix left to
// precompute is the constant KDF tag of the reward key derivation, which saves
// one of the reward candidate's seven permutations.
//
// The circuit v0.5.6 form, zkhash(BLEND_POW_V1, pol_epoch_nonce, pow_nonce), is
// kept as a reference line so the two forms can be compared on one machine.
//
// THREADS=n adds an aggregate-throughput run of the Blend candidate on n threads,
// for the whole-board basis; everything else is single-threaded.
use ark_bn254::Fr;
use ark_ff::{AdditiveGroup, Field};
use logos_blockchain_poseidon2::{Digest, Poseidon2Bn254Hasher as Poseidon2Hasher};
use std::time::Instant;

type Params = jf_poseidon2::constants::bn254::Poseidon2ParamsBn3;
use logos_blockchain_poseidon2::Poseidon2Bn254;

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
    println!("  {label:<58} {:>10.0} ns   {:>12.0} /s", per * 1e9, 1.0 / per);
    per
}

fn main() {
    let epoch_nonce = Fr::from(0x9e3779b97f4a7c15u64);
    let block_hash = Fr::from(0xb10cb10cu64);
    let kdf_tag = Fr::from(0x4b4446u64); // b"KDF" as a field element
    let dst = Fr::from(0x424c454e445f504fu64); // stand-in for BLEND_POW_V1, reference only

    println!("Poseidon2 / BN254, t=3 -- single core, release build\n");

    let t_perm = bench("one permutation", 2_000_000, |_| {
        let mut s = [Fr::ONE, Fr::ZERO, Fr::ZERO];
        permute(&mut s);
        s[0]
    });

    // ---- Blend: zkhash(pow_nonce, pol_epoch_nonce), the nonce first ----
    let t_blend = bench("blend candidate: zkhash(nonce, epoch) (3 perms)", 500_000, |i| {
        Poseidon2Hasher::digest(&[Fr::from(i), epoch_nonce])
    });

    // ---- Reference: the v0.5.6 wiring, tag and epoch nonce first ----
    let t_blend_v056 = bench("blend candidate v0.5.6: zkhash(tag, epoch, nonce) (4 perms)", 300_000, |i| {
        Poseidon2Hasher::digest(&[dst, epoch_nonce, Fr::from(i)])
    });
    let mut s_pre = [Fr::ZERO; 3];
    s_pre[0] += dst;
    permute(&mut s_pre);
    s_pre[0] += epoch_nonce;
    permute(&mut s_pre);
    let t_blend_v056_opt = bench("blend candidate v0.5.6, prefix precomputed (2 perms)", 500_000, |i| {
        let mut s = s_pre;
        s[0] += Fr::from(i);
        permute(&mut s);
        s[0] += Fr::ONE;
        permute(&mut s);
        s[0]
    });

    // ---- Reward: derive the key, then the three-input ticket with the key first ----
    let t_reward_naive = bench("reward candidate: kdf + zkhash(pk, block, epoch) (7 perms)", 200_000, |i| {
        let pk = Poseidon2Hasher::digest(&[kdf_tag, Fr::from(i)]);
        Poseidon2Hasher::digest(&[pk, block_hash, epoch_nonce])
    });
    // The KDF tag is constant, so its absorption is done once.
    let mut s_kdf = [Fr::ZERO; 3];
    s_kdf[0] += kdf_tag;
    permute(&mut s_kdf);
    let t_reward_opt = bench("reward candidate, KDF prefix precomputed (6 perms)", 200_000, |i| {
        let mut s = s_kdf;
        s[0] += Fr::from(i);
        permute(&mut s);
        s[0] += Fr::ONE;
        permute(&mut s);
        let pk = s[0];
        Poseidon2Hasher::digest(&[pk, block_hash, epoch_nonce])
    });

    println!(
        "\n  permutations per candidate: blend {:.1} (v0.5.6 {:.1}, its optimiser {:.1});  reward naive {:.1}, KDF prefix {:.1}",
        t_blend / t_perm,
        t_blend_v056 / t_perm,
        t_blend_v056_opt / t_perm,
        t_reward_naive / t_perm,
        t_reward_opt / t_perm
    );
    println!(
        "  candidates/second, one core: blend {:>10.0}   reward {:>10.0}   (blend v0.5.6 -> now: x{:.2})",
        1.0 / t_blend,
        1.0 / t_reward_naive,
        t_blend_v056 / t_blend
    );

    // Machine-readable block for scripts/run_pi5.sh -- keep the keys stable.
    // blend_opt_ns equals blend_naive_ns by construction: the searched input is
    // absorbed first, so there is no prefix to precompute.
    println!("\nMACHINE one_permutation_ns={:.0}", t_perm * 1e9);
    println!("MACHINE blend_naive_ns={:.0}", t_blend * 1e9);
    println!("MACHINE blend_opt_ns={:.0}", t_blend * 1e9);
    println!("MACHINE reward_naive_ns={:.0}", t_reward_naive * 1e9);
    println!("MACHINE reward_opt_ns={:.0}", t_reward_opt * 1e9);
    println!("MACHINE blend_v056_naive_ns={:.0}", t_blend_v056 * 1e9);

    println!("\n  Blend threshold cost, seconds per solution (expected; the wait is exponential,");
    println!("  median 0.69x and 95th percentile 3.0x of it):\n");
    println!("  {:>6} {:>12} {:>12} {:>14} {:>14}", "k", "candidates", "one core", "whole board", "msgs/day/core");
    println!("  {}", "-".repeat(64));
    let fmt = |s: f64| if s < 120.0 { format!("{s:.1} s") } else { format!("{:.1} min", s / 60.0) };
    for k in [17u32, 18, 19, 20, 21, 22, 23] {
        let n = 2f64.powi(k as i32);
        let s = n * t_blend;
        println!(
            "  {:>6} {:>12.0} {:>12} {:>14} {:>14.0}",
            format!("2^{k}"),
            n,
            fmt(s),
            fmt(s / 4.0),
            86400.0 / s
        );
    }

    // ---- Optional: aggregate throughput on several threads, for the whole-board basis ----
    if let Ok(n) = std::env::var("THREADS") {
        let n: usize = n.parse().expect("THREADS must be an integer");
        let iters = 300_000u64;
        let t0 = Instant::now();
        let handles: Vec<_> = (0..n)
            .map(|t| {
                std::thread::spawn(move || {
                    let base = (t as u64) << 40;
                    let mut acc = Fr::ZERO;
                    for i in 0..iters {
                        acc += Poseidon2Hasher::digest(&[Fr::from(base + i), epoch_nonce]);
                    }
                    std::hint::black_box(acc)
                })
            })
            .collect();
        for h in handles {
            h.join().unwrap();
        }
        let secs = t0.elapsed().as_secs_f64();
        let rate = (n as u64 * iters) as f64 / secs;
        println!(
            "\n  {n} threads: blend candidates/second aggregate {rate:>10.0}   ({:.2}x one thread)",
            rate * t_blend
        );
        println!("MACHINE blend_threads={n}");
        println!("MACHINE blend_aggregate_per_s={rate:.0}");
    }
}
