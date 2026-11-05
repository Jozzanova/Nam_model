// node model/js_twin_test.js  — checks modelsim.js against the Python run recorded in simulation.json
const fs = require("fs"), path = require("path");
const sim = require(path.join(__dirname, "modelsim.js"));
const S = JSON.parse(fs.readFileSync(path.join(__dirname, "simulation.json"), "utf8"));
const inp = S.sim_inputs, P = S.params, A = S.assumptions;
let worst = 0;
const cmp = (name, a, b) => { const e = Math.max(...a.map((x, i) => Math.abs(x - b[i]))); worst = Math.max(worst, e); console.log(`${name.padEnd(28)} max |js − py| = ${e.toExponential(1)}`); };
for (const kind of ["exo", "flx", "sm", "est"]) {
  const f = sim.forecast(inp, P, A, 16, kind);
  for (const k of ["infl4", "infl4u", "u", "g4y", "v", "R", "RS", "g4w"]) cmp(`forecast ${kind} ${k}`, f.out[k], S.forecast[kind][k]);
}
for (const kind of ["exo", "flx", "sm"]) {
  const m = sim.multipliers(inp, P, A, 48, kind, P.shock_bp);
  for (const k of ["infl4", "u_pp", "g4y", "v_level", "g4rw"]) cmp(`shock ${kind} ${k}`, m.out[k], S.shock[kind][k]);
}
{
  const E = JSON.parse(fs.readFileSync(path.join(__dirname, "estimates.json"), "utf8")), keys = ["wage", "price", "imp", "fx", "unemp", "output", "mm", "bridge"];
  const common = keys.map(k => new Set(E.equations[k].dates)).reduce((a, b) => new Set([...a].filter(x => b.has(x)))), dates = [...common].sort();
  const Rm = {keys, rows: dates.map(q => keys.map(k => E.equations[k].resid[E.equations[k].dates.indexOf(q)]))};
  const t0 = Date.now(), B = sim.bootstrap(inp, P, A, 16, "exo", Rm, 500, 20261031), ms = Date.now() - t0, B2 = sim.bootstrap(inp, P, A, 16, "exo", Rm, 500, 7);
  let wb = 0, wjj = 0;   // JS vs Python, and JS vs JS with another seed: the two should be of the same order (sampling error of the percentiles)
  for (const k of ["infl4", "u", "g4y", "v", "RS"]) for (const q of ["lo", "hi", "lo25", "hi75"]) { wb = Math.max(wb, ...B.bands[k][q].map((x, i) => Math.abs(x - S.bands[k][q][i]))); wjj = Math.max(wjj, ...B.bands[k][q].map((x, i) => Math.abs(x - B2.bands[k][q][i]))); }
  console.log(`bootstrap 500 reps in ${ms} ms; max |js − py| over the 5/25/75/95 percentiles = ${wb.toFixed(3)}, max |js seed A − js seed B| = ${wjj.toFixed(3)} (different draws, so sampling error only)`);
  if (wb > 2 * Math.max(wjj, 0.3)) { console.log("BANDS MISMATCH"); process.exit(1); }
}
{
  const U = sim.ustar(P, S.ustar.data, S.ustar.z_growth); cmp("u* series", U.ustar, S.ustar.ustar);
  const E = JSON.parse(fs.readFileSync(path.join(__dirname, "estimates.json"), "utf8")), keys = S.bands.resid_matrix ? S.bands.resid_matrix.keys : ["wage", "price", "imp", "fx", "unemp", "output", "mm", "bridge"];
  const common = keys.map(k => new Set(E.equations[k].dates)).reduce((a, b) => new Set([...a].filter(x => b.has(x)))), dates = [...common].sort();
  const Rm = {keys, rows: dates.map(q => keys.map(k => E.equations[k].resid[E.equations[k].dates.indexOf(q)]))};
  const t0 = Date.now(), L = sim.lossSim(inp, P, A, S.loss.h, ["exo", "flx", "sm", "est"], Rm, S.loss.reps, S.loss.seed), ms = Date.now() - t0, L2 = sim.lossSim(inp, P, A, S.loss.h, ["exo", "flx", "sm", "est"], Rm, S.loss.reps, 7);
  let wl = 0, wll = 0;
  for (const k of ["exo", "flx", "sm", "est"]) for (const q of ["var_pu", "var_gy", "var_dR", "msd_pu", "mean_pu"]) { const py = S.loss.rules[k][q], sc = Math.max(0.05, Math.abs(py)); wl = Math.max(wl, Math.abs(L[k][q] - py) / sc); wll = Math.max(wll, Math.abs(L[k][q] - L2[k][q]) / sc); }
  console.log(`loss table (4 rules × ${S.loss.reps} reps × ${S.loss.h} quarters) in ${ms} ms; max relative |js − py| = ${wl.toFixed(3)}, |js seed A − js seed B| = ${wll.toFixed(3)} (sampling error only)`);
  if (wl > 2 * Math.max(wll, 0.05)) { console.log("LOSS MISMATCH"); process.exit(1); }
}
{
  const E = JSON.parse(fs.readFileSync(path.join(__dirname, "estimates.json"), "utf8")), keys = ["wage", "price", "imp", "fx", "unemp", "output", "mm", "bridge"], chol = {};
  for (const k of keys) chol[k] = E.equations[k].chol;
  const SB = S.shock.bands, t0 = Date.now(), M = sim.multiplierBands(inp, P, A, 48, "exo", chol, SB.reps, SB.seed), ms = Date.now() - t0, M2 = sim.multiplierBands(inp, P, A, 48, "exo", chol, SB.reps, 11);
  let wm = 0, wmm = 0;
  for (const k of ["infl4", "u_pp", "g4y", "v_level"]) for (const q of ["lo", "hi", "lo25", "hi75"]) { const sc = Math.max(0.05, ...SB[k].hi.map(Math.abs)); wm = Math.max(wm, ...M.bands[k][q].map((x, i) => Math.abs(x - SB[k][q][i]) / sc)); wmm = Math.max(wmm, ...M.bands[k][q].map((x, i) => Math.abs(x - M2.bands[k][q][i]) / sc)); }
  console.log(`multiplier bands (${SB.reps} coefficient draws × 48 quarters) in ${ms} ms; max relative |js − py| = ${wm.toFixed(3)}, |js seed A − js seed B| = ${wmm.toFixed(3)} (sampling error only)`);
  if (wm > 2 * Math.max(wmm, 0.08)) { console.log("MULTIPLIER BANDS MISMATCH"); process.exit(1); }
}
const f = sim.forecast(inp, P, A, 16, "exo");
console.log("SELFTEST", JSON.stringify(Object.fromEntries(["infl4", "u", "g4y", "v", "RS"].map(k => [k, +f.out[k].reduce((a, b) => a + b, 0).toFixed(6)]))));
console.log(worst < 2e-3 ? "JS TWIN OK" : "JS TWIN MISMATCH", "(worst", worst.toExponential(1) + "; Python values are rounded to 4 decimals)");
process.exit(worst < 2e-3 ? 0 : 1);
