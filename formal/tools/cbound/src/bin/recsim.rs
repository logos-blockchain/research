//! Monte Carlo of phase *recurrences* (not of an attack), on the same random
//! strings:
//!
//! * `LC`: the longest-chain recurrence (Cryptarchia/Settle/Recurrence.lean);
//! * `U-proven`: the weighted recurrence proven with honest progress `hD` only
//!   (CryptarchiaU/Settle/WReach.lean);
//! * `U-HI`: a candidate under honest uncle inclusion (an honest block credits every
//!   eligible honest block it knows): the lookback counts adversarial slots only;
//! * `U-HI+gain`: also the gain: a burst of n honest slots adds `credit(n)`, realized
//!   by the next honest block if it is within the window of the orphans' parent. In
//!   the cold margin step only (`U-HI+gain`), or in the reach step too (`...+R`).
//!
//! The candidates are *not proven*: they say what a proof under HI could certify.
//!
//! For each run: a target slot, the reach/margin bounds from there on, and the first
//! phase end after which the margin stays cold (the settlement depth certified on
//! this string). Prints quantiles, in blocks.
//!
//! usage: recsim f beta delta win runs horizon [lookback_windows=2]

struct Rng(u64);
impl Rng {
    fn next(&mut self) -> f64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        (self.0 >> 11) as f64 / (1u64 << 53) as f64
    }
}

/// Adversary-optimal credited count of a burst of n honest slots.
fn credit(n: i64) -> i64 {
    if n <= 3 {
        return n;
    }
    (1..=n).map(|k| (n + k - 1) / k + k - 1).min().unwrap()
}

#[derive(Clone, Copy, PartialEq)]
enum Mode {
    Lc,
    Proven,
    Hi,
    HiGain,
    HiGainR,
    HiGainU,
    Local,
    Parent,
    ParentDp,
    ParentExact,
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let f: f64 = a[1].parse().unwrap();
    let beta: f64 = a[2].parse().unwrap();
    let delta: usize = a[3].parse().unwrap();
    let win: usize = a[4].parse().unwrap();
    let runs: usize = a[5].parse().unwrap();
    let horizon: usize = a[6].parse().unwrap();
    let lbw: usize = a.get(7).map(|x| x.parse().unwrap()).unwrap_or(2);
    // slot law: P(>= 1 honest leader), P(exactly one), P(adversarial leader)
    let h = 1.0 - (1.0 - f).powf(1.0 - beta);
    let p1 = (1.0 - beta) * (-(1.0 - f).ln()) * (1.0 - f).powf(1.0 - beta);
    let pa = 1.0 - (1.0 - f).powf(beta);
    let modes = [Mode::Lc, Mode::Proven, Mode::Hi, Mode::HiGain, Mode::HiGainR, Mode::HiGainU, Mode::Local, Mode::Parent, Mode::ParentDp, Mode::ParentExact];
    let names = ["LC", "U-proven", "U-HI", "U-HI+gain", "U-HI+gain (also R)", "U-HI+gain, uncle-anchored", "fork-local uncle weight", "credit to uncle parent", "parent credit, DP-pessimistic", "parent credit, exact carriers"];
    let mut res: Vec<Vec<usize>> = vec![vec![]; modes.len()];
    let mut rng = Rng(0x9E3779B97F4A7C15);
    let pre = 4 * win + 4 * delta + 400;
    let len = pre + horizon;
    for _ in 0..runs {
        let mut hc = vec![0u8; len + 1];
        let mut ad = vec![false; len + 1];
        for s in 1..=len {
            let u = rng.next();
            hc[s] = if u < p1.min(h) { 1 } else if u < h { 2 } else { 0 };
            ad[s] = rng.next() < pa;
        }
        let occ = |s: usize| hc[s] > 0 || ad[s];
        let quiet = |n: usize| (n.saturating_sub(delta) + 1..=n).all(|j| j == 0 || hc[j] == 0);
        let ends: Vec<usize> = (1..=len).filter(|&n| quiet(n)).collect();
        let hd = |n0: usize, n1: usize| -> i64 {
            let mut b = n1;
            let mut c = 0;
            while b > n0 {
                if hc[b] > 0 {
                    c += 1;
                    if b < delta + 1 {
                        break;
                    }
                    b -= delta + 1;
                } else {
                    b -= 1;
                }
            }
            c
        };
        // per phase quantities
        struct Ph {
            n0: usize,
            aa: i64,
            hs: Vec<usize>,
            hdd: i64,
            x_occ: i64,
            x_adv: i64,
            single: bool,
            gain: i64, // realized pending credit (beyond hD) in this phase
            gain_u: i64, // the same with the window anchored at the uncle
            a_tail: i64, // adversarial slots after the last honest slot, up to n0
            gain_d: i64, // realized gain, assuming the burst spanned (m-1) Delta
            nsum: i64, // honest leaders in the burst
            carriers: i64, // adversarial slots within the window after the burst's first honest slot
            nfirst: i64, // honest leaders within Delta of the burst's first honest slot (built on the tip)
        }
        let mut phs: Vec<Ph> = vec![];
        let mut last_honest: usize = 0; // last honest slot seen
        let mut pending: Option<(i64, usize, usize)> = None;
        let mut pend_d: Option<(i64, usize)> = None; // (extra, deadline for the next burst's first slot) // (extra credit, orphans' parent label, first orphan label)
        for wdw in ends.windows(2) {
            let (n0, n1) = (wdw[0], wdw[1]);
            let aa = (n0 + 1..=n1).filter(|&s| ad[s]).count() as i64;
            let hs: Vec<usize> = (n0 + 1..=n1).filter(|&s| hc[s] > 0).collect();
            let hdd = hd(n0, n1);
            let lo = n0.saturating_sub(lbw * win);
            let x_occ = (lo + 1..=n0).filter(|&s| occ(s)).count() as i64;
            let x_adv = (lo + 1..=n0).filter(|&s| ad[s]).count() as i64;
            let single = aa == 0 && hs.len() == 1 && hc[hs[0]] == 1;
            let a_tail = (last_honest + 1..=n0).filter(|&s| ad[s]).count() as i64;
            let mut gain = 0;
            let mut gain_u = 0;
            let mut gain_d = 0;
            let nsum: i64 = hs.iter().map(|&s| hc[s] as i64).sum();
            let nfirst: i64 = match hs.first() {
                Some(&f0) => hs.iter().filter(|&&s| s <= f0 + delta).map(|&s| hc[s] as i64).sum(),
                None => 0,
            };
            let carriers = match hs.first() {
                Some(&f0) => (f0 + 1..=(f0 + win).min(len)).filter(|&s| ad[s]).count() as i64,
                None => 0,
            };
            if let Some(&first) = hs.first() {
                if let Some((extra, dl)) = pend_d.take() {
                    if first <= dl {
                        gain_d = extra;
                    }
                }
                if let Some((extra, par, orph)) = pending.take() {
                    if first <= par + win {
                        gain = extra;
                    }
                    // every orphan is at or after the burst's first honest slot
                    if first <= orph + win {
                        gain_u = extra;
                    }
                }
                // this burst's credit beyond hD, pending on the next honest block
                let n: i64 = hs.iter().map(|&s| hc[s] as i64).sum();
                let extra = (credit(n) - hdd).max(0);
                if extra > 0 {
                    pending = Some((extra, last_honest, hs[0]));
                    let lastb = *hs.last().unwrap();
                    let span = (hs.len() - 1) * delta;
                    if lastb + win >= span {
                        pend_d = Some((extra, lastb + win - span));
                    }
                }
                last_honest = *hs.last().unwrap();
            }
            phs.push(Ph { n0, aa, hs, hdd, x_occ, x_adv, single, gain, gain_u, a_tail, gain_d, nsum, carriers, nfirst });
        }
        for (mi, &mode) in modes.iter().enumerate() {
            let (mut r, mut m): (i64, i64) = (0, 0);
            let mut target: Option<usize> = None;
            let mut cold_since: Option<usize> = None;
            let mut pend: Option<i64> = None;
            let mut share: Option<usize> = None;
            for p in &phs {
                let uncle = !matches!(mode, Mode::Lc | Mode::Local | Mode::Parent | Mode::ParentDp | Mode::ParentExact);
                let gain_m = matches!(mode, Mode::HiGain | Mode::HiGainR);
                let gain_r = mode == Mode::HiGainR;
                let x = match mode {
                    Mode::Proven => p.x_occ,
                    _ => p.x_adv,
                };
                let gv = if mode == Mode::ParentDp { p.gain_d } else if matches!(mode, Mode::HiGainU | Mode::Local | Mode::Parent | Mode::ParentExact) { p.gain_u } else { p.gain };
                let gg = matches!(mode, Mode::HiGainU | Mode::Local | Mode::Parent | Mode::ParentDp | Mode::ParentExact);
                let g_r = p.hdd + if gain_r || gg { gv } else { 0 };
                let g_m = p.hdd + if gain_m || gg { gv } else { 0 };
                let newr = if p.hs.is_empty() {
                    r + p.aa - g_r
                } else if uncle {
                    // potential beyond the anchor's weight: adversarial slots of the
                    // lookback and the phase, and the phase's other honest slots
                    // (attached, not yet credited; none without a window)
                    let hon_other = if win > 0 { p.hs.len() as i64 - 1 } else { 0 };
                    (r + p.aa - g_r).max(x + p.aa + hon_other)
                } else if mode == Mode::ParentExact {
                    let sh = if win > 0 { p.nfirst.min(4 * p.carriers) } else { 0 };
                    (r + p.aa - g_r).max(p.aa).max(p.a_tail + p.aa + sh - g_r)
                } else if mode == Mode::ParentDp {
                    // any chain can gain the honest blocks of the phase attached to it,
                    // with carriers (the fork's one-time share, at most once per chain)
                    // forks at the honest tip share the burst's honest blocks (counted at
                    // once, carriers ignored); they start from the tip's reach, the
                    // adversarial slots since the last honest slot
                    let sh = if win > 0 { p.nsum.min(4 * p.carriers) } else { 0 };
                    (r + p.aa - g_r).max(p.aa).max(p.a_tail + p.aa + sh - g_r)
                } else if mode == Mode::Parent {
                    // a fork at the honest tip gains the next honest block (if it has a
                    // carrier) and can use the adversarial slots since the tip
                    (r + p.aa - g_r).max(if win > 0 && p.aa > 0 { p.aa + p.a_tail } else { p.aa })
                } else {
                    (r + p.aa - g_r).max(p.aa)
                };
                if target.is_none() && p.n0 >= pre {
                    target = Some(p.n0);
                    m = r;
                }
                if let Some(tg) = target {
                    let after = p.hs.first().map_or(false, |&s| s > tg);
                    let cold = m + p.aa + 1 <= 0;
                    let mut nm = if cold {
                        let mut v = m + p.aa - g_m;
                        if mode == Mode::ParentDp && share.is_some() && p.aa > 0 {
                            v += 1;
                            share = None;
                        }
                        if matches!(mode, Mode::Parent | Mode::ParentExact) {
                            if let Some(exp) = share {
                                if p.aa > 0 && p.n0 < exp {
                                    v += 1;
                                    share = None;
                                } else if p.n0 >= exp {
                                    share = None;
                                }
                            }
                        }
                        v
                    } else if p.single && after {
                        if matches!(mode, Mode::Parent | Mode::ParentDp | Mode::ParentExact) && win > 0 {
                            share = Some(p.hs[0] + win);
                        }
                        if uncle && win > 0 { r - p.hdd + 1 } else { r - p.hdd }
                    } else {
                        newr
                    };
                    // two-phase crossing (margin_cross2): two single-honest bursts after
                    // the target with no adversarial slot from the first to the second
                    // (gaps in between allowed), from a reach <= 0 before the first
                    if p.hs.is_empty() {
                        if p.aa > 0 {
                            pend = None;
                        }
                    } else if p.single && after {
                        if uncle && win > 0 {
                            if let Some(r_pp) = pend {
                                if r_pp <= 0 {
                                    nm = nm.min(r_pp - 1 - p.hdd + 1);
                                }
                            }
                        }
                        pend = Some(r);
                    } else {
                        pend = None;
                    }
                    nm = nm.min(newr);
                    if !cold {
                        cold_since = None;
                    } else if cold_since.is_none() {
                        cold_since = Some(p.n0);
                    }
                    m = nm;
                }
                r = newr;
            }
            res[mi].push(match (cold_since, target) {
                (Some(c), Some(t)) => c - t,
                _ => usize::MAX,
            });
        }
    }
    for (name, v) in names.iter().zip(res.iter_mut()) {
        v.sort();
        let q = |p: f64| {
            let x = v[((v.len() as f64 * p) as usize).min(v.len() - 1)];
            if x == usize::MAX { "never".to_string() } else { format!("{:.1}", x as f64 * f) }
        };
        let never = v.iter().filter(|&&x| x == usize::MAX).count() as f64 / v.len() as f64;
        println!("{:20} median {:>7}  p90 {:>7}  p99 {:>7}  unsettled {:.3}", name, q(0.5), q(0.9), q(0.99), never);
    }
}
