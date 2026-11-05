/* JavaScript twin of model/simulate.py (simulate(), outputs(), the exogenous extension).  Inlined into the dashboard by
   build.py; tested against the Python output by model/js_twin_test.js.  Keep the two in step line by line. */
const modelSim = (() => {
  const ENDO = ["w", "p", "pu", "pi", "v", "u", "y", "R", "RS"];
  const GROW = {z: "z_growth", g: "g_growth", pf: "pf_infl", pstar: "pstar_infl", pen: "pen_infl"};
  const clone = o => JSON.parse(JSON.stringify(o));

  // exogenous arrays beyond the data: four-quarter growth for the trending series, constants, the R* path by year, the HP trend
  function extend(inp, assume) {
    const X = clone(inp.exo), T = inp.T, idx = inp.index;
    for (const [c, key] of Object.entries(GROW)) {
      const last = inp.exo_last[c], gr = assume[key];
      for (let i = last + 1; i < T; i++) X[c][i] = X[c][i - 4] + Math.log(1 + gr / 100);
    }
    for (const c of ["oil", "t1", "t3"]) { const last = inp.exo_last[c]; for (let i = last + 1; i < T; i++) X[c][i] = X[c][i - 1]; }
    { const last = inp.exo_last.Rs, path = assume.Rs_path || {};
      for (let i = last + 1; i < T; i++) { const yr = idx[i].slice(0, 4); X.Rs[i] = yr in path ? +path[yr] : X.Rs[i - 1]; } }
    { const last = inp.exo_last.ytrend; for (let i = last + 1; i < T; i++) X.ytrend[i] = X.ytrend[i - 1] + inp.ytrend_growth; }
    return X;
  }

  function simulate(P, X, H, t0, t1, R_path, shock, resid) {
    const Y = {}; for (const k of ENDO) Y[k] = H[k].slice(); for (const k of ENDO) while (Y[k].length <= t1) Y[k].push(NaN);
    const eq = P.eq, lr = P.lr, rule = P.rule;
    const sea = (c, t) => (c.s1 || 0) * X.s1[t] + (c.s2 || 0) * X.s2[t] + (c.s3 || 0) * X.s3[t];
    const seap = (c, t) => (c.s1p || 0) * X.s1p[t] + (c.s2p || 0) * X.s2p[t] + (c.s3p || 0) * X.s3p[t];
    const dum = (c, t) => ["covidq1", "covidq2", "covidq3", "covidq4", "ukrw"].reduce((s, k) => s + (k in c ? c[k] * X[k][t] : 0), 0);
    const r = (k, t) => (resid && resid[k] ? resid[k][t] : 0);
    const w = Y.w, p = Y.p, pu = Y.pu, pi = Y.pi, v = Y.v, u = Y.u, y = Y.y, R = Y.R, RS = Y.RS;
    const infl4 = s => 100 * (p[s] - p[s - 4]), infl4s = s => 100 * (X.pstar[s] - X.pstar[s - 4]), infl4u = s => 100 * (pu[s] - pu[s - 4]);
    const rex = s => v[s] + X.pstar[s] - p[s], rr = s => RS[s] - infl4(s), g4y = s => 100 * (y[s] - y[s - 4]), gap = s => y[s] - X.ytrend[s];
    const ecm_w = s => w[s] - p[s] - X.z[s] + lr.gamma_u * u[s];
    const ecm_p = s => p[s] - (1 - lr.phi) * (w[s] + X.t1[s] - X.z[s]) - lr.phi * pi[s] - lr.eta * X.t3[s];
    const ecm_pi = s => pi[s] - v[s] - X.pf[s];
    const ecm_v = s => rex(s) - lr.kappa_fx * ((R[s] - infl4(s)) - (X.Rs[s] - infl4s(s)));
    const ecm_y = s => y[s] - lr.y_g * X.g[s] - lr.y_rex * rex(s) + lr.y_rr * rr(s);
    for (let t = t0; t <= t1; t++) {
      for (const k of ENDO) Y[k][t] = Y[k][t - 1];
      for (let it = 0; it < 40; it++) {
        const prev = ENDO.map(k => Y[k][t]);
        let c = eq.output;
        y[t] = y[t - 1] + c.const + c.Dy_l1 * (y[t - 1] - y[t - 2]) + c.Dg * (X.g[t] - X.g[t - 1]) + c.ecm_y_l1 * ecm_y(t - 1) + sea(c, t) + dum(c, t) + r("output", t);
        c = eq.unemp;
        u[t] = u[t - 1] + c.const + c.Du_l1 * (u[t - 1] - u[t - 2]) + c.Du_l4 * (u[t - 4] - u[t - 5]) + c.Dy * (y[t] - y[t - 1]) + c.Dy_l1 * (y[t - 1] - y[t - 2])
          + c.u_l2 * u[t - 2] + c.Dwp_l2 * ((w[t - 2] - p[t - 2]) - (w[t - 3] - p[t - 3])) + c.rr_l2 * rr(t - 2) + c.g4y_l2 * g4y(t - 2) + sea(c, t) + seap(c, t) + dum(c, t) + r("unemp", t);
        if (rule.kind === "exo") R[t] = R_path[t] + (shock ? shock[t] : 0);
        else if (rule.kind === "flx" || rule.kind === "sm") {
          const rho = rule.kind === "sm" ? rule.rho : 0;
          R[t] = rho * R[t - 1] + (1 - rho) * (rule.pi_bar + rule.rr_bar) + rule.theta_pi * (infl4u(t) - rule.pi_bar) + rule.theta_y * (g4y(t) - rule.g_bar) + (shock ? shock[t] : 0);
        } else {
          c = eq.rule_est;
          R[t] = R[t - 1] + c.const + c.R_l1 * R[t - 1] + c.pigap_u * (infl4u(t) - X.tgt[t]) + c.g4y * g4y(t) + c.u_l1 * u[t - 1] + c.DRs * (X.Rs[t] - X.Rs[t - 1]) + c.DR_l1 * (R[t - 1] - R[t - 2]) + (shock ? shock[t] : 0) + r("rule_est", t);
        }
        c = lr.use_alpha_v ? eq.fx_level : eq.fx;
        const dRd = X.d_it[t] * ((R[t] - X.Rs[t]) - (R[t - 1] - X.Rs[t - 1]));
        v[t] = v[t - 1] + c.const + c.dRdiff_it * dRd + c.Doil * (X.oil[t] - X.oil[t - 1]) + c.Dv_l1 * (v[t - 1] - v[t - 2])
          + (lr.use_alpha_v ? c.ecm_v_l1 * ecm_v(t - 1) : 0) + dum(c, t) + r(lr.use_alpha_v ? "fx_level" : "fx", t);
        c = eq.imp;
        pi[t] = pi[t - 1] + c.const + c.Dv * (v[t] - v[t - 1]) + c.Dpf * (X.pf[t] - X.pf[t - 1]) + c.Dv_l1 * (v[t - 1] - v[t - 2])
          + c.Dpi14 * ((pi[t - 1] - pi[t - 2]) - (pi[t - 4] - pi[t - 5])) + c.ecm_pi_l1 * ecm_pi(t - 1) + c.rex_l1 * rex(t - 1) + sea(c, t) + r("imp", t);
        c = eq.price;
        p[t] = p[t - 1] + c.const + c.Dp_l4 * (p[t - 4] - p[t - 5]) + c.Dpi * (pi[t] - pi[t - 1]) + c.Dpen * (X.pen[t] - X.pen[t - 1]) + c.gap_l1 * gap(t - 1)
          + c.ecm_p_l1 * ecm_p(t - 1) + sea(c, t) + dum(c, t) + r("price", t);
        c = eq.wage;
        w[t] = w[t - 4] + c.const + c.D4p_tgt * ((p[t - 1] - p[t - 5]) - X.tgt[t] / 100) + c.D4z * (X.z[t] - X.z[t - 4]) + c.D4u * (u[t] - u[t - 4])
          + c.ecm_w_l4 * ecm_w(t - 4) + sea(c, t) + r("wage", t);
        c = eq.mm;
        RS[t] = RS[t - 1] + c.const + c.DR * (R[t] - R[t - 1]) + c.RS_l1 * RS[t - 1] + c.R_l1 * R[t - 1] + c.DRs * (X.Rs[t] - X.Rs[t - 1]) + c.Rs_l1 * X.Rs[t - 1] + dum(c, t) + r("mm", t);
        c = eq.bridge;
        pu[t] = pu[t - 1] + c.const + c.Dp * (p[t] - p[t - 1]) + c.Dpen * (X.pen[t] - X.pen[t - 1]) + c.Dt3 * (X.t3[t] - X.t3[t - 1])
          + c.Dpu_l1 * (pu[t - 1] - pu[t - 2]) + c.Dpu_l4 * (pu[t - 4] - pu[t - 5]) + r("bridge", t);
        let mx = 0; ENDO.forEach((k, i) => { mx = Math.max(mx, Math.abs(Y[k][t] - prev[i])); }); if (mx < 1e-11) break;
      }
    }
    return Y;
  }

  function outputs(Y, X, t0, t1) {
    const o = {infl4: [], infl4u: [], u: [], g4y: [], v: [], i44: [], R: [], RS: [], g4w: [], g4rw: [], gap: []};
    for (let t = t0; t <= t1; t++) {
      o.infl4.push(100 * (Y.p[t] - Y.p[t - 4])); o.infl4u.push(100 * (Y.pu[t] - Y.pu[t - 4])); o.u.push(Math.exp(Y.u[t])); o.g4y.push(100 * (Y.y[t] - Y.y[t - 4]));
      o.v.push(100 * (Y.v[t] - Y.v[t - 4])); o.i44.push(Math.exp(Y.v[t])); o.R.push(Y.R[t]); o.RS.push(Y.RS[t]);
      o.g4w.push(100 * (Y.w[t] - Y.w[t - 4])); o.g4rw.push(100 * ((Y.w[t] - Y.p[t]) - (Y.w[t - 4] - Y.p[t - 4]))); o.gap.push(100 * (Y.y[t] - X.ytrend[t]));
    }
    return o;
  }

  // forecast from the origin over `h` quarters; returns {index, out}
  function forecast(inp, P, assume, h, rule) {
    const X = extend(inp, assume), o = inp.origin_pos, t1 = Math.min(o + h, inp.T - 1);
    const Pk = clone(P); if (rule) Pk.rule.kind = rule;
    const Y = simulate(Pk, X, inp.endo_hist, o + 1, t1, inp.R_path);
    return {index: inp.index.slice(o + 1, t1 + 1), out: outputs(Y, X, o + 1, t1)};
  }
  // permanent policy-rate shock of `bp` basis points from the first forecast quarter: differences from the baseline
  function multipliers(inp, P, assume, h, rule, bp) {
    const X = extend(inp, assume), o = inp.origin_pos, t1 = Math.min(o + h, inp.T - 1);
    const Pk = clone(P); if (rule) Pk.rule.kind = rule;
    const base = outputs(simulate(Pk, X, inp.endo_hist, o + 1, t1, inp.R_path), X, o + 1, t1);
    const sh = new Array(inp.T).fill(0); for (let i = o + 1; i < inp.T; i++) sh[i] = bp / 100;
    const alt = outputs(simulate(Pk, X, inp.endo_hist, o + 1, t1, inp.R_path, sh), X, o + 1, t1);
    const d = {}; for (const k of ["infl4", "infl4u", "u", "g4y", "v", "R", "RS", "g4rw", "gap"]) d[k] = base[k].map((b, i) => alt[k][i] - b);
    d.v_level = base.i44.map((b, i) => 100 * (Math.log(alt.i44[i]) - Math.log(b))); d.u_pp = base.u.map((b, i) => alt.u[i] - b);
    return {index: inp.index.slice(o + 1, t1 + 1), out: d};
  }
  // bootstrap bands for any setting: residual vectors of the estimated equations resampled by quarter (keeping their
  // cross-equation correlation) and added to the forecast quarters; percentiles as numpy's default (linear interpolation).
  // Rm = {keys, rows}: one row per sample quarter, one column per equation key.  Seeded, so the same setting gives the same bands.
  const mulberry32 = a => () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const pct = (sorted, q) => { const i = (sorted.length - 1) * q / 100, lo = Math.floor(i), hi = Math.ceil(i); return sorted[lo] + (sorted[hi] - sorted[lo]) * (i - lo); };
  function bootstrap(inp, P, assume, h, rule, Rm, reps, seed) {
    const X = extend(inp, assume), o = inp.origin_pos, t1 = Math.min(o + h, inp.T - 1);
    const Pk = clone(P); if (rule) Pk.rule.kind = rule;
    const rnd = mulberry32(seed || 20261031), n = Rm.rows.length, vars = ["infl4", "infl4u", "u", "g4y", "v", "R", "RS", "g4w"], draws = {};
    for (const v of vars) draws[v] = [];
    for (let r = 0; r < reps; r++) {
      const res = {}; for (const k of Rm.keys) res[k] = new Array(inp.T).fill(0);
      for (let t = o + 1; t <= t1; t++) { const row = Rm.rows[Math.floor(rnd() * n)]; for (let ki = 0; ki < Rm.keys.length; ki++) res[Rm.keys[ki]][t] = row[ki]; }
      const ob = outputs(simulate(Pk, X, inp.endo_hist, o + 1, t1, inp.R_path, null, res), X, o + 1, t1);
      for (const v of vars) draws[v].push(ob[v]);
    }
    const bands = {};
    for (const v of vars) {
      const b = {lo: [], hi: [], lo25: [], hi75: []};
      for (let j = 0; j <= t1 - o - 1; j++) { const col = draws[v].map(a => a[j]).sort((x, y) => x - y); b.lo.push(pct(col, 5)); b.hi.push(pct(col, 95)); b.lo25.push(pct(col, 25)); b.hi75.push(pct(col, 75)); }
      bands[v] = b;
    }
    return {index: inp.index.slice(o + 1, t1 + 1), bands, reps};
  }
  // ABE2005 eq (10) ingredients by stochastic simulation: identical residual draws for every rule (re-seeded), variances
  // pooled over quarters and draws of CPI-ATE inflation, four-quarter GDP growth and the quarterly change of the policy rate.
  function lossSim(inp, P, assume, h, rules, Rm, reps, seed) {
    const X = extend(inp, assume), o = inp.origin_pos, t1 = Math.min(o + h, inp.T - 1), n = Rm.rows.length, out = {}, tgt = P.rule.pi_bar;
    const mean = a => a.reduce((s, x) => s + x, 0) / a.length, vr = a => { const m = mean(a); return a.reduce((s, x) => s + (x - m) * (x - m), 0) / a.length; };
    for (const kind of rules) {
      const Pk = clone(P); Pk.rule.kind = kind; const rnd = mulberry32(seed || 20261031);
      const pu = [], gy = [], dR = [], pi_ = [];
      for (let r = 0; r < reps; r++) {
        const res = {}; for (const k of Rm.keys) res[k] = new Array(inp.T).fill(0);
        for (let t = o + 1; t <= t1; t++) { const row = Rm.rows[Math.floor(rnd() * n)]; for (let ki = 0; ki < Rm.keys.length; ki++) res[Rm.keys[ki]][t] = row[ki]; }
        const Yb = simulate(Pk, X, inp.endo_hist, o + 1, t1, inp.R_path, null, res), ob = outputs(Yb, X, o + 1, t1);
        pu.push(...ob.infl4u); gy.push(...ob.g4y); pi_.push(...ob.infl4); for (let t = o + 1; t <= t1; t++) dR.push(Yb.R[t] - Yb.R[t - 1]);
      }
      out[kind] = {var_pu: vr(pu), var_gy: vr(gy), var_dR: vr(dR), msd_pu: mean(pu.map(x => (x - tgt) * (x - tgt))), mean_pu: mean(pu), mean_gy: mean(gy), mean_pi: mean(pi_), mean_absdR: mean(dR.map(Math.abs))};
    }
    return out;
  }
  // coefficient-uncertainty bands of the +100 bp responses (see simulate.py multiplier_bands); chol = {eqkey: {names, L}}
  function multiplierBands(inp, P, assume, h, rule, chol, reps, seed) {
    const X = extend(inp, assume), o = inp.origin_pos, t1 = Math.min(o + h, inp.T - 1), n = t1 - o, rnd = mulberry32(seed || 20261101);
    const gauss = () => { let u = 0, v = 0; while (u === 0) u = rnd(); v = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
    const Pk = clone(P); Pk.rule.kind = rule || "exo"; const sh = new Array(inp.T).fill(0); for (let i = o + 1; i < inp.T; i++) sh[i] = P.shock_bp / 100;
    const vars = ["infl4", "infl4u", "u_pp", "g4y", "v_level", "g4rw"], draws = {}; for (const v of vars) draws[v] = [];
    for (let r = 0; r < reps; r++) {
      const Pd = clone(Pk);
      for (const k in chol) { const ch = chol[k], z = ch.names.map(gauss); ch.names.forEach((nm, i) => { let dev = 0; for (let j = 0; j <= i; j++) dev += ch.L[i][j] * z[j]; Pd.eq[k][nm] = Pk.eq[k][nm] + dev; }); }
      const base = outputs(simulate(Pd, X, inp.endo_hist, o + 1, t1, inp.R_path), X, o + 1, t1), alt = outputs(simulate(Pd, X, inp.endo_hist, o + 1, t1, inp.R_path, sh), X, o + 1, t1);
      for (const v of ["infl4", "infl4u", "g4y", "g4rw"]) draws[v].push(base[v].map((b, i) => alt[v][i] - b));
      draws.u_pp.push(base.u.map((b, i) => alt.u[i] - b)); draws.v_level.push(base.i44.map((b, i) => 100 * (Math.log(alt.i44[i]) - Math.log(b))));
    }
    const bands = {};
    for (const v of vars) {
      const b = {lo: [], hi: [], lo25: [], hi75: []};
      for (let j = 0; j < n; j++) { const col = draws[v].map(a => a[j]).filter(Number.isFinite).sort((x, y) => x - y); b.lo.push(pct(col, 5)); b.hi.push(pct(col, 95)); b.lo25.push(pct(col, 25)); b.hi75.push(pct(col, 75)); }
      bands[v] = b;
    }
    return {index: inp.index.slice(o + 1, t1 + 1), bands, reps};
  }
  // the unemployment rate at which the wage curve and the price mark-up hold together (see simulate.py ustar_series)
  function ustar(P, data, z_growth) {
    const w = P.eq.wage, pq = P.eq.price, lr = P.lr;
    const sw = ((w.s1 || 0) + (w.s2 || 0) + (w.s3 || 0)) / 4, sp = ((pq.s1 || 0) + (pq.s2 || 0) + (pq.s3 || 0)) / 4, gz = Math.log(1 + z_growth / 100);
    const out = []; let ecm_w = 0, ecm_p = 0;
    for (let i = 0; i < data.index.length; i++) {
      const pi = data.tgt[i] / 100;
      ecm_w = ((pi + gz) - w.const - w.D4z * gz - sw) / w.ecm_w_l4;
      ecm_p = ((pi / 4) * (1 - pq.Dp_l4 - pq.Dpi - pq.Dpen) - pq.const - sp) / pq.ecm_p_l1;
      out.push(Math.exp((ecm_p + lr.eta * data.t3[i] + (1 - lr.phi) * (ecm_w + data.t1[i]) - lr.phi * data.wedge[i]) / ((1 - lr.phi) * lr.gamma_u)));
    }
    return {ustar: out, ecm_w_star: ecm_w, ecm_p_star: ecm_p, sens_wedge: lr.phi / ((1 - lr.phi) * lr.gamma_u)};
  }
  return {extend, simulate, outputs, forecast, multipliers, bootstrap, lossSim, ustar, multiplierBands, ENDO};
})();
if (typeof module !== "undefined") module.exports = modelSim;
