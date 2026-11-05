"""Dynamic simulation of the estimated system: in-sample tracking, a forecast under stated exogenous assumptions,
bootstrap bands, and the permanent +100 bp policy-rate experiment under an exogenous rate and under the ABE2005 rules.

Reads model/data.csv, model/estimates.json, model/norges_bank_projections.json; writes model/simulation.json.
The core `simulate()` is written with explicit index arithmetic (no pandas) so that the JavaScript twin on the page
(`modelSim` in template.html) is a line-by-line port; `python -X utf8 model/simulate.py --selftest` prints a few
checksums that the JS test (`model/js_twin_test.js`) must reproduce.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import estimate as E

HERE = Path(__file__).resolve().parent
NaN = float("nan")
ENDO = ["w", "p", "pu", "pi", "v", "u", "y", "R", "RS"]
EXO = ["z", "g", "pf", "pstar", "pen", "oil", "t1", "t3", "Rs", "tgt", "ytrend", "d_it", "s1", "s2", "s3", "s1p", "s2p", "s3p",
       "covidq1", "covidq2", "covidq3", "covidq4", "ukrw"]
RULES = {"exo": "Exogenous policy rate (Norges Bank's published path, then constant)",
         "flx": "FLX rule: R = π̄ + r̄r + 1.5(Δ₄pu − π̄) + 0.5(Δ₄y − ḡ)  (ABE2005 Table 1, ρ = 0)",
         "sm": "SM rule: R = 0.75R₋₁ + 0.25(π̄ + r̄r) + 1.5(Δ₄pu − π̄) + 0.5(Δ₄y − ḡ)  (ABE2005 Table 1, ρ = 0.75)",
         "est": "Estimated reaction function 2004Q1–latest (reference only; NAM2026 §3.10)"}


def coefs_of(eq: dict) -> dict:
    return {c["name"]: c["est"] for c in eq["coef"]}


def default_params(est: dict) -> dict:
    """Everything the simulator needs, all of it user-adjustable on the page."""
    eqs = est["equations"]
    return {"eq": {k: coefs_of(eqs[k]) for k in ["wage", "price", "imp", "fx", "fx_level", "unemp", "output", "mm", "bridge", "rule_est"]},
            "lr": {"gamma_u": 0.1, "phi": 0.4, "eta": 1.0, "kappa_fx": 0.12, "y_g": 0.9, "y_rex": 0.16, "y_rr": 0.06, "use_alpha_v": False},
            "rule": {"kind": "exo", "theta_pi": 1.5, "theta_y": 0.5, "rho": 0.75, "rr_bar": 3.5, "pi_bar": 2.0, "g_bar": 2.5},
            "shock_bp": 100}


def extend_exogenous(d: pd.DataFrame, origin: int, T: int, assume: dict, nb: dict, idx: list) -> dict:
    """Exogenous arrays over the whole master index; beyond the data they follow the stated assumptions."""
    X = {}
    for c in EXO:
        s = d[c] if c in d else None
        arr = [float(s.iloc[i]) if s is not None and i < len(s) and not pd.isna(s.iloc[i]) else NaN for i in range(T)]
        X[c] = arr
    q = [int(p[-1]) for p in idx]
    for i in range(T):
        X["s1"][i], X["s2"][i], X["s3"][i] = float(q[i] == 1), float(q[i] == 2), float(q[i] == 3)
        pre = idx[i] < "2015Q1"
        X["s1p"][i], X["s2p"][i], X["s3p"][i] = X["s1"][i] * pre, X["s2"][i] * pre, X["s3"][i] * pre
        for c in ["covidq1", "covidq2", "covidq3", "covidq4", "ukrw"]:
            if math.isnan(X[c][i]): X[c][i] = 0.0
        if math.isnan(X["d_it"][i]): X["d_it"][i] = 1.0
        if math.isnan(X["tgt"][i]): X["tgt"][i] = 2.0
    # growth-rate assumptions (four-quarter growth keeps the seasonal pattern of unadjusted series)
    g4 = {"z": assume["z_growth"], "g": assume["g_growth"], "pf": assume["pf_infl"], "pstar": assume["pstar_infl"], "pen": assume["pen_infl"]}
    for c, gr in g4.items():
        last = max(i for i in range(T) if not math.isnan(X[c][i]))
        for i in range(last + 1, T): X[c][i] = X[c][i - 4] + math.log(1 + gr / 100)
    for c in ["oil", "t1", "t3"]:
        last = max(i for i in range(T) if not math.isnan(X[c][i]))
        for i in range(last + 1, T): X[c][i] = X[c][i - 1]
    # foreign short rate: Norges Bank's trading-partner policy-rate assumption (annual) interpolated, then constant
    last = max(i for i in range(T) if not math.isnan(X["Rs"][i]))
    path = assume.get("Rs_path") or {}
    for i in range(last + 1, T):
        yr = idx[i][:4]
        X["Rs"][i] = float(path[yr]) if yr in path else X["Rs"][i - 1]
    # HP trend continued at its mean growth over the last 40 quarters
    last = max(i for i in range(T) if not math.isnan(X["ytrend"][i]))
    gtr = (X["ytrend"][last] - X["ytrend"][last - 40]) / 40
    for i in range(last + 1, T): X["ytrend"][i] = X["ytrend"][i - 1] + gtr
    return X


def simulate(P: dict, X: dict, H: dict, t0: int, t1: int, R_path: list | None, shock: list | None = None, resid: dict | None = None) -> dict:
    """Dynamic simulation over positions t0..t1 (inclusive). H holds the endogenous history (actuals before t0).
    R_path: exogenous policy rate by position (used when rule kind is 'exo'); shock: additive path to the policy rate
    (exogenous case) or to the rule intercept; resid: optional residual add-factors {eqkey: array} for bootstrap draws."""
    Y = {k: list(H[k]) for k in ENDO}
    eq, lr, rule = P["eq"], P["lr"], P["rule"]
    sea = lambda c, t: c.get("s1", 0) * X["s1"][t] + c.get("s2", 0) * X["s2"][t] + c.get("s3", 0) * X["s3"][t]
    seap = lambda c, t: c.get("s1p", 0) * X["s1p"][t] + c.get("s2p", 0) * X["s2p"][t] + c.get("s3p", 0) * X["s3p"][t]
    dum = lambda c, t: sum(c.get(k, 0) * X[k][t] for k in ["covidq1", "covidq2", "covidq3", "covidq4", "ukrw"] if k in c)
    r = lambda k, t: (resid[k][t] if resid and k in resid else 0.0)
    for t in range(t0, t1 + 1):
        # start values: last quarter's levels
        for k in ENDO: Y[k][t] = Y[k][t - 1]
        for it in range(40):
            prev = [Y[k][t] for k in ENDO]
            w, p, pu, pi, v, u, y, R, RS = (Y[k] for k in ENDO)
            # derived (lagged) terms
            infl4 = lambda s: 100 * (p[s] - p[s - 4]); infl4s = lambda s: 100 * (X["pstar"][s] - X["pstar"][s - 4]); infl4u = lambda s: 100 * (pu[s] - pu[s - 4])
            rex = lambda s: v[s] + X["pstar"][s] - p[s]; rr = lambda s: RS[s] - infl4(s); g4y = lambda s: 100 * (y[s] - y[s - 4]); gap = lambda s: y[s] - X["ytrend"][s]
            ecm_w = lambda s: w[s] - p[s] - X["z"][s] + lr["gamma_u"] * u[s]
            ecm_p = lambda s: p[s] - (1 - lr["phi"]) * (w[s] + X["t1"][s] - X["z"][s]) - lr["phi"] * pi[s] - lr["eta"] * X["t3"][s]
            ecm_pi = lambda s: pi[s] - v[s] - X["pf"][s]
            ecm_v = lambda s: rex(s) - lr["kappa_fx"] * ((R[s] - infl4(s)) - (X["Rs"][s] - infl4s(s)))
            ecm_y = lambda s: y[s] - lr["y_g"] * X["g"][s] - lr["y_rex"] * rex(s) + lr["y_rr"] * rr(s)
            # 1 output
            c = eq["output"]
            y[t] = y[t - 1] + c["const"] + c["Dy_l1"] * (y[t - 1] - y[t - 2]) + c["Dg"] * (X["g"][t] - X["g"][t - 1]) + c["ecm_y_l1"] * ecm_y(t - 1) + sea(c, t) + dum(c, t) + r("output", t)
            # 2 unemployment
            c = eq["unemp"]
            u[t] = u[t - 1] + c["const"] + c["Du_l1"] * (u[t - 1] - u[t - 2]) + c["Du_l4"] * (u[t - 4] - u[t - 5]) + c["Dy"] * (y[t] - y[t - 1]) + c["Dy_l1"] * (y[t - 1] - y[t - 2]) \
                + c["u_l2"] * u[t - 2] + c["Dwp_l2"] * ((w[t - 2] - p[t - 2]) - (w[t - 3] - p[t - 3])) + c["rr_l2"] * rr(t - 2) + c["g4y_l2"] * g4y(t - 2) + sea(c, t) + seap(c, t) + dum(c, t) + r("unemp", t)
            # 3 policy rate
            if rule["kind"] == "exo":
                R[t] = R_path[t] + (shock[t] if shock else 0.0)
            elif rule["kind"] in ("flx", "sm"):
                rho = rule["rho"] if rule["kind"] == "sm" else 0.0
                R[t] = rho * R[t - 1] + (1 - rho) * (rule["pi_bar"] + rule["rr_bar"]) + rule["theta_pi"] * (infl4u(t) - rule["pi_bar"]) + rule["theta_y"] * (g4y(t) - rule["g_bar"]) + (shock[t] if shock else 0.0)
            else:
                c = eq["rule_est"]
                R[t] = R[t - 1] + c["const"] + c["R_l1"] * R[t - 1] + c["pigap_u"] * (infl4u(t) - X["tgt"][t]) + c["g4y"] * g4y(t) + c["u_l1"] * u[t - 1] + c["DRs"] * (X["Rs"][t] - X["Rs"][t - 1]) + c["DR_l1"] * (R[t - 1] - R[t - 2]) + (shock[t] if shock else 0.0) + r("rule_est", t)
            # 4 exchange rate
            c = eq["fx_level"] if lr["use_alpha_v"] else eq["fx"]
            dRd = X["d_it"][t] * ((R[t] - X["Rs"][t]) - (R[t - 1] - X["Rs"][t - 1]))
            v[t] = v[t - 1] + c["const"] + c["dRdiff_it"] * dRd + c["Doil"] * (X["oil"][t] - X["oil"][t - 1]) + c["Dv_l1"] * (v[t - 1] - v[t - 2]) \
                + (c["ecm_v_l1"] * ecm_v(t - 1) if lr["use_alpha_v"] else 0.0) + dum(c, t) + r("fx_level" if lr["use_alpha_v"] else "fx", t)
            # 5 import prices
            c = eq["imp"]
            pi[t] = pi[t - 1] + c["const"] + c["Dv"] * (v[t] - v[t - 1]) + c["Dpf"] * (X["pf"][t] - X["pf"][t - 1]) + c["Dv_l1"] * (v[t - 1] - v[t - 2]) \
                + c["Dpi14"] * ((pi[t - 1] - pi[t - 2]) - (pi[t - 4] - pi[t - 5])) + c["ecm_pi_l1"] * ecm_pi(t - 1) + c["rex_l1"] * rex(t - 1) + sea(c, t) + r("imp", t)
            # 6 consumer prices
            c = eq["price"]
            p[t] = p[t - 1] + c["const"] + c["Dp_l4"] * (p[t - 4] - p[t - 5]) + c["Dpi"] * (pi[t] - pi[t - 1]) + c["Dpen"] * (X["pen"][t] - X["pen"][t - 1]) + c["gap_l1"] * gap(t - 1) \
                + c["ecm_p_l1"] * ecm_p(t - 1) + sea(c, t) + dum(c, t) + r("price", t)
            # 7 wages (four-quarter form)
            c = eq["wage"]
            w[t] = w[t - 4] + c["const"] + c["D4p_tgt"] * ((p[t - 1] - p[t - 5]) - X["tgt"][t] / 100) + c["D4z"] * (X["z"][t] - X["z"][t - 4]) + c["D4u"] * (u[t] - u[t - 4]) \
                + c["ecm_w_l4"] * ecm_w(t - 4) + sea(c, t) + r("wage", t)
            # 8 money-market rate
            c = eq["mm"]
            RS[t] = RS[t - 1] + c["const"] + c["DR"] * (R[t] - R[t - 1]) + c["RS_l1"] * RS[t - 1] + c["R_l1"] * R[t - 1] + c["DRs"] * (X["Rs"][t] - X["Rs"][t - 1]) + c["Rs_l1"] * X["Rs"][t - 1] + dum(c, t) + r("mm", t)
            # 9 CPI-ATE bridge
            c = eq["bridge"]
            pu[t] = pu[t - 1] + c["const"] + c["Dp"] * (p[t] - p[t - 1]) + c["Dpen"] * (X["pen"][t] - X["pen"][t - 1]) + c["Dt3"] * (X["t3"][t] - X["t3"][t - 1]) \
                + c["Dpu_l1"] * (pu[t - 1] - pu[t - 2]) + c["Dpu_l4"] * (pu[t - 4] - pu[t - 5]) + r("bridge", t)
            if max(abs(Y[k][t] - pv) for k, pv in zip(ENDO, prev)) < 1e-11: break
    return Y


def outputs(Y: dict, X: dict, t0: int, t1: int) -> dict:
    """Reporting variables over t0..t1: annual CPI and CPI-ATE inflation, unemployment rate, four-quarter GDP growth,
    log exchange rate, policy and money-market rates, real-wage growth (four-quarter), wage growth."""
    p, pu, u, y, v, w, R, RS = (Y[k] for k in ["p", "pu", "u", "y", "v", "w", "R", "RS"])
    rng = range(t0, t1 + 1)
    return {"infl4": [100 * (p[t] - p[t - 4]) for t in rng], "infl4u": [100 * (pu[t] - pu[t - 4]) for t in rng],
            "u": [math.exp(u[t]) for t in rng], "g4y": [100 * (y[t] - y[t - 4]) for t in rng], "v": [100 * (v[t] - v[t - 4]) for t in rng],
            "i44": [math.exp(v[t]) for t in rng], "R": [R[t] for t in rng], "RS": [RS[t] for t in rng],
            "g4w": [100 * (w[t] - w[t - 4]) for t in rng], "g4rw": [100 * ((w[t] - p[t]) - (w[t - 4] - p[t - 4])) for t in rng],
            "gap": [100 * (y[t] - X["ytrend"][t]) for t in rng]}


def loss_stats(P: dict, X: dict, H: dict, o: int, h: int, R_path: list, Rm: np.ndarray, keys: list, reps: int, seed: int, rules=("exo", "flx", "sm", "est")) -> dict:
    """ABE2005 eq (10) ingredients by stochastic simulation: for each policy-rate setting, the same `reps` residual draws
    (re-seeded per rule, so every rule faces identical shocks) over `h` quarters; variances pooled over quarters and draws
    of CPI-ATE inflation (Δ₄pu), four-quarter GDP growth (Δ₄y) and the quarterly change of the policy rate (ΔR), plus the
    mean squared deviation of Δ₄pu from the target and the mean levels. The loss L = V[Δ₄pu] + λV[Δ₄y] + κV[ΔR] is formed on
    the page from these, with λ and κ chosen there. Mirrored line by line in modelsim.js (lossSim)."""
    T = len(X["s1"]); n = len(Rm); out = {}
    for kind in rules:
        Pk = json.loads(json.dumps(P)); Pk["rule"]["kind"] = kind
        rng = np.random.default_rng(seed)
        pu, gy, dR, pi_ = [], [], [], []
        for rep in range(reps):
            pick = rng.integers(0, n, size=h)
            res = {k: [0.0] * T for k in keys}
            for j, t in enumerate(range(o + 1, o + h + 1)):
                for ki, k in enumerate(keys): res[k][t] = float(Rm[pick[j], ki])
            Yb = simulate(Pk, X, H, o + 1, o + h, R_path, resid=res); ob = outputs(Yb, X, o + 1, o + h)
            pu += ob["infl4u"]; gy += ob["g4y"]; pi_ += ob["infl4"]; dR += [Yb["R"][t] - Yb["R"][t - 1] for t in range(o + 1, o + h + 1)]
        tgt = P["rule"]["pi_bar"]
        var = lambda a: float(np.var(np.array(a)))
        out[kind] = {"var_pu": var(pu), "var_gy": var(gy), "var_dR": var(dR), "msd_pu": float(np.mean((np.array(pu) - tgt) ** 2)),
                     "mean_pu": float(np.mean(pu)), "mean_gy": float(np.mean(gy)), "mean_pi": float(np.mean(pi_)), "mean_absdR": float(np.mean(np.abs(dR)))}
    return out


def multiplier_bands(P: dict, X: dict, H: dict, o: int, h: int, R_path: list, est: dict, keys: list, reps: int, seed: int, rule: str = "exo") -> dict:
    """Coefficient uncertainty of the +100 bp responses: in every draw each estimated equation's coefficients are perturbed by
    L·z (L the Cholesky factor of its OLS covariance, z standard normal; the imposed long-run coefficients are fixed and the
    draws are independent across equations), the baseline and the shocked path are simulated with the same coefficients and
    their difference collected; 5–95% and 25–75% ranges. Residual resampling would give zero width because the system is
    linear in logs, so this is the uncertainty that matters for the multipliers. Mirrored in modelsim.js (multiplierBands)."""
    T = len(X["s1"]); rng = np.random.default_rng(seed); vars_ = ["infl4", "infl4u", "u_pp", "g4y", "v_level", "g4rw"]; draws = {v: [] for v in vars_}
    Pk = json.loads(json.dumps(P)); Pk["rule"]["kind"] = rule
    sh = [0.0] * T
    for i in range(o + 1, T): sh[i] = P["shock_bp"] / 100
    for rep in range(reps):
        Pd = json.loads(json.dumps(Pk))
        for k in keys:
            ch = est["equations"][k]["chol"]; L = np.array(ch["L"]); z = rng.standard_normal(len(ch["names"])); dev = L @ z
            for i, n in enumerate(ch["names"]): Pd["eq"][k][n] = Pk["eq"][k][n] + float(dev[i])
        base = outputs(simulate(Pd, X, H, o + 1, o + h, R_path), X, o + 1, o + h); alt = outputs(simulate(Pd, X, H, o + 1, o + h, R_path, shock=sh), X, o + 1, o + h)
        for v in ["infl4", "infl4u", "g4y", "g4rw"]: draws[v].append([alt[v][i] - base[v][i] for i in range(h)])
        draws["u_pp"].append([alt["u"][i] - base["u"][i] for i in range(h)]); draws["v_level"].append([100 * (math.log(alt["i44"][i]) - math.log(base["i44"][i])) for i in range(h)])
    out = {}
    for v, a_ in draws.items():
        A = np.array(a_); A = np.where(np.isfinite(A), A, np.nan)
        out[v] = {"lo": rnd(np.nanpercentile(A, 5, axis=0).tolist(), 4), "hi": rnd(np.nanpercentile(A, 95, axis=0).tolist(), 4), "lo25": rnd(np.nanpercentile(A, 25, axis=0).tolist(), 4), "hi75": rnd(np.nanpercentile(A, 75, axis=0).tolist(), 4)}
    return out


def ustar_series(P: dict, data: dict, z_growth: float) -> dict:
    """The rate of unemployment at which the wage curve (w − p − z = −γ_u·u + μ_w) and the price mark-up
    (p = (1 − ϕ)(w + τ1 − z) + ϕ·pi + η·τ3 + μ_p) hold at the same time, given the wedge p − pi and the tax rates:
        u* = [μ_p + η·τ3 + (1 − ϕ)(μ_w + τ1) − ϕ(p − pi)] / ((1 − ϕ)γ_u),
    with μ_w and μ_p the steady-state values of the two EqCM terms implied by the estimated wage and price equations at
    inflation on target and productivity growing at `z_growth` (BJN2003 §2.3, BEJN2005 ch. 6). Mirrored in modelsim.js."""
    w, pq, lr = P["eq"]["wage"], P["eq"]["price"], P["lr"]
    sw = (w.get("s1", 0) + w.get("s2", 0) + w.get("s3", 0)) / 4; sp = (pq.get("s1", 0) + pq.get("s2", 0) + pq.get("s3", 0)) / 4
    gz = math.log(1 + z_growth / 100); out, mw, mp = [], [], []
    for i in range(len(data["index"])):
        pi = data["tgt"][i] / 100
        ecm_w = ((pi + gz) - w["const"] - w["D4z"] * gz - sw) / w["ecm_w_l4"]
        ecm_p = ((pi / 4) * (1 - pq["Dp_l4"] - pq["Dpi"] - pq["Dpen"]) - pq["const"] - sp) / pq["ecm_p_l1"]
        us = (ecm_p + lr["eta"] * data["t3"][i] + (1 - lr["phi"]) * (ecm_w + data["t1"][i]) - lr["phi"] * data["wedge"][i]) / ((1 - lr["phi"]) * lr["gamma_u"])
        out.append(math.exp(us)); mw.append(ecm_w); mp.append(ecm_p)
    return {"ustar": out, "ecm_w_star": mw[-1], "ecm_p_star": mp[-1], "sens_wedge": lr["phi"] / ((1 - lr["phi"]) * lr["gamma_u"])}


def rnd(o, n=5):
    if isinstance(o, float): return None if math.isnan(o) else round(o, n)
    if isinstance(o, list): return [rnd(x, n) for x in o]
    if isinstance(o, dict): return {k: rnd(v, n) for k, v in o.items()}
    return o


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--track-start", default="2001Q1"); ap.add_argument("--out", default=str(HERE / "simulation.json"))
    a = ap.parse_args(argv)
    est = json.loads((HERE / "estimates.json").read_text(encoding="utf-8")); cfg = est["config"]
    raw = pd.read_csv(HERE / "data.csv", index_col=0); raw.index = pd.PeriodIndex(raw.index, freq="Q")
    d, _ = E.build(raw, cfg)
    nb = json.loads((HERE / "norges_bank_projections.json").read_text(encoding="utf-8"))
    nam = json.loads((HERE / "nam_forecasts.json").read_text(encoding="utf-8"))
    # master index 1995Q1 .. origin + 48 quarters
    origin_q = est["last_quarter"]["qna"]; origin = pd.Period(origin_q, "Q")
    idx = [str(q) for q in pd.period_range("1995Q1", origin + 48, freq="Q")]; T = len(idx); pos = {q: i for i, q in enumerate(idx)}
    d = d.reindex(pd.PeriodIndex(idx, freq="Q"))
    # assumptions
    nbv = nb["variables"]
    rs_path = {x["period"]: x["value"] for x in nbv.get("trading_partner_policy_rate", []) if "Q" not in x["period"] and "M" not in x["period"]}
    z10 = float(100 * (d.z.dropna().iloc[-1] - d.z.dropna().iloc[-41]) / 10); g10 = float(100 * (d.g.dropna().iloc[-1] - d.g.dropna().iloc[-41]) / 10)
    assume = {"z_growth": round(z10, 2), "g_growth": round(g10, 2), "pf_infl": 2.0, "pstar_infl": 2.0, "pen_infl": 2.0, "Rs_path": rs_path,
              "labels": {"z_growth": "Productivity z: four-quarter growth, % (default = average of the last ten years)",
                         "g_growth": "Public consumption g: four-quarter growth, % (default = average of the last ten years)",
                         "pf_infl": "Foreign producer prices pf: four-quarter inflation, %", "pstar_infl": "Foreign consumer prices p*: four-quarter inflation, %",
                         "pen_infl": "Energy prices pe: four-quarter inflation, %",
                         "Rs_path": "Foreign short rate R*: Norges Bank's trading-partner policy-rate assumption by year (MPR 3/26 Table 3), then constant",
                         "oil": "Oil price: constant at the last quarter", "t1_t3": "Tax wedges τ1, τ3: constant at the last quarter",
                         "ytrend": "HP trend of mainland GDP continued at its mean growth over the last 40 quarters (the gap is y − trend)",
                         "R": "Policy rate: Norges Bank's MPR 3/26 quarterly path to 2030Q2, then constant (exogenous-rate case)"}}
    X = extend_exogenous(d, pos[origin_q], T, assume, nb, idx)
    _yl = max(i for i in range(T) if not pd.isna(d.ytrend.iloc[i])); gtr_global = (X["ytrend"][_yl] - X["ytrend"][_yl - 40]) / 40
    H = {k: [float(x) if not pd.isna(x) else NaN for x in d[k]] for k in ENDO}
    P = default_params(est)
    # policy-rate path: actual to the origin (and 2026Q3 if known), then Norges Bank's projection, then constant
    R_path = list(H["R"]); nbR = {x["period"]: x["value"] for x in nbv["policy_rate"] if "Q" in x["period"]}
    for i in range(pos[origin_q] + 1, T):
        R_path[i] = float(nbR[idx[i]]) if idx[i] in nbR else R_path[i - 1]
    o = pos[origin_q]; h_end = o + 16; s_end = o + 48
    out = {"built": pd.Timestamp.today().strftime("%Y-%m-%d"), "index": idx, "origin": origin_q, "horizon": [idx[o + 1], idx[h_end]], "shock_horizon": [idx[o + 1], idx[s_end]],
           "params": P, "assumptions": assume, "rules": RULES, "config": cfg}
    # ---- history for the charts (reporting variables on actual data)
    first = pos["1996Q1"]; last_m = max(i for i in range(T) if not math.isnan(H["p"][i]))
    Hc = {k: [x if not math.isnan(x) else (H[k][i - 1] if i and not math.isnan(H[k][i - 1]) else NaN) for i, x in enumerate(H[k])] for k in ENDO}  # pad ragged edge for display only
    hist = outputs(H, X, first, o); hist_m = outputs(Hc, X, o + 1, last_m)
    out["history"] = {"index": idx[first:o + 1], **rnd(hist, 4)}
    out["ragged"] = {"index": idx[o + 1:last_m + 1], **rnd({k: v for k, v in hist_m.items() if k in ("infl4", "infl4u", "v", "i44", "R", "RS")}, 4),
                     "note": "Monthly series (CPI, CPI-ATE, I-44, rates) already observed for quarters after the national-accounts origin."}
    # ---- in-sample dynamic tracking: exogenous actual, R actual, all endogenous simulated from track-start
    ts = pos[a.track_start]
    Yt = simulate(P, X, H, ts, o, R_path)
    out["tracking"] = {"start": a.track_start, "index": idx[ts:o + 1], "sim": rnd(outputs(Yt, X, ts, o), 4), "actual": rnd(outputs(H, X, ts, o), 4),
                       "note": "Deterministic dynamic simulation from the start quarter with every exogenous variable and the policy rate at their actual values; no residuals added back, so the paths show how far the system drifts from the data on its own dynamics (BJN2003 Figure 7, NAM2026 §2.3 practice)."}
    # ---- forecast under each rule
    out["forecast"] = {}
    for kind in ["exo", "flx", "sm", "est"]:
        Pk = json.loads(json.dumps(P)); Pk["rule"]["kind"] = kind
        Yf = simulate(Pk, X, H, o + 1, h_end, R_path)
        out["forecast"][kind] = rnd(outputs(Yf, X, o + 1, h_end), 4)
    out["forecast"]["index"] = idx[o + 1:h_end + 1]
    # ---- bootstrap bands for the exogenous-rate forecast: resample residual quarters jointly across equations
    eqs = est["equations"]; keys = ["wage", "price", "imp", "fx", "unemp", "output", "mm", "bridge"]
    common = sorted(set.intersection(*[set(eqs[k]["dates"]) for k in keys]))
    Rm = np.array([[eqs[k]["resid"][eqs[k]["dates"].index(q)] for k in keys] for q in common])
    rng = np.random.default_rng(20261031); draws = {v: [] for v in ["infl4", "infl4u", "u", "g4y", "v", "R", "RS", "g4w"]}
    for rep in range(a.reps):
        pick = rng.integers(0, len(common), size=h_end - o)
        res = {k: [0.0] * T for k in keys}
        for j, t in enumerate(range(o + 1, h_end + 1)):
            for ki, k in enumerate(keys): res[k][t] = float(Rm[pick[j], ki])
        Yb = simulate(P, X, H, o + 1, h_end, R_path, resid=res); ob = outputs(Yb, X, o + 1, h_end)
        for v in draws: draws[v].append(ob[v])
    out["bands"] = {v: {"lo": rnd(np.percentile(np.array(a_), 5, axis=0).tolist(), 4), "hi": rnd(np.percentile(np.array(a_), 95, axis=0).tolist(), 4),
                        "lo25": rnd(np.percentile(np.array(a_), 25, axis=0).tolist(), 4), "hi75": rnd(np.percentile(np.array(a_), 75, axis=0).tolist(), 4)} for v, a_ in draws.items()}
    out["bands"]["note"] = f"{a.reps} bootstrap replications: residual vectors of the eight estimated equations resampled by quarter (keeping their cross-equation correlation) and added to the forecast quarters; 5–95% and 25–75% ranges of the resulting paths. Coefficient uncertainty is not included (NAM2026 reports 90% bands from stochastic simulation)."
    # ---- ABE2005 loss-function ingredients by stochastic simulation, 24 quarters, same draws for every rule
    LH = 24
    out["loss"] = {"h": LH, "reps": a.reps, "seed": 20261031, "rules": rnd(loss_stats(P, X, H, o, LH, R_path, Rm, keys, a.reps, 20261031), 5),
                   "note": (f"{a.reps} stochastic simulations of {LH} quarters from the origin under each policy-rate setting, with identical residual draws (the eight equations' residual vectors "
                            "resampled by quarter) so that the rules face the same shocks. V[·] is the variance pooled over quarters and draws, as in the counterfactual simulations of "
                            "ABE2005 eq (10); the mean squared deviation of CPI-ATE inflation from the target is given beside it because the variance ignores a biased path. "
                            "Coefficient uncertainty is not included.")}
    # ---- the equilibrium rate of unemployment implied by the wage curve and the price mark-up
    ud = d.loc[pd.Period("1996Q1", "Q"):origin]
    udata = {"index": [str(q) for q in ud.index], "wedge": rnd([float(x) for x in (ud.p - ud.pi)], 6), "t1": rnd([float(x) for x in ud.t1], 6), "t3": rnd([float(x) for x in ud.t3], 6), "tgt": [float(x) for x in ud.tgt],
             "u": rnd([float(math.exp(x)) for x in ud.u], 4)}
    out["ustar"] = {"data": udata, "z_growth": assume["z_growth"], **rnd(ustar_series(P, udata, assume["z_growth"]), 5),
                    "note": ("u* is the unemployment rate at which the imposed wage curve and price mark-up hold together, given the actual wedge between consumer and import prices "
                             "and the actual tax rates; the constants of the two long-run relations are the steady-state values of the EqCM terms implied by the estimated wage and "
                             "price equations with inflation on target and productivity growing at the assumed rate. It is not an estimate of a NAIRU: in this model the equilibrium "
                             "rate moves with the real exchange rate and the terms of trade (BJN2003 §2.3; Bårdsen, Eitrheim, Jansen and Nymoen 2005, ch. 6).")}
    # ---- +100 bp experiment: differences from the baseline, 48 quarters, per rule
    out["shock"] = {"index": idx[o + 1:s_end + 1]}
    for kind in ["exo", "flx", "sm"]:
        Pk = json.loads(json.dumps(P)); Pk["rule"]["kind"] = kind
        base = outputs(simulate(Pk, X, H, o + 1, s_end, R_path), X, o + 1, s_end)
        sh = [0.0] * T
        for i in range(o + 1, T): sh[i] = P["shock_bp"] / 100
        alt = outputs(simulate(Pk, X, H, o + 1, s_end, R_path, shock=sh), X, o + 1, s_end)
        out["shock"][kind] = rnd({v: [alt[v][i] - base[v][i] for i in range(len(base[v]))] for v in ["infl4", "infl4u", "u", "g4y", "v", "R", "RS", "g4rw", "gap"]}, 4)
        # level of the exchange rate and of u in per cent of baseline
        out["shock"][kind]["v_level"] = rnd([100 * (math.log(alt["i44"][i]) - math.log(base["i44"][i])) for i in range(len(base["i44"]))], 4)
        out["shock"][kind]["u_pp"] = rnd([alt["u"][i] - base["u"][i] for i in range(len(base["u"]))], 4)
    out["shock"]["bands"] = {"rule": "exo", "reps": 1000, "seed": 20261101, **multiplier_bands(P, X, H, o, s_end - o, R_path, est, keys, 1000, 20261101, "exo"),
                            "note": ("Coefficient uncertainty, exogenous-rate case: 1000 draws of every estimated equation's coefficients from its OLS sampling distribution (Cholesky factor of the "
                                     "covariance; imposed long-run coefficients fixed; draws independent across equations), each draw simulated with and without the shock; 25–75% and 5–95% "
                                     "ranges of the differences. Residual resampling would give no width here because the system is linear in logs. The outer range is heavy-tailed: a few draws have "
                                     "near-unstable dynamics, so the interquartile range is the robust reading.")}
    out["shock"]["note"] = ("Permanent +100 bp to the policy rate from the first forecast quarter (exogenous case) or to the rule's intercept (FLX, SM), "
                            "shown as differences from the baseline path; the system is linear in logs, so the multipliers do not depend on the baseline. "
                            "Published comparators: BJN2003 §6.1 (a permanent +1 point in RS lowers annual inflation by about 0.4 point in the long run); "
                            "BN2008 Figure 5 (impact appreciation about 3%, inflation multiplier approaching −1 point after four years).")
    # ---- comparators
    out["norges_bank"] = {"report": nb["report"], "published": nb["published"], "url": nb["url"], "variables": {k: [x for x in nbv[k] if "Q" in x["period"]] for k in ["policy_rate", "cpi_inflation", "cpi_ate_inflation", "unemployment_registered", "mainland_gdp_growth", "i44", "output_gap"] if k in nbv},
                          "annual": {k: [x for x in nbv[k] if "Q" not in x["period"] and "M" not in x["period"]] for k in nbv}}
    out["nam"] = {"status": nam.get("model_status_2026"), "publications": [{"source": p["source"], "published": p["published"], "url": p.get("url"), "variables": p["variables"], "assumptions": p.get("exogenous_assumptions")} for p in nam["publications"][:2]]}
    # annual averages of the exogenous-rate forecast for the comparison table
    def annual(vals, index):
        yrs = {}
        for q, v in zip(index, vals): yrs.setdefault(q[:4], []).append(v)
        return {y: round(sum(v) / len(v), 2) for y, v in yrs.items() if len(v) == 4}
    fi = out["forecast"]["index"]; fe = out["forecast"]["exo"]
    out["annual"] = {"model_exo": {k: annual(fe[k], fi) for k in ["infl4", "infl4u", "u", "g4y", "R"]}}
    # ---- inputs for the JS twin
    exo_last = {}
    for k in ["z", "g", "pf", "pstar", "pen", "oil", "t1", "t3", "Rs", "ytrend"]:
        s_ = d[k]; exo_last[k] = max(i for i in range(T) if not pd.isna(s_.iloc[i])) - (o - 8)
    out["sim_inputs"] = {"exo": rnd({k: X[k][o - 8:] for k in EXO}, 8), "exo_last": exo_last, "endo_hist": rnd({k: H[k][o - 8:o + 1] for k in ENDO}, 8), "R_path": rnd(R_path[o - 8:], 4),
                         "offset": o - 8, "origin_pos": 8, "T": T - (o - 8), "index": idx[o - 8:], "ytrend_growth": rnd(gtr_global, 10),
                         "note": "Arrays start eight quarters before the origin (position 8) so that every lag the equations use is available."}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print("origin", origin_q, "horizon", out["horizon"], "written", a.out, "size", Path(a.out).stat().st_size)
    print("forecast exo infl4:", [round(x, 2) for x in out["forecast"]["exo"]["infl4"]])
    print("forecast exo u:", [round(x, 2) for x in out["forecast"]["exo"]["u"]])
    print("forecast exo g4y:", [round(x, 2) for x in out["forecast"]["exo"]["g4y"]])
    print("annual", out["annual"])
    print("shock exo infl4 @4,8,16,32,48:", [round(out["shock"]["exo"]["infl4"][i - 1], 3) for i in (4, 8, 16, 32, 48)])
    print("shock exo v_level @1,4,48:", [round(out["shock"]["exo"]["v_level"][i - 1], 3) for i in (1, 4, 48)], " u_pp @8,48:", [round(out["shock"]["exo"]["u_pp"][i - 1], 3) for i in (8, 48)])
    print("shock exo g4y @4,8:", [round(out["shock"]["exo"]["g4y"][i - 1], 3) for i in (4, 8)])
    print("multiplier bands infl4 @48: lo/hi", out["shock"]["bands"]["infl4"]["lo"][47], out["shock"]["bands"]["infl4"]["hi"][47], " v_level @1:", out["shock"]["bands"]["v_level"]["lo"][0], out["shock"]["bands"]["v_level"]["hi"][0])
    print("loss (exo/flx/sm/est) var_pu:", [round(out["loss"]["rules"][k]["var_pu"], 3) for k in ["exo", "flx", "sm", "est"]], " var_dR:", [round(out["loss"]["rules"][k]["var_dR"], 3) for k in ["exo", "flx", "sm", "est"]])
    print("u* last / actual u last:", round(out["ustar"]["ustar"][-1], 2), round(udata["u"][-1], 2), " sensitivity to the wedge", round(out["ustar"]["sens_wedge"], 2))
    print("tracking end: sim vs actual infl4", round(out["tracking"]["sim"]["infl4"][-1], 2), round(out["tracking"]["actual"]["infl4"][-1], 2), " u", round(out["tracking"]["sim"]["u"][-1], 2), round(out["tracking"]["actual"]["u"][-1], 2))
    if a.selftest:
        Yf = simulate(P, X, H, o + 1, h_end, R_path); ob = outputs(Yf, X, o + 1, h_end)
        print("SELFTEST", json.dumps({k: round(sum(ob[k]), 6) for k in ["infl4", "u", "g4y", "v", "RS"]}))
    return out


if __name__ == "__main__":
    main()
