//! Reconstruction latency as a function of `k`, the number of references in a
//! proposal that resolve ambiguously in the validator's mempool.
//!
//! This is the defender's side of the asymmetry. Manufacturing `k` colliding
//! pairs costs the attacker roughly sqrt(k) times one collision, because the
//! birthday search keeps finding pairs as it goes. An *uncapped* validator, by
//! contrast, must walk the product of the candidate-set sizes — 2^k
//! combinations for `k` two-way collisions — and each combination re-encodes
//! and re-hashes every transaction in the block.
//!
//! Two policies are measured:
//!
//! * `uncapped` — the deterministic lookup logos-lips#389 v3 argues for, on the
//!   grounds that at a long enough prefix ambiguity cannot be manufactured.
//! * `capped` — what `logos-blockchain` merged: refuse the proposal outright
//!   once the combination product passes `MAX_RECONSTRUCTION_COMBINATIONS`.
//!   Cheap, but refusing an *honest* proposal is itself the liveness failure.
//!
//! Output is a CSV; `scripts/analyse.py` turns it into the report's table and
//! plot.
//!
//! ```text
//! cargo run --release --bin reconstruction -- --machine mac
//! ```

use std::{
    fmt::Write as _,
    time::{Duration, Instant},
};

use reference_prefix_bench::{
    MAX_BLOCK_TRANSACTIONS, Reconstruction, SLOT_DURATION, candidate_sets,
    honest_block_and_proposal, sample_op_proof, sample_tx_encoded_len, search_reconstruction,
};

struct Args {
    machine: String,
    block_sizes: Vec<usize>,
    k_max: usize,
    repeats: usize,
    budget: Duration,
    out: Option<String>,
}

impl Args {
    fn parse() -> Self {
        let mut args = Self {
            machine: "unknown".to_owned(),
            block_sizes: vec![MAX_BLOCK_TRANSACTIONS],
            k_max: 16,
            repeats: 5,
            budget: Duration::from_secs(60),
            out: None,
        };

        let mut argv = std::env::args().skip(1);
        while let Some(flag) = argv.next() {
            let mut value = || {
                argv.next()
                    .unwrap_or_else(|| panic!("{flag} needs a value"))
            };
            match flag.as_str() {
                "--machine" => args.machine = value(),
                "--block-sizes" => {
                    args.block_sizes = value()
                        .split(',')
                        .map(|s| s.trim().parse().expect("block size must be a number"))
                        .collect();
                }
                "--k-max" => args.k_max = value().parse().expect("k-max must be a number"),
                "--repeats" => args.repeats = value().parse().expect("repeats must be a number"),
                "--budget-secs" => {
                    args.budget =
                        Duration::from_secs(value().parse().expect("budget must be a number"));
                }
                "--out" => args.out = Some(value()),
                "--help" | "-h" => {
                    eprintln!(
                        "reconstruction --machine <name> [--block-sizes 1024,128] \
                         [--k-max 16] [--repeats 5] [--budget-secs 60] [--out FILE]"
                    );
                    std::process::exit(0);
                }
                other => panic!("unknown flag {other}"),
            }
        }

        for &n in &args.block_sizes {
            assert!(
                n <= MAX_BLOCK_TRANSACTIONS,
                "block size {n} exceeds MAX_BLOCK_TRANSACTIONS ({MAX_BLOCK_TRANSACTIONS})"
            );
        }
        args
    }
}

fn median(mut samples: Vec<Duration>) -> Duration {
    samples.sort_unstable();
    samples[samples.len() / 2]
}

fn main() {
    let args = Args::parse();

    println!(
        "reconstruction latency vs. mempool collision multiplicity\n\
         machine            : {}\n\
         slot (the deadline): {:?}\n\
         sample tx          : {} bytes encoded\n",
        args.machine,
        SLOT_DURATION,
        sample_tx_encoded_len()
    );

    let mut csv = String::from(
        "machine,block_txs,k,policy,combinations,attempts,outcome,\
         median_s,min_s,max_s,repeats,over_slot\n",
    );

    for &n in &args.block_sizes {
        let (transactions, proposal, header) = honest_block_and_proposal(n);
        let signature = *proposal.signature();
        let proof = sample_op_proof();

        println!("--- block of {n} transactions ---");
        println!(
            "{:>3}  {:>12}  {:>10}  {:>12}  {}",
            "k", "combinations", "attempts", "median", "verdict"
        );

        let mut first_over_slot: Option<usize> = None;

        for k in 0..=args.k_max.min(n) {
            // The uncapped policy: what #389 v3 specifies.
            let mut samples = Vec::new();
            let mut outcome = Reconstruction::Failed { attempts: 0 };

            for _ in 0..args.repeats {
                // Candidate sets are rebuilt outside the timed region: a real
                // validator receives them from the mempool, it does not clone
                // them into existence.
                let candidates = candidate_sets(&transactions, k, &proof);

                let start = Instant::now();
                outcome = search_reconstruction(&header, &signature, candidates, false);
                samples.push(start.elapsed());

                // Stop repeating once a single run is already expensive; the
                // spread at that scale is far smaller than the effect measured.
                if samples[0] > Duration::from_secs(2) {
                    break;
                }
            }

            let repeats = samples.len();
            let med = median(samples.clone());
            let min = *samples.iter().min().expect("at least one sample");
            let max = *samples.iter().max().expect("at least one sample");
            let combinations = 1u64 << k;
            let attempts = match outcome {
                Reconstruction::Rebuilt { attempts } | Reconstruction::Failed { attempts } => {
                    attempts
                }
                _ => 0,
            };
            let over_slot = med > SLOT_DURATION;
            if over_slot && first_over_slot.is_none() {
                first_over_slot = Some(k);
            }

            println!(
                "{k:>3}  {combinations:>12}  {attempts:>10}  {:>12}  {}",
                format!("{:.3?}", med),
                if over_slot {
                    "OVER SLOT — block production stalls"
                } else {
                    "within slot"
                }
            );

            writeln!(
                csv,
                "{},{n},{k},uncapped,{combinations},{attempts},{},{:.9},{:.9},{:.9},{repeats},{}",
                args.machine,
                match outcome {
                    Reconstruction::Rebuilt { .. } => "rebuilt",
                    Reconstruction::Failed { .. } => "failed",
                    Reconstruction::RefusedTooManyCombinations { .. } => "refused_combinations",
                    Reconstruction::RefusedAmbiguousReference => "refused_ambiguous",
                },
                med.as_secs_f64(),
                min.as_secs_f64(),
                max.as_secs_f64(),
                over_slot,
            )
            .expect("writing to a String cannot fail");

            // The capped policy, for the same k.
            let (capped_outcome, capped_time) =
                capped_sample(&header, &signature, &transactions, k, &proof);
            writeln!(
                csv,
                "{},{n},{k},capped,{combinations},0,{},{:.9},{:.9},{:.9},1,false",
                args.machine,
                match capped_outcome {
                    Reconstruction::Rebuilt { .. } => "rebuilt",
                    Reconstruction::Failed { .. } => "failed",
                    Reconstruction::RefusedTooManyCombinations { .. } => "refused_combinations",
                    Reconstruction::RefusedAmbiguousReference => "refused_ambiguous",
                },
                capped_time.as_secs_f64(),
                capped_time.as_secs_f64(),
                capped_time.as_secs_f64(),
            )
            .expect("writing to a String cannot fail");

            if med > args.budget {
                println!(
                    "    stopping at k={k}: a single run exceeded the {} s measurement budget",
                    args.budget.as_secs()
                );
                break;
            }
        }

        match first_over_slot {
            Some(k) => println!(
                "\n  uncapped reconstruction first exceeds the {:?} slot at k = {k} \
                 ({} combinations)\n",
                SLOT_DURATION,
                1u64 << k
            ),
            None => println!(
                "\n  uncapped reconstruction stayed within the {:?} slot for every k measured\n",
                SLOT_DURATION
            ),
        }
    }

    let path = args
        .out
        .unwrap_or_else(|| format!("results/{}/reconstruction.csv", args.machine));
    if let Some(parent) = std::path::Path::new(&path).parent() {
        std::fs::create_dir_all(parent).expect("results directory must be creatable");
    }
    std::fs::write(&path, csv).expect("results file must be writable");
    println!("wrote {path}");
}

/// Time the capped policy — the merged node's behaviour — at the same `k`.
///
/// Below the cap this is the same search the uncapped policy runs. At and above
/// it, the node refuses before searching, which is fast but drops an honest
/// proposal: the liveness failure the report prices.
fn capped_sample(
    header: &lb_core::header::Header,
    signature: &lb_key_management_system_keys::keys::Ed25519Signature,
    transactions: &[reference_prefix_bench::Tx],
    k: usize,
    proof: &lb_core::mantle::OpProof,
) -> (Reconstruction, Duration) {
    let candidates = candidate_sets(transactions, k, proof);
    let start = Instant::now();
    let outcome = search_reconstruction(header, signature, candidates, true);
    (outcome, start.elapsed())
}
