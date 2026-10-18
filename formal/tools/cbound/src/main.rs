//! Rust port of `model/cryptarchia_bound.py` + `cryptarchia_params.run`:
//! the numeric evaluation of P(not GoodL) for the Cryptarchia settlement theorem
//! (see the Python docstrings for the model and the pessimistic simplifications).
//!
//! Input (stdin): JSON array of configs `[f, beta, Delta, cap_hours, N, fine, p_late?, rule?, wslots?, h?, p1?, a?]`
//! (`h, p1, a`: an explicit slot law, P(some honest leader), P(exactly one), P(adversary wins)).
//! (`rule` 0 longest chain, 1 uncle weight; `wslots` the uncle-weight window in slots).
//! (`p_late`: probability an honest proposal is not delivered within Delta; late
//! proposals count as adversarial, as in the Lean `lotStrS` with lateness).
//! Output (stdout): JSON array of results with the same keys as the Python sweep
//! (`f, beta, Delta, cap, N, fine, K, mean_phase, curve, curve_block`).
//! Configs run in parallel (rayon).

use rayon::prelude::*;
use serde_json::{json, Value};
use std::io::Read;

const AMAX: usize = 60;
const HMAX: usize = 40;

/// Per-slot law of the lottery string: honest leaders Poisson(rh), each proposal
/// independently late with probability `p` (late proposals count as adversarial,
/// `lotStrS` with lateness): timely leaders Poisson(rh (1-p)); P(no timely honest)
/// = e^{-rh'}; P(exactly one) = rh' e^{-rh'}; adversarial flag = adversary wins or
/// some proposal is late, 1 - (1-a) e^{-rh p}.
fn slot_law(f: f64, beta: f64, p: f64) -> (f64, f64, f64) {
    let lam = -(1.0 - f).ln();
    let rh0 = (1.0 - beta) * lam;
    let rh = rh0 * (1.0 - p);
    let h = 1.0 - (-rh).exp();
    let p1 = rh * (-rh).exp();
    let a0 = 1.0 - (1.0 - f).powf(beta);
    let a = 1.0 - (1.0 - a0) * (-rh0 * p).exp();
    (h, p1, a)
}

/// P[A][H][c], B[A][H][c] (flattened), lost mass, gap law P(G>=1, A_gap=j), h.
/// Every transition probability is inflated by this relative amount before the DP.
/// It exceeds the rounding error of computing them (a few ulps, at most ~1e-10
/// relative even where a subtraction cancels), so the DP runs on an entrywise
/// larger operator. The DP then adds and multiplies nonnegative numbers only, so
/// every state mass and failure probability can only be over-estimated.
const INFL: f64 = 1e-9;

/// Uncles per block that count for weight (spec `MAX_UNCLES` = 4; `CB_MAXU` overrides
/// it, to study a smaller cap for weight credit).
fn max_uncles() -> usize {
    std::env::var("CB_MAXU").ok().and_then(|x| x.parse().ok()).unwrap_or(4)
}

struct PhaseLaw {
    p: Vec<f64>,
    b: Vec<f64>,
    lost: f64,
    gap_g1: Vec<f64>,
    h: f64,
}

#[inline]
fn pidx(a: usize, h: usize, c: usize) -> usize {
    (a * (HMAX + 1) + h) * 2 + c
}

impl PhaseLaw {
    fn inflated(&self, eps: f64) -> PhaseLaw {
        let k = 1.0 + eps;
        PhaseLaw {
            p: self.p.iter().map(|x| x * k).collect(),
            b: self.b.iter().map(|x| x * k).collect(),
            lost: self.lost * k,
            gap_g1: self.gap_g1.iter().map(|x| x * k).collect(),
            h: self.h * k,
        }
    }
}

/// Uncle weight, conjectured gain (DESIGN.md, W2): a burst of `n` honest slots adds
/// at least `c(n) = min_k ceil(n/k) + k - 1` credited weight (the adversary-optimal
/// split into k chained branches, each losing branch keeping its first block).
fn credit(n: usize) -> usize {
    if n <= 3 {
        return n;
    }
    (1..=n).map(|k| (n + k - 1) / k + k - 1).min().unwrap()
}

/// `credit_mode`: count every honest slot of a burst (uncle weight) and map the
/// count n to `credit(n)`; otherwise the Delta-isolated count (longest chain).
fn phase_law(law: (f64, f64, f64), delta: usize, tol: f64, credit_mode: bool) -> PhaseLaw {
    let (h, p1, a) = law;
    let d1 = delta + 1;
    let nd = d1 + 1;
    // cur[q][d][H][A][one]
    let sz = delta * nd * (HMAX + 1) * (AMAX + 1) * 2;
    let idx = |q: usize, d: usize, hh: usize, aa: usize, one: usize| -> usize {
        ((((q * nd + d) * (HMAX + 1) + hh) * (AMAX + 1) + aa) * 2) + one
    };
    let inner = (HMAX + 1) * (AMAX + 1) * 2;
    let mut cur = vec![0.0f64; sz];
    for (adv, pa) in [(0usize, 1.0 - a), (1usize, a)] {
        cur[idx(0, 0, 1, adv, 1)] += (p1 / h) * pa;
        cur[idx(0, 0, 1, adv, 0)] += (1.0 - p1 / h) * pa;
    }
    // done[H][A][one]
    let didx = |hh: usize, aa: usize, one: usize| -> usize { (hh * (AMAX + 1) + aa) * 2 + one };
    let mut done = vec![0.0f64; inner];
    let mut lost = 0.0f64;
    let dn: Vec<usize> = (0..nd).map(|d| (d + 1).min(d1)).collect();
    loop {
        let total: f64 = cur.iter().sum();
        if total <= tol {
            break;
        }
        let mut new = vec![0.0f64; sz];
        for (adv, pa) in [(0usize, 1.0 - a), (1usize, a)] {
            // shA = cur shifted by adv in A
            let sh: Vec<f64> = if adv == 1 {
                let mut s = vec![0.0f64; sz];
                for q in 0..delta {
                    for d in 0..nd {
                        for hh in 0..=HMAX {
                            for one in 0..2 {
                                lost += cur[idx(q, d, hh, AMAX, one)] * pa;
                            }
                            for aa in 1..=AMAX {
                                for one in 0..2 {
                                    s[idx(q, d, hh, aa, one)] = cur[idx(q, d, hh, aa - 1, one)];
                                }
                            }
                        }
                    }
                }
                s
            } else {
                cur.clone()
            };
            // no honest success: q += 1; burst ends when q reaches Delta
            for q in 0..delta {
                for d in 0..nd {
                    let base = idx(q, d, 0, 0, 0);
                    if q + 1 == delta {
                        for k in 0..inner {
                            done[k] += sh[base + k] * pa * (1.0 - h);
                        }
                    } else {
                        let dst = idx(q + 1, dn[d], 0, 0, 0);
                        for k in 0..inner {
                            new[dst + k] += sh[base + k] * pa * (1.0 - h);
                        }
                    }
                }
            }
            // honest success: q = 0; taken iff advanced d == D1
            for q in 0..delta {
                for d in 0..nd {
                    let ndd = dn[d];
                    for hh in 0..=HMAX {
                        for aa in 0..=AMAX {
                            let m = (sh[idx(q, d, hh, aa, 0)] + sh[idx(q, d, hh, aa, 1)]) * pa * h;
                            if m == 0.0 {
                                continue;
                            }
                            if ndd == d1 || credit_mode {
                                if hh == HMAX {
                                    lost += m;
                                } else {
                                    new[idx(0, 0, hh + 1, aa, 0)] += m;
                                }
                            } else {
                                new[idx(0, ndd, hh, aa, 0)] += m;
                            }
                        }
                    }
                }
            }
        }
        cur = new;
    }
    let dg = 1.0 - (1.0 - h) * (1.0 - a);
    let x = (1.0 - h) * a / dg;
    let gap: Vec<f64> = (0..=AMAX).map(|j| h / dg * x.powi(j as i32)).collect();
    lost += x.powi((AMAX + 1) as i32);
    let mut p = vec![0.0f64; (AMAX + 1) * (HMAX + 1) * 2];
    for hh in 0..=HMAX {
        for one in 0..2 {
            for i in 0..=AMAX {
                if gap[i] == 0.0 {
                    continue;
                }
                for j in 0..=AMAX - i {
                    p[pidx(i + j, hh, 0)] += gap[i] * done[didx(hh, j, one)];
                }
            }
        }
    }
    for hh in 0..=HMAX {
        let c0 = gap[0] * done[didx(hh, 0, 1)];
        p[pidx(0, hh, 0)] -= c0;
        p[pidx(0, hh, 1)] += c0;
    }
    lost += cur.iter().sum::<f64>();
    let mut b = vec![0.0f64; (AMAX + 1) * (HMAX + 1) * 2];
    for hh in 0..=HMAX {
        for aa in 0..=AMAX {
            b[pidx(aa, hh, 0)] = done[didx(hh, aa, 0)] + done[didx(hh, aa, 1)];
        }
        b[pidx(0, hh, 0)] -= done[didx(hh, 0, 1)];
        b[pidx(0, hh, 1)] = done[didx(hh, 0, 1)];
    }
    let mut gap_g1 = gap.clone();
    gap_g1[0] -= h;
    if credit_mode {
        // H index n (honest slots) -> credited weight c(n)
        let remap = |v: &Vec<f64>| -> Vec<f64> {
            let mut o = vec![0.0f64; v.len()];
            for aa in 0..=AMAX {
                for n in 0..=HMAX {
                    for c in 0..2 {
                        o[pidx(aa, credit(n), c)] += v[pidx(aa, n, c)];
                    }
                }
            }
            o
        };
        let (p, b) = (remap(&p), remap(&b));
        return PhaseLaw { p, b, lost, gap_g1, h };
    }
    PhaseLaw { p, b, lost, gap_g1, h }
}

struct Lengths {
    pmf: Vec<f64>,
    rest: f64,
    h: f64,
    delta: usize,
}

fn burst_length_law(law: (f64, f64, f64), delta: usize) -> Lengths {
    let (h, _, _) = law;
    let mut cur = vec![0.0f64; delta];
    cur[0] = 1.0;
    let mut pmf = vec![0.0f64];
    while cur.iter().sum::<f64>() > 1e-40 {
        pmf.push(cur[delta - 1] * (1.0 - h));
        let mut new = vec![0.0f64; delta];
        for q in 1..delta {
            new[q] = cur[q - 1] * (1.0 - h);
        }
        new[0] = cur.iter().sum::<f64>() * h;
        cur = new;
    }
    Lengths { pmf, rest: cur.iter().sum(), h, delta }
}

impl Lengths {
    fn log_mgf(&self, theta: f64) -> f64 {
        let h = self.h;
        if (1.0 - h) * theta.exp() >= 1.0 {
            return f64::INFINITY;
        }
        let mg = h / (1.0 - (1.0 - h) * theta.exp());
        let mut mb: f64 = self
            .pmf
            .iter()
            .enumerate()
            .map(|(l, p)| p * (theta * l as f64).exp())
            .sum();
        if self.rest > 0.0 && theta > 0.0 {
            let dl = self.delta as f64;
            let rc = 1.0 - (1.0 - h).powf(dl);
            if rc * (theta * dl).exp() >= 1.0 {
                return f64::INFINITY;
            }
            let lt = self.rest.ln() + theta * self.pmf.len() as f64 + theta * (dl + 1.0) + (1.0 - rc).ln()
                - (1.0 - rc * (theta * dl).exp()).ln();
            if lt > 700.0 {
                return f64::INFINITY;
            }
            mb += lt.exp();
        }
        mg.ln() + mb.ln()
    }
    fn mean(&self) -> f64 {
        (1.0 - self.h) / self.h + self.pmf.iter().enumerate().map(|(l, p)| p * l as f64).sum::<f64>()
    }
}

fn geomspace(a: f64, b: f64, n: usize) -> Vec<f64> {
    (0..n).map(|i| a * (b / a).powf(i as f64 / (n - 1) as f64)).collect()
}

fn phases_bound(len: &Lengths, n: f64, eps: f64) -> f64 {
    let m = len.mean();
    let mut k = (n / m).floor();
    let ths = geomspace(1e-7, 0.5, 300);
    loop {
        let mut best = 0.0f64;
        for &th in &ths {
            best = best.min(k * len.log_mgf(-th) + th * n);
        }
        if best <= eps.ln() {
            return k;
        }
        k = (k * 1.01).floor() + 1.0;
    }
}

fn normalize_until(mut pi: Vec<f64>, mut f: impl FnMut(&[f64]) -> Vec<f64>) -> Vec<f64> {
    for _ in 0..200000 {
        let mut new = f(&pi);
        let s: f64 = new.iter().sum();
        for x in new.iter_mut() {
            *x /= s;
        }
        let diff: f64 = new.iter().zip(pi.iter()).map(|(a, b)| (a - b).abs()).sum();
        pi = new;
        if diff < 1e-15 {
            break;
        }
    }
    pi
}

/// One transition of a unit: `ae` the reach floor (the unit's adversarial slots,
/// plus under uncle weight the adversarial slots of the window before it, which a
/// chain ending at a fresh honest block can still credit), the unit's adversarial
/// slots `a` (margin drift a - h, cold cut-off, failure check) and honest progress
/// `h`, the crossing flag `c` and the probability `p`. Every adversarial slot is
/// counted once, in its own unit; the window only adds to the floor, and once, at
/// the divergence (`x0` in `analyse`).
#[derive(Clone, Copy, Debug)]
struct Tr {
    ae: usize,
    a: usize,
    h: usize,
    c: usize,
    p: f64,
}

/// Transitions from a law over (A, H, c) and the window penalty's law `px`;
/// entries below `thr` are dropped (their mass is returned, counted as failure).
fn build_trans(law: &[f64], px: &[f64], thr: f64) -> (Vec<Tr>, f64) {
    let mut map: std::collections::HashMap<(usize, usize, usize, usize), f64> = std::collections::HashMap::new();
    let mut dropped = 0.0;
    for aa in 0..=AMAX {
        for hh in 0..=HMAX {
            for c in 0..2 {
                let q = law[pidx(aa, hh, c)];
                if q <= 0.0 {
                    continue;
                }
                for (x, &qx) in px.iter().enumerate() {
                    let pr = q * qx;
                    // window slots a chain can still credit: they need carriers, at
                    // most MAX_UNCLES per adversarial block of the unit
                    let ae = aa + x.min(max_uncles() * aa);
                    if pr > thr {
                        *map.entry((ae, aa, hh, c)).or_insert(0.0) += pr;
                    } else {
                        dropped += pr;
                    }
                }
            }
        }
    }
    let mut v: Vec<Tr> = map.into_iter().map(|((ae, a, h, c), p)| Tr { ae, a, h, c, p }).collect();
    v.sort_by(|x, y| (x.ae, x.a, x.h, x.c).cmp(&(y.ae, y.a, y.h, y.c)));
    (v, dropped)
}

/// Stationary law of the reach rho' = max(rho + A - H, A_eff), on 0..R.
fn reach_stationary(trs: &[Tr], gap: &[f64], h: f64, r: usize, fine: bool) -> Vec<f64> {
    let mut pi0 = vec![0.0f64; r + 1];
    pi0[0] = 1.0;
    let ri = r as i64;
    normalize_until(pi0, |pi| {
        let mid: Vec<f64> = if fine {
            let mut mid: Vec<f64> = pi.iter().map(|x| h * x).collect();
            for (j, g) in gap.iter().enumerate() {
                for rr in 0..=r {
                    mid[(rr + j).min(r)] += g * pi[rr];
                }
            }
            mid
        } else {
            pi.to_vec()
        };
        let mut new = vec![0.0f64; r + 1];
        for t in trs {
            for rr in 0..=ri {
                let r2 = (rr + t.a as i64 - t.h as i64).max(t.ae as i64).min(ri) as usize;
                new[r2] += t.p * mid[rr as usize];
            }
        }
        new
    })
}

/// V_n(mu) = P(some unit check fails within the next n units | margin mu), for the
/// cold dynamics mu += A - H (a check fails iff mu + A >= 0), by n steps of
/// V_{t+1} = F + Q V_t from V_0 = 0 on mu in [-M, -1]; below -M the margin is raised
/// to -M (V is increasing in mu, so this only over-estimates). Only sums of
/// nonnegative terms: every entry has small relative error. (With the clip at -M
/// the infinite-horizon value is 1, so the horizon matters: the block union needs
/// failures before slot N only, i.e. within n = K units.) Returned on mu = -M..R.
fn ever_fail(trs: &[Tr], m: usize, r: usize, horizon: usize) -> Vec<f64> {
    let n = m;
    let mut rows: Vec<Vec<(usize, f64)>> = vec![vec![]; n];
    let mut f = vec![0.0f64; n];
    for t in trs {
        for i in 0..n {
            let mu = i as i64 - m as i64;
            if mu + t.a as i64 >= 0 {
                f[i] += t.p;
            } else {
                let j = ((mu + t.a as i64 - t.h as i64).max(-(m as i64)) + m as i64) as usize;
                match rows[i].iter_mut().find(|e| e.0 == j) {
                    Some(e) => e.1 += t.p,
                    None => rows[i].push((j, t.p)),
                }
            }
        }
    }
    let mut v = vec![0.0f64; n];
    for _ in 0..horizon {
        let nv: Vec<f64> = (0..n).map(|i| f[i] + rows[i].iter().map(|&(j, p)| p * v[j]).sum::<f64>()).collect();
        v = nv;
    }
    let mut out: Vec<f64> = v.iter().map(|x| x.min(1.0)).collect();
    out.extend(std::iter::repeat(1.0).take(r + 1));
    out
}

struct Grid {
    r: usize,
    m: usize,
    w: usize,
}

/// Transitions of one burst, arranged for the pull step: `cold` merged over c,
/// `groups` the cold transitions by drift d = a - h with the cold cut-off folded
/// into per-column weights (valid for rows at or above `hfloor`, where the reach
/// floor max(., A_eff) is inactive for every transition), and for every
/// destination row the list of (group or transition, source row) that write to it.
struct Trans {
    cold: Vec<(usize, usize, usize, f64)>,
    warm: Vec<Tr>,
    groups: Vec<(i64, Vec<f64>)>,
    items: Vec<Vec<(bool, u32, u32)>>,
    max_items: usize,
}

impl Trans {
    fn new(trs: &[Tr], g: &Grid) -> Trans {
        let (r, m) = (g.r, g.m);
        let mut cold: Vec<(usize, usize, usize, f64)> = vec![];
        for t in trs {
            match cold.iter_mut().find(|x| x.0 == t.ae && x.1 == t.a && x.2 == t.h) {
                Some(x) => x.3 += t.p,
                None => cold.push((t.ae, t.a, t.h, t.p)),
            }
        }
        // the floor max(row + d, ae) is active iff row < ae - a + h
        let hfloor = cold.iter().filter(|x| x.1 < m).map(|x| x.0 - x.1 + x.2).max().unwrap_or(0);
        let mut groups: Vec<(i64, Vec<f64>)> = vec![];
        for &(_ae, a, h, p) in &cold {
            if a >= m {
                continue;
            }
            let d = a as i64 - h as i64;
            let gi = match groups.iter().position(|x| x.0 == d) {
                Some(i) => i,
                None => {
                    groups.push((d, vec![0.0; m]));
                    groups.len() - 1
                }
            };
            for i in 0..=(m - a - 1) {
                groups[gi].1[i] += p;
            }
        }
        let mut items: Vec<Vec<(bool, u32, u32)>> = vec![vec![]; r + 1];
        for sr in 0..=r {
            if sr >= hfloor {
                for (gi, (d, _)) in groups.iter().enumerate() {
                    let dst = ((sr as i64 + d).min(r as i64)) as usize;
                    items[dst].push((true, gi as u32, sr as u32));
                }
            } else {
                for (ti, &(ae, a, h, _)) in cold.iter().enumerate() {
                    if a >= m {
                        continue;
                    }
                    let d = a as i64 - h as i64;
                    let dst = ((sr as i64 + d).max(ae as i64).min(r as i64)) as usize;
                    items[dst].push((false, ti as u32, sr as u32));
                }
            }
        }
        let max_items = items.iter().map(|v| v.len()).max().unwrap_or(0);
        // warm collapses: for c = 0 the target depends on (d, ae) only
        let mut warm: Vec<Tr> = vec![];
        for t in trs {
            if t.c == 0 {
                let d = t.a as i64 - t.h as i64;
                if let Some(x) = warm.iter_mut().find(|x| x.c == 0 && x.ae == t.ae && x.a as i64 - x.h as i64 == d) {
                    x.p += t.p;
                    continue;
                }
            }
            warm.push(*t);
        }
        Trans { cold, warm, groups, items, max_items }
    }
}

/// Add `c[i] * src[i]` (or `p * src[i]`) for columns lo..=hi into `dst` at column
/// max(i + d, 0).
#[inline]
fn shift_add(dst: &mut [f64], src: &[f64], lo: usize, hi: usize, d: i64, wv: Option<&[f64]>, p: f64) {
    if d >= 0 {
        let du = d as usize;
        match wv {
            Some(c) => {
                for ((o, x), cc) in dst[lo + du..=hi + du].iter_mut().zip(&src[lo..=hi]).zip(&c[lo..=hi]) {
                    *o += cc * x;
                }
            }
            None => {
                for (o, x) in dst[lo + du..=hi + du].iter_mut().zip(&src[lo..=hi]) {
                    *o += p * x;
                }
            }
        }
    } else {
        let nd = (-d) as usize;
        if lo < nd {
            let e = nd.min(hi + 1);
            let acc: f64 = match wv {
                Some(c) => src[lo..e].iter().zip(&c[lo..e]).map(|(x, cc)| cc * x).sum(),
                None => p * src[lo..e].iter().sum::<f64>(),
            };
            dst[0] += acc;
        }
        let st = lo.max(nd);
        if st <= hi {
            match wv {
                Some(c) => {
                    for ((o, x), cc) in dst[st - nd..=hi - nd].iter_mut().zip(&src[st..=hi]).zip(&c[st..=hi]) {
                        *o += cc * x;
                    }
                }
                None => {
                    for (o, x) in dst[st - nd..=hi - nd].iter_mut().zip(&src[st..=hi]) {
                        *o += p * x;
                    }
                }
            }
        }
    }
}

fn spans(s: &[f64], g: &Grid) -> Vec<(usize, usize)> {
    let w = g.w;
    s.par_chunks(w)
        .map(|x| match x.iter().position(|&v| v != 0.0) {
            Some(lo) => (lo, x.iter().rposition(|&v| v != 0.0).unwrap()),
            None => (1, 0),
        })
        .collect()
}

/// One burst phase (`step_cases`) on S[rho][mu + M], as a pull: every destination
/// row gathers its sources (in parallel over rows, no per-thread copies); the warm
/// collapses (one entry per source row and transition) are then added serially.
fn step(s: &[f64], tr: &Trans, g: &Grid, out: &mut [f64]) {
    let (r, m, w) = (g.r, g.m, g.w);
    let span = spans(s, g);
    out.par_chunks_mut(w).enumerate().for_each(|(rp, orow)| {
        orow.iter_mut().for_each(|x| *x = 0.0);
        for &(grp, idx, sr) in &tr.items[rp] {
            let sr = sr as usize;
            let (lo, hi) = span[sr];
            if lo > hi {
                continue;
            }
            let src = &s[sr * w..(sr + 1) * w];
            if grp {
                let (d, wv) = &tr.groups[idx as usize];
                let hi2 = hi.min(m - 1);
                if lo <= hi2 {
                    shift_add(orow, src, lo, hi2, *d, Some(wv), 0.0);
                }
            } else {
                let (_ae, a, h, p) = tr.cold[idx as usize];
                let hi2 = hi.min(m - a - 1);
                if lo <= hi2 {
                    shift_add(orow, src, lo, hi2, a as i64 - h as i64, None, p);
                }
            }
        }
    });
    // warm part: suffix sums per row, suf[row][i] = sum_{i' >= i} S[row][i']
    // only the columns a warm collapse reads: start = m - ae for each distinct ae
    let starts: Vec<usize> = {
        let mut v: Vec<usize> = tr.warm.iter().map(|t| m.saturating_sub(t.a).min(w)).collect();
        v.sort();
        v.dedup();
        v
    };
    let suf: Vec<Vec<f64>> = s
        .par_chunks(w)
        .map(|x| {
            // suffix sums at the needed starts, from the right
            let mut out = vec![0.0f64; starts.len()];
            let mut acc = 0.0;
            let mut col = w;
            for (k, &st) in starts.iter().enumerate().rev() {
                while col > st {
                    col -= 1;
                    acc += x[col];
                }
                out[k] = acc;
            }
            out
        })
        .collect();
    let spos = |st: usize| starts.binary_search(&st).unwrap();
    for t in &tr.warm {
        let si = spos(m.saturating_sub(t.a).min(w));
        let d = t.a as i64 - t.h as i64;
        for row in 0..=r {
            let wsum = suf[row][si];
            if wsum == 0.0 {
                continue;
            }
            let r2 = ((row as i64 + d).max(t.ae as i64).min(r as i64)) as usize;
            let col = if t.c == 1 {
                ((row as i64 - t.h as i64).max(-(m as i64)) + m as i64) as usize
            } else {
                r2 + m
            };
            out[r2 * w + col] += t.p * wsum;
        }
    }
}

/// A gap of single-slot phases, composed (`_step_gap` of cryptarchia_bound.py):
/// with probability `h` nothing changes; otherwise the gap's adversarial count j
/// (law `gap[j]`, geometric for j >= 1: gap[j] = c x^j) shifts both reach and margin
/// by j, the reach clipped at R; a state that would reach margin >= 0 ends on the
/// diagonal. The shift is along diagonals of the grid, so each diagonal is one
/// convolution with a geometric kernel, computed by the recursion z <- s + x z
/// (one pass, instead of one pass per j). Terms beyond j = AMAX (mass x^(AMAX+1),
/// already counted as lost) are included: extra nonnegative mass, conservative.
fn step_gap(s: &[f64], gap: &[f64], h: f64, g: &Grid, out: &mut [f64]) {
    let (r, m, w) = (g.r, g.m, g.w);
    let g0 = gap[0];
    let c1 = gap.get(1).cloned().unwrap_or(0.0);
    let x = if c1 > 0.0 { gap[2] / c1 } else { 0.0 };
    let cx = c1; // gap[j] = c x^j for j >= 1, so the weight of z (lag 1) is c x = gap[1]
    // G = 0: unchanged
    out.par_iter_mut().zip(s.par_iter()).for_each(|(o, v)| *o = h * v);
    // z[d] = sum_{j >= 0} x^j s[row - 1 - j][col - 1 - j] along diagonal d = col - row.
    // Diagonals are independent: blocks of them run in parallel through all rows;
    // for a fixed row a block's diagonals cross a contiguous run of columns.
    let ext = AMAX + 40;
    let off = r + ext; // index of diagonal d is d + off, over 0..w + off
    let nd = w + off;
    let chunk = (nd + 63) / 64;
    struct P(*mut f64);
    unsafe impl Send for P {}
    unsafe impl Sync for P {}
    impl P {
        fn at(&self, k: usize) -> *mut f64 {
            unsafe { self.0.add(k) }
        }
    }
    let op = P(out.as_mut_ptr());
    let op = &op;
    let (warm, rowr) = (0..nd.div_ceil(chunk))
        .into_par_iter()
        .fold(
            || (vec![0.0f64; r + 1], vec![0.0f64; m]),
            |(mut warm, mut rowr), ci| {
                let (d0, d1) = (ci * chunk, ((ci + 1) * chunk).min(nd));
                let mut z = vec![0.0f64; d1 - d0];
                let mut zout = 0.0f64; // this block's diagonals past column w - 1
                for row in 0..=(r + ext) {
                    let rr = row.min(r);
                    warm[rr] += cx * zout;
                    zout *= x;
                    // columns of this block at this row: col = idx - off + row
                    let c0 = (d0 + row) as i64 - off as i64;
                    let c1 = (d1 + row) as i64 - off as i64; // exclusive
                    let lo = c0.max(0) as usize;
                    let hi = (c1.min(w as i64)).max(0) as usize; // exclusive
                    if lo >= hi {
                        if c0 >= w as i64 && zout < 1e-300 {
                            break;
                        }
                        continue;
                    }
                    let zo = (lo as i64 - c0) as usize; // z index of column lo
                    let zs = &mut z[zo..zo + (hi - lo)];
                    let mid = m.clamp(lo, hi); // columns lo..mid cold, mid..hi warm
                    let (zl, zr) = zs.split_at_mut(mid - lo);
                    let mut wsum = 0.0;
                    if row <= r {
                        let src = &s[row * w + lo..row * w + hi];
                        let (sl, sr) = src.split_at(mid - lo);
                        if row < r {
                            for (k, (zz, sv)) in zl.iter_mut().zip(sl).enumerate() {
                                unsafe { *op.at(row * w + lo + k) += g0 * sv + cx * *zz };
                                *zz = sv + x * *zz;
                            }
                        } else {
                            let rw: &mut [f64] = if lo < m { &mut rowr[lo..mid] } else { &mut [] };
                            for ((zz, sv), o) in zl.iter_mut().zip(sl).zip(rw.iter_mut()) {
                                *o += g0 * sv + cx * *zz;
                                *zz = sv + x * *zz;
                            }
                        }
                        for (zz, sv) in zr.iter_mut().zip(sr) {
                            wsum += g0 * sv + cx * *zz;
                            *zz = sv + x * *zz;
                        }
                    } else {
                        let mut mx = zout;
                        let rw: &mut [f64] = if lo < m { &mut rowr[lo..mid] } else { &mut [] };
                        for (zz, o) in zl.iter_mut().zip(rw.iter_mut()) {
                            *o += cx * *zz;
                            *zz *= x;
                            mx = mx.max(*zz);
                        }
                        for zz in zr.iter_mut() {
                            wsum += cx * *zz;
                            *zz *= x;
                            mx = mx.max(*zz);
                        }
                        if mx < 1e-300 {
                            warm[rr] += wsum;
                            break;
                        }
                    }
                    warm[rr] += wsum;
                    // the diagonal at column w - 1 (if in this block) leaves the grid
                    if hi == w && c1 > w as i64 - 1 {
                        let k = (w - 1) as i64 - c0;
                        if k >= 0 && (k as usize) < z.len() {
                            zout += z[k as usize];
                            z[k as usize] = 0.0;
                        }
                    }
                }
                (warm, rowr)
            },
        )
        .reduce(
            || (vec![0.0f64; r + 1], vec![0.0f64; m]),
            |(mut a1, mut b1), (a2, b2)| {
                for (x, y) in a1.iter_mut().zip(&a2) {
                    *x += y;
                }
                for (x, y) in b1.iter_mut().zip(&b2) {
                    *x += y;
                }
                (a1, b1)
            },
        );
    for (cc, v) in rowr.iter().enumerate() {
        out[r * w + cc] += v;
    }
    for (rr, v) in warm.iter().enumerate() {
        out[rr * w + rr + m] += v;
    }
}

struct Analysis {
    q: Vec<f64>,
    ev: Vec<f64>,
    k: f64,
}

/// Law of the window penalty of uncle weight (DESIGN.md, W3/W4): the adversarial
/// slots and the honest slots in the `wslots` slots before a unit, each Binomial,
/// convolved; mass beyond the truncation is returned (counted as failure).
fn window_law(wslots: usize, a: f64, h: f64) -> (Vec<f64>, f64) {
    let binom = |n: usize, q: f64| -> Vec<f64> {
        let mut v = vec![0.0f64; n + 1];
        if q <= 0.0 {
            v[0] = 1.0;
            return v;
        }
        // pmf by the ratio recurrence, in logs for stability
        let lq = q.ln();
        let l1 = (1.0 - q).ln();
        let mut lc = 0.0f64; // ln C(n, k)
        for k in 0..=n {
            if k > 0 {
                lc += ((n - k + 1) as f64).ln() - (k as f64).ln();
            }
            v[k] = (lc + k as f64 * lq + (n - k) as f64 * l1).exp();
        }
        v
    };
    let (va, vh) = (binom(wslots, a), binom(wslots, h));
    let mut v = vec![0.0f64; 2 * wslots + 1];
    for (i, x) in va.iter().enumerate() {
        if *x < 1e-30 {
            continue;
        }
        for (j, y) in vh.iter().enumerate() {
            v[i + j] += x * y;
        }
    }
    // truncate the tail below 1e-20 (added to the lost mass)
    let mut cut = v.len();
    let mut tail = 0.0;
    while cut > 1 && tail + v[cut - 1] < 1e-20 {
        tail += v[cut - 1];
        cut -= 1;
    }
    v.truncate(cut);
    (v, tail)
}

/// `rule`: 0 longest chain; 1 uncle weight with the conjectured credited count and
/// the window penalty over `wslots` slots.
fn analyse(law: (f64, f64, f64), delta: usize, n: f64, jmax: usize, fine: bool, rule: usize, wslots: usize) -> Analysis {
    // margin grid depth: clipping mu at -M is pessimistic, so any M is sound; 200
    // changes no result by more than 3e-8 relative against 300 (tested at beta 33-40 %)
    let m: usize = std::env::var("CB_M").ok().and_then(|x| x.parse().ok()).unwrap_or(200);
    let mut r = 300usize;
    let dbg = std::env::var("CB_DEBUG").is_ok();
    let t0 = std::time::Instant::now();
    let pl = phase_law(law, delta, 1e-22, rule == 1);
    let (hs, _, a_s) = law;
    // reach floor: adversarial slots of the window (a chain ending at a fresh honest
    // block can credit them); at the divergence, once: adversarial slots of the
    // window and the honest blocks there, which both tines can credit (W4)
    let (px, px_lost) = if rule == 1 && wslots > 0 { window_law(wslots, a_s, 0.0) } else { (vec![1.0], 0.0) };
    // honest blocks both tines can credit at the divergence are fork-first only: the
    // honest branch's first block, and honest blocks of the window that collided
    // (another honest success within Delta before them); deeper honest blocks of the
    // honest branch are not valid uncles for the other tine
    let q_coll = 1.0 - (1.0 - hs).powi(delta as i32);
    let (px0, px0_lost) = if rule == 1 && wslots > 0 {
        let (v, l) = window_law(wslots, a_s, hs * q_coll);
        let mut v1 = vec![0.0f64];
        v1.extend(v);
        (v1, l)
    } else {
        (vec![1.0], 0.0)
    };
    if dbg { eprintln!("phase_law {:.2}s  (window law support {})", t0.elapsed().as_secs_f64(), px.len()); }
    let pi = {
        let (trs_r, _) = build_trans(if fine { &pl.b } else { &pl.p }, &px, 1e-30);
        let mut pi = reach_stationary(&trs_r, &pl.gap_g1, pl.h, r, fine);
        // shrink the reach grid to where the tail is negligible
        let mut tail = vec![0.0f64; r + 2];
        for i in (0..=r).rev() {
            tail[i] = tail[i + 1] + pi[i];
        }
        let r2 = (0..=r).find(|&i| tail[i] < 1e-30).unwrap_or(r);
        r = ((r2 + 20).max(40)).min(r);
        let rest: f64 = pi[r..].iter().sum();
        pi.truncate(r);
        pi.push(rest);
        pi
    };
    if dbg { eprintln!("reach {:.2}s (R={})", t0.elapsed().as_secs_f64(), r); }
    // from here on: the inflated (entrywise larger) transition law, see INFL
    let pl = pl.inflated(INFL);
    let thr = 1e-22;
    let (unit_trs, _) = build_trans(&pl.p, &px, 0.0);
    let len = burst_length_law(law, delta);
    let k = phases_bound(&len, n, 1e-12);
    // value iteration over nonnegative numbers: rounding inflates by at most
    // (1 + u)^(K (n_terms + 1)) with n_terms <= M; 1e-8 covers it for K < 1e5
    let v: Vec<f64> = ever_fail(&unit_trs, m, r, k as usize).iter().map(|x| x * (1.0 + 1e-8)).collect();
    if dbg { eprintln!("ever_fail {:.2}s", t0.elapsed().as_secs_f64()); }
    let g = Grid { r, m, w: r + m + 1 };
    // failure weight: P(A >= -mu) for the whole unit
    let aemax = unit_trs.iter().map(|t| t.a).max().unwrap_or(0);
    let mut pa = vec![0.0f64; aemax + 1];
    for t in &unit_trs {
        pa[t.a] += t.p;
    }
    let mut tail_a = vec![0.0f64; aemax + 2];
    for aa in (0..=aemax).rev() {
        tail_a[aa] = tail_a[aa + 1] + pa[aa];
    }
    let wfail: Vec<f64> = (0..g.w)
        .map(|i| {
            let mu = i as i64 - m as i64;
            if mu >= 0 { 1.0 } else { tail_a[((-mu) as usize).min(aemax + 1)] }
        })
        .collect();
    let (trans, dropped0) = build_trans(if fine { &pl.b } else { &pl.p }, &px, thr);
    let dropped = dropped0 + px_lost + px0_lost;
    let tr = Trans::new(&trans, &g);
    if dbg {
        eprintln!("R={} trans={} groups={} max items/row={} jmax={}", r, trans.len(), tr.groups.len(), tr.max_items, jmax);
    }
    let mut s = vec![0.0f64; (r + 1) * g.w];
    for row in 0..=r {
        for (x0, q0) in px0.iter().enumerate() {
            // margin starts at the reach plus the one-time window bonus (clipped to
            // the grid: margins >= 0 all fail anyway)
            s[row * g.w + (row + m + x0).min(g.w - 1)] += pi[row] * q0;
        }
    }
    let mut tmp = vec![0.0f64; s.len()];
    let mut tmp2 = vec![0.0f64; s.len()];
    let mut q = Vec::with_capacity(jmax + 1);
    let mut ev = Vec::with_capacity(jmax + 1);
    let pi_tail = *pi.last().unwrap();
    let early = std::env::var("CB_NOSTOP").is_err();
    let mut qdp: Vec<f64> = Vec::with_capacity(jmax + 1);
    let mut prof = [0.0f64; 3];
    for jj in 0..=jmax {
        let ta = std::time::Instant::now();
        let (qs, es) = s
            .par_chunks(g.w)
            .map(|row| {
                let mut a = 0.0;
                let mut b = 0.0;
                for ((x, wf), vv) in row.iter().zip(&wfail).zip(&v) {
                    a += x * wf;
                    b += x * vv;
                }
                (a, b)
            })
            .reduce(|| (0.0, 0.0), |x, y| (x.0 + y.0, x.1 + y.1));
        let adj = dropped * jj as f64 + pl.lost * (jj as f64 + 1.0) + pi_tail;
        q.push(qs + adj);
        ev.push(es + adj);
        qdp.push(qs);
        prof[2] += ta.elapsed().as_secs_f64();
        if jj == jmax {
            break;
        }
        // Early exits. Both fill the remaining units with failure probability 1, which
        // is always a valid (pessimistic) value, so the curves stay upper bounds:
        // (a) converged: every later unit would add < 1e-14 over the epoch, far below
        //     the 1e-12 floor, and the min over J already has a unit this good;
        // (b) hopeless: the geometric decay measured over [J/2, J] extrapolates to a
        //     bound above 1 over the epoch even at the last unit (a larger eps than any
        //     table or the dashboard uses by 1000x).
        let conv = k * (qs + adj).max(es + adj) < 1e-14;
        let hopeless = jj >= 400 && jj == jmax / 4 && {
            let a = qdp[jj / 2];
            let rate = if a > 0.0 && qs > 0.0 { (qs / a).powf(1.0 / (jj - jj / 2) as f64) } else { 0.0 };
            rate >= 1.0 || k * qs * rate.powf((jmax - jj) as f64) > 1.0
        };
        if early && (conv || hopeless) {
            if dbg { eprintln!("early exit at J={} of {} ({})", jj, jmax, if conv { "converged" } else { "hopeless" }); }
            q.resize(jmax + 1, 1.0);
            ev.resize(jmax + 1, 1.0);
            break;
        }
        if fine {
            let ta = std::time::Instant::now();
            step_gap(&s, &pl.gap_g1, pl.h, &g, &mut tmp);
            prof[0] += ta.elapsed().as_secs_f64();
            let ta = std::time::Instant::now();
            step(&tmp, &tr, &g, &mut tmp2);
            prof[1] += ta.elapsed().as_secs_f64();
            std::mem::swap(&mut s, &mut tmp2);
        } else {
            step(&s, &tr, &g, &mut tmp);
            std::mem::swap(&mut s, &mut tmp);
        }
    }
    if dbg { eprintln!("dp {:.2}s  (gap {:.2}s, burst {:.2}s, readout {:.2}s)", t0.elapsed().as_secs_f64(), prof[0], prof[1], prof[2]); }
    // ROUNDING. Each DP step computes every entry as a sum of products of
    // nonnegative numbers with at most `terms` terms, so round-to-nearest gives at
    // least (1 - u)^(terms + 1) times the exact value (for the computed inputs).
    // Over J units (2 sub-steps each with fine phases) the computed q_J, ev_J are
    // at least (1 - u)^(J * steps * (terms + 1)) times the exact ones; dividing by
    // that factor makes them upper bounds whatever the rounding.
    {
        let u = f64::EPSILON / 2.0;
        // per entry and step: at most max_items shifted adds, each possibly a sum of
        // up to HMAX + 1 terms (the collapse at column 0), plus the warm collapses and
        // the gap step's sources
        let terms = (tr.max_items as f64 + (AMAX + 2) as f64 * (AMAX + 2) as f64) * (HMAX + 2) as f64
            + (tr.warm.len() * (r + 1)) as f64 + g.w as f64 + 8.0;
        let steps = if fine { 2.0 } else { 1.0 };
        for (jj, (qq, ee)) in q.iter_mut().zip(ev.iter_mut()).enumerate() {
            let fct = (-(jj as f64) * steps * (terms + 1.0) * (1.0 - u).ln()).exp() * (1.0 + 1e-12);
            *qq *= fct;
            *ee *= fct;
        }
    }
    if dbg { eprintln!("phases_bound {:.2}s", t0.elapsed().as_secs_f64()); }
    if let Ok(path) = std::env::var("CB_DUMP") {
        std::fs::write(path, serde_json::to_string(&json!({"q": q, "ev": ev, "V": v, "R": r})).unwrap()).unwrap();
    }
    Analysis { q, ev, k }
}

fn run(cfg: &[f64]) -> Value {
    let (f, beta, delta) = (cfg[0], cfg[1], cfg[2] as usize);
    let cap = if cfg.len() > 3 { cfg[3] as usize } else { 30 };
    let n = if cfg.len() > 4 { cfg[4] } else { 648000.0 };
    let fine = cfg.len() > 5 && cfg[5] != 0.0;
    let p = if cfg.len() > 6 { cfg[6] } else { 0.0 };
    let rule = if cfg.len() > 7 { cfg[7] as usize } else { 0 };
    let wslots = if cfg.len() > 8 { cfg[8] as usize } else { 0 };
    // an explicit slot law `(h, p1, a)` (fields 9-11) replaces the one from `f`, `beta`, `p_late`:
    // a vertex of a band's honest polytope with the adversary at `amax` (`band.py`)
    let law = if cfg.len() > 11 { (cfg[9], cfg[10], cfg[11]) } else { slot_law(f, beta, p) };
    let len = burst_length_law(law, delta);
    let mean = len.mean();
    let jmax = (cap as f64 * 3600.0 / mean) as usize + 50;
    let an = analyse(law, delta, n, jmax, fine, rule, wslots);
    let ths: Vec<(f64, f64)> = geomspace(1e-7, 0.05, 400)
        .into_iter()
        .map(|t| (t, len.log_mgf(t)))
        .filter(|(_, l)| l.is_finite())
        .collect();
    let kfail = 1e-12;
    let blocks = [1usize, 2, 3, 5, 8, 12, 20, 30, 50, 80, 120, 200];
    let mut curve = vec![];
    let mut curve_block = vec![];
    let nq = an.q.len();
    let mut w = 900usize;
    while w <= cap * 3600 {
        let e: Vec<f64> = (0..nq)
            .map(|j| {
                let v = ths
                    .iter()
                    .map(|&(t, l)| (j as f64 + 1.0) * l - t * w as f64)
                    .fold(f64::INFINITY, f64::min);
                v.min(0.0).exp() * (1.0 + 1e-10) // exp/ln rounding (|v| u << 1e-10)
            })
            .collect();
        let (mut bj, mut bv) = (0usize, f64::INFINITY);
        for j in 0..nq {
            let t = an.k * (e[j] + an.q[j]) + kfail;
            if t < bv {
                bv = t;
                bj = j;
            }
        }
        curve.push(json!([w, bv, bj]));
        let (mut bt, mut bj1, mut bm) = (f64::INFINITY, 0usize, 1usize);
        for &mm in &blocks {
            if mm > nq {
                break;
            }
            for j1 in 0..=(nq - mm) {
                let val = e[j1 + mm - 1] + an.ev[j1];
                let t = (an.k / mm as f64).ceil() * val + kfail;
                if t < bt {
                    bt = t;
                    bj1 = j1;
                    bm = mm;
                }
            }
        }
        curve_block.push(json!([w, bt, bj1, bm]));
        w += 900;
    }
    json!({"f": f, "beta": beta, "Delta": delta, "cap": cap, "N": n, "fine": fine, "p_late": p, "rule": rule, "wslots": wslots,
           "law": [law.0, law.1, law.2], "K": an.k,
           "mean_phase": mean, "curve": curve, "curve_block": curve_block})
}

fn main() {
    let mut input = String::new();
    std::io::stdin().read_to_string(&mut input).unwrap();
    let cfgs: Vec<Vec<f64>> = serde_json::from_str(&input).expect("configs");
    let out: Vec<Value> = cfgs
        .par_iter()
        .map(|c| {
            let t = std::time::Instant::now();
            let r = run(c);
            eprintln!("{:?} done in {:.1}s", c, t.elapsed().as_secs_f64());
            r
        })
        .collect();
    println!("{}", serde_json::to_string(&out).unwrap());
}
