//! Protocol structs: the job-spec read from stdin and the result written to
//! stdout. Mirrors runners/c/equix_runner.c and adapters/README.md.

use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct Job {
    #[serde(default)]
    pub operation: Option<String>,
    #[serde(default)]
    pub runtime: Option<String>,
    #[serde(default)]
    pub challenge_hex: Option<String>,
    /// When set, each rep derives a fresh challenge by SHA-256-chaining this
    /// seed (challenge generation is excluded from every timed region).
    #[serde(default)]
    pub challenge_seed_hex: Option<String>,
    #[serde(default)]
    pub challenge_base_hex: Option<String>,
    #[serde(default)]
    pub solution_hex: Option<String>,
    #[serde(default)]
    pub nonce_bytes: Option<u64>,
    #[serde(default)]
    pub nonce_start: Option<u64>,
    #[serde(default)]
    pub target_effort: Option<u64>,
    #[serde(default)]
    pub max_attempts: Option<u64>,
    #[serde(default)]
    pub repetitions: Option<u64>,
    #[serde(default)]
    pub warmup: Option<u64>,
}

#[derive(Serialize)]
pub struct RunOut {
    pub index: usize,
    pub wall_ns: u64,
    pub solutions: i64,
    pub compile_ns: u64,
    pub attempts: u64,
    pub achieved_effort: u32,
    pub verify_result: Option<String>,
}

#[derive(Serialize)]
pub struct ImplInfo {
    pub name: String,
    pub version: String,
    pub commit: String,
    pub runtime_effective: Option<String>,
}

#[derive(Serialize)]
pub struct EnvInfo {
    pub os: String,
    pub compiler: String,
    pub cpu: String,
    pub arch: String,
    pub device: String,
    pub os_version: String,
}

#[derive(Serialize)]
pub struct Output {
    pub schema_version: u32,
    pub ok: bool,
    #[serde(rename = "impl")]
    pub impl_info: ImplInfo,
    pub operation: String,
    pub runtime_requested: String,
    pub runtime_effective: Option<String>,
    pub env: EnvInfo,
    pub runs: Vec<RunOut>,
    pub solutions_hex: Option<Vec<String>>,
    /// effort op only: the wire bytes of the winning token's nonce (LE,
    /// exactly `nonce_bytes` long) — lets the harness measure message sizes.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub winning_nonce_hex: Option<String>,
    pub peak_rss_kb: i64,
    pub error: Option<String>,
}
