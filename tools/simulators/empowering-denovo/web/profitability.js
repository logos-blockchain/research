/* Mining profitability, computed live.
 *
 *   cost_usd_per_claim    = candidates_per_claim * wh_per_candidate / 1000 * electricity
 *   revenue_usd_per_claim = (reward - claim_fee) / 1e9 * token_price
 *   break_even_token      = cost / ((reward - claim_fee) / 1e9)
 *
 * Every input but the token price is measured or derived; profitability.json carries the
 * device profiles, the difficulty floor and the stylised price paths, all generated from the
 * same Python the reports use.
 */
const D = await (await fetch("profitability.json")).json();
const FIELD = BigInt(D.field_modulus);
const FLOOR = BigInt(D.genesis_difficulty_target);

const state = {
  device: "pi5-board",
  electricity: D.reference_electricity_usd_per_kwh,
  difficultyMult: 1,          // multiples of the bootstrap floor (higher = harder)
  reward: "anchor",
  refPrice: 1.00,             // USD per LGO at the curves' 1.0 mark
};

const rewardLepta = () =>
  state.reward === "opening" ? D.opening_reward_lepta : D.anchor_lepta;
const netLgo = () => Math.max(0, rewardLepta() - D.claim_fee_lepta) / 1e9;
const device = () => D.devices.find((d) => d.key === state.device);

// candidates per claim = modulus / target, and the target is the floor divided by the multiple
const candidatesPerClaim = () =>
  Number(FIELD / (FLOOR / BigInt(Math.max(1, Math.round(state.difficultyMult)))));

const costPerClaim = () =>
  candidatesPerClaim() * device().wh_per_candidate / 1000 * state.electricity;
const revenuePerClaim = (tok) => netLgo() * tok;
const breakEven = () => (netLgo() > 0 ? costPerClaim() / netLgo() : Infinity);

// ---- controls ---------------------------------------------------------------------------
function buildControls() {
  const host = document.getElementById("controls");
  const devOpts = D.devices.map((d) =>
    `<option value="${d.key}"${d.key === state.device ? " selected" : ""}>${d.label}</option>`).join("");
  host.innerHTML = `
    <fieldset><legend>the miner</legend>
      <div class="ctl"><span class="lab">device profile (measured)</span>
        <select id="device">${devOpts}</select></div>
      <div class="ctl"><span class="lab">electricity, USD per kWh</span>
        <input type="range" id="r_elec" min="0.02" max="0.60" step="0.01">
        <input type="number" id="n_elec" min="0.02" max="0.60" step="0.01"></div>
      <div class="ctl"><span class="lab">difficulty, × the bootstrap floor</span>
        <input type="range" id="r_diff" min="1" max="500" step="1">
        <input type="number" id="n_diff" min="1" max="500" step="1"></div>
    </fieldset>
    <fieldset><legend>the reward</legend>
      <div class="ctl"><span class="lab">which reward</span>
        <select id="reward">
          <option value="opening"${state.reward === "opening" ? " selected" : ""}>bootstrap, opening (11.87 LGO)</option>
          <option value="anchor"${state.reward === "anchor" ? " selected" : ""}>post-phase, the anchor (11,158 lepta)</option>
        </select></div>
      <div class="ctl"><span class="lab">reference token price, USD per LGO</span>
        <input type="range" id="r_ref" min="0.001" max="5" step="0.001">
        <input type="number" id="n_ref" min="0.001" max="5" step="0.001"></div>
    </fieldset>`;
  host.querySelector("#device").onchange = (e) => { state.device = e.target.value; render(); };
  host.querySelector("#reward").onchange = (e) => { state.reward = e.target.value; render(); };
  for (const [key, prop] of [["elec", "electricity"], ["diff", "difficultyMult"], ["ref", "refPrice"]])
    for (const pre of ["r_", "n_"])
      host.querySelector(`#${pre}${key}`).addEventListener("input", (e) => {
        state[prop] = Number(e.target.value); render();
      });
}

const fmt = (x, d = 2) => x.toLocaleString("en-US", { maximumFractionDigits: d });
const usd = (x) => (Math.abs(x) < 0.01 ? `$${x.toExponential(2)}` : `$${fmt(x, 4)}`);

function row(tb, cls, label, value, note) {
  const tr = document.createElement("tr");
  tr.className = cls;
  const mark = cls === "ok" ? "✓" : cls === "bad" ? "✕" : cls === "warn" ? "△" : "";
  tr.innerHTML = `<td>${label}</td><td class="v">${value}</td><td class="m">${mark}</td><td class="n">${note}</td>`;
  tb.appendChild(tr);
}

function underwater() {
  const cost = costPerClaim();
  return D.curves.map((c) => ({
    label: c.label,
    frac: c.points.filter((p) => revenuePerClaim(p * state.refPrice) < cost).length
          / c.points.length,
  }));
}

function renderReadouts() {
  const tb = document.getElementById("readouts");
  tb.innerHTML = "";
  const cost = costPerClaim(), be = breakEven(), rev = revenuePerClaim(state.refPrice);
  row(tb, "", "candidates per claim", fmt(candidatesPerClaim(), 0),
      `at ${fmt(state.difficultyMult, 0)}× the bootstrap floor`);
  row(tb, "", "electricity per claim", usd(cost),
      `${device().label} at $${fmt(state.electricity, 2)}/kWh`);
  row(tb, "", "the claim keeps", `${fmt(netLgo(), 6)} LGO`,
      "the reward net of the claim's own fee");
  row(tb, rev > cost ? "ok" : "bad", "profit per claim at the reference price",
      usd(rev - cost), rev > cost ? "mining pays here" : "mining loses money here");
  row(tb, "", "break-even token price", `${usd(be)} / LGO`,
      "below this a rational miner stops");
  row(tb, be < state.refPrice ? "ok" : "warn", "margin at the reference price",
      `${fmt(state.refPrice / be, 2)}×`, "the reference price over the break-even");
  const uw = underwater();
  const worst = uw.reduce((a, b) => (b.frac > a.frac ? b : a));
  row(tb, worst.frac === 0 ? "ok" : worst.frac > 0.5 ? "bad" : "warn",
      "epochs underwater, worst price path",
      worst.frac === 0 ? "none" : `${(worst.frac * 100).toFixed(0)}%`,
      worst.frac === 0
        ? "every path stays profitable at this reward, price and difficulty"
        : `${worst.label} — mining stops paying for that share of the run`);
  for (const u of uw)
    if (u.frac > 0)
      row(tb, "", `— ${u.label}`, `${(u.frac * 100).toFixed(0)}%`, "of epochs below break-even");
}

// ---- charts -----------------------------------------------------------------------------
const INK2 = "#6a737d", LINE = "#e6e9ec";
const C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"];
const RED = "#e34948";

function frame(id, title) {
  const cv = document.getElementById(id), dpr = window.devicePixelRatio || 1;
  const w = cv.clientWidth, h = cv.clientHeight;
  cv.width = w * dpr; cv.height = h * dpr;
  const g = cv.getContext("2d"); g.scale(dpr, dpr); g.clearRect(0, 0, w, h);
  g.font = "600 13px system-ui"; g.fillStyle = "#1b1f23"; g.fillText(title, 12, 20);
  return [g, w, h];
}
const box = (g, x0, y0, x1, y1) => { g.strokeStyle = LINE; g.lineWidth = 1; g.strokeRect(x0, y0, x1 - x0, y1 - y0); };

function drawCurve() {
  const [g, w, h] = frame("curve", "profit per claim against the token price (both log)");
  const x0 = 64, y0 = 34, x1 = w - 14, y1 = h - 32;
  box(g, x0, y0, x1, y1);
  const be = breakEven();
  const lo = be / 100, hi = be * 100;
  const X = (t) => x0 + (x1 - x0) * (Math.log(t / lo) / Math.log(hi / lo));
  const cost = costPerClaim();
  const vlo = cost / 50, vhi = cost * 50;
  const Y = (v) => y1 - (y1 - y0) * (Math.log(Math.max(v, vlo) / vlo) / Math.log(vhi / vlo));

  g.strokeStyle = LINE; g.setLineDash([3, 3]);
  g.beginPath(); g.moveTo(x0, Y(cost)); g.lineTo(x1, Y(cost)); g.stroke(); g.setLineDash([]);
  g.fillStyle = INK2; g.font = "11px system-ui";
  g.fillText(`electricity per claim: ${usd(cost)}`, x0 + 6, Y(cost) - 6);

  g.strokeStyle = C[0]; g.lineWidth = 2; g.beginPath();
  for (let i = 0; i <= 200; i++) {
    const t = lo * Math.pow(hi / lo, i / 200);
    const v = revenuePerClaim(t);
    i ? g.lineTo(X(t), Y(v)) : g.moveTo(X(t), Y(v));
  }
  g.stroke();
  g.strokeStyle = RED; g.setLineDash([4, 3]);
  g.beginPath(); g.moveTo(X(be), y0); g.lineTo(X(be), y1); g.stroke(); g.setLineDash([]);
  g.fillStyle = RED; g.fillText(`break-even ${usd(be)}`, X(be) + 5, y0 + 15);
  g.fillStyle = C[0]; g.fillText("what a claim earns", X(be * 8), Y(revenuePerClaim(be * 8)) - 7);
  g.fillStyle = INK2;
  g.fillText("token price, USD per LGO →", x0 + 6, y1 + 20);
}

function drawPrices() {
  const [g, w, h] = frame("prices", "four stylised token-price paths (not backtests)");
  const x0 = 52, y0 = 34, x1 = w - 12, y1 = h - 30;
  box(g, x0, y0, x1, y1);
  const n = D.curves[0].points.length;
  const hiP = Math.max(...D.curves.flatMap((c) => c.points));
  const X = (i) => x0 + (x1 - x0) * i / (n - 1);
  const Y = (p) => y1 - (y1 - y0) * (Math.log(Math.max(p, 0.05) / 0.05) / Math.log(hiP * 1.2 / 0.05));
  D.curves.forEach((c, k) => {
    g.strokeStyle = C[k]; g.lineWidth = 2; g.beginPath();
    c.points.forEach((p, i) => (i ? g.lineTo(X(i), Y(p)) : g.moveTo(X(i), Y(p))));
    g.stroke();
    g.fillStyle = C[k]; g.font = "11px system-ui";
    g.fillText(c.label, x0 + 8, y0 + 16 + k * 14);
  });
  g.fillStyle = INK2; g.fillText("epoch →", x0 + 6, y1 + 18);
  g.save(); g.translate(15, (y0 + y1) / 2); g.rotate(-Math.PI / 2); g.textAlign = "center";
  g.fillText("× the reference price (log)", 0, 0); g.restore();
}

function drawMargin() {
  const [g, w, h] = frame("margin", "profit per claim each path implies");
  const x0 = 60, y0 = 34, x1 = w - 12, y1 = h - 30;
  box(g, x0, y0, x1, y1);
  const n = D.curves[0].points.length, cost = costPerClaim();
  const series = D.curves.map((c) => c.points.map((p) => revenuePerClaim(p * state.refPrice)));
  const hiV = Math.max(cost * 4, ...series.flat());
  const loV = Math.min(cost / 8, ...series.flat().filter((v) => v > 0), cost / 8);
  const X = (i) => x0 + (x1 - x0) * i / (n - 1);
  const Y = (v) => y1 - (y1 - y0) * (Math.log(Math.max(v, loV) / loV) / Math.log(hiV / loV));
  g.strokeStyle = RED; g.setLineDash([4, 3]); g.lineWidth = 1.4;
  g.beginPath(); g.moveTo(x0, Y(cost)); g.lineTo(x1, Y(cost)); g.stroke(); g.setLineDash([]);
  g.fillStyle = RED; g.font = "11px system-ui";
  g.fillText("break-even — below this, mining loses", x0 + 6, Y(cost) - 6);
  series.forEach((s, k) => {
    g.strokeStyle = C[k]; g.lineWidth = 2; g.beginPath();
    s.forEach((v, i) => (i ? g.lineTo(X(i), Y(v)) : g.moveTo(X(i), Y(v))));
    g.stroke();
  });
  g.font = "11px system-ui"; g.fillStyle = INK2;
  g.fillText("epoch →", x0 + 6, y1 + 18);
}

function render() {
  for (const [key, prop] of [["elec", "electricity"], ["diff", "difficultyMult"], ["ref", "refPrice"]]) {
    document.getElementById(`r_${key}`).value = state[prop];
    document.getElementById(`n_${key}`).value = state[prop];
  }
  renderReadouts(); drawCurve(); drawPrices(); drawMargin();
}

document.getElementById("badge").textContent =
  `${D.devices.length} measured device profiles · ${D.curves.length} stylised price paths · every figure computed live`;
document.getElementById("badge").className = "badge ok";
buildControls();
render();
window.addEventListener("resize", render);
