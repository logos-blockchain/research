//! Empirical check of the birthday model the prefix length is chosen against,
//! plus the measured grinding rate that turns it into a cost.
//!
//! The security argument rests on one claim: an adversary who wants *any* two
//! transactions sharing a reference prefix needs about 2^(b/2) candidates, not
//! 2^b. Rather than assert that, this harness measures it — it grinds real
//! `mantle_txhash` outputs at prefix lengths short enough to collide in
//! seconds, and reports the observed number of candidates against the
//! prediction.
//!
//! For a uniform b-bit output the expected number of draws before the first
//! repeat is sqrt(pi/2) * 2^(b/2) ≈ 1.2533 * 2^(b/2). If the measured ratio
//! sits near 1.0 across several values of b, the extrapolation to b = 64 and
//! b = 128 is sound, and the only remaining input is the grinding rate.
//!
//! ```text
//! cargo run --release --bin birthday -- --machine mac
//! ```

use std::{
    collections::HashMap,
    fmt::Write as _,
    time::{Duration, Instant},
};

use reference_prefix_bench::{AttackerHasher, sample_preimage_len, sample_tx_encoded_len};

/// sqrt(pi / 2), the constant in the expected number of draws before the first
/// birthday repeat.
const SQRT_HALF_PI: f64 = 1.253_314_137_315_500_3;

struct Args {
    machine: String,
    prefix_bits: Vec<u32>,
    trials: usize,
    out: Option<String>,
}

impl Args {
    fn parse() -> Self {
        let mut args = Self {
            machine: "unknown".to_owned(),
            // 2, 3, 4 and 5 byte prefixes. Long enough to span 24 bits of
            // doubling, short enough that every trial finishes in seconds.
            prefix_bits: vec![16, 24, 32, 40],
            trials: 8,
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
                "--prefix-bits" => {
                    args.prefix_bits = value()
                        .split(',')
                        .map(|s| s.trim().parse().expect("prefix bits must be a number"))
                        .collect();
                }
                "--trials" => args.trials = value().parse().expect("trials must be a number"),
                "--out" => args.out = Some(value()),
                "--help" | "-h" => {
                    eprintln!(
                        "birthday --machine <name> [--prefix-bits 16,24,32,40] \
                         [--trials 8] [--out FILE]"
                    );
                    std::process::exit(0);
                }
                other => panic!("unknown flag {other}"),
            }
        }
        args
    }
}

/// Grind candidates until two share their leading `bits` bits, starting the
/// nonce sequence at `start` so repeated trials are independent.
///
/// Returns the number of candidates drawn and how long it took.
fn first_collision(hasher: &mut AttackerHasher, bits: u32, start: u64) -> (u64, Duration) {
    let mut seen: HashMap<u64, u64> = HashMap::new();
    let shift = 64 - bits;
    let mut nonce = start;
    let max = hasher.max_nonce();

    let began = Instant::now();
    let mut drawn = 0u64;
    loop {
        let hash = hasher.hash_candidate(nonce);
        // The prefix is the leading bytes of the hash; read them big-endian so
        // that "leading `bits` bits" means what it says.
        let leading = u64::from_be_bytes(hash[..8].try_into().expect("8 bytes")) >> shift;
        drawn += 1;

        if seen.insert(leading, nonce).is_some() {
            return (drawn, began.elapsed());
        }

        nonce = if nonce >= max { 0 } else { nonce + 1 };
    }
}

fn main() {
    let args = Args::parse();

    let mut hasher = AttackerHasher::new();
    // If this diverges, every number below is meaningless, so it is checked
    // before anything is measured.
    hasher.verify_against_real_path();

    println!(
        "birthday self-collision on real mantle_txhash output\n\
         machine   : {}\n\
         sample tx : {} bytes encoded, {} bytes hashed\n\
         expected  : sqrt(pi/2) * 2^(b/2) candidates before the first repeat\n",
        args.machine,
        sample_tx_encoded_len(),
        sample_preimage_len()
    );

    println!(
        "{:>5}  {:>6}  {:>13}  {:>13}  {:>16}  {:>12}",
        "bits", "bytes", "predicted N", "measured N", "ratio +- SE", "search H/s"
    );

    let mut csv = String::from(
        "machine,prefix_bits,prefix_bytes,trials,predicted_n,measured_n_mean,\
         measured_n_stderr,ratio,ratio_stderr,search_hashes_per_second\n",
    );

    for &bits in &args.prefix_bits {
        let predicted = SQRT_HALF_PI * 2f64.powf(f64::from(bits) / 2.0);

        let mut draws: Vec<f64> = Vec::with_capacity(args.trials);
        let mut elapsed = Duration::ZERO;
        for trial in 0..args.trials {
            // Offset each trial so it draws a different region of the nonce
            // space, making the trials independent samples.
            let start = (trial as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15) % hasher.max_nonce();
            let (drawn, took) = first_collision(&mut hasher, bits, start);
            draws.push(drawn as f64);
            elapsed += took;
        }

        let n = draws.len() as f64;
        let mean = draws.iter().sum::<f64>() / n;
        // The first-collision distribution is strongly right-skewed, so the
        // spread across trials is large by nature. The standard error of the
        // mean is what says whether the ratio is consistent with 1.0.
        let variance = draws.iter().map(|d| (d - mean).powi(2)).sum::<f64>() / (n - 1.0);
        let stderr = (variance / n).sqrt();

        let ratio = mean / predicted;
        let ratio_stderr = stderr / predicted;
        let rate = draws.iter().sum::<f64>() / elapsed.as_secs_f64();

        println!(
            "{bits:>5}  {:>6}  {predicted:>13.0}  {mean:>13.0}  \
             {:>16}  {rate:>12.3e}",
            bits / 8,
            format!("{ratio:.3} +- {ratio_stderr:.3}")
        );

        writeln!(
            csv,
            "{},{bits},{},{},{predicted:.1},{mean:.1},{stderr:.1},{ratio:.4},{ratio_stderr:.4},{rate:.1}",
            args.machine,
            bits / 8,
            args.trials
        )
        .expect("writing to a String cannot fail");
    }

    println!(
        "\nA ratio consistent with 1.0 means the 2^(b/2) model holds on real \
         transaction hashes,\nso the cost at b = 64 and b = 128 follows from \
         the grinding rate alone.\n\n\
         The 'search H/s' column is NOT R_gen: it includes the hash-table \
         insert this harness\nuses to detect a repeat. A real parallel \
         collision search (van Oorschot-Wiener) is\nmemoryless and does not pay \
         that cost. Take R_gen from the criterion benchmark."
    );

    let path = args
        .out
        .unwrap_or_else(|| format!("results/{}/birthday.csv", args.machine));
    if let Some(parent) = std::path::Path::new(&path).parent() {
        std::fs::create_dir_all(parent).expect("results directory must be creatable");
    }
    std::fs::write(&path, csv).expect("results file must be writable");
    println!("wrote {path}");
}
