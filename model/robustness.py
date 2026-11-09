"""Further robustness exercises on the estimated equations, in the tradition of the model's authors:

  1. Impulse- and step-indicator saturation (IIS, SIS; Hendry, Johansen and Santos 2008; Castle, Doornik and Hendry 2012)
     on every core equation, split-half algorithm with backward elimination, so that the data rather than the modeller
     locate the outliers and level shifts; compared with the hand-picked Covid dummies.
  2. Super-exogeneity tests (Engle and Hendry 1993; Hendry and Santos 2010): indicators retained by IIS/SIS in the marginal
     models of the policy rate, the exchange rate and the conditioning variables are added to the conditional equations
     and tested jointly; rejection means the conditional equation's parameters shifted with the marginal process, which is
     what the Lucas critique would predict (Bårdsen, Eitrheim, Jansen and Nymoen 2005, ch. 9; Castle, Doornik, Hendry and
     Nymoen 2014).
  3. New Keynesian Phillips curve by 2SLS/GMM with the encompassing tests of Bårdsen, Jansen and Nymoen (2004, OBES):
     the hybrid NKPC on its own, the NKPC with the EqCM's variables added, and the EqCM with the instrumented lead added.
  4. Recursive Johansen analysis (Hansen and Johansen 1999 in spirit): trace statistics and the first cointegrating vector
     re-estimated on samples ending at every quarter from 2005Q4, for the wage and the price systems.
  5. 2SLS for the equations with a contemporaneous endogenous regressor (price: Δpi; import prices: Δv; unemployment: Δy),
     with first-stage F and a Durbin–Wu–Hausman test against OLS.

Reads model/data.csv and model/estimates.json; writes model/robustness.json.  python -X utf8 model/robustness.py
"""
from __future__ import annotations
import json, math, sys, time, warnings
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
import estimate as E

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
CORE = ["wage", "price", "imp", "fx", "unemp", "output", "mm", "bridge"]
NAMES = {"wage": "Wages", "price": "Consumer prices", "imp": "Import prices", "fx": "Exchange rate", "unemp": "Unemployment", "output": "Mainland GDP", "mm": "Money-market rate", "bridge": "CPI-ATE bridge"}


def ols(y, X):
    return sm.OLS(y, X).fit()


def design(d: pd.DataFrame, eq: dict, est_eq: dict, end: str, with_dummies: bool):
    """y vector and regressor frame (constant first) of an equation as estimated, optionally without the impulse dummies."""
    y = eq["lhs"]; X = [c["name"] for c in est_eq["coef"] if c["name"] != "const" and (with_dummies or c["kind"] != "dummy")]
    df = d.loc[eq["start"]:end, [y] + X].dropna()
    return df[y], sm.add_constant(df[X], has_constant="add"), df.index

# ----------------------------------------------------------------------------------------------- 1. IIS / SIS

def saturate(yv: np.ndarray, Xb: np.ndarray, index, kind: str, alpha: float, nblocks: int) -> dict:
    T = len(yv); k = Xb.shape[1]
    if kind == "iis":
        I = np.eye(T); names = [str(q) for q in index]
    else:
        I = np.array([[1.0 if t >= j else 0.0 for j in range(1, T)] for t in range(T)]); names = [str(index[j]) for j in range(1, T)]
    cols = list(range(I.shape[1])); blocks = [list(b) for b in np.array_split(np.array(cols), nblocks)]
    cv = lambda dfr: float(stats.t.ppf(1 - alpha / 2, max(dfr, 1)))
    retained = []
    for b in blocks:
        Z = np.column_stack([Xb, I[:, b]]); m = ols(yv, Z); tv = m.tvalues[k:]
        retained += [b[i] for i in range(len(b)) if abs(tv[i]) > cv(m.df_resid)]
    sel = sorted(set(retained))
    while sel:                                   # backward elimination on the union of the blocks' survivors
        Z = np.column_stack([Xb, I[:, sel]]); m = ols(yv, Z); tv = m.tvalues[k:]
        worst = int(np.argmin(np.abs(tv)))
        if abs(tv[worst]) > cv(m.df_resid): break
        sel.pop(worst)
    m0 = ols(yv, Xb); mf = ols(yv, np.column_stack([Xb, I[:, sel]])) if sel else m0
    out = {"kind": kind, "alpha": alpha, "blocks": nblocks, "candidates": I.shape[1], "expected_spurious": round(alpha * I.shape[1], 2),
           "retained": [{"date": names[j], "coef": round(float(mf.params[k + i]), 5), "t": round(float(mf.tvalues[k + i]), 2)} for i, j in enumerate(sel)],
           "sigma_before": float(math.sqrt(m0.scale)), "sigma_after": float(math.sqrt(mf.scale))}
    # the other coefficients before and after, for the stability reading
    out["coef_shift"] = [{"name": n, "before": round(float(m0.params[i]), 5), "after": round(float(mf.params[i]), 5), "se_before": round(float(m0.bse[i]), 5)} for i, n in enumerate(["const"] + list(getattr(Xb, "columns", [])))] if hasattr(Xb, "columns") else None
    return out


def saturation_block(d, eqs, est, end):
    out = {}
    for k in CORE:
        y, X, index = design(d, eqs[k], est["equations"][k], end, with_dummies=False)
        yv, Xb = y.values, X.values
        iis = saturate(yv, Xb, index, "iis", 0.01, 2); sis = saturate(yv, Xb, index, "sis", 0.01, 4)
        for r in (iis, sis):
            r["coef_shift"] = [{"name": n, "before": None, "after": None} for n in []]
        # coefficient shifts: estimated regressors before/after adding the retained impulses
        m0 = ols(yv, Xb)
        def shifts(res):
            if not res["retained"]: return []
            idx = [str(q) for q in index]
            if res["kind"] == "iis": I = np.column_stack([np.array([1.0 if str(q) == r["date"] else 0.0 for q in index]) for r in res["retained"]])
            else: I = np.column_stack([np.array([1.0 if str(q) >= r["date"] else 0.0 for q in index]) for r in res["retained"]])
            mf = ols(yv, np.column_stack([Xb, I]))
            return [{"name": n, "before": round(float(m0.params[i]), 4), "after": round(float(mf.params[i]), 4), "se": round(float(m0.bse[i]), 4)} for i, n in enumerate(X.columns) if n != "const" and not n.startswith("s")]
        iis["coef_shift"] = shifts(iis); sis["coef_shift"] = shifts(sis)
        hand = [c["name"] for c in est["equations"][k]["coef"] if c["kind"] == "dummy"]
        out[k] = {"label": NAMES[k], "T": len(yv), "hand_dummies": hand, "iis": iis, "sis": sis}
    out["note"] = ("Split-half impulse-indicator saturation (two blocks) and step-indicator saturation (four blocks) at α = 0.01 with backward elimination on the union of "
                   "the blocks' survivors; the equations are taken as estimated but without the hand-picked Covid dummies, so that the data locate the breaks. Expected number "
                   "of spurious retentions = α × candidates. σ̂ before and after; coefficient shifts show how far the estimated regressors move when the retained indicators are added.")
    return out

# ----------------------------------------------------------------------------------------------- 2. super-exogeneity

def superexo_block(d, eqs, est, end):
    start = est["config"]["start"]
    marg = {"DR": ("policy rate ΔR", 4, False), "Dv": ("exchange rate Δv", 4, False), "Dpi": ("import prices Δpi", 4, True), "Dpen": ("energy prices Δpe", 4, True),
            "D4z": ("productivity Δ₄z", 4, False), "D4u": ("unemployment Δ₄u", 4, False), "Dy": ("GDP Δy", 4, True)}
    found = {}
    for c, (label, p, seas) in marg.items():
        df = d.loc[start:end].copy()
        cols = [f"{c}_l{j}" for j in range(1, p + 1)]
        for j in range(1, p + 1): df[f"{c}_l{j}"] = d[c].shift(j)
        X = cols + (["s1", "s2", "s3"] if seas else [])
        df = df[[c] + X].dropna(); yv = df[c].values; Xb = sm.add_constant(df[X], has_constant="add").values
        iis = saturate(yv, Xb, df.index, "iis", 0.01, 2); sis = saturate(yv, Xb, df.index, "sis", 0.01, 4)
        found[c] = {"label": label, "model": f"AR({p}){' with seasonals' if seas else ''}", "T": len(yv), "impulses": [r["date"] for r in iis["retained"]], "steps": [r["date"] for r in sis["retained"]]}
    def indicators(cs, index):
        cols = {}
        for c in cs:
            for q in found[c]["impulses"]: cols[f"I:{q}"] = np.array([1.0 if str(t) == q else 0.0 for t in index])
            for q in found[c]["steps"]: cols[f"S:{q}"] = np.array([1.0 if str(t) >= q else 0.0 for t in index])
        return cols
    tests = []
    sets = {"wage": [("conditioning variables", ["D4z", "D4u"]), ("policy and exchange rate", ["DR", "Dv"])],
            "price": [("conditioning variables", ["Dpi", "Dpen"]), ("policy and exchange rate", ["DR", "Dv"])],
            "imp": [("conditioning variable", ["Dv"]), ("policy rate", ["DR"])],
            "unemp": [("conditioning variable", ["Dy"]), ("policy and exchange rate", ["DR", "Dv"])],
            "output": [("policy and exchange rate", ["DR", "Dv"])]}
    for k, lst in sets.items():
        y, X, index = design(d, eqs[k], est["equations"][k], end, with_dummies=True)
        for label, cs in lst:
            ind = indicators(cs, index)
            # drop indicators collinear with what is already in the equation (e.g. a Covid impulse already included)
            keep = {n: v for n, v in ind.items() if v.std() > 0 and not any(np.allclose(v, X[c].values) for c in X.columns)}
            m0 = ols(y.values, X.values)
            if not keep:
                tests.append({"eq": k, "label": NAMES[k], "marginals": label, "vars": [found[c]["label"] for c in cs], "n_ind": 0, "F": None, "df": None, "p": None, "verdict": "no breaks found in the marginal models"}); continue
            Z = np.column_stack([X.values] + list(keep.values())); m1 = ols(y.values, Z); q = len(keep)
            F = ((m0.ssr - m1.ssr) / q) / (m1.ssr / m1.df_resid); p = float(1 - stats.f.cdf(F, q, m1.df_resid))
            tests.append({"eq": k, "label": NAMES[k], "marginals": label, "vars": [found[c]["label"] for c in cs], "n_ind": q, "indicators": list(keep.keys()), "F": round(float(F), 2), "df": [q, int(m1.df_resid)], "p": round(p, 4),
                          "verdict": "rejected: the equation shifted with the marginal process" if p < 0.05 else "not rejected: invariant to the breaks found"})
    return {"marginals": found, "tests": tests,
            "note": ("Hendry–Santos procedure: IIS and SIS (α = 0.01) on an AR(4) model of each marginal variable locate its outliers and level shifts; those indicators are then added to the "
                     "conditional equation and tested jointly by F. A rejection says the conditional equation's parameters moved when the marginal process did, as the Lucas critique would "
                     "imply for the policy and exchange-rate processes; no rejection supports super-exogeneity of the conditioning variables for the parameters of interest. "
                     "The test has power only against the breaks the marginal models actually reveal; indicators already in the equation are left out.")}

# ----------------------------------------------------------------------------------------------- 3. NKPC and encompassing

def tsls(y: np.ndarray, X: np.ndarray, Z: np.ndarray, names: list, lags: int = 4) -> dict:
    """2SLS with Newey–West (Bartlett, `lags`) standard errors; Sargan statistic; returns coefficients and tests."""
    PZ = Z @ np.linalg.pinv(Z.T @ Z) @ Z.T; Xh = PZ @ X
    b = np.linalg.solve(Xh.T @ X, Xh.T @ y); u = y - X @ b; n, k = X.shape
    S = (Xh * u[:, None]).T @ (Xh * u[:, None]) / n
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1); G = (Xh[L:] * u[L:, None]).T @ (Xh[:-L] * u[:-L, None]) / n; S += w * (G + G.T)
    A = np.linalg.inv(Xh.T @ X / n); V = A @ S @ A / n; se = np.sqrt(np.diag(V))
    sargan = float(n * (1 - np.sum(ols(u, Z).resid ** 2) / np.sum((u - u.mean()) ** 2))); dfs = Z.shape[1] - k
    return {"coef": [{"name": nm, "est": round(float(b[i]), 4), "se": round(float(se[i]), 4), "t": round(float(b[i] / se[i]), 2)} for i, nm in enumerate(names)],
            "sigma": round(float(math.sqrt(np.sum(u ** 2) / (n - k))), 5), "T": int(n), "sargan": {"stat": round(sargan, 2), "df": dfs, "p": round(float(1 - stats.chi2.cdf(sargan, dfs)), 3) if dfs > 0 else None},
            "resid": u}


def nkpc_block(d, est, end):
    start = est["config"]["start"]; df = d.loc[start:end].copy()
    df["Dp_f1"] = d.Dp.shift(-1); df["share"] = (d.w + d.t1 - d.z - d.p); df["share"] -= df["share"].mean()
    for c, L in [("Dp", 4), ("share", 2), ("gap", 2), ("Dpi", 1), ("Dpen", 1), ("Dw", 1)]:
        for j in range(1, L + 1): df[f"{c}_l{j}"] = d[c if c != "share" else "Dp"].shift(j) if c != "share" else df["share"].shift(j)
    df["ecm_p_l1"] = d.ecm_p.shift(1); df["gap_l1"] = d.gap.shift(1); df["Dp_l4"] = d.Dp.shift(4)
    S = ["s1", "s2", "s3"]; out = {"variants": [], "T": None}
    instr_base = ["Dp_l1", "Dp_l2", "Dp_l3", "Dp_l4", "Dpi_l1", "Dpen_l1", "Dw_l1", "gap_l1"]
    for xname, xcol in [("wage share (w + τ1 − z − p)", "share"), ("output gap", "gap")]:
        xl = [f"{xcol}_l1", f"{xcol}_l2"]
        cols = ["Dp", "Dp_f1", "Dp_l1", xcol, "Dpi", "Dpen", "ecm_p_l1", "Dp_l4", "gap_l1"] + S + instr_base + xl
        dd = df[list(dict.fromkeys(cols))].dropna(); y = dd.Dp.values; n = len(dd); out["T"] = n
        Z = sm.add_constant(dd[instr_base + xl + S], has_constant="add").values
        # (a) hybrid NKPC: Dp = c + b_f Dp_{t+1} + b_b Dp_{t-1} + b_x x_t + seasonals, lead and x instrumented
        X = sm.add_constant(dd[["Dp_f1", "Dp_l1", xcol] + S], has_constant="add").values
        a = tsls(y, X, Z, ["const", "Δp_{t+1}", "Δp_{t−1}", "x_t"] + S)
        # first-stage F for the lead and for x
        fs = {}
        for c in ["Dp_f1", xcol]:
            m1 = ols(dd[c].values, Z); m0 = ols(dd[c].values, sm.add_constant(dd[S], has_constant="add").values)
            q = Z.shape[1] - 4; F = ((m0.ssr - m1.ssr) / q) / (m1.ssr / m1.df_resid); fs[c] = round(float(F), 1)
        # (b) NKPC augmented with the EqCM's variables (Δpi_t, Δpe_t, Δp_{t−4}, gap_{t−1}, EqCM_{t−1}); Wald test of the added block (HAC)
        Xb = sm.add_constant(dd[["Dp_f1", "Dp_l1", xcol, "Dpi", "Dpen", "Dp_l4", "gap_l1", "ecm_p_l1"] + S], has_constant="add").values
        Zb = np.column_stack([Z, dd[["Dpi", "Dpen", "Dp_l4", "ecm_p_l1"]].values])
        b = tsls(y, Xb, Zb, ["const", "Δp_{t+1}", "Δp_{t−1}", "x_t", "Δpi_t", "Δpe_t", "Δp_{t−4}", "gap_{t−1}", "EqCM_{t−1}"] + S)
        # Wald on the five EqCM terms via the difference in 2SLS fit (homoskedastic F, reported as such)
        ua, ub = a["resid"], b["resid"]; q = 5; F = ((np.sum(ua ** 2) - np.sum(ub ** 2)) / q) / (np.sum(ub ** 2) / (n - Xb.shape[1]))
        wald = {"F": round(float(F), 2), "df": [q, int(n - Xb.shape[1])], "p": round(float(1 - stats.f.cdf(F, q, n - Xb.shape[1])), 4)}
        # (c) the EqCM augmented with the instrumented lead
        Xc = sm.add_constant(dd[["Dp_l4", "Dpi", "Dpen", "gap_l1", "ecm_p_l1", "Dp_f1"] + S], has_constant="add").values
        c_ = tsls(y, Xc, Zb, ["const", "Δp_{t−4}", "Δpi_t", "Δpe_t", "gap_{t−1}", "EqCM_{t−1}", "Δp_{t+1}"] + S)
        for r in (a, b, c_): r.pop("resid")
        out["variants"].append({"forcing": xname, "nkpc": a, "first_stage_F": {"lead": fs["Dp_f1"], "x": fs[xcol]}, "nkpc_plus_eqcm": b, "eqcm_terms_wald": wald, "eqcm_plus_lead": c_})
    out["instruments"] = "constant, Δp_{t−1..t−4}, x_{t−1}, x_{t−2}, Δpi_{t−1}, Δpe_{t−1}, Δw_{t−1}, gap_{t−1}, seasonals (plus the EqCM's own regressors where they appear)"
    out["note"] = ("Hybrid New Keynesian Phillips curve Δp_t = b_f E_tΔp_{t+1} + b_b Δp_{t−1} + b_x x_t, estimated by 2SLS with the lead and the forcing variable instrumented by lags "
                   "(Newey–West standard errors, 4 lags; Sargan test of the overidentifying restrictions). Bårdsen, Jansen and Nymoen (2004) found for Norway that the forward term "
                   "loses its significance once the EqCM's variables are added, while the lead adds nothing to the EqCM: the two tests reproduced here. Quarterly CPI inflation, "
                   "unadjusted with seasonals; the wage share is the real unit labour cost of the price EqCM, demeaned. The Wald test of the EqCM block uses the homoskedastic F form.")
    return out

# ----------------------------------------------------------------------------------------------- 4. recursive cointegration

def recursive_coint(d, est, end):
    start = est["config"]["start"]; out = {}
    systems = {"wage": (lambda x: pd.DataFrame({"w−p": x.w - x.p, "z": x.z, "u": x.u}), ["w", "p", "z", "u"], "u", "coefficient on u (wage curve, imposed −0.1)"),
               "price": (lambda x: pd.DataFrame({"p−τ3": x.p - x.t3, "w+τ1−z": x.w + x.t1 - x.z, "pi": x.pi}), ["p", "w", "t1", "z", "pi", "t3"], "pi", "weight on import prices ϕ (imposed 0.4)")}
    ends = [str(q) for q in pd.period_range("2005Q4", end, freq="Q")]
    for key, (mk, cols, coefname, coeflabel) in systems.items():
        x = d.loc[start:end, cols].dropna(); rows = []
        for e in ends:
            X = mk(x.loc[:e])
            try:
                J = coint_johansen(E.deseason(X), 0, 4)
            except Exception:
                continue
            b = J.evec[:, 0] / J.evec[0, 0]
            # normalised so that the first variable has coefficient 1: w − p = −b_z z − b_u u  ->  report −b (the "right-hand side" coefficient)
            rows.append({"end": e, "T": len(X), "trace0": round(float(J.lr1[0]), 2), "trace1": round(float(J.lr1[1]), 2), "cv0": round(float(J.cvt[0, 1]), 2), "cv1": round(float(J.cvt[1, 1]), 2),
                         "coef": round(float(-b[list(X.columns).index(coefname)]), 3), "eig1": round(float(J.eig[0]), 3)})
        out[key] = {"vars": list(mk(x.iloc[:8]).columns), "coef_label": coeflabel, "rows": rows}
    out["note"] = ("Johansen trace statistics for r = 0 and r ≤ 1 (unrestricted constant, 4 lags, data de-seasonalised by quarterly dummies within each sample) re-estimated on samples "
                   "ending at every quarter from 2005Q4, shown as ratios to their 5% critical values (above 1 = rejection of that rank), with the first cointegrating vector's key coefficient "
                   "and the largest eigenvalue. Everything is re-estimated at each end point (the Z-representation of Hansen and Johansen 1999); the critical values ignore the "
                   "de-seasonalisation and the short sample, so read the paths for stability rather than for the levels.")
    return out

# ----------------------------------------------------------------------------------------------- 5. 2SLS checks

def iv_block(d, eqs, est, end):
    spec = {"price": ("Dpi", ["Dpi_l1", "Dpi_l2", "Dv_l1", "Dpf", "Dpf_l1", "Doil"]),
            "imp": ("Dv", ["Doil", "dRdiff_it", "Dv_l1", "Dv_l2", "Doil_l1"]),
            "unemp": ("Dy", ["Dg", "Dy_l1", "Dy_l2", "Dg_l1", "Dz"])}
    out = {}
    for k, (endog, instr) in spec.items():
        df = d.loc[est["config"]["start"]:end].copy()
        for c in instr + [endog]:
            if "_l" in c and c not in df:
                base, L = c.rsplit("_l", 1); df[c] = d[base].shift(int(L))
        y, X, index = design(df, eqs[k], est["equations"][k], end, with_dummies=True)
        dd = df.loc[index, instr].dropna(); idx = dd.index; yv = y.loc[idx].values; Xv = X.loc[idx]
        exog = [c for c in Xv.columns if c != endog]
        Z = np.column_stack([Xv[exog].values, dd.values])
        r = tsls(yv, Xv.values, Z, list(Xv.columns), lags=4); u = r.pop("resid")
        m1 = ols(Xv[endog].values, Z); m0 = ols(Xv[endog].values, Xv[exog].values); q = len(instr)
        F1 = ((m0.ssr - m1.ssr) / q) / (m1.ssr / m1.df_resid)
        # Durbin–Wu–Hausman by the control function: add the first-stage residual to the OLS equation
        mc = ols(yv, np.column_stack([Xv.values, m1.resid])); t_dwh = float(mc.tvalues[-1])
        mo = ols(yv, Xv.values)
        out[k] = {"label": NAMES[k], "endogenous": endog, "instruments": instr, "T": len(idx), "first_stage_F": round(float(F1), 1), "first_stage_df": [q, int(m1.df_resid)],
                  "dwh_t": round(t_dwh, 2), "dwh_p": round(float(2 * (1 - stats.t.cdf(abs(t_dwh), mc.df_resid))), 3),
                  "rows": [{"name": nm, "ols": round(float(mo.params[i]), 4), "ols_se": round(float(mo.bse[i]), 4), "tsls": c["est"], "tsls_se": c["se"]} for i, (nm, c) in enumerate(zip(Xv.columns, r["coef"])) if not nm.startswith("s") and nm != "const" and not nm.startswith("covid")],
                  "sigma_ols": round(float(math.sqrt(mo.scale)), 5), "sigma_tsls": r["sigma"], "sargan": r["sargan"]}
    out["note"] = ("The published wage–price blocks are estimated by FIML; here each equation is single-equation OLS, which is consistent only if its contemporaneous regressor is "
                   "uncorrelated with the disturbance. 2SLS with lagged and exogenous instruments (Newey–West standard errors) is the check: the Durbin–Wu–Hausman t is the "
                   "first-stage residual's t-value when added to the OLS equation (|t| > 2 means OLS and 2SLS differ significantly); the first-stage F says whether the instruments are strong.")
    return out

# ----------------------------------------------------------------------------------------------- main

def main():
    t0 = time.time()
    est = json.loads((HERE / "estimates.json").read_text(encoding="utf-8")); cfg = est["config"]
    raw = pd.read_csv(HERE / "data.csv", index_col=0); raw.index = pd.PeriodIndex(raw.index, freq="Q")
    d, _ = E.build(raw, cfg); end = est["last_quarter"]["qna"]
    for c in ["Dpi", "Dv", "Dpf", "Doil", "Dy", "Dg"]:
        for L in (1, 2): d[f"{c}_l{L}"] = d[c].shift(L)
    for c in ["u", "rr", "g4y", "ecm_w", "ecm_p", "ecm_pi", "ecm_y", "rex", "Dp", "Du", "Dwp", "Dpu", "RS", "R", "Rs", "DR", "gap", "Dv", "Dy"]:
        for L in (1, 2, 4): E.lagcol(d, c, L)
    eqs = {e["key"]: e for e in E.equations(d, cfg)}
    out = {"built": pd.Timestamp.today().strftime("%Y-%m-%d"), "sample": [cfg["start"], end]}
    out["saturation"] = saturation_block(d, eqs, est, end); print("saturation done", round(time.time() - t0), "s")
    for k in CORE:
        s = out["saturation"][k]; print(f"  {k:7s} IIS {[r['date'] for r in s['iis']['retained']]}  SIS {[r['date'] for r in s['sis']['retained']]}  hand {s['hand_dummies']}")
    out["superexo"] = superexo_block(d, eqs, est, end); print("super-exogeneity done", round(time.time() - t0), "s")
    for t in out["superexo"]["tests"]: print(f"  {t['eq']:7s} {t['marginals']:28s} ind {t['n_ind']}  F {t['F']} p {t['p']}  {t['verdict']}")
    out["nkpc"] = nkpc_block(d, est, end); print("nkpc done")
    for v in out["nkpc"]["variants"]:
        print("  ", v["forcing"], "b_f", v["nkpc"]["coef"][1], "b_b", v["nkpc"]["coef"][2], "b_x", v["nkpc"]["coef"][3], "sargan", v["nkpc"]["sargan"], "| +EqCM: b_f", v["nkpc_plus_eqcm"]["coef"][1], "wald", v["eqcm_terms_wald"], "| EqCM+lead:", v["eqcm_plus_lead"]["coef"][6])
    out["recursive_coint"] = recursive_coint(d, est, end); print("recursive cointegration done", round(time.time() - t0), "s")
    out["iv"] = iv_block(d, eqs, est, end); print("iv done")
    for k in ["price", "imp", "unemp"]:
        r = out["iv"][k]; print(f"  {k:6s} endog {r['endogenous']} F1 {r['first_stage_F']} DWH t {r['dwh_t']} p {r['dwh_p']}  ", [(x['name'], x['ols'], x['tsls']) for x in r['rows'] if x['name'] == r['endogenous']])
    (HERE / "robustness.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print("written robustness.json", (HERE / "robustness.json").stat().st_size // 1024, "kB", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
