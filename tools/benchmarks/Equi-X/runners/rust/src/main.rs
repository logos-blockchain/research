//! Equi-X Rust benchmark runner (arti `equix` + `hashx` crates).
//!
//! Reads one job-spec JSON on stdin, runs the requested operation, writes one
//! result JSON on stdout. Mirrors the C runner's protocol exactly so the Python
//! harness can compare them cell-for-cell.

mod effort;
mod job;

use std::io::Read;
use std::time::Instant;

use equix::{EquiXBuilder, RuntimeOption, SolverMemory};

use job::{EnvInfo, ImplInfo, Job, Output, RunOut};

const MAX_CHALLENGE: usize = 256;

#[cfg(target_os = "linux")]
fn peak_rss_kb() -> i64 {
    std::fs::read_to_string("/proc/self/status")
        .ok()
        .and_then(|s| {
            s.lines()
                .find(|l| l.starts_with("VmHWM:"))
                .and_then(|l| l.split_whitespace().nth(1))
                .and_then(|v| v.parse().ok())
        })
        .unwrap_or(-1)
}

#[cfg(target_os = "macos")]
fn peak_rss_kb() -> i64 {
    // macOS has no /proc; getrusage.ru_maxrss is in BYTES here (Linux uses KB).
    unsafe {
        let mut ru: libc::rusage = std::mem::zeroed();
        if libc::getrusage(libc::RUSAGE_SELF, &mut ru) == 0 {
            (ru.ru_maxrss as i64) / 1024
        } else {
            -1
        }
    }
}

#[cfg(not(any(target_os = "linux", target_os = "macos")))]
fn peak_rss_kb() -> i64 {
    -1
}

fn hex_decode(s: &str) -> Option<Vec<u8>> {
    if s.len() % 2 != 0 {
        return None;
    }
    (0..s.len() / 2)
        .map(|i| u8::from_str_radix(&s[2 * i..2 * i + 2], 16).ok())
        .collect()
}

fn hex_encode(b: &[u8]) -> String {
    let mut o = String::with_capacity(b.len() * 2);
    for x in b {
        o.push_str(&format!("{:02x}", x));
    }
    o
}

fn runtime_option(s: &str) -> RuntimeOption {
    match s {
        "interpret" => RuntimeOption::InterpretOnly,
        "must-compile" => RuntimeOption::CompileOnly,
        _ => RuntimeOption::TryCompile,
    }
}

fn eff_str(runtime_dbg: &str, requested: &str) -> String {
    let compiled = runtime_dbg.to_lowercase().contains("compil");
    if compiled {
        "compiled".to_string()
    } else if requested == "try-compile" {
        "interpreted (fallback)".to_string()
    } else {
        "interpreted".to_string()
    }
}

fn impl_info(runtime_effective: Option<String>) -> ImplInfo {
    ImplInfo {
        name: "equix-rust".to_string(),
        version: std::env::var("EQUIX_RUST_VERSION").unwrap_or_else(|_| "0.7.0".to_string()),
        commit: std::env::var("EQUIX_RUST_COMMIT").unwrap_or_else(|_| "crate-0.7.0".to_string()),
        runtime_effective,
    }
}

#[cfg(target_os = "linux")]
fn cpu_model() -> String {
    // Priority order works across arches: "model name" (x86), "Model" (Raspberry
    // Pi board), "Hardware" (older ARM), "cpu model" (others).
    let text = std::fs::read_to_string("/proc/cpuinfo").unwrap_or_default();
    for field in ["model name", "Model", "Hardware", "cpu model"] {
        for line in text.lines() {
            if let Some((k, v)) = line.split_once(':') {
                if k.trim() == field && !v.trim().is_empty() {
                    return v.trim().to_string();
                }
            }
        }
    }
    "unknown".to_string()
}

#[cfg(not(target_os = "linux"))]
fn cpu_model() -> String {
    // macOS (and other non-Linux): no /proc. `sysctl` reports the CPU brand on
    // both Intel and Apple Silicon (e.g. "Apple M2").
    std::process::Command::new("sysctl")
        .args(["-n", "machdep.cpu.brand_string"])
        .output()
        .ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "unknown".to_string())
}

#[cfg(target_os = "linux")]
fn os_version() -> String {
    std::fs::read_to_string("/proc/sys/kernel/osrelease")
        .ok()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "unknown".to_string())
}

#[cfg(not(target_os = "linux"))]
fn os_version() -> String {
    // macOS/BSD: kernel release via `uname -r` (e.g. Darwin "23.5.0").
    std::process::Command::new("uname")
        .arg("-r")
        .output()
        .ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "unknown".to_string())
}

fn env_info() -> EnvInfo {
    EnvInfo {
        os: std::env::consts::OS.to_string(), // "linux", "macos", ...
        compiler: std::env::var("EQUIX_RUST_RUSTC").unwrap_or_else(|_| "rustc".to_string()),
        cpu: cpu_model(),
        arch: std::env::consts::ARCH.to_string(),
        device: "cpu".to_string(),
        os_version: os_version(),
    }
}

fn fail(op: &str, req: &str, msg: &str) -> ! {
    let out = Output {
        schema_version: 1,
        ok: false,
        impl_info: impl_info(None),
        operation: op.to_string(),
        runtime_requested: req.to_string(),
        runtime_effective: None,
        env: env_info(),
        runs: vec![],
        solutions_hex: None,
        winning_nonce_hex: None,
        peak_rss_kb: peak_rss_kb(),
        error: Some(msg.to_string()),
    };
    println!("{}", serde_json::to_string(&out).unwrap());
    std::process::exit(1);
}

fn emit(
    op: &str,
    req: &str,
    eff: &str,
    runs: Vec<RunOut>,
    solutions_hex: Option<Vec<String>>,
) {
    emit_with_nonce(op, req, eff, runs, solutions_hex, None)
}

fn emit_with_nonce(
    op: &str,
    req: &str,
    eff: &str,
    runs: Vec<RunOut>,
    solutions_hex: Option<Vec<String>>,
    winning_nonce_hex: Option<String>,
) {
    let out = Output {
        schema_version: 1,
        ok: true,
        impl_info: impl_info(Some(eff.to_string())),
        operation: op.to_string(),
        runtime_requested: req.to_string(),
        runtime_effective: Some(eff.to_string()),
        env: env_info(),
        runs,
        solutions_hex,
        winning_nonce_hex,
        peak_rss_kb: peak_rss_kb(),
        error: None,
    };
    println!("{}", serde_json::to_string(&out).unwrap());
}

/// Probe-build to discover the effective runtime (and surface hard failures).
fn effective_runtime(
    builder: &EquiXBuilder,
    challenge: &[u8],
    req: &str,
) -> Result<String, String> {
    match builder.build(challenge) {
        Ok(eq) => Ok(eff_str(&format!("{:?}", eq.runtime()), req)),
        Err(e) => Err(format!("{:?}", e)),
    }
}

/// SHA-256 of `data`. Used only to derive per-rep challenges from a seed
/// (between timed measurements) — never on a timed path.
fn sha256(data: &[u8]) -> [u8; 32] {
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(data);
    h.finalize().into()
}

fn build_nonce_challenge(base: &[u8], nonce: u64, nonce_bytes: usize) -> Vec<u8> {
    let mut c = Vec::with_capacity(base.len() + nonce_bytes);
    c.extend_from_slice(base);
    for i in 0..nonce_bytes {
        c.push(((nonce >> (8 * i)) & 0xff) as u8);
    }
    c
}

/// First challenge for a solve/verify op: either the fixed `challenge_hex`, or
/// (seed mode) SHA-256(seed). Returns (challenge_bytes, seeded?).
fn first_challenge(job: &Job, op: &str, req: &str) -> (Vec<u8>, bool) {
    if let Some(seed_hex) = job.challenge_seed_hex.as_ref() {
        let seed = hex_decode(seed_hex)
            .unwrap_or_else(|| fail(op, req, "invalid challenge_seed_hex"));
        (sha256(&seed).to_vec(), true)
    } else {
        let chex = job
            .challenge_hex
            .as_ref()
            .unwrap_or_else(|| fail(op, req, "requires challenge_hex or challenge_seed_hex"));
        (hex_decode(chex).unwrap_or_else(|| fail(op, req, "invalid challenge_hex")), false)
    }
}

fn op_solve(job: &Job, req: &str, reps: u64, warmup: u64) {
    let (mut challenge, seeded) = first_challenge(job, "solve", req);

    let mut builder = EquiXBuilder::new();
    builder.runtime(runtime_option(req));
    let eff = match effective_runtime(&builder, &challenge, req) {
        Ok(e) => e,
        Err(e) => fail("solve", req, &e),
    };

    let mut mem = SolverMemory::new();
    for _ in 0..warmup {
        if let Ok(eq) = builder.build(&challenge) {
            let _ = eq.solve_with_memory(&mut mem);
        }
        if seeded {
            challenge = sha256(&challenge).to_vec(); // advance the chain (untimed)
        }
    }

    let mut runs = Vec::with_capacity(reps as usize);
    let mut last_sols: Vec<String> = vec![];
    for i in 0..reps {
        let t0 = Instant::now();
        let arr = match builder.build(&challenge) {
            Ok(eq) => eq.solve_with_memory(&mut mem),
            Err(_) => Default::default(),
        };
        let ns = t0.elapsed().as_nanos() as u64;
        if seeded {
            challenge = sha256(&challenge).to_vec(); // next challenge AFTER stopping the timer
        }
        if i + 1 == reps {
            last_sols = arr.iter().map(|s| hex_encode(&s.to_bytes())).collect();
        }
        runs.push(RunOut {
            index: i as usize,
            wall_ns: ns,
            solutions: arr.len() as i64,
            compile_ns: 0,
            attempts: 0,
            achieved_effort: 0,
            verify_result: None,
        });
    }
    emit("solve", req, &eff, runs, Some(last_sols));
}

/// Seed mode, two-phase so the timed region contains ONLY verify_bytes:
/// phase 1 (untimed) walks the SHA-256 chain, self-solving each challenge to
/// collect (challenge, solution) pairs — keeping the ~1.8 MB solver pass out of
/// timing so it cannot pollute the cache the tiny verify reads from; phase 2
/// (timed) verifies the collected pairs back-to-back. Solution-less skipped.
fn op_verify_seeded(job: &Job, req: &str, reps: u64, warmup: u64) {
    let (mut challenge, _) = first_challenge(job, "verify", req);
    let mut builder = EquiXBuilder::new();
    builder.runtime(runtime_option(req));
    let eff = match effective_runtime(&builder, &challenge, req) {
        Ok(e) => e,
        Err(e) => fail("verify", req, &e),
    };

    let mut mem = SolverMemory::new();
    let want = warmup + reps;
    let guard_max = want * 8 + 128;
    // Phase 1: collect valid (challenge, solution) pairs, untimed.
    let mut pairs: Vec<(Vec<u8>, [u8; 16])> = Vec::with_capacity(want as usize);
    let mut guard = 0u64;
    while (pairs.len() as u64) < want && guard < guard_max {
        let sol = match builder.build(&challenge) {
            Ok(eq) => eq.solve_with_memory(&mut mem).iter().next().map(|s| s.to_bytes()),
            Err(_) => None,
        };
        if let Some(sb) = sol {
            pairs.push((challenge.clone(), sb));
        }
        challenge = sha256(&challenge).to_vec(); // advance (untimed)
        guard += 1;
    }

    let warm = (warmup as usize).min(pairs.len());
    for (c, sb) in &pairs[..warm] {
        let _ = builder.verify_bytes(c, sb);
    }

    let mut runs = Vec::with_capacity(pairs.len() - warm);
    for (c, sb) in &pairs[warm..] {
        let t0 = Instant::now();
        let r = builder.verify_bytes(c, sb);
        let ns = t0.elapsed().as_nanos() as u64;
        let (vr, ok) = match &r {
            Ok(_) => ("OK".to_string(), 1),
            Err(e) => (format!("{:?}", e), 0),
        };
        runs.push(RunOut {
            index: runs.len(),
            wall_ns: ns,
            solutions: ok,
            compile_ns: 0,
            attempts: 0,
            achieved_effort: 0,
            verify_result: Some(vr),
        });
    }
    emit("verify", req, &eff, runs, None);
}

fn op_verify(job: &Job, req: &str, reps: u64, warmup: u64) {
    if job.challenge_seed_hex.is_some() {
        return op_verify_seeded(job, req, reps, warmup);
    }
    let chex = job
        .challenge_hex
        .as_ref()
        .unwrap_or_else(|| fail("verify", req, "verify requires challenge_hex"));
    let shex = job
        .solution_hex
        .as_ref()
        .unwrap_or_else(|| fail("verify", req, "verify requires solution_hex"));
    let challenge =
        hex_decode(chex).unwrap_or_else(|| fail("verify", req, "invalid challenge_hex"));
    let sb = hex_decode(shex).unwrap_or_else(|| fail("verify", req, "invalid solution_hex"));
    if sb.len() != 16 {
        fail("verify", req, "solution_hex must be 16 bytes");
    }
    let mut sol_bytes = [0u8; 16];
    sol_bytes.copy_from_slice(&sb);

    let mut builder = EquiXBuilder::new();
    builder.runtime(runtime_option(req));
    let eff = match effective_runtime(&builder, &challenge, req) {
        Ok(e) => e,
        Err(e) => fail("verify", req, &e),
    };

    for _ in 0..warmup {
        let _ = builder.verify_bytes(&challenge, &sol_bytes);
    }

    let mut runs = Vec::with_capacity(reps as usize);
    for i in 0..reps {
        let t0 = Instant::now();
        let r = builder.verify_bytes(&challenge, &sol_bytes);
        let ns = t0.elapsed().as_nanos() as u64;
        let (vr, ok) = match &r {
            Ok(_) => ("OK".to_string(), 1),
            Err(e) => (format!("{:?}", e), 0),
        };
        runs.push(RunOut {
            index: i as usize,
            wall_ns: ns,
            solutions: ok,
            compile_ns: 0,
            attempts: 0,
            achieved_effort: 0,
            verify_result: Some(vr),
        });
    }
    emit("verify", req, &eff, runs, None);
}

fn op_effort(job: &Job, req: &str, reps: u64, warmup: u64) {
    let bhex = job
        .challenge_base_hex
        .as_ref()
        .unwrap_or_else(|| fail("effort", req, "effort requires challenge_base_hex"));
    let base = hex_decode(bhex).unwrap_or_else(|| fail("effort", req, "invalid challenge_base_hex"));
    let nonce_bytes = job.nonce_bytes.unwrap_or(8) as usize;
    let nonce_start = job.nonce_start.unwrap_or(0);
    let target = job.target_effort.unwrap_or(1000) as u32;
    let max_attempts = job.max_attempts.unwrap_or(5_000_000);
    if nonce_bytes > 8 || base.len() + nonce_bytes > MAX_CHALLENGE {
        fail("effort", req, "nonce_bytes out of range");
    }

    let mut builder = EquiXBuilder::new();
    builder.runtime(runtime_option(req));
    let eff = match effective_runtime(&builder, &base, req) {
        Ok(e) => e,
        Err(e) => fail("effort", req, &e),
    };

    let mut mem = SolverMemory::new();
    // (attempts, best effort, winning token bytes: (nonce wire bytes, solution))
    let search = |mem: &mut SolverMemory| -> (u64, u32, Option<(Vec<u8>, Vec<u8>)>) {
        let mut nonce = nonce_start;
        let mut attempts = 0u64;
        let mut best = 0u32;
        let mut token: Option<(Vec<u8>, Vec<u8>)> = None;
        for _ in 0..max_attempts {
            let chal = build_nonce_challenge(&base, nonce, nonce_bytes);
            let arr = match builder.build(&chal) {
                Ok(eq) => eq.solve_with_memory(mem),
                Err(_) => Default::default(),
            };
            attempts += 1;
            let mut done = false;
            for s in arr.iter() {
                let e = effort::effort_of(&chal, &s.to_bytes());
                if e > best {
                    best = e;
                }
                if e >= target && !done {
                    // The token as it would go on the wire: the nonce's
                    // nonce_bytes-long LE encoding + the 16-byte solution.
                    token = Some((chal[base.len()..].to_vec(), s.to_bytes().to_vec()));
                    done = true;
                }
            }
            if done {
                break;
            }
            nonce = nonce.wrapping_add(1);
        }
        (attempts, best, token)
    };

    for _ in 0..warmup {
        let _ = search(&mut mem);
    }

    let mut runs = Vec::with_capacity(reps as usize);
    let mut winning: Option<(Vec<u8>, Vec<u8>)> = None;
    for i in 0..reps {
        let t0 = Instant::now();
        let (attempts, best, token) = search(&mut mem);
        let ns = t0.elapsed().as_nanos() as u64;
        if token.is_some() {
            winning = token;
        }
        runs.push(RunOut {
            index: i as usize,
            wall_ns: ns,
            solutions: (best >= target) as i64,
            compile_ns: 0,
            attempts,
            achieved_effort: best,
            verify_result: None,
        });
    }
    let (sols_hex, nonce_hex) = match winning {
        Some((nonce_bytes_wire, sol)) => (
            Some(vec![hex_encode(&sol)]),
            Some(hex_encode(&nonce_bytes_wire)),
        ),
        None => (None, None),
    };
    emit_with_nonce("effort", req, &eff, runs, sols_hex, nonce_hex);
}

fn op_hashx_compile(job: &Job, req: &str, reps: u64, warmup: u64) {
    use hashx::{HashXBuilder, RuntimeOption as HxRt};
    let bhex = job
        .challenge_base_hex
        .as_ref()
        .or(job.challenge_hex.as_ref())
        .unwrap_or_else(|| fail("hashx_compile", req, "hashx_compile requires a challenge"));
    let base = hex_decode(bhex).unwrap_or_else(|| fail("hashx_compile", req, "invalid challenge"));
    let nonce_start = job.nonce_start.unwrap_or(0);

    let hxrt = match req {
        "interpret" => HxRt::InterpretOnly,
        "must-compile" => HxRt::CompileOnly,
        _ => HxRt::TryCompile,
    };
    let mut hb = HashXBuilder::new();
    hb.runtime(hxrt);

    // Probe for effective runtime / hard failure.
    let probe_seed = build_nonce_challenge(&base, nonce_start, 8);
    let eff = match hb.build(&probe_seed) {
        Ok(h) => eff_str(&format!("{:?}", h.runtime()), req),
        Err(e) => fail("hashx_compile", req, &format!("{:?}", e)),
    };

    for _ in 0..warmup {
        let seed = build_nonce_challenge(&base, nonce_start, 8);
        if let Ok(h) = hb.build(&seed) {
            let _ = h.hash_to_bytes(0);
        }
    }

    let mut runs = Vec::with_capacity(reps as usize);
    for i in 0..reps {
        let seed = build_nonce_challenge(&base, nonce_start + i, 8);
        let t0 = Instant::now();
        let built = hb.build(&seed);
        let compile_ns = t0.elapsed().as_nanos() as u64;
        let (wall_ns, sols) = match built {
            Ok(h) => {
                let e0 = Instant::now();
                let _ = h.hash_to_bytes(0);
                (e0.elapsed().as_nanos() as u64, 1)
            }
            Err(_) => (0, 0),
        };
        runs.push(RunOut {
            index: i as usize,
            wall_ns,
            solutions: sols,
            compile_ns,
            attempts: 0,
            achieved_effort: 0,
            verify_result: None,
        });
    }
    emit("hashx_compile", req, &eff, runs, None);
}

fn main() {
    let mut input = String::new();
    if std::io::stdin().read_to_string(&mut input).is_err() {
        fail("", "", "failed to read stdin");
    }
    let job: Job = match serde_json::from_str(&input) {
        Ok(j) => j,
        Err(e) => fail("", "", &format!("invalid job JSON: {}", e)),
    };

    let op = job.operation.clone().unwrap_or_else(|| "solve".to_string());
    let req = job.runtime.clone().unwrap_or_else(|| "try-compile".to_string());
    let reps = job.repetitions.unwrap_or(10).max(1);
    let warmup = job.warmup.unwrap_or(3);

    match op.as_str() {
        "solve" => op_solve(&job, &req, reps, warmup),
        "verify" => op_verify(&job, &req, reps, warmup),
        "effort" => op_effort(&job, &req, reps, warmup),
        "hashx_compile" => op_hashx_compile(&job, &req, reps, warmup),
        _ => fail(&op, &req, "unknown operation"),
    }
}
