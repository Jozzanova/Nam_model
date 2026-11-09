"""Rolling pseudo-out-of-sample forecast evaluation of the estimated system, in the spirit of Eitrheim, Husebø and
Nymoen (1999, 'Equilibrium-correction vs. differencing in macroeconometric forecasting', Economic Modelling) and
Eitrheim, Jansen and Nymoen (2002, 'Progress from forecast failure', Econometrics Journal).

For every forecast origin from 2007Q1 to the quarter before the last national-accounts quarter, every equation is
re-estimated on the data up to the origin (expanding window from the estimation start, the same specification and the
same |t| >= 2 rule for the impulse dummies) and the system is simulated dynamically eight quarters ahead with the
exogenous variables and the policy rate at their actual values. Five forecasters are compared:

  eqcm   the model (equilibrium-correction form)
  dvar   the same equations with every level (equilibrium-correction) term dropped and re-estimated: the
         'differenced' model that EHN1999 show to be robust to shifts in the equilibrium means
  ic     the model with an intercept correction: each equation's last in-sample residual is added to every forecast
         quarter (Clements and Hendry's 'setting the model back on track')
  naive  no change: the reported variable stays at its value in the origin quarter
  ar     a univariate AR(4) with constant for the reported variable, estimated on the same expanding window

Measured on the reported variables (CPI inflation, the unemployment rate, four-quarter GDP growth, the four-quarter
change of the exchange rate): root mean squared forecast error and bias by horizon, also with the Covid quarters
2020Q1–2021Q4 left out of the targets, Diebold–Mariano tests against the model (HAC with h − 1 lags, Harvey,
Leybourne and Newbold small-sample correction), the paths from every origin, and the error series at 1, 4 and 8 quarters.
The data are the current vintage, not real-time vintages; the test is of the equations' dynamics, not a real-time contest.

Reads model/data.csv, model/estimates.json, model/simulation.json, model/norges_bank_projections.json;
writes model/forecast_eval.json.  Usage: python -X utf8 model/forecast_eval.py [--first 2007Q1] [--h 8]
"""
from __future__ import annotations
import argparse, json, math, sys, time
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
import estimate as E, simulate as Sm

HERE = Path(__file__).resolve().parent
NaN = float("nan")
LEVEL_TERMS = {"wage": ["ecm_w_l4"], "price": ["ecm_p_l1"], "imp": ["ecm_pi_l1", "rex_l1"], "unemp": ["u_l2", "rr_l2"],
               "output": ["ecm_y_l1"], "mm": ["RS_l1", "R_l1", "Rs_l1"], "fx": [], "bridge": []}
SIM_EQS = ["wage", "price", "imp", "fx", "unemp", "output", "mm", "bridge"]
VARS = {"infl4": "CPI inflation, four-quarter, %", "u": "unemployment rate, %", "g4y": "mainland GDP growth, four-quarter, %", "v": "exchange rate I-44, four-quarter change, % (up = weaker)"}
MODELS = {"eqcm": {"label": "EqCM (the model)", "desc": "every equation re-estimated on the data to the origin; dynamic simulation with the exogenous variables and the policy rate at their actual values"},
          "dvar": {"label": "dVAR (level terms dropped)", "desc": "the same equations with the equilibrium-correction and other level terms removed and re-estimated (EHN1999)"},
          "ic": {"label": "EqCM, intercept-corrected", "desc": "the model with each equation's last residual added to every forecast quarter (Clements–Hendry)"},
          "naive": {"label": "No change", "desc": "the reported variable stays at its origin-quarter value"},
          "ar": {"label": "AR(4)", "desc": "univariate AR(4) with constant for the reported variable, same expanding window"}}


def ols(df, y, X):
    return sm.OLS(df[y], sm.add_constant(df[X], has_constant="add")).fit()


def fit_at(d: pd.DataFrame, eq: dict, end: str, drop: list[str]) -> tuple[dict, float]:
    """Coefficients of one equation estimated on eq.start..end with the columns in `drop` removed; the same impulse-dummy
    rule as estimate.fit_equation (candidates with |t| >= 2 kept), skipping dummies that are all zero in the sample."""
    y = eq["lhs"]; base = [c for c, _, _ in eq["regs"] if c not in drop] + eq["seasonals"]
    df = d.loc[eq["start"]:end, [y] + base + eq["candidates"]].dropna(subset=[y] + base)
    cands = [c for c in eq["candidates"] if df[c].abs().sum() > 0]
    keep = []
    if cands:
        m0 = ols(df, y, base + cands)
        keep = [c for c in cands if abs(float(m0.tvalues[c])) >= 2]
    X = base + keep; m = ols(df, y, X)
    co = {c: float(m.params[c]) for c in ["const"] + X}
    for c in drop: co[c] = 0.0
    return co, float(m.resid.iloc[-1])


def ar_forecast(series: pd.Series, end_pos: int, h: int, p: int = 4) -> list[float]:
    """AR(p) with constant on the reported series up to end_pos (inclusive), iterated h steps."""
    y = series.iloc[:end_pos + 1].dropna().values
    if len(y) < p + 12: return [NaN] * h
    Y = y[p:]; X = np.column_stack([y[p - j - 1:len(y) - j - 1] for j in range(p)])
    b = sm.OLS(Y, sm.add_constant(X, has_constant="add")).fit().params
    hist = list(y[-p:]); out = []
    for _ in range(h):
        f = b[0] + sum(b[j + 1] * hist[-j - 1] for j in range(p)); out.append(float(f)); hist.append(f)
    return out


def dm_test(e1: np.ndarray, e2: np.ndarray, h: int) -> tuple[float, float]:
    """Diebold–Mariano statistic (HLN-corrected) and two-sided p-value for d = e1² − e2²; negative d favours model 1."""
    d = e1 ** 2 - e2 ** 2; n = len(d)
    if n < 10: return NaN, NaN
    dbar = d.mean(); dc = d - dbar
    var = float(dc @ dc) / n
    for L in range(1, h):
        w = 1 - L / h; var += 2 * w * float(dc[L:] @ dc[:-L]) / n
    if var <= 0: return NaN, NaN
    dm = dbar / math.sqrt(var / n)
    dm *= math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    return float(dm), float(2 * (1 - stats.t.cdf(abs(dm), n - 1)))


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--first", default="2007Q1"); ap.add_argument("--h", type=int, default=8)
    ap.add_argument("--out", default=str(HERE / "forecast_eval.json"))
    a = ap.parse_args(argv); Hh = a.h; t_start = time.time()
    est = json.loads((HERE / "estimates.json").read_text(encoding="utf-8")); cfg = est["config"]
    sim = json.loads((HERE / "simulation.json").read_text(encoding="utf-8"))
    nb = json.loads((HERE / "norges_bank_projections.json").read_text(encoding="utf-8"))
    raw = pd.read_csv(HERE / "data.csv", index_col=0); raw.index = pd.PeriodIndex(raw.index, freq="Q")
    d, _ = E.build(raw, cfg)
    end = est["last_quarter"]["qna"]; origin = pd.Period(end, "Q")
    idx = [str(q) for q in pd.period_range("1995Q1", origin + 48, freq="Q")]; T = len(idx); pos = {q: i for i, q in enumerate(idx)}
    dd = d.reindex(pd.PeriodIndex(idx, freq="Q"))
    X = Sm.extend_exogenous(dd, pos[end], T, sim["assumptions"], nb, idx)
    H = {k: [float(x) if not pd.isna(x) else NaN for x in dd[k]] for k in Sm.ENDO}
    R_path = list(H["R"])
    P0 = Sm.default_params(est)
    eqs = {e["key"]: e for e in E.equations(d, cfg)}
    actual_all = Sm.outputs(H, X, pos["1996Q1"], pos[end]); act_index = idx[pos["1996Q1"]:pos[end] + 1]
    act = {v: pd.Series(actual_all[v], index=act_index) for v in VARS}
    origins = [q for q in idx if a.first <= q < end]
    paths = {v: {"origins": origins, "eqcm": [], "dvar": [], "ic": []} for v in VARS}
    errors = {v: {m: [[] for _ in range(Hh)] for m in MODELS} for v in VARS}        # errors[v][m][h-1] = list of (origin, target, error)
    for oq in origins:
        o = pos[oq]; hmax = min(Hh, pos[end] - o); t1 = o + hmax
        # the exchange-rate drift assumption as on the dashboard: the equation's constant is off beyond each origin unless kept
        X["fx_drift"] = [1.0 if i <= o or sim["assumptions"].get("fx_drift") == "est" else 0.0 for i in range(T)]
        # the model and the dVAR, re-estimated at the origin
        P = {"eqcm": json.loads(json.dumps(P0)), "dvar": json.loads(json.dumps(P0))}; last_res = {}
        for k in SIM_EQS:
            co, r_last = fit_at(d, eqs[k], oq, []); P["eqcm"]["eq"][k] = co; last_res[k] = r_last
            co2, _ = fit_at(d, eqs[k], oq, LEVEL_TERMS[k]); P["dvar"]["eq"][k] = co2
        res_ic = {k: [0.0] * T for k in SIM_EQS}
        for k in SIM_EQS:
            for t in range(o + 1, t1 + 1): res_ic[k][t] = last_res[k]
        fc = {"eqcm": Sm.outputs(Sm.simulate(P["eqcm"], X, H, o + 1, t1, R_path), X, o + 1, t1),
              "dvar": Sm.outputs(Sm.simulate(P["dvar"], X, H, o + 1, t1, R_path), X, o + 1, t1),
              "ic": Sm.outputs(Sm.simulate(P["eqcm"], X, H, o + 1, t1, R_path, resid=res_ic), X, o + 1, t1)}
        for v in VARS:
            a0 = float(act[v].loc[oq]); fc_naive = [a0] * hmax
            fc_ar = ar_forecast(act[v], act_index.index(oq), hmax)
            allf = {"eqcm": fc["eqcm"][v], "dvar": fc["dvar"][v], "ic": fc["ic"][v], "naive": fc_naive, "ar": fc_ar}
            for m in ["eqcm", "dvar", "ic"]: paths[v][m].append([round(x, 4) for x in allf[m]])
            for h in range(1, hmax + 1):
                tq = idx[o + h]; av = float(act[v].loc[tq])
                for m in MODELS:
                    f = allf[m][h - 1]
                    if not (isinstance(f, float) and math.isnan(f)): errors[v][m][h - 1].append((oq, tq, av - f))
    # summary statistics
    covid = set(str(q) for q in pd.period_range("2020Q1", "2021Q4", freq="Q"))
    out = {"built": pd.Timestamp.today().strftime("%Y-%m-%d"), "first_origin": origins[0], "last_origin": origins[-1], "n_origins": len(origins), "h": Hh,
           "vars": VARS, "models": MODELS, "rmsfe": {}, "bias": {}, "n": {}, "rmsfe_xcovid": {}, "n_xcovid": {}, "dm": {}, "paths": paths, "errors": {},
           "actual": {v: {"index": act_index, "values": [round(float(x), 4) for x in act[v]]} for v in VARS}}
    for v in VARS:
        out["rmsfe"][v] = {}; out["bias"][v] = {}; out["rmsfe_xcovid"][v] = {}; out["dm"][v] = {}; out["errors"][v] = {}
        out["n"][v] = [len(errors[v]["eqcm"][h]) for h in range(Hh)]
        out["n_xcovid"][v] = [sum(1 for (_, tq, _) in errors[v]["eqcm"][h] if tq not in covid) for h in range(Hh)]
        for m in MODELS:
            out["rmsfe"][v][m] = [round(math.sqrt(np.mean([e ** 2 for (_, _, e) in errors[v][m][h]])), 4) if errors[v][m][h] else None for h in range(Hh)]
            out["bias"][v][m] = [round(float(np.mean([e for (_, _, e) in errors[v][m][h]])), 4) if errors[v][m][h] else None for h in range(Hh)]
            xc = [[e for (_, tq, e) in errors[v][m][h] if tq not in covid] for h in range(Hh)]
            out["rmsfe_xcovid"][v][m] = [round(math.sqrt(np.mean([e ** 2 for e in xc[h]])), 4) if xc[h] else None for h in range(Hh)]
            out["errors"][v][m] = {str(h): [dict((oq, round(e, 4)) for (oq, _, e) in errors[v][m][h - 1]).get(oq) for oq in origins] for h in (1, 4, Hh)}   # aligned with origins, null where no target yet
            if m != "eqcm":
                dmp = []
                for h in range(1, Hh + 1):
                    e1 = {oq: e for (oq, _, e) in errors[v]["eqcm"][h - 1]}; e2 = {oq: e for (oq, _, e) in errors[v][m][h - 1]}
                    com = [oq for oq in e1 if oq in e2]
                    st, pv = dm_test(np.array([e1[q] for q in com]), np.array([e2[q] for q in com]), h)
                    dmp.append({"stat": None if math.isnan(st) else round(st, 2), "p": None if math.isnan(pv) else round(pv, 3)})
                out["dm"][v][m] = dmp
    out["errors_note"] = "errors[var][model][h]: actual minus forecast, one entry per origin in `paths[var].origins` (null where the target quarter is beyond the data)."
    out["note"] = ("Expanding-window re-estimation at every origin from " + origins[0] + " (" + str(len(origins)) + " origins), eight-quarter dynamic forecasts conditional on the actual "
                   "paths of the exogenous variables and the policy rate; current data vintage. RMSFE in the units of each variable (percentage points). "
                   "Diebold–Mariano: HAC variance with h − 1 Bartlett lags, Harvey–Leybourne–Newbold correction, two-sided p-values; a negative statistic means the model has the smaller squared errors.")
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"forecast evaluation: {len(origins)} origins {origins[0]}–{origins[-1]}, h = {Hh}, {time.time() - t_start:.0f} s, written {a.out} ({Path(a.out).stat().st_size // 1024} kB)")
    for v in VARS:
        print(f"  {v:6s} RMSFE h=1/4/8:", "  ".join(f"{m}: {out['rmsfe'][v][m][0]}/{out['rmsfe'][v][m][3]}/{out['rmsfe'][v][m][Hh - 1]}" for m in MODELS))
    return out


if __name__ == "__main__":
    main()
