/* The calculator's controls, readouts and two charts. Model arithmetic lives in model.js;
 * this file only formats and draws. */
import { M, computeAll, selfCheck } from "./model.js";

const params = await (await fetch("params.json")).json();
const golden = await (await fetch("golden.json")).json();

// ---- self-check badge -------------------------------------------------------------------
{
  const el = document.getElementById("selfcheck");
  const fails = selfCheck(params, golden);
  const n = golden.rows.length * Object.keys(golden.rows[0].out).length;
  if (fails.length) {
    el.textContent = `JS model DISAGREES with Python on ${fails.length} of ${n} values`;
    el.className = "badge bad";
    console.error(fails);
  } else {
    el.textContent = `JS model agrees with Python on all ${n} golden values`;
    el.className = "badge ok";
  }
}

// ---- state and controls -----------------------------------------------------------------
const REF = { pool: params.reference.pool_fraction * 100,
              nodes: params.reference.expected_nodes,
              years: params.reference.expected_years,
              txs: params.reference.txs_per_block, k: 10 };
const state = { ...REF };

const CTLS = [
  ["pool", "PoW pool, % of TGE (R4)", 0.1, 2.0, 0.05],
  ["nodes", "expected nodes onboarded (R4)", 1000, 60000, 500],
  ["years", "expected duration, years (R4)", 1, 10, 0.25],
  ["txs", "transactions per block (scenario)", 20, 1024, 10],
  ["k", "spike size, × the arrival rate (scenario)", 1, 200, 1],
];

function buildControls() {
  const host = document.getElementById("controls");
  host.innerHTML = "";
  const fs = document.createElement("fieldset");
  fs.innerHTML = "<legend>parameters</legend>";
  for (const [key, label, lo, hi, step] of CTLS) {
    const div = document.createElement("div");
    div.className = "ctl";
    div.innerHTML = `<span class="lab">${label}</span>
      <input type="range" id="r_${key}" min="${lo}" max="${hi}" step="${step}">
      <input type="number" id="n_${key}" min="${lo}" max="${hi}" step="${step}">`;
    fs.appendChild(div);
    for (const pre of ["r_", "n_"])
      div.querySelector(`#${pre}${key}`).addEventListener("input", (ev) => {
        state[key] = Number(ev.target.value);
        render();
      });
  }
  host.appendChild(fs);
}

const fmt = (x, d = 0) => x.toLocaleString("en-US", { maximumFractionDigits: d });
const lgo = (lepta, d = 2) => fmt(lepta / params.base_units_per_lgo, d) + " LGO";

function triple() {
  return { pool_fraction: state.pool / 100, expected_nodes: state.nodes,
           expected_years: state.years, txs_per_block: state.txs, spike_k: state.k };
}

// ---- readouts ---------------------------------------------------------------------------
function row(tb, cls, label, value, note) {
  const tr = document.createElement("tr");
  tr.className = cls;
  const mark = cls === "ok" ? "✓" : cls === "warn" ? "△" : cls === "bad" ? "✕" : "";
  tr.innerHTML = `<td>${label}</td><td class="v">${value}</td><td class="m">${mark}</td>
    <td class="n">${note}</td>`;
  tb.appendChild(tr);
}

function renderReadouts(o) {
  const tb = document.getElementById("readouts");
  tb.innerHTML = "";
  const lo = params.efficiency_persistent, hi = params.efficiency_retiring;
  const effCls = o.satisfiable ? "ok" : "bad";
  row(tb, "", "bootstrap epochs", fmt(o.bootstrap_epochs),
      `${state.years} years at ${params.epochs_per_year} epochs a year`);
  row(tb, "", "endowment", lgo(o.endowment_lepta, 0), `${state.pool}% of TGE`);
  row(tb, effCls, "implied conversion efficiency", (o.implied_efficiency * 100).toFixed(1) + "%",
      o.satisfiable
        ? `inside the measured ${(lo * 100).toFixed(1)}–${(hi * 100).toFixed(1)}% band`
        : o.implied_efficiency > hi
          ? `above ${(hi * 100).toFixed(1)}% — more nodes than this pool can bond even if every bonded miner retires`
          : `below ${(lo * 100).toFixed(1)}% — the pool over-funds the target; expect surplus or more nodes`);
  row(tb, "", "opening sub-pool", lgo(o.sub_pool_lepta, 0), "one epoch's schedule at genesis");
  const mult = o.reward0_lepta / o.anchor_lepta;
  row(tb, mult > 10 ? "ok" : "warn", "opening reward", lgo(o.reward0_lepta),
      `${fmt(mult, 0)}× the anchor — the bootstrap subsidy`);
  row(tb, o.claims_to_bond < 5000 ? "ok" : "warn", "claims to a bond, at the opening reward",
      fmt(o.claims_to_bond), "min_stake over the net reward");
  row(tb, "", "a spike ×" + state.k + " saturates its epoch near block",
      fmt(o.spike_saturation_block), `of ${fmt(params.blocks_per_epoch)} — then borrows`);
  row(tb, "ok", "and the phase still ends when it was going to",
      "≈ " + fmt(o.bootstrap_epochs) + " either way",
      `the epoch spends about ${fmt(o.spike_borrow_multiple)} budgets, and the schedule `
      + "re-spreads the remainder over the epochs that remain");
  const ceil_binds = o.whale_epoch_ceiling_lepta >= o.endowment_lepta;
  row(tb, "warn", "one epoch's drain ceiling (whale, block-space bound)",
      ceil_binds ? "the whole endowment" : lgo(o.whale_epoch_ceiling_lepta, 0),
      (ceil_binds ? `block space × the opening reward alone allows ${lgo(o.whale_epoch_ceiling_lepta, 0)} — `
                  : "blocks × block cap × the opening reward — ")
      + "the documented Q8 exposure");
}

function renderPost(o) {
  const tb = document.getElementById("postReadouts");
  tb.innerHTML = "";
  row(tb, "", "the anchor", fmt(o.anchor_lepta) + " lepta",
      "a transfer plus an inscription, at resting prices");
  row(tb, "", "fee drag at the anchor", (o.fee_drag_at_anchor * 100).toFixed(1) + "%",
      "the claim's own fee, out of its reward");
  row(tb, o.target_per_block >= 2 ? "ok" : "warn", "post-phase capacity",
      fmt(o.capacity_post) + " claims/epoch",
      `pow_share × txs_per_epoch / 2 at ${state.txs} txs a block`);
  row(tb, "", "throttle target", fmt(o.target_per_block) + " claims/block",
      o.target_per_block === 1 ? "the sparse floor — saturation arrives early" : "spread across the epoch");
}

// ---- charts -----------------------------------------------------------------------------
const INK2 = "#6a737d", LINE = "#e6e9ec";
const BLUE = "#2a78d6", ORANGE = "#eb6834", GREEN = "#1baf7a", RED = "#e34948";

function frame(cv, title) {
  const dpr = window.devicePixelRatio || 1;
  const w = cv.clientWidth, h = cv.clientHeight;
  cv.width = w * dpr; cv.height = h * dpr;
  const g = cv.getContext("2d");
  g.scale(dpr, dpr);
  g.clearRect(0, 0, w, h);
  g.font = "600 13px system-ui"; g.fillStyle = "#1b1f23";
  g.fillText(title, 12, 20);
  return [g, w, h];
}

function axes(g, x0, y0, x1, y1) {
  g.strokeStyle = LINE; g.lineWidth = 1;
  g.strokeRect(x0, y0, x1 - x0, y1 - y0);
}

function drawEndowment(o) {
  const cv = document.getElementById("endowment");
  const [g, w, h] = frame(cv, "the endowment's schedule, and the spike's dent");
  const x0 = 46, y0 = 34, x1 = w - 12, y1 = h - 30;
  axes(g, x0, y0, x1, y1);
  const B = o.bootstrap_epochs, k = state.k;
  const spikeAt = Math.round(B / 6);
  const horizon = B * 1.25;
  const X = (e) => x0 + (x1 - x0) * e / horizon;
  const Y = (f) => y1 - (y1 - y0) * f;

  // baseline: linear to zero at B
  g.strokeStyle = BLUE; g.lineWidth = 2;
  g.beginPath(); g.moveTo(X(0), Y(1));
  g.lineTo(X(B), Y(0)); g.lineTo(X(horizon), Y(0)); g.stroke();

  // spiked: a dent at spikeAt, then a SHALLOWER slope to the SAME end -- the schedule
  // re-spreads what is left over the epochs that remain, so the deadline does not move.
  const dent = Math.min(0.9 * (1 - spikeAt / B), (k - 1) / B);
  const atSpike = 1 - spikeAt / B;
  const after = Math.max(0, atSpike - dent);
  g.strokeStyle = ORANGE;
  g.beginPath(); g.moveTo(X(0), Y(1)); g.lineTo(X(spikeAt), Y(atSpike));
  g.lineTo(X(spikeAt), Y(after)); g.lineTo(X(B), Y(0));
  g.lineTo(X(horizon), Y(0)); g.stroke();

  g.fillStyle = INK2; g.font = "11px system-ui";
  g.fillText("expected end: " + B, X(B) - 34, y1 + 16);
  g.fillStyle = ORANGE;
  g.fillText(`×${k} spike — same end, thinner tail`, X(spikeAt) + 6, Y(after) - 6);
  g.fillStyle = BLUE; g.fillText("uniform", X(B * 0.45), Y(0.62));
  g.fillStyle = INK2;
  g.save(); g.translate(14, (y0 + y1) / 2); g.rotate(-Math.PI / 2);
  g.textAlign = "center"; g.fillText("endowment, share of genesis", 0, 0); g.restore();
}

function drawReward(o) {
  const cv = document.getElementById("reward");
  const [g, w, h] = frame(cv, "the reward's admissible band (log scale)");
  const x0 = 46, y0 = 34, x1 = w - 12, y1 = h - 30;
  axes(g, x0, y0, x1, y1);
  const B = o.bootstrap_epochs, horizon = B * 1.25;
  const top = o.reward0_lepta * 2, bot = o.anchor_lepta / 2;
  const X = (e) => x0 + (x1 - x0) * e / horizon;
  const Y = (v) => y1 - (y1 - y0) * (Math.log(v / bot) / Math.log(top / bot));

  // band: upper = one block's budget share (flat on schedule), lower = anchor
  g.fillStyle = "rgba(42,120,214,0.12)";
  g.beginPath();
  g.moveTo(X(0), Y(o.reward0_lepta)); g.lineTo(X(B), Y(o.reward0_lepta));
  g.lineTo(X(B), Y(o.anchor_lepta)); g.lineTo(X(0), Y(o.anchor_lepta));
  g.closePath(); g.fill();
  g.strokeStyle = BLUE; g.lineWidth = 2;
  g.beginPath(); g.moveTo(X(0), Y(o.reward0_lepta)); g.lineTo(X(B), Y(o.reward0_lepta)); g.stroke();
  g.strokeStyle = GREEN;
  g.beginPath(); g.moveTo(X(0), Y(o.anchor_lepta)); g.lineTo(X(horizon), Y(o.anchor_lepta)); g.stroke();

  // post-phase: exactly the anchor
  g.strokeStyle = RED; g.setLineDash([4, 3]);
  g.beginPath(); g.moveTo(X(B), y0 + 4); g.lineTo(X(B), y1); g.stroke();
  g.setLineDash([]);

  g.fillStyle = BLUE; g.font = "11px system-ui";
  g.fillText("quiet-epoch ceiling: one block's budget share", X(2), Y(o.reward0_lepta) - 6);
  g.fillStyle = GREEN;
  g.fillText("the anchor — and the whole post-phase", X(2), Y(o.anchor_lepta) - 8);
  g.fillStyle = INK2;
  g.fillText("transition", X(B) + 4, y0 + 16);
  g.fillText("demand decides where in the band the price runs —",
             X(B * 0.18), (Y(o.reward0_lepta) + Y(o.anchor_lepta)) / 2 - 4);
  g.fillText("the simulator's job, not a closed form's",
             X(B * 0.18), (Y(o.reward0_lepta) + Y(o.anchor_lepta)) / 2 + 12);
}

// ---- wiring -----------------------------------------------------------------------------
function render() {
  for (const [key] of CTLS) {
    document.getElementById(`r_${key}`).value = state[key];
    document.getElementById(`n_${key}`).value = state[key];
  }
  const o = computeAll(params, triple());
  renderReadouts(o);
  renderPost(o);
  drawEndowment(o);
  drawReward(o);
}

document.getElementById("reset").onclick = () => { Object.assign(state, REF); render(); };
document.getElementById("tight").onclick = () => {
  Object.assign(state, { pool: 0.5, nodes: 25000, years: 2, txs: 600, k: 100 }); render();
};
document.getElementById("sparse").onclick = () => {
  Object.assign(state, { pool: 0.5, nodes: 25000, years: 4, txs: 20, k: 10 }); render();
};

buildControls();
render();
window.addEventListener("resize", render);
