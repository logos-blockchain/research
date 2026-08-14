//! Aggregate candidate-generation throughput as a function of thread count.
//!
//! The security margin is a function of the adversary's *aggregate* rate, not
//! their single-core rate, and the two are not related by a clean multiple.
//! On a heterogeneous CPU — Apple Silicon's performance and efficiency cores,
//! or the RPi5's shared memory bandwidth — the last few threads are worth less
//! than the first. So this measures the whole-machine rate directly rather
//! than multiplying a one-core number by the core count.
//!
//! Parallel collision search (van Oorschot–Wiener) is memoryless and
//! embarrassingly parallel: `m` machines find a collision about `m` times
//! sooner, with no communication and no shared table. Aggregate throughput is
//! therefore the honest cost basis, which is why it is measured here.
//!
//! ```text
//! cargo run --release --bin throughput -- --machine mac
//! ```

use std::{
    fmt::Write as _,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
    thread,
    time::{Duration, Instant},
};

use reference_prefix_bench::{AttackerHasher, sample_preimage_len, sample_tx_encoded_len};

struct Args {
    machine: String,
    threads: Vec<usize>,
    seconds: u64,
    out: Option<String>,
}

impl Args {
    fn parse() -> Self {
        let available = thread::available_parallelism().map_or(1, std::num::NonZero::get);

        let mut args = Self {
            machine: "unknown".to_owned(),
            threads: (1..=available).collect(),
            seconds: 3,
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
                "--threads" => {
                    args.threads = value()
                        .split(',')
                        .map(|s| s.trim().parse().expect("thread count must be a number"))
                        .collect();
                }
                "--seconds" => args.seconds = value().parse().expect("seconds must be a number"),
                "--out" => args.out = Some(value()),
                "--help" | "-h" => {
                    eprintln!(
                        "throughput --machine <name> [--threads 1,2,4,8] [--seconds 3] [--out FILE]"
                    );
                    std::process::exit(0);
                }
                other => panic!("unknown flag {other}"),
            }
        }
        args
    }
}

/// Grind for `duration` on `threads` threads, returning total candidates hashed.
fn measure(threads: usize, duration: Duration) -> (u64, Duration) {
    let stop = Arc::new(AtomicBool::new(false));
    let began = Instant::now();

    let handles: Vec<_> = (0..threads)
        .map(|t| {
            let stop = Arc::clone(&stop);
            thread::spawn(move || {
                let mut hasher = AttackerHasher::new();
                let max = hasher.max_nonce();
                let mut nonce = (t as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15) % max;
                let mut count = 0u64;
                // Check the flag every 4096 hashes: often enough to stop
                // promptly, rarely enough that the atomic load is not itself
                // part of what is being measured.
                while !stop.load(Ordering::Relaxed) {
                    for _ in 0..4096 {
                        std::hint::black_box(hasher.hash_candidate(nonce));
                        nonce = if nonce >= max { 0 } else { nonce + 1 };
                    }
                    count += 4096;
                }
                count
            })
        })
        .collect();

    thread::sleep(duration);
    stop.store(true, Ordering::Relaxed);

    let total: u64 = handles
        .into_iter()
        .map(|h| h.join().expect("grinding thread must not panic"))
        .sum();

    (total, began.elapsed())
}

fn main() {
    let args = Args::parse();

    // Validate the shortcut before trusting any rate it produces.
    AttackerHasher::new().verify_against_real_path();

    println!(
        "aggregate candidate-generation throughput\n\
         machine   : {}\n\
         cores     : {} reported available\n\
         sample tx : {} bytes encoded, {} bytes hashed\n",
        args.machine,
        thread::available_parallelism().map_or(1, std::num::NonZero::get),
        sample_tx_encoded_len(),
        sample_preimage_len()
    );

    println!(
        "{:>8}  {:>16}  {:>14}  {:>10}",
        "threads", "candidates/s", "per thread", "scaling"
    );

    let mut csv = String::from(
        "machine,threads,candidates_per_second,per_thread_candidates_per_second,\
         scaling_vs_one_thread,seconds\n",
    );

    let mut one_thread_rate = 0.0f64;

    for &threads in &args.threads {
        let (total, elapsed) = measure(threads, Duration::from_secs(args.seconds));
        let rate = total as f64 / elapsed.as_secs_f64();
        if threads == 1 {
            one_thread_rate = rate;
        }
        let per_thread = rate / threads as f64;
        let scaling = if one_thread_rate > 0.0 {
            rate / one_thread_rate
        } else {
            f64::NAN
        };

        println!("{threads:>8}  {rate:>16.4e}  {per_thread:>14.4e}  {scaling:>9.2}x");

        writeln!(
            csv,
            "{},{threads},{rate:.1},{per_thread:.1},{scaling:.3},{}",
            args.machine, args.seconds
        )
        .expect("writing to a String cannot fail");
    }

    println!(
        "\n'scaling' is measured, not assumed. Use the highest-thread row as \
         the per-machine\naggregate rate when pricing an adversary."
    );

    let path = args
        .out
        .unwrap_or_else(|| format!("results/{}/throughput.csv", args.machine));
    if let Some(parent) = std::path::Path::new(&path).parent() {
        std::fs::create_dir_all(parent).expect("results directory must be creatable");
    }
    std::fs::write(&path, csv).expect("results file must be writable");
    println!("wrote {path}");
}
