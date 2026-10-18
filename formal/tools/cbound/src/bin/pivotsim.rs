//! Monte Carlo of a *pivot* (Nakamoto-block) settlement criterion, after Dembo et
//! al., "Everything is a Race and Nakamoto Always Wins" (CCS 2020), for longest
//! chain and for uncle weight, on the same random strings.
//!
//! A phase end `n` (a quiet point right after a burst) is a **pivot** if every fork
//! loses its race: for all phase ends s < n <= r,
//!
//!     adversarial potential over (s, r]  <  honest growth over (s, r].
//!
//! * Longest chain: potential = A(s, r]; growth = hD per phase.
//! * Uncle weight: potential = A(s - win, r] (withheld forks near the fork point
//!   can be credited) + B(s), the honest blocks the fork may share: those built on
//!   the prefix, i.e. within Delta of the first honest block after s; growth = hD
//!   plus the burst's collision credit c(n) - hD, realized by the next burst if it
//!   starts within `win` of the orphans (uncle-anchored window) or of their parent
//!   (parent-anchored).
//!
//! The extra (shared blocks and withheld forks) needs carriers: at most MAX_UNCLES
//! per adversarial block of the race, none without one (their timing is ignored,
//! which only helps the adversary). Races whose honest lead exceeds the extra by
//! 256 blocks are not followed further (a Monte Carlo shortcut). The certified settlement depth of a
//! target is the distance to the first pivot after it (forward races checked up to
//! the end of the horizon). These criteria are *candidates*, not proven; the
//! longest-chain one calibrates against `recsim`'s LC.
//!
//! usage: pivotsim f beta delta win runs horizon

struct Rng(u64);
impl Rng {
    fn next(&mut self) -> f64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        (self.0 >> 11) as f64 / (1u64 << 53) as f64
    }
}

fn credit(n: i64) -> i64 {
    if n <= 3 {
        return n;
    }
    (1..=n).map(|k| (n + k - 1) / k + k - 1).min().unwrap()
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let f: f64 = a[1].parse().unwrap();
    let beta: f64 = a[2].parse().unwrap();
    let delta: usize = a[3].parse().unwrap();
    let win: usize = a[4].parse().unwrap();
    let runs: usize = a[5].parse().unwrap();
    let horizon: usize = a[6].parse().unwrap();
    let h = 1.0 - (1.0 - f).powf(1.0 - beta);
    let p1 = (1.0 - beta) * (-(1.0 - f).ln()) * (1.0 - f).powf(1.0 - beta);
    let pa = 1.0 - (1.0 - f).powf(beta);
    let names = ["LC pivot (loners)", "LC pivot", "U pivot, no gain", "U pivot, parent-anchored", "U pivot, uncle-anchored"];
    let mut res: Vec<Vec<usize>> = vec![vec![]; names.len()];
    let mut rng = Rng(0x9E3779B97F4A7C15);
    let pre = 4 * win + 4 * delta + 3000;
    let len = pre + horizon;
    for _ in 0..runs {
        let mut hc = vec![0u8; len + 1];
        let mut ad = vec![false; len + 1];
        for s in 1..=len {
            let u = rng.next();
            hc[s] = if u < p1.min(h) { 1 } else if u < h { 2 } else { 0 };
            ad[s] = rng.next() < pa;
        }
        let quiet = |n: usize| (n.saturating_sub(delta) + 1..=n).all(|j| j == 0 || hc[j] == 0);
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
        // phase ends: the quiet points right after a burst (and the start)
        let quiets: Vec<usize> = (1..=len).filter(|&n| quiet(n)).collect();
        let mut ends: Vec<usize> = vec![quiets[0]];
        for w in quiets.windows(2) {
            if (w[0] + 1..=w[1]).any(|s| hc[s] > 0) {
                ends.push(w[1]);
            }
        }
        let k = ends.len();
        // per phase i = (ends[i-1], ends[i]]: A, hD, burst slots
        let mut aa = vec![0i64; k];
        let mut g_lc = vec![0i64; k];
        let mut g_lo = vec![0i64; k];
        let mut g_p = vec![0i64; k];
        let mut g_u = vec![0i64; k];
        let mut first = vec![0usize; k];
        let mut last_h = 0usize;
        let mut pend: Option<(i64, usize, usize)> = None;
        for i in 1..k {
            let (n0, n1) = (ends[i - 1], ends[i]);
            aa[i] = (n0 + 1..=n1).filter(|&s| ad[s]).count() as i64;
            let hs: Vec<usize> = (n0 + 1..=n1).filter(|&s| hc[s] > 0).collect();
            let d = hd(n0, n1);
            g_lc[i] = d;
            // a loner: the burst is one slot with exactly one honest leader
            g_lo[i] = (hs.len() == 1 && hc[hs[0]] == 1) as i64;
            g_p[i] = d;
            g_u[i] = d;
            first[i] = hs[0];
            if let Some((extra, par, orph)) = pend.take() {
                if hs[0] <= par + win {
                    g_p[i] += extra;
                }
                if hs[0] <= orph + win {
                    g_u[i] += extra;
                }
            }
            let n: i64 = hs.iter().map(|&s| hc[s] as i64).sum();
            let extra = (credit(n) - d).max(0);
            if extra > 0 {
                pend = Some((extra, last_h, hs[0]));
            }
            last_h = *hs.last().unwrap();
        }
        // fork-point terms at end j: lookback A(ends[j] - win, ends[j]] and B(j):
        // honest slots within Delta of the first honest slot after ends[j]
        let lb: Vec<i64> = (0..k)
            .map(|j| (ends[j].saturating_sub(win) + 1..=ends[j]).filter(|&s| s > 0 && ad[s]).count() as i64)
            .collect();
        let bsh: Vec<i64> = (0..k)
            .map(|j| {
                if j + 1 >= k {
                    return 0;
                }
                let f0 = first[j + 1];
                (f0..=(f0 + delta).min(len)).map(|s| hc[s] as i64).sum()
            })
            .collect();
        let target_idx = ends.iter().position(|&e| e >= pre).unwrap();
        let target = ends[target_idx];
        for (mi, _) in names.iter().enumerate() {
            let g: &Vec<i64> = match mi {
                0 => &g_lo,
                1 => &g_lc,
                2 => &g_lc,
                3 => &g_p,
                _ => &g_u,
            };
            let uncle = mi > 1 && win > 0;
            // prefix sums of A - G and of A
            let mut cd = vec![0i64; k];
            let mut ca = vec![0i64; k];
            for i in 1..k {
                cd[i] = cd[i - 1] + aa[i] - g[i];
                ca[i] = ca[i - 1] + aa[i];
            }
            let ex = |j: usize| -> i64 { if uncle { lb[j] + bsh[j] } else { 0 } };
            // race from fork end j to end r: A + extra - G, where the extra (shared
            // honest blocks and withheld forks near j) needs carriers: at most
            // maxU per adversarial block of the race, none without one
            let race = |j: usize, r: usize| -> i64 {
                let a = ca[r] - ca[j];
                cd[r] - cd[j] + ex(j).min(4 * a)
            };
            // forward maxima from i: without adversarial slots (A(i, r] = 0) and overall
            let mut piv = None;
            for i in target_idx + 1..k {
                // quick necessary condition without the extra
                let mut ok = true;
                'outer: for j in 0..i {
                    // honest lead from j to i must survive every r >= i
                    for r in i..k {
                        if race(j, r) >= 0 {
                            ok = false;
                            break 'outer;
                        }
                        // beyond the point where the honest lead is safely larger than
                        // any extra plus the adversary's best forward excursion, stop
                        if cd[r] - cd[j] < -(ex(j) + 4 * 64) && r > i + 64 {
                            break;
                        }
                    }
                }
                if ok {
                    piv = Some(i);
                    break;
                }
            }
            res[mi].push(match piv {
                Some(i) => ends[i] - target,
                None => usize::MAX,
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
        println!("{:26} median {:>7}  p90 {:>7}  p99 {:>7}  unsettled {:.3}", name, q(0.5), q(0.9), q(0.99), never);
    }
}
