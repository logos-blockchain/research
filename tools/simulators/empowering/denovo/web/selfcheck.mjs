/* Runs the panel's own self-check outside the browser, so `make web` can fail on drift
 * rather than leaving it to whoever opens the page. */
import { readFileSync } from "node:fs";
import { selfCheck } from "./model.js";
const params = JSON.parse(readFileSync("params.json", "utf8"));
const golden = JSON.parse(readFileSync("golden.json", "utf8"));
const fails = selfCheck(params, golden);
const n = golden.rows.length * Object.keys(golden.rows[0].out).length;
if (fails.length) {
  console.error(`FAIL: ${fails.length} of ${n} values differ from the Python model`);
  for (const f of fails.slice(0, 25))
    console.error(`  ${JSON.stringify(f.row)} ${f.key}: js=${f.have} py=${f.want}`);
  process.exit(1);
}
console.log(`  JS model agrees with Python on all ${n} values (${golden.rows.length} configs)`);
