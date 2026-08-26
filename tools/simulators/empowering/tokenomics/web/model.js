/* The EmPoWering tokenomics model, in the browser.
 *
 * A line-for-line transcription of src/empowering/core.py and the closed forms in
 * sampled.py. It is a second implementation, so it is checked against the first: golden.json
 * carries a grid of inputs with the outputs Python computes, and selfCheck() recomputes every
 * row here and reports agreement. The page shows that result rather than assuming it.
 *
 * Nothing is hardcoded that the config carries -- params.json is generated from the same TOML.
 */

export const P_FIELD = 21888242871839275222246405745257275088548364400416034343698204186575808495617n;

export const M = {
  // --- fees -------------------------------------------------------------------------
  claimFee: (p, price) => (p.claim_tx_bytes + p.claim_tx_gas) * (price ?? p.price_resting)
                          / p.base_units_per_lgo,
  transferFee: (p, price) => (p.transfer_tx_bytes + p.transfer_tx_gas) * (price ?? p.price_resting)
                             / p.base_units_per_lgo,
  phi: (p) => M.claimFee(p),
  psi: (p) => M.transferFee(p) / M.claimFee(p),
  beta: (p) => p.beta_num / p.beta_den,
  rho: (p) => p.rho_num / p.rho_den,
  R0: (p) => p.genesis_pool_fraction * p.S_tge,
  shapeLoad: (p, bytes, gas) => (bytes + gas) / (p.claim_tx_bytes + p.claim_tx_gas),

  // --- pool -------------------------------------------------------------------------
  sigma: (R, p) => (R * p.rho_num) / (p.rho_den * p.T * p.N_b),
  epochRefill: (p, n) => M.beta(p) * p.N_b * (n ?? p.n_tx_ref) * M.transferFee(p),
  rStar: (p, n) => M.epochRefill(p, n) / M.rho(p),
  rMin: (p) => M.phi(p) * p.T * p.N_b / M.rho(p),
  sigmaOverPhi: (p, n) => M.psi(p) * M.beta(p) * (n ?? p.n_tx_ref) / p.T,

  // --- the collapsed fee axis (report 4.9) -------------------------------------------
  feeLoad: (p, n) => M.transferFee(p) * (n ?? p.n_tx_ref) / M.phi(p),
  sigmaOverPhiFromLoad: (p, load) => M.beta(p) * load / p.T,
  minFeeLoad: (p, ratio = 1) => M.beta(p) <= 0 ? Infinity : ratio * p.T / M.beta(p),

  // --- constraints ------------------------------------------------------------------
  builderEdge: (p, n) => {
    const r = M.sigmaOverPhi(p, n);
    return r <= 1 ? Infinity : 1 + p.tip_fraction / (r - 1);
  },
  drainPerBlock: (p) => p.T * p.rho_den / p.rho_num,
  drainSafeT: (p) => p.max_block_txs * p.rho_num / p.rho_den,
  subordinationCap: (p) => {
    const rl = p.subordination_ratio * p.leader_fee_share;
    return rl / (1 + rl);
  },
  subordination: (p) => M.beta(p) / (p.leader_fee_share * (1 - M.beta(p))),
  isoMarginWindow: (p) => {
    if (M.beta(p) <= 0) return [NaN, NaN];
    const ray = p.T / M.beta(p);
    return [M.drainSafeT(p), ray * M.subordinationCap(p)];
  },

  // --- controller -------------------------------------------------------------------
  nextRewardDifficulty: (d, claims, p) => {
    const demand = Math.max(1, (p.P_ema - p.F_ema) * claims + p.F_ema * p.T);
    return Math.min((p.T * d * p.P_ema) / demand, Number.MAX_SAFE_INTEGER);
  },
  reconvergenceBlocks: (p, step = 10, tol = 0.1, limit = 400) => {
    let d = 1.0;                       // difficulty relative to equilibrium; scale cancels
    for (let n = 0; n < limit; n++) {
      const lam = step * p.T * d;
      if (Math.abs(lam - p.T) <= tol * p.T) return n;
      d = d * (p.T * p.P_ema) / Math.max(1, (p.P_ema - p.F_ema) * lam + p.F_ema * p.T);
    }
    return null;
  },

  // --- sampled arrivals, closed forms (report 4.8) ------------------------------------
  rateBias: (p) => (p.P_ema - p.F_ema) / (2 * p.P_ema),
  relSd: (p) => Math.sqrt(2 * p.P_ema / ((p.P_ema + p.F_ema) * p.T)),
  amplification: (p) => Math.sqrt(2 * p.P_ema / (p.P_ema + p.F_ema)),
  epochSd: (p) => Math.sqrt(2 * p.T * p.P_ema ** 2 / (p.P_ema ** 2 - p.F_ema ** 2)),

  // --- trajectories -------------------------------------------------------------------
  simulatePool: (p, epochs, n) => {
    const F = M.epochRefill(p, n), rows = [];
    let R = M.R0(p);
    for (let e = 0; e < epochs; e++) {
      const s = M.sigma(R, p);
      const enabled = s > 0 && R >= s;
      rows.push({ epoch: e, years: e / p.epochs_per_year, pool: R, sigma: s,
                  sigmaOverPhi: s / M.phi(p), enabled });
      R = R - (enabled ? p.T * p.N_b * s : 0) + F;
      if (R < 0) break;
    }
    return rows;
  },
  logisticTraffic: (p, e, years, n0 = 20) => {
    const nMax = p.max_block_txs, em = years * p.epochs_per_year;
    if (em <= 0) return nMax;
    return n0 + (nMax - n0) / (1 + Math.exp(-12 * (e - em / 2) / em));
  },
  peakAdversaryShare: (p, h, honestStake, d0, rows) => {
    rows = rows ?? M.simulatePool(p, p.horizon_epochs);
    let adv = 0, pendA = 0, honest = 0, pendH = 0, peak = 0;
    for (const r of rows) {
      adv += pendA; honest += pendH;
      const d = r.enabled ? p.T * p.N_b * r.sigma : 0;
      pendA = d * h; pendH = d * (1 - h) * honestStake;
      const tot = d0 * p.S_tge + adv + honest;
      if (tot) peak = Math.max(peak, adv / tot);
    }
    return peak;
  },
  adversaryAsymptote: (h, s) => { const den = h + (1 - h) * s; return den ? h / den : 0; },

  // --- blend admission -----------------------------------------------------------------
  blendSeconds: (p, exp) => Math.pow(2, exp ?? p.blend_base_exp) * p.sec_per_candidate,

  // --- emission -------------------------------------------------------------------------
  deflationPrice: (p) => (p.I_max * p.S_tge / p.blocks_per_year * p.base_units_per_lgo)
                         / (p.max_block_txs * (p.transfer_tx_bytes + p.transfer_tx_gas)),
};

/* Poisson by Knuth's method, matching sampled.poisson. */
export function poisson(rng, lam) {
  if (lam <= 0) return 0;
  if (lam > 500) return Math.max(0, Math.round(lam + Math.sqrt(lam) * gauss(rng)));
  const limit = Math.exp(-lam);
  let k = 0, prod = 1;
  for (;;) { prod *= rng(); if (prod <= limit) return k; k++; }
}
function gauss(rng) {
  const u = Math.max(rng(), 1e-12);
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rng());
}
/* mulberry32: a small seeded PRNG, so a run in the panel is reproducible. */
export function seeded(seed) {
  let a = seed >>> 0;
  return () => { a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

/* Block-by-block with Poisson arrivals and the real retarget, mirroring sampled.simulate. */
export function sampleArrivals(p, seed, blocks) {
  const rng = seeded(seed);
  let d = 1.0, sum = 0, sumSq = 0, peak = 0;
  const hist = new Map();
  for (let n = 0; n < blocks; n++) {
    const lam = p.T * d;
    let c = poisson(rng, lam);
    c = Math.min(c, p.max_block_txs);
    sum += c; sumSq += c * c; peak = Math.max(peak, c);
    hist.set(c, (hist.get(c) ?? 0) + 1);
    d = d * (p.T * p.P_ema) / Math.max(1, (p.P_ema - p.F_ema) * c + p.F_ema * p.T);
  }
  const mean = sum / blocks;
  const sd = Math.sqrt(Math.max(0, sumSq / blocks - mean * mean) * blocks / (blocks - 1));
  return { mean, sd, relSd: sd / mean, peak, hist, blocks };
}

/* --- the anti-drift check ----------------------------------------------------------- */
const SENT = { inf: Infinity, "-inf": -Infinity, nan: NaN };
const num = (v) => (typeof v === "string" && v in SENT) ? SENT[v] : v;

export function selfCheck(baseParams, golden) {
  const out = [];
  for (const row of golden.rows) {
    const p = { ...baseParams, ...row.in };
    delete p.n_tx;
    const got = {
      phi_lepta: M.phi(p) * p.base_units_per_lgo, psi: M.psi(p),
      sigma_over_phi: M.sigmaOverPhi(p, row.in.n_tx), fee_load: M.feeLoad(p, row.in.n_tx),
      min_fee_load: M.minFeeLoad(p), r_star: M.rStar(p, row.in.n_tx), r_min: M.rMin(p),
      sigma0_over_phi: M.sigma(M.R0(p), p) / M.phi(p),
      builder_edge: M.builderEdge(p, row.in.n_tx), drain_per_block: M.drainPerBlock(p),
      subordination_cap: M.subordinationCap(p), drain_safe_T: M.drainSafeT(p),
      window_lo: M.isoMarginWindow(p)[0], window_hi: M.isoMarginWindow(p)[1],
      reconverge: M.reconvergenceBlocks(p), rate_bias: M.rateBias(p),
      rel_sd: M.relSd(p), epoch_sd: M.epochSd(p),
      peak_adversary: M.peakAdversaryShare(p, p.adversary_h, 1.0, 0.30),
      asymptote: M.adversaryAsymptote(p.adversary_h, 1.0),
    };
    for (const [k, raw] of Object.entries(row.out)) {
      const want = num(raw), have = got[k];
      let ok;
      if (Number.isNaN(want)) ok = Number.isNaN(have);
      else if (!Number.isFinite(want)) ok = have === want;
      else if (want === null) ok = have === null;
      else ok = Math.abs(have - want) <= 1e-9 * Math.max(1, Math.abs(want));
      if (!ok) out.push({ row: row.in, key: k, want, have });
    }
  }
  return out;
}
