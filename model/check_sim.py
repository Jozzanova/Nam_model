"""Consistency check: with every equation's estimated residual added back, the dynamic simulation must reproduce the
actual data to machine precision. Run after estimate.py; exits non-zero if any endogenous variable deviates by more
than 1e-6 over 2005Q1–origin (the CPI-ATE bridge starts in 2004Q2)."""
import sys, json, math
from pathlib import Path
import pandas as pd, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import simulate as Sm, estimate as E
HERE = Path(__file__).resolve().parent
est = json.loads((HERE / "estimates.json").read_text(encoding="utf-8")); cfg = est["config"]
raw = pd.read_csv(HERE / "data.csv", index_col=0); raw.index = pd.PeriodIndex(raw.index, freq="Q")
d, _ = E.build(raw, cfg); nb = json.loads((HERE / "norges_bank_projections.json").read_text(encoding="utf-8"))
origin = pd.Period(est["last_quarter"]["qna"], "Q"); idx = [str(q) for q in pd.period_range("1995Q1", origin + 48, freq="Q")]; T = len(idx); pos = {q: i for i, q in enumerate(idx)}
d = d.reindex(pd.PeriodIndex(idx, freq="Q"))
X = Sm.extend_exogenous(d, pos[str(origin)], T, {"z_growth": 1, "g_growth": 2, "pf_infl": 2, "pstar_infl": 2, "pen_infl": 2, "Rs_path": {}}, nb, idx)
H = {k: [float(x) if not pd.isna(x) else float("nan") for x in d[k]] for k in Sm.ENDO}
P = Sm.default_params(est); R_path = list(H["R"])
eqs = est["equations"]; keys = ["wage", "price", "imp", "fx", "fx_level", "unemp", "output", "mm", "bridge"]
res = {k: [0.0] * T for k in keys}
for k in keys:
    for q, r in zip(eqs[k]["dates"], eqs[k]["resid"]): res[k][pos[q]] = r
t0, t1 = pos["2005Q1"], pos[str(origin)]
worst = 0.0
for use_level in (False, True):
    P["lr"]["use_alpha_v"] = use_level
    Y = Sm.simulate(P, X, H, t0, t1, R_path, resid=res)
    for k in Sm.ENDO:
        err = max(abs(Y[k][t] - H[k][t]) for t in range(t0, t1 + 1)); worst = max(worst, err)
        print(f"  PPP anchor {'on ' if use_level else 'off'}  {k:3s} max |sim − actual| = {err:.1e}")
print("CHECK", "OK" if worst < 1e-6 else "FAILED", f"(worst {worst:.1e})")
sys.exit(0 if worst < 1e-6 else 1)
