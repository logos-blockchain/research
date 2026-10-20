//! Rust port of `model/cryptarchia_recurrence_ablation.py` (modes `proven` and
//! `attack`): on the same simulated lottery strings, fine phases, per unit with
//! ell = unit end - Lw, the frequency with which
//!   proven : the Lean recurrence (`step_cases`) fails its check,
//!   attack : GRR's practical adversary (a lower bound on the true risk) succeeds.
//! Usage: ablate FDEN BETA DELTA LW_HOURS(comma list) NSLOTS [SEED]
//! Output: one line per window: Lw, units tested, failures and rate per mode.

use rayon::prelude::*;

struct Rng(u64);
impl Rng {
    fn next(&mut self) -> u64 {
        // splitmix64
        self.0 = self.0.wrapping_add(0x9E3779B97F4A7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB);
        z ^ (z >> 31)
    }
    fn unif(&mut self) -> f64 {
        (self.next() >> 11) as f64 / (1u64 << 53) as f64
    }
    fn poisson(&mut self, lam: f64) -> u32 {
        let l = (-lam).exp();
        let (mut k, mut p) = (0u32, 1.0);
        loop {
            p *= self.unif();
            if p <= l {
                return k;
            }
            k += 1;
        }
    }
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let fden: f64 = a[1].parse().unwrap();
    let beta: f64 = a[2].parse().unwrap();
    let delta: usize = a[3].parse().unwrap();
    let lws: Vec<i64> = a[4].split(',').map(|x| (x.parse::<f64>().unwrap() * 3600.0) as i64).collect();
    let nslots: usize = a[5].parse::<f64>().unwrap() as usize;
    let seed: u64 = if a.len() > 6 { a[6].parse().unwrap() } else { 5 };
    let f = 1.0 / fden;
    let lam = -(1.0 - f).ln();
    let rh = (1.0 - beta) * lam;
    let pa = 1.0 - (1.0 - f).powf(beta);
    let mut rng = Rng(seed);
    let mut hon = vec![0u8; nslots + 1];
    let mut adv = vec![false; nslots + 1];
    if let Ok(path) = std::env::var("ABLATE_STR") {
        // bytes: hon[0..=nslots] then adv[0..=nslots] (as written by numpy)
        let b = std::fs::read(path).unwrap();
        for s in 0..=nslots {
            hon[s] = b[s];
            adv[s] = b[nslots + 1 + s] != 0;
        }
    } else {
        for s in 1..=nslots {
            hon[s] = rng.poisson(rh).min(255) as u8;
            adv[s] = rng.unif() < pa;
        }
    }
    // units: (start, g1, end): gap slots start+1..=g1, burst g1+1..=end
    let mut units: Vec<(usize, usize, usize)> = vec![];
    let (mut i, mut start) = (1usize, 0usize);
    loop {
        let mut j = i;
        while j <= nslots && hon[j] == 0 {
            j += 1;
        }
        if j > nslots {
            break;
        }
        let g1 = j - 1;
        let mut last = j;
        let mut m = j;
        while m <= nslots && m - last < delta {
            m += 1;
            if m <= nslots && hon[m] > 0 {
                last = m;
            }
        }
        if m > nslots {
            break;
        }
        units.push((start, g1, m));
        start = m;
        i = m + 1;
    }
    let u = units.len();
    let mut ag = vec![0i64; u];
    let mut gl = vec![0i64; u];
    let mut ab = vec![0i64; u];
    let mut hh = vec![0i64; u];
    let mut cs = vec![-1i64; u];
    let mut hall = vec![0i64; u];
    // uncle weight with collision denial: the adversary splits a burst's n honest
    // slots into k chained branches; the heaviest wins, each losing branch keeps
    // only its first block (an uncle): credited min_k ceil(n/k) + k - 1 (<= n)
    let deny = |n: i64| -> i64 {
        if n <= 3 {
            return n;
        }
        (1..=n).map(|k| (n + k - 1) / k + k - 1).min().unwrap()
    };
    let mut hden = vec![0i64; u];
    let mut ends = vec![0i64; u];
    for (k, &(s, g, b)) in units.iter().enumerate() {
        ag[k] = (s + 1..=g).filter(|&x| adv[x]).count() as i64;
        gl[k] = (g - s) as i64;
        ab[k] = (g + 1..=b).filter(|&x| adv[x]).count() as i64;
        let hs: Vec<usize> = (g + 1..=b).filter(|&x| hon[x] > 0).collect();
        // Delta-isolated honest successes counted backwards from the end
        let mut c = 0;
        let mut pos = b as i64;
        while pos > g as i64 {
            if hon[pos as usize] > 0 {
                c += 1;
                pos -= delta as i64 + 1;
            } else {
                pos -= 1;
            }
        }
        hh[k] = c;
        hall[k] = hs.len() as i64;
        hden[k] = deny(hs.len() as i64);
        if ab[k] == 0 && hs.len() == 1 && hon[hs[0]] == 1 {
            cs[k] = hs[0] as i64;
        }
        ends[k] = b as i64;
    }
    // reach sequences
    let mut rho_p = vec![0i64; u + 1];
    let mut rho_a = vec![0i64; u + 1];
    let mut rho_u = vec![0i64; u + 1];
    let mut rho_d = vec![0i64; u + 1];
    for k in 0..u {
        let r = rho_d[k] + ag[k];
        rho_d[k + 1] = (r + ab[k] - hden[k]).max(0);
        let r = rho_u[k] + ag[k];
        rho_u[k + 1] = (r + ab[k] - hall[k]).max(0);
        let r = rho_p[k] + ag[k];
        rho_p[k + 1] = (r + ab[k] - hh[k]).max(ab[k]);
        let r = rho_a[k] + ag[k];
        rho_a[k + 1] = (r + ab[k] - hh[k]).max(0);
    }
    let step_p = |r: i64, mu: i64, j: usize, ell: i64| -> (i64, i64) {
        let a = ag[j];
        let (r2, mu2) = if gl[j] >= 1 { (r + a, if mu + a <= -1 { mu + a } else { r + a }) } else { (r, mu) };
        let (a, d) = (ab[j], hh[j]);
        let rn = (r2 + a - d).max(a);
        if mu2 < -a {
            return (rn, mu2 + a - d);
        }
        if cs[j] >= ell {
            return (rn, r2 - d);
        }
        (rn, rn)
    };
    // the same practical attack against an uncle-weighted fork choice: every honest
    // occupied slot of the burst adds honest weight (collided siblings are uncles)
    let step_u = |r: i64, mu: i64, j: usize| -> (i64, i64) {
        let a = ag[j];
        let (r2, mu2) = if gl[j] >= 1 {
            let mut m2 = if mu < 0 { mu + a } else { 0 };
            if mu < 0 && mu + a >= 0 {
                m2 = 0;
            }
            (r + a, m2)
        } else {
            (r, mu)
        };
        let (a, d) = (ab[j], hall[j]);
        let rn = (r2 + a - d).max(0);
        let mn = if mu2 < 0 { mu2 + a - d } else if r2 + a - d < 0 { r2 + a - d } else { 0 };
        (rn, mn)
    };
    let step_g = |r: i64, mu: i64, j: usize, cred: &Vec<i64>| -> (i64, i64) {
        let a = ag[j];
        let (r2, mu2) = if gl[j] >= 1 {
            let mut m2 = if mu < 0 { mu + a } else { 0 };
            if mu < 0 && mu + a >= 0 {
                m2 = 0;
            }
            (r + a, m2)
        } else {
            (r, mu)
        };
        let (a, d) = (ab[j], cred[j]);
        let rn = (r2 + a - d).max(0);
        let mn = if mu2 < 0 { mu2 + a - d } else if r2 + a - d < 0 { r2 + a - d } else { 0 };
        (rn, mn)
    };
    let step_a = |r: i64, mu: i64, j: usize| -> (i64, i64) {
        let a = ag[j];
        let (r2, mu2) = if gl[j] >= 1 {
            let mut m2 = if mu < 0 { mu + a } else { 0 };
            if mu < 0 && mu + a >= 0 {
                m2 = 0;
            }
            (r + a, m2)
        } else {
            (r, mu)
        };
        let (a, d) = (ab[j], hh[j]);
        let rn = (r2 + a - d).max(0);
        let mn = if mu2 < 0 { mu2 + a - d } else if r2 + a - d < 0 { r2 + a - d } else { 0 };
        (rn, mn)
    };
    for &lw in &lws {
        // first unit whose end exceeds ell, for each tested unit k
        let (tested, fp, fa, fu, fdn) = (0..u)
            .into_par_iter()
            .map(|k| {
                let ell = ends[k] - lw;
                if ell <= 0 {
                    return (0u64, 0u64, 0u64, 0u64, 0u64);
                }
                let j0 = ends.partition_point(|&e| e <= ell);
                // proven
                let (mut r, mut mu) = (rho_p[j0], rho_p[j0]);
                for j in j0..k {
                    let s = step_p(r, mu, j, ell);
                    r = s.0;
                    mu = s.1;
                }
                let fpv = (mu + ag[k] + ab[k] >= 0) as u64;
                // attack
                let (mut r, mut mu) = (rho_a[j0], rho_a[j0]);
                for j in j0..k {
                    let s = step_a(r, mu, j);
                    r = s.0;
                    mu = s.1;
                }
                let fav = (step_a(r, mu, k).1 >= 0) as u64;
                // attack against the uncle-weighted fork choice
                let (mut r, mut mu) = (rho_u[j0], rho_u[j0]);
                for j in j0..k {
                    let s = step_u(r, mu, j);
                    r = s.0;
                    mu = s.1;
                }
                let fuv = (step_u(r, mu, k).1 >= 0) as u64;
                // uncle weight, with collision denial
                let (mut r, mut mu) = (rho_d[j0], rho_d[j0]);
                for j in j0..k {
                    let s = step_g(r, mu, j, &hden);
                    r = s.0;
                    mu = s.1;
                }
                let fdv = (step_g(r, mu, k, &hden).1 >= 0) as u64;
                (1, fpv, fav, fuv, fdv)
            })
            .reduce(|| (0, 0, 0, 0, 0), |x, y| (x.0 + y.0, x.1 + y.1, x.2 + y.2, x.3 + y.3, x.4 + y.4));
        println!(
            "Lw={}h units={} proven={} ({:.3e}) attack={} ({:.3e}) attack_vs_uncle_weight={} ({:.3e}) uncle_with_denial={} ({:.3e})",
            lw as f64 / 3600.0,
            tested,
            fp,
            fp as f64 / tested.max(1) as f64,
            fa,
            fa as f64 / tested.max(1) as f64,
            fu,
            fu as f64 / tested.max(1) as f64,
            fdn,
            fdn as f64 / tested.max(1) as f64
        );
    }
}
