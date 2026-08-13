/* EmPoWering tokenomics panel — every parameter live, no backend.
 *
 * The model lives in model.js (a transcription of the Python); this file is the UI: the
 * control schema, the readouts with their verdicts, and the plots. Plotting is plain canvas
 * so the page has no dependencies and works offline.
 */
import { M, sampleArrivals, selfCheck } from "./model.js";

const C = {                                  // Okabe-Ito, the same set the figures use
  blue: "#0072B2", verm: "#D55E00", green: "#009E73", pink: "#CC79A7",
  orange: "#E69F00", sky: "#56B4E9", ink: "#1b1f23", muted: "#6a737d",
  fail: "#F7D5C4", marginal: "#FBEAC8", works: "#CDE8DE", grid: "#e6e9ec",
};

/* Every parameter the model takes, grouped as the config groups them. `step:0` means the
 * control is an integer. Anything here can be swept by the panel because everything the
 * model reads comes from this object. */
const SCHEMA = [
  ["Proof of work", [
    ["T", "TARGET_CLAIMS_PER_BLOCK", 1, 200, 1],
    ["beta_num", "POW_SHARE (per SHARE_DEN)", 0, 100, 1],
    ["rho_den", "1/ρ  (epochs of reserve)", 10, 500, 1],
    ["genesis_pool_fraction", "R₀ / supply", 0, 0.2, 0.0005],
    ["F_ema", "EMA_SMOOTHING_FACTOR  F", 1, 99, 1],
    ["P_ema", "EMA_SMOOTHING_PRECISION  P", 2, 100, 1],
    ["reward_difficulty_exp", "genesis reward difficulty  p/2^k", 8, 40, 1],
  ]],
  ["Traffic and fees", [
    ["n_tx_ref", "transactions per block", 1, 1024, 1],
    ["price_resting", "price level (lepta per gas)", 1, 100000, 1],
    ["claim_tx_bytes", "claim tx bytes", 50, 2000, 1],
    ["claim_tx_gas", "claim tx gas", 10, 5000, 1],
    ["transfer_tx_bytes", "transfer bytes", 50, 2000, 1],
    ["transfer_tx_gas", "transfer gas", 10, 5000, 1],
  ]],
  ["Consensus and supply", [
    ["N_b", "blocks per epoch", 100, 50000, 1],
    ["max_block_txs", "MAX_BLOCK_TXS", 16, 8192, 1],
    ["S_tge", "launch supply (LGO)", 1e8, 1e12, 1e8],
    ["I_max", "max emission / year", 0, 0.1, 0.001],
  ]],
  ["Economics (ASSUMED)", [
    ["leader_fee_share", "leader share of undiverted fees  L", 0.05, 1, 0.01],
    ["subordination_ratio", "PoW ≤ this × leader share  r", 0.05, 2, 0.01],
    ["tip_fraction", "tip fraction returning to a builder", 0, 1, 0.01],
  ]],
  ["Security and blend", [
    ["adversary_h", "adversary hashrate share  h", 0, 0.9, 0.01],
    ["horizon_epochs", "horizon (epochs)", 10, 3000, 10],
    ["blend_base_exp", "BLEND_DIFFICULTY_BASE  p/2^k", 10, 30, 1],
    ["sec_per_candidate", "seconds per blend candidate", 1e-6, 1e-3, 1e-6],
    ["pi5_cores", "cores on the target board", 1, 16, 1],
  ]],
];

let P = null, BASE = null, GOLDEN = null;
const $ = (id) => document.getElementById(id);
const fmt = (v, d = 2) => !Number.isFinite(v) ? (Number.isNaN(v) ? "—" : "∞")
  : Math.abs(v) >= 1e6 || (Math.abs(v) < 1e-3 && v !== 0)
    ? v.toExponential(2) : v.toLocaleString(undefined, { maximumFractionDigits: d });
const pct = (v, d = 2) => Number.isFinite(v) ? (100 * v).toFixed(d) + " %" : "—";

/* ---------- readouts ---------------------------------------------------------------- */
function verdict(ok, warn) {
  return ok ? ["ok", "✓"] : warn ? ["warn", "!"] : ["bad", "✗"];
}

function readouts() {
  const u = P.base_units_per_lgo;
  const r = M.sigmaOverPhi(P), load = M.feeLoad(P), be = M.minFeeLoad(P);
  const drain = M.drainPerBlock(P), cap = M.subordinationCap(P), sub = M.subordination(P);
  const [lo, hi] = M.isoMarginWindow(P);
  const ints = [];
  if (Number.isFinite(lo) && Number.isFinite(hi))
    for (let t = Math.floor(lo) + 1; t <= Math.floor(hi); t++) ints.push(t);
  const rows = [
    ["σ*/φ — reward over the claim's own fee", fmt(r, 3),
      ...verdict(r >= 2, r >= 1), r >= 2 ? "works" : r >= 1 ? "thin" : "under water"],
    ["fee load Φ̂ (claim fees per block)", fmt(load, 1), ...verdict(load >= be), `break-even ${fmt(be, 0)}`],
    ["builder edge (self-dealing)", fmt(M.builderEdge(P), 3) + "×",
      ...verdict(M.builderEdge(P) <= 1.2, M.builderEdge(P) <= 2), "≤ 1.2× comfortable"],
    ["claim share of traffic", pct(P.T / P.n_tx_ref), ...verdict(P.T / P.n_tx_ref <= M.psi(P) * M.beta(P)),
      `ceiling ψβ = ${pct(M.psi(P) * M.beta(P))}`],
    ["within-epoch drain (claims/block)", fmt(drain, 0),
      ...verdict(drain > P.max_block_txs, true),
      drain > P.max_block_txs ? "impossible by construction" : `reachable — cap ${P.max_block_txs}`],
    ["subordination — PoW vs leader share", pct(sub),
      ...verdict(sub <= P.subordination_ratio, sub <= 1.2 * P.subordination_ratio),
      `cap β = ${pct(cap)}`],
    ["T/β window that also closes the drain", Number.isFinite(lo) ? `(${fmt(lo, 2)}, ${fmt(hi, 2)}]` : "—",
      ...verdict(ints.length > 0, true), ints.length ? `integers ${ints.join(", ")}` : "none"],
    ["φ — claim fee", fmt(M.phi(P) * u, 0) + " lepta", "ok", "", `ψ = ${fmt(M.psi(P), 3)}`],
    ["R₀ / R* — endowment over fixed point", fmt(M.R0(P) / M.rStar(P), 0) + "×", "ok", "",
      `R* ${fmt(M.rStar(P), 0)} LGO, R_min ${fmt(M.rMin(P), 0)}`],
    ["σ₀/φ — reward at genesis", fmt(M.sigma(M.R0(P), P) / M.phi(P), 0) + "×", "ok", "",
      "decays toward σ*/φ"],
    ["controller reconvergence (10× step)", (M.reconvergenceBlocks(P) ?? "never") + " blocks",
      ...verdict(M.reconvergenceBlocks(P) !== null), `pole F/P = ${fmt(P.F_ema / P.P_ema, 3)}`],
    ["arrival noise 1/√T · amplified", pct(M.relSd(P), 1), "ok", "",
      `retarget overshoot +${pct(M.rateBias(P) / P.T, 2)}`],
    ["peak adversary share (D₀ = 30 %)", pct(M.peakAdversaryShare(P, P.adversary_h, 1, 0.30)),
      ...verdict(M.peakAdversaryShare(P, P.adversary_h, 1, 0.30) < 1 / 3),
      `asymptote ${pct(M.adversaryAsymptote(P.adversary_h, 1), 0)}`],
    ["blend admission — one target core", fmt(M.blendSeconds(P), 1) + " s",
      ...verdict(M.blendSeconds(P) >= 30 && M.blendSeconds(P) <= 120, true),
      `${fmt(86400 / M.blendSeconds(P), 0)} msgs/day`],
  ];
  $("readouts").innerHTML = rows.map(([k, v, cls, mark, note]) =>
    `<tr class="${cls}"><td>${k}</td><td class="v">${v}</td>
     <td class="m">${mark}</td><td class="n">${note}</td></tr>`).join("");
}

/* ---------- plotting ----------------------------------------------------------------- */
function plot(id, draw) {
  const cv = $(id), dpr = window.devicePixelRatio || 1;
  const w = cv.clientWidth, h = cv.clientHeight;
  cv.width = w * dpr; cv.height = h * dpr;
  const g = cv.getContext("2d");
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, w, h);
  const pad = { l: 62, r: 14, t: 24, b: 40 };
  draw(g, { w, h, pad, iw: w - pad.l - pad.r, ih: h - pad.t - pad.b });
}

function axes(g, b, opts) {
  const { xlab, ylab, xs, ys, xlog, ylog, title } = opts;
  const X = (v) => b.pad.l + ((xlog ? Math.log10(v) - Math.log10(xs[0]) : v - xs[0])
    / (xlog ? Math.log10(xs[1] / xs[0]) : xs[1] - xs[0])) * b.iw;
  const Y = (v) => b.pad.t + b.ih - ((ylog ? Math.log10(Math.max(v, 1e-12)) - Math.log10(ys[0])
    : v - ys[0]) / (ylog ? Math.log10(ys[1] / ys[0]) : ys[1] - ys[0])) * b.ih;
  g.strokeStyle = C.grid; g.lineWidth = 1; g.font = "11px system-ui"; g.fillStyle = C.muted;
  const ticks = (lo, hi, log) => {
    if (!log) { const o = []; for (let i = 0; i <= 4; i++) o.push(lo + (hi - lo) * i / 4); return o; }
    const o = []; for (let e = Math.ceil(Math.log10(lo)); e <= Math.floor(Math.log10(hi)); e++)
      o.push(10 ** e); return o;
  };
  for (const t of ticks(ys[0], ys[1], ylog)) {
    const y = Y(t); g.beginPath(); g.moveTo(b.pad.l, y); g.lineTo(b.pad.l + b.iw, y); g.stroke();
    g.textAlign = "right"; g.fillText(ylog ? t.toExponential(0) : fmt(t, 2), b.pad.l - 6, y + 4);
  }
  for (const t of ticks(xs[0], xs[1], xlog)) {
    const x = X(t); g.beginPath(); g.moveTo(x, b.pad.t); g.lineTo(x, b.pad.t + b.ih); g.stroke();
    g.textAlign = "center"; g.fillText(xlog ? t.toExponential(0) : fmt(t, 2), x, b.pad.t + b.ih + 16);
  }
  g.fillStyle = C.ink; g.textAlign = "center"; g.font = "12px system-ui";
  g.fillText(xlab, b.pad.l + b.iw / 2, b.h - 6);
  g.save(); g.translate(14, b.pad.t + b.ih / 2); g.rotate(-Math.PI / 2);
  g.fillText(ylab, 0, 0); g.restore();
  if (title) { g.textAlign = "left"; g.font = "600 12px system-ui";
    g.fillText(title, b.pad.l, 15); }
  return { X, Y };
}

function line(g, pts, colour, width = 2, dash = []) {
  g.save(); g.setLineDash(dash); g.strokeStyle = colour; g.lineWidth = width;
  g.beginPath(); pts.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y));
  g.stroke(); g.restore();
}

const PLOTS = {
  pool: (g, b) => {
    const rows = M.simulatePool(P, Math.round(40 * P.epochs_per_year));
    const ys = [Math.max(1e-3, M.rMin(P) / 4), Math.max(M.R0(P), M.rStar(P)) * 2];
    const a = axes(g, b, { xlab: "years from genesis", ylab: "reward pool (LGO)",
      xs: [0, 40], ys, ylog: true, title: "Pool trajectory" });
    line(g, rows.map(r => [a.X(r.years), a.Y(r.pool)]), C.blue);
    line(g, [[a.X(0), a.Y(M.rStar(P))], [a.X(40), a.Y(M.rStar(P))]], C.green, 1.5, [6, 4]);
    line(g, [[a.X(0), a.Y(M.rMin(P))], [a.X(40), a.Y(M.rMin(P))]], C.verm, 1.5, [2, 3]);
    g.fillStyle = C.muted; g.font = "10px system-ui"; g.textAlign = "right";
    g.fillText(`R* ${fmt(M.rStar(P), 0)}`, b.pad.l + b.iw - 4, a.Y(M.rStar(P)) - 4);
    g.fillText(`R_min ${fmt(M.rMin(P), 0)}`, b.pad.l + b.iw - 4, a.Y(M.rMin(P)) - 4);
  },
  reward: (g, b) => {
    const rows = M.simulatePool(P, Math.round(40 * P.epochs_per_year));
    const top = Math.max(rows[0].sigmaOverPhi, 10) * 2;
    const a = axes(g, b, { xlab: "years from genesis", ylab: "σₑ / φ",
      xs: [0, 40], ys: [0.1, top], ylog: true, title: "Reward per claim, against its own fee" });
    line(g, rows.map(r => [a.X(r.years), a.Y(r.sigmaOverPhi)]), C.blue);
    line(g, [[a.X(0), a.Y(1)], [a.X(40), a.Y(1)]], C.verm, 1.5, [2, 3]);
    line(g, [[a.X(0), a.Y(M.sigmaOverPhi(P))], [a.X(40), a.Y(M.sigmaOverPhi(P))]], C.green, 1.5, [6, 4]);
  },
  fee: (g, b) => {
    const be = M.minFeeLoad(P), hi = Math.max(be * 20, M.feeLoad(P) * 3, 100);
    const a = axes(g, b, { xlab: "fee load Φ̂ (claim fees per block)", ylab: "σ*/φ",
      xs: [1, hi], ys: [0.02, 60], xlog: true, ylog: true, title: "Working fee range" });
    for (const [x0, x1, col] of [[1, be, C.fail], [be, 2 * be, C.marginal], [2 * be, hi, C.works]]) {
      if (!Number.isFinite(x1)) continue;
      g.fillStyle = col; g.fillRect(a.X(x0), b.pad.t, Math.max(0, a.X(x1) - a.X(x0)), b.ih);
    }
    const pts = []; for (let i = 0; i <= 200; i++) {
      const x = 1 * Math.pow(hi, i / 200);
      pts.push([a.X(x), a.Y(M.sigmaOverPhiFromLoad(P, x))]);
    }
    line(g, pts, C.blue, 2.4);
    const L = M.feeLoad(P);
    g.fillStyle = C.ink; g.beginPath(); g.arc(a.X(L), a.Y(M.sigmaOverPhi(P)), 5, 0, 7); g.fill();
  },
  plane: (g, b) => {
    const a = axes(g, b, { xlab: "T", ylab: "β  (%)", xs: [1, 60], ys: [0.5, 30],
      title: "T–β plane: economics sees only the ratio" });
    const cap = 100 * M.subordinationCap(P), tD = M.drainSafeT(P);
    // feasible: sigma*/phi >= 2, beta <= cap, T > drain-safe
    g.fillStyle = C.works;
    for (let px = 0; px < b.iw; px += 2) {
      const T = 1 + (60 - 1) * px / b.iw;
      if (T <= tD) continue;
      const bLo = 100 * 2 * T / (M.psi(P) * P.n_tx_ref);
      if (bLo >= cap) continue;
      g.fillRect(b.pad.l + px, a.Y(cap), 2, Math.max(0, a.Y(bLo) - a.Y(cap)));
    }
    line(g, [[a.X(tD), b.pad.t], [a.X(tD), b.pad.t + b.ih]], C.pink, 2);
    line(g, [[b.pad.l, a.Y(cap)], [b.pad.l + b.iw, a.Y(cap)]], C.verm, 2, [7, 4]);
    const ray = P.T / M.beta(P);
    line(g, [[a.X(1), a.Y(100 * 1 / ray)], [a.X(60), a.Y(100 * 60 / ray)]], C.muted, 1.5, [3, 3]);
    g.fillStyle = C.ink; g.beginPath();
    g.arc(a.X(P.T), a.Y(100 * M.beta(P)), 6, 0, 7); g.fill();
    g.font = "10px system-ui"; g.fillStyle = C.muted; g.textAlign = "left";
    g.fillText(`drain safe T > ${fmt(tD, 2)}`, a.X(tD) + 4, b.pad.t + 12);
    g.fillText(`subordination cap ${cap.toFixed(2)} %`, b.pad.l + 6, a.Y(cap) - 5);
  },
  controller: (g, b) => {
    const a = axes(g, b, { xlab: "blocks", ylab: "claims per block", xs: [0, 80],
      ys: [0.5, Math.max(200, 20 * P.T)], ylog: true, title: "Reward difficulty recovery" });
    [[100, C.blue], [10, C.verm], [0.1, C.green], [0.01, C.pink]].forEach(([mult, col]) => {
      let d = mult; const pts = [];
      for (let n = 0; n < 80; n++) {
        const c = Math.min(Math.max(0, Math.round(P.T * d)), P.max_block_txs);
        pts.push([a.X(n), a.Y(Math.max(c, 0.5))]);
        d = d * (P.T * P.P_ema) / Math.max(1, (P.P_ema - P.F_ema) * c + P.F_ema * P.T);
      }
      line(g, pts, col, 1.8);
    });
    line(g, [[a.X(0), a.Y(P.T)], [a.X(80), a.Y(P.T)]], C.muted, 1.5, [5, 4]);
  },
  arrivals: (g, b) => {
    const s = sampleArrivals(P, 12345, 60000);
    const keys = [...s.hist.keys()].sort((x, y) => x - y);
    const hi = Math.max(keys[keys.length - 1], P.T * 2), maxc = Math.max(...s.hist.values());
    const a = axes(g, b, { xlab: "claims in a block", ylab: "blocks", xs: [0, hi],
      ys: [0, maxc * 1.08], title: `Sampled arrivals — sd ${(100 * s.relSd).toFixed(1)} %, mean ${s.mean.toFixed(3)}` });
    g.fillStyle = C.blue;
    for (const k of keys) {
      const x0 = a.X(k - 0.45), x1 = a.X(k + 0.45);
      g.fillRect(x0, a.Y(s.hist.get(k)), Math.max(1, x1 - x0), a.Y(0) - a.Y(s.hist.get(k)));
    }
    line(g, [[a.X(P.T), b.pad.t], [a.X(P.T), b.pad.t + b.ih]], C.verm, 2, [5, 4]);
    line(g, [[a.X(s.mean), b.pad.t], [a.X(s.mean), b.pad.t + b.ih]], C.green, 2);
  },
  sweep: (g, b) => {
    const axis = $("sweepAxis").value;
    const spec = { T: [1, 120, "T"], beta_num: [0, 60, "β numerator"],
      rho_den: [10, 400, "1/ρ"], n_tx_ref: [1, 1024, "transactions per block"],
      genesis_pool_fraction: [0, 0.1, "R₀ / supply"] }[axis];
    const [lo, hi, lab] = spec;
    const pts = [], edge = [];
    for (let i = 0; i <= 240; i++) {
      const v = lo + (hi - lo) * i / 240;
      const q = { ...P, [axis]: axis === "genesis_pool_fraction" ? v : Math.round(v) };
      pts.push([v, M.sigmaOverPhi(q)]);
      edge.push([v, Math.min(M.builderEdge(q), 20)]);
    }
    const a = axes(g, b, { xlab: lab, ylab: "σ*/φ  (blue) · builder edge (orange)",
      xs: [lo, hi], ys: [0.05, 60], ylog: true, title: `Sweep: ${lab}` });
    line(g, pts.map(([x, y]) => [a.X(x), a.Y(Math.max(y, 1e-3))]), C.blue, 2.2);
    line(g, edge.map(([x, y]) => [a.X(x), a.Y(Math.max(y, 1e-3))]), C.orange, 1.8, [5, 3]);
    line(g, [[a.X(lo), a.Y(1)], [a.X(hi), a.Y(1)]], C.verm, 1.4, [2, 3]);
    const cur = P[axis];
    line(g, [[a.X(cur), b.pad.t], [a.X(cur), b.pad.t + b.ih]], C.ink, 1.2, [4, 3]);
  },
};

function redraw() {
  readouts();
  for (const id of Object.keys(PLOTS)) plot(id, PLOTS[id]);
}

/* ---------- controls ------------------------------------------------------------------ */
function buildControls() {
  $("controls").innerHTML = SCHEMA.map(([group, items]) => `
    <fieldset><legend>${group}</legend>${items.map(([key, label, min, max, step]) => `
      <label class="ctl" title="${key}">
        <span class="lab">${label}</span>
        <input type="range" id="r_${key}" min="${min}" max="${max}" step="${step}" value="${P[key]}">
        <input type="number" id="n_${key}" min="${min}" max="${max}" step="${step}" value="${P[key]}">
      </label>`).join("")}</fieldset>`).join("");
  for (const [, items] of SCHEMA) for (const [key] of items) {
    const r = $(`r_${key}`), n = $(`n_${key}`);
    const set = (v) => { P[key] = Number(v); r.value = v; n.value = v; redraw(); };
    r.addEventListener("input", (e) => set(e.target.value));
    n.addEventListener("input", (e) => set(e.target.value));
  }
}

function syncControls() {
  for (const [, items] of SCHEMA) for (const [key] of items) {
    const r = $(`r_${key}`), n = $(`n_${key}`);
    if (r) { r.value = P[key]; n.value = P[key]; }
  }
}

/* ---------- boot ----------------------------------------------------------------------- */
async function boot() {
  const [params, golden] = await Promise.all([
    fetch("params.json").then(r => r.json()),
    fetch("golden.json").then(r => r.json()),
  ]);
  BASE = params; GOLDEN = golden; P = { ...params };
  buildControls();

  const fails = selfCheck(BASE, GOLDEN);
  const n = GOLDEN.rows.length * Object.keys(GOLDEN.rows[0].out).length;
  $("selfcheck").className = fails.length ? "badge bad" : "badge ok";
  $("selfcheck").textContent = fails.length
    ? `self-check FAILED — ${fails.length} of ${n} values differ from the Python model`
    : `self-check passed — all ${n} values agree with the Python model (config: ${GOLDEN.config})`;
  if (fails.length) console.table(fails.slice(0, 40));

  $("reset").addEventListener("click", () => { P = { ...BASE }; syncControls(); redraw(); });
  $("t11").addEventListener("click", () => {
    P = { ...P, T: 11, beta_num: Math.round(P.beta_den * 11 * M.beta(BASE) / BASE.T) };
    syncControls(); redraw();
  });
  $("sweepAxis").addEventListener("change", redraw);
  window.addEventListener("resize", redraw);
  redraw();
}
boot();
