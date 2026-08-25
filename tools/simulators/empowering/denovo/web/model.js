/* The de-novo EmPoWering model, in the browser.
 *
 * A transcription of src/empowering_denovo_sim/params.py and the closed forms of MODEL.md.
 * It is a second implementation, so it is checked against the first: golden.json carries a
 * grid of triples with the outputs Python computes, and selfCheck() recomputes every row
 * here. The page wears the result as a badge rather than assuming agreement.
 *
 * Every floor/ceil mirrors the Python's integer arithmetic; values stay in lepta until
 * display. Nothing here is hardcoded that params.json carries.
 */

export const M = {
  epochs: (p, years) => Math.round(years * p.epochs_per_year),
  endowment: (p, poolFraction) =>
    Math.round(poolFraction * p.launch_supply_lgo * p.base_units_per_lgo),
  impliedEfficiency: (p, nodes, poolFraction) =>
    nodes * p.min_stake_lepta / M.endowment(p, poolFraction),
  // Feasible on incentives alone: persistence is what nothing pays anyone to avoid. A triple
  // BELOW the persistent efficiency merely over-funds, which is not infeasible -- so this is
  // one-sided, matching params.py. A two-sided band was wrong and the golden check caught it.
  satisfiable: (p, nodes, poolFraction) =>
    M.impliedEfficiency(p, nodes, poolFraction) <= p.efficiency_persistent,
  satisfiableIfRetiring: (p, nodes, poolFraction) =>
    M.impliedEfficiency(p, nodes, poolFraction) <= p.efficiency_retiring_fast,
  anchor: (p) => 2 * p.transfer_fee_lepta,

  subPool: (p, poolFraction, years) =>
    Math.floor(M.endowment(p, poolFraction) / M.epochs(p, years)),
  reward0: (p, poolFraction, years) =>
    Math.max(M.anchor(p), Math.floor(M.subPool(p, poolFraction, years) / p.blocks_per_epoch)),
  claimsToBond: (p, poolFraction, years) =>
    Math.ceil(p.min_stake_lepta / (M.reward0(p, poolFraction, years) - p.claim_fee_lepta)),
  feeDrag: (p) => p.claim_fee_lepta / M.anchor(p),

  divertedPerBlock: (p, txs) =>
    Math.floor(txs * p.transfer_fee_lepta * p.pow_share_num / p.pow_share_den),
  budgetPost: (p, txs) => M.divertedPerBlock(p, txs) * p.blocks_per_epoch,
  capacityPost: (p, txs) => Math.floor(M.budgetPost(p, txs) / M.anchor(p)),
  targetPerBlock: (p, txs) =>
    Math.max(1, Math.floor(M.capacityPost(p, txs) / p.blocks_per_epoch)),

  spikeSaturationBlock: (p, k) => Math.floor(p.blocks_per_epoch / k),
  // A spike does NOT move the phase's end: the schedule re-spreads the remainder over
  // the epochs that remain. What it does move is how many budgets the epoch spends.
  spikeBorrowMultiple: (k) => k,
  whaleEpochCeiling: (p, poolFraction, years) =>
    p.blocks_per_epoch * p.max_block_txs * M.reward0(p, poolFraction, years),
};

export function computeAll(p, tin) {
  const { pool_fraction: f, expected_years: y, txs_per_block: n, spike_k: k } = tin;
  return {
    bootstrap_epochs: M.epochs(p, y),
    endowment_lepta: M.endowment(p, f),
    implied_efficiency: M.impliedEfficiency(p, tin.expected_nodes, f),
    satisfiable: M.satisfiable(p, tin.expected_nodes, f),
    satisfiable_if_retiring: M.satisfiableIfRetiring(p, tin.expected_nodes, f),
    sub_pool_lepta: M.subPool(p, f, y),
    reward0_lepta: M.reward0(p, f, y),
    claims_to_bond: M.claimsToBond(p, f, y),
    anchor_lepta: M.anchor(p),
    fee_drag_at_anchor: M.feeDrag(p),
    capacity_post: M.capacityPost(p, n),
    target_per_block: M.targetPerBlock(p, n),
    spike_saturation_block: M.spikeSaturationBlock(p, k),
    spike_borrow_multiple: M.spikeBorrowMultiple(k),
    whale_epoch_ceiling_lepta: M.whaleEpochCeiling(p, f, y),
  };
}

const close = (a, b) => {
  if (typeof a === "boolean" || typeof b === "boolean") return a === b;
  if (a === b) return true;
  return Math.abs(a - b) <= 1e-9 * Math.max(Math.abs(a), Math.abs(b), 1);
};

export function selfCheck(params, golden) {
  const fails = [];
  for (const row of golden.rows) {
    const have = computeAll(params, row.in);
    for (const key of Object.keys(row.out))
      if (!close(have[key], row.out[key]))
        fails.push({ row: row.in, key, have: have[key], want: row.out[key] });
  }
  return fails;
}
