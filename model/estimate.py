"""Estimate the dashboard's small quarterly equilibrium-correction model of Norway.

Reads  model/data.csv (built by fetch_data.py), writes model/estimates.json.
Every equation is a single OLS regression on seasonally unadjusted quarterly data with seasonal dummies, with the
long-run (cointegration) coefficients imposed from the published papers (BJN2003, ABE2005, BN2008, NAM2026 — see
model_spec.md Parts B–D) and a free estimate reported beside each imposed relation. Nothing here is "the authors'
model": the equations follow their published forms, the data are the dashboard's own (see DEPARTURES in
model_spec.md D.3 and the `notes` list written to estimates.json).

Usage:  python -X utf8 model/estimate.py [--start 1996Q1] [--u reg|lfs] [--pi trad|total] [--covid dummies|exclude]
"""
from __future__ import annotations
import argparse, json, math, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_breusch_godfrey, het_arch, het_breuschpagan, linear_reset
from statsmodels.stats.stattools import jarque_bera, durbin_watson
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from scipy import stats

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
S = ["s1", "s2", "s3"]
COVID = ["covidq1", "covidq2", "covidq3", "covidq4"]

# ----------------------------------------------------------------------------------------------- data construction

def splice_back(main: pd.Series, proxy: pd.Series) -> pd.Series:
    """Extend `main` backwards with the growth rates of `proxy` (log series)."""
    out = main.copy(); idx = list(main.index); first = main.first_valid_index()
    if first is None: return out
    i0 = idx.index(first)
    for i in range(i0 - 1, -1, -1):
        t, tn = idx[i], idx[i + 1]
        if pd.isna(proxy.get(t)) or pd.isna(proxy.get(tn)) or pd.isna(out[tn]): break
        out[t] = out[tn] - (proxy[tn] - proxy[t])
    return out


def build(raw: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, dict]:
    """All model variables (lower case = log) plus a dict of construction notes."""
    d = pd.DataFrame(index=raw.index); L = np.log; notes = {}
    d["w"] = raw.l_w; d["wc"] = raw.l_wc; d["p"] = raw.l_p; d["pu"] = raw.l_pu; d["z"] = raw.l_z
    d["y"] = raw.l_y; d["g"] = raw.l_g; d["v"] = raw.l_v; d["oil"] = raw.l_oil
    d["u"] = raw.l_u if cfg["u"] == "reg" else raw.l_ulfs
    d["u_alt"] = raw.l_ulfs if cfg["u"] == "reg" else raw.l_u
    d["pi"] = raw.l_pitrad if cfg["pi"] == "trad" else raw.l_pi
    d["pi_alt"] = raw.l_pi if cfg["pi"] == "trad" else raw.l_pitrad
    d["pf"] = splice_back(raw.l_pf, raw.l_pfde)
    notes["pf"] = "Foreign producer prices pf: euro-area domestic-output PPI (Eurostat, from 2000Q1) extended backwards with the German PPI's growth rates (1976Q1–1999Q4)."
    d["pstar"] = splice_back(raw.l_pstar, L(raw.cpi_de))
    notes["pstar"] = "Foreign consumer prices p*: euro-area HICP (ECB, from 1996Q1) extended backwards with the German CPI's growth rates (OECD)."
    # energy: CPI 04.5 (electricity, gas, other fuels) and 07.2.2 (fuels and lubricants), weights ≈ 42 and 25 per 1000 of the CPI
    # (StatBank 14700 KpiVektMnd, 2003–2026 averages) -> shares 0.63 / 0.37 of the energy composite
    pen = 0.63 * L(raw.cpi_elgas) + 0.37 * L(raw.cpi_fuel)
    e = L(raw.cpi) - L(raw.cpi_xe)                      # energy's cumulative contribution to the CPI (KPI-JE from 1995M01)
    x = (pen - L(raw.cpi_xe)).diff(); yy = e.diff(); ok = x.notna() & yy.notna()
    share = float((x[ok] * yy[ok]).sum() / (x[ok] ** 2).sum())
    proxy = e.diff() / share + L(raw.cpi_xe).diff()     # implied energy-price growth before 2000Q3
    pen2 = pen.copy(); idx = list(d.index); i0 = idx.index(pen.first_valid_index())
    for i in range(i0 - 1, -1, -1):
        t, tn = idx[i], idx[i + 1]
        if pd.isna(proxy[tn]): break
        pen2[t] = pen2[tn] - proxy[tn]
    d["pen"] = pen2
    notes["pen"] = (f"Energy prices pe: composite of CPI 04.5 electricity, gas and other fuels (share 0.63) and 07.2.2 fuels and lubricants (0.37), "
                    f"StatBank 14700 from 2000Q3; before that its growth is backed out of ln(CPI) − ln(CPI excl. energy) with an estimated energy "
                    f"share of {share:.3f} (regression 2000Q4–latest, correlation with the actual series 0.97).")
    d["pen_share"] = share
    d["t1"] = np.log1p(raw.t1_sa)
    notes["t1"] = "Payroll-tax wedge τ1 = ln(1 + wage costs/wages − 1) from SSB's seasonally adjusted 09175 series (the unadjusted ratio has a ±2 pp seasonal that would otherwise enter the price EqCM)."
    d["t3"] = raw.t3.fillna(0.0)
    notes["t3"] = "Indirect-tax term τ3 = ln(CPI) − ln(CPI-AT), available from 2003Q1; set to 0 before (a constant shift only)."
    d["R"] = raw.r_policy_spliced; d["Rs"] = raw.euribor3m.fillna(raw.ir3_de); d["RS"] = raw.rs
    d["tgt"] = np.where(d.index < pd.Period("2018Q1", "Q"), 2.5, 2.0)
    notes["tgt"] = "Inflation target π̄: 2.5 to 2017Q4 (also used for 1996–2001Q1, before inflation targeting, where only the constant absorbs it), 2.0 from 2018Q1."
    d["infl4"] = 100 * d.p.diff(4); d["infl4s"] = 100 * d.pstar.diff(4); d["infl4u"] = 100 * d.pu.diff(4)
    cyc, trend = sm.tsa.filters.hpfilter(d.y.dropna(), 1600); d["gap"] = cyc; d["ytrend"] = trend
    notes["gap"] = "Output gap: Hodrick–Prescott (λ = 1600) cycle of log mainland GDP, unadjusted, over the whole 1978Q1–latest sample (BJN App. B); end-point sensitivity applies."
    d["rex"] = d.v + d.pstar - d.p
    d["rr"] = d.RS - d.infl4
    d["g4y"] = 100 * d.y.diff(4)
    d["ecm_w"] = d.w - d.p - d.z + 0.1 * d.u
    d["ecm_p"] = d.p - 0.6 * (d.w + d.t1 - d.z) - 0.4 * d.pi - d.t3
    d["ecm_pi"] = d.pi - d.v - d.pf
    d["ecm_v"] = d.rex - 0.12 * ((d.R - d.infl4) - (d.Rs - d.infl4s))
    d["ecm_y"] = d.y - 0.9 * d.g - 0.16 * d.rex + 0.06 * d.rr
    d["dRdiff"] = (d.R - d.Rs).diff(); d["dRdiff_it"] = d.dRdiff * raw.d_it
    d["Dwp"] = (d.w - d.p).diff()
    d["pigap_u"] = d.infl4u - raw.infl_target
    for c in ["w", "p", "pu", "pi", "pi_alt", "v", "u", "u_alt", "y", "g", "z", "pf", "pstar", "pen", "oil", "R", "Rs", "RS", "t3", "t1"]:
        d["D" + c] = d[c].diff(); d["D4" + c] = d[c].diff(4)
    d["D4p_tgt"] = d.D4p.shift(1) - d.tgt / 100          # (Δ4p_{t-1} − π̄), NAM2026 eq 3.33 form
    d["Dpi14"] = d.Dpi.shift(1) - d.Dpi.shift(4)          # NAM2026 Table 5.38 own-lag term
    for c in S + COVID + ["ukrw", "d_it"]: d[c] = raw[c]
    pre15 = (d.index < pd.Period("2015Q1", "Q")).astype(float)
    for q in S: d[q + "p"] = d[q] * pre15
    notes["u_seam"] = ("Registered unemployment: SSB/NAV unadjusted to 2014Q4, Norges Bank's seasonally adjusted history from 2015Q1; "
                       "the unemployment equation therefore uses seasonal dummies only up to 2014Q4 (s1p–s3p).")
    return d, notes


def lagcol(d: pd.DataFrame, c: str, k: int) -> str:
    n = f"{c}_l{k}"
    if n not in d: d[n] = d[c].shift(k)
    return n

# ----------------------------------------------------------------------------------------------- equation catalogue

def equations(d: pd.DataFrame, cfg: dict) -> list[dict]:
    """Each entry: key, label, lhs, regressors [(column, label, published)], sample, candidates (dummies kept if |t|>=2)."""
    Lg = lambda c, k: lagcol(d, c, k)
    useS = cfg["u"] == "reg"
    Su = [q + "p" for q in S] if useS else S
    E = [
        dict(key="wage", label="Wages", lhs="D4w", lhs_label="Δ₄w (four-quarter growth of hourly wages, Mainland Norway)",
             form="Δ₄w_t = c + a₁(Δ₄p_{t−1} − π̄) + a₂Δ₄z_t + a₃Δ₄u_t − α_w[w − p − z + 0.1u]_{t−4} + seasonals",
             published_form="NAM2026 eq 3.33 / Table 5.25 form (annual differences, EqCM lagged four quarters) with the BJN2003 Table 1 Panel 4 long run (γ_u = 0.1, homogeneity in p and z) imposed",
             regs=[("D4p_tgt", "Δ₄p_{t−1} − π̄", ("0.256 (t 1.8)", "NAM2026 Table 5.25")),
                   ("D4z", "Δ₄z_t", ("0.166 on Δ₄py + Δ₄z", "NAM2026 Table 5.25")),
                   ("D4u", "Δ₄u_t", ("−0.039 on Δ²u_{t−1} + Δu_{t−3}", "BN2008 eq 39")),
                   (Lg("ecm_w", 4), "EqCM_w,t−4 = [w − p − z + 0.1u]_{t−4}", ("−0.226 (t −5.7)", "NAM2026 Table 5.25; BN2008 eq 39: −0.065; BJN2003 eq 18: −0.08"))],
             seasonals=S, candidates=[], start=cfg["start"]),
        dict(key="price", label="Consumer prices", lhs="Dp", lhs_label="Δp (quarterly CPI inflation)",
             form="Δp_t = c + b₁Δp_{t−4} + b₂Δpi_t + b₃Δpe_t + b₄gap_{t−1} − α_p[p − 0.6(w + τ1 − z) − 0.4pi − τ3]_{t−1} + seasonals",
             published_form="BN2008 eq 38 regressor set (Δpi_t, Δpe_t, output term) with the BJN2003 Table 1 Panel 4 long run (ϕ = 0.4, η = 1) imposed; gap_{t−1} as in BJN2003 eq 18; the lagged inflation term is Δp_{t−4} as in NAM2026 Table 5.24 (BN2008's Δp_{t−2} leaves residual autocorrelation on this sample, AR 1–5 p = 0.01, and is insignificant)",
             regs=[(Lg("Dp", 4), "Δp_{t−4}", ("0.058 (t 5.1)", "NAM2026 Table 5.24; BN2008 eq 38 has 0.29 on Δp_{t−2}")),
                   ("Dpi", "Δpi_t", ("0.024 (0.011)", "BN2008 eq 38; BJN2003: 0.028")),
                   ("Dpen", "Δpe_t", ("0.059 (0.0038)", "BN2008 eq 38")),
                   (Lg("gap", 1), "gap_{t−1}", ("0.06 (0.02)", "BJN2003 eq 18; BN2008 uses 0.042 Δy_{t−1}")),
                   (Lg("ecm_p", 1), "EqCM_p,t−1 = [p − 0.6(w + τ1 − z) − 0.4pi − τ3]_{t−1}", ("−0.08 (0.01)", "BJN2003 eq 18; BN2008 eq 38: −0.052; NAM2026 Table 5.24: −0.195 (relative to the GDP deflator)"))],
             seasonals=S, candidates=["ukrw"], start=cfg["start"]),
        dict(key="imp", label="Import prices", lhs="Dpi", lhs_label="Δpi (quarterly change of the import deflator, traditional goods)" if cfg["pi"] == "trad" else "Δpi (quarterly change of the total import deflator)",
             form="Δpi_t = c + d₁Δv_t + d₂Δpf_t + d₃Δv_{t−1} + d₄[Δpi_{t−1} − Δpi_{t−4}] − α_pi[pi − v − pf]_{t−1} + d₅ rex_{t−1} + seasonals",
             published_form="BN2008 eq 37 (long-run homogeneity in v and pf imposed; the pricing-to-market level rex = v + p* − p estimated freely, κ = d₅/α_pi) with NAM2026 Table 5.38's own-lag term [Δpi_{t−1} − Δpi_{t−4}] and one lag of Δv",
             regs=[("Dv", "Δv_t", ("0.429 (0.072)", "BN2008 eq 37; NAM2026 Table 5.38: 0.481")),
                   ("Dpf", "Δpf_t", ("1.07 (0.21)", "BN2008 eq 37; NAM2026: 0.658")),
                   (Lg("Dv", 1), "Δv_{t−1}", None), ("Dpi14", "Δpi_{t−1} − Δpi_{t−4}", ("−0.124 (t −4.4)", "NAM2026 Table 5.38")),
                   (Lg("ecm_pi", 1), "EqCM_pi,t−1 = [pi − v − pf]_{t−1}", ("−0.431 (0.081)", "BN2008 eq 37; NAM2026: −0.300")),
                   (Lg("rex", 1), "rex_{t−1} = (v + p* − p)_{t−1}", ("κ = 0.55 (as −α_pi·κ)", "BN2008 eq 48; NAM2026: −0.068 and −0.049"))],
             seasonals=S, candidates=[], start=cfg["start"]),
        dict(key="fx", label="Exchange rate", lhs="Dv", lhs_label="Δv (quarterly change of log I-44; up = weaker krone)",
             form="Δv_t = c + e₁ IT·Δ(R − R*)_t + e₂Δoil_t + e₃Δv_{t−1}",
             published_form="NAM2026 Table 5.44 form (no level term): interest differential as in BN2008 eq 36 (IT-interacted), oil, Δv_{t−1}. The BN2008 version with the PPP/real-rate level term is estimated separately below.",
             regs=[("dRdiff_it", "IT·Δ(R − R*)_t", ("−0.0361 (0.0069)", "BN2008 eq 36; NAM2026: −0.045 on Δ(RS − RS*)")),
                   ("Doil", "Δoil_t", ("−0.036 on Δ²oil_{t−1}", "BN2008 eq 36; NAM2026: −0.088 on Δoil_t")),
                   (Lg("Dv", 1), "Δv_{t−1}", ("−0.286 (t −4.6)", "NAM2026 Table 5.44"))],
             seasonals=[], candidates=COVID, start=cfg["start"]),
        dict(key="fx_level", label="Exchange rate with the BN2008 level term", lhs="Dv", lhs_label="Δv (quarterly change of log I-44; up = weaker krone)",
             form="Δv_t = c + e₁ IT·Δ(R − R*)_t + e₂Δoil_t + e₃Δv_{t−1} − α_v[(v + p* − p) − 0.12((R − π) − (R* − π*))]_{t−1}",
             published_form="BN2008 eq 36: PPP/real-interest-differential level term with 0.12 imposed from eq 47. Used in the simulation only when the 'PPP anchor' switch is on.",
             regs=[("dRdiff_it", "IT·Δ(R − R*)_t", ("−0.0361 (0.0069)", "BN2008 eq 36")),
                   ("Doil", "Δoil_t", ("−0.036 on Δ²oil_{t−1}", "BN2008 eq 36")),
                   (Lg("Dv", 1), "Δv_{t−1}", None),
                   (Lg("ecm_v", 1), "EqCM_v,t−1 = [(v + p* − p) − 0.12((R − π) − (R* − π*))]_{t−1}", ("−0.042 (0.012)", "BN2008 eq 36; NAM2026: no level term"))],
             seasonals=[], candidates=COVID, start=cfg["start"]),
        dict(key="unemp", label="Unemployment", lhs="Du", lhs_label="Δu (quarterly change of log " + ("registered" if cfg["u"] == "reg" else "LFS") + " unemployment rate)",
             form="Δu_t = c + f₁Δu_{t−1} + f₂Δu_{t−4} + f₃Δy_t + f₄Δy_{t−1} − α_u u_{t−2} + f₅Δ(w − p)_{t−2} + f₆(RS − π)_{t−2} + f₇ 100Δ₄y_{t−2} + seasonals" + (" (to 2014Q4)" if useS else ""),
             published_form="BN2008 eq 41 (level of u with real-wage growth and real rate minus GDP growth, Δu_{t−1}, Δu_{t−4}) with the long-run coefficients θ₁ = −f₅/α_u, θ₂ = −f₆/α_u left free; Δy_t, Δy_{t−1} as in BJN2003 §4.3",
             regs=[(Lg("Du", 1), "Δu_{t−1}", ("0.44 (0.071)", "BN2008 eq 41")), (Lg("Du", 4), "Δu_{t−4}", ("0.49 (0.059)", "BN2008 eq 41")),
                   ("Dy", "Δy_t", None), (Lg("Dy", 1), "Δy_{t−1}", None),
                   (Lg("u", 2), "u_{t−2}", ("−0.078 (0.019)", "BN2008 eq 41")),
                   (Lg("Dwp", 2), "Δ(w − p)_{t−2}", ("θ₁ = 7.69 → 0.60", "BN2008 eq 41")),
                   (Lg("rr", 2), "(RS − π)_{t−2}", ("θ₂ = 0.05 → 0.004", "BN2008 eq 41 (RL − π)")),
                   (Lg("g4y", 2), "100Δ₄y_{t−2}", ("−0.004", "BN2008 eq 41"))],
             seasonals=Su, candidates=COVID, start=cfg["start"]),
        dict(key="output", label="Mainland GDP", lhs="Dy", lhs_label="Δy (quarterly growth of mainland GDP, unadjusted)",
             form="Δy_t = c + g₁Δy_{t−1} + g₂Δg_t − α_y[y − 0.9g − 0.16(v + p* − p) + 0.06(RS − π)]_{t−1} + seasonals",
             published_form="BN2008 eq 44 without the credit term, long run eq 55 (0.9, 0.16, 0.06) imposed; RS replaces the loan rate RL",
             regs=[(Lg("Dy", 1), "Δy_{t−1}", ("−0.74", "BN2008 eq 44")), ("Dg", "Δg_t", ("0.42", "BN2008 eq 44")),
                   (Lg("ecm_y", 1), "EqCM_y,t−1 = [y − 0.9g − 0.16rex + 0.06(RS − π)]_{t−1}", ("−0.21", "BN2008 eq 44"))],
             seasonals=S, candidates=COVID, start=cfg["start"]),
        dict(key="mm", label="Money-market rate", lhs="DRS", lhs_label="ΔRS (3-month NIBOR)",
             form="ΔRS_t = c + h₁ΔR_t + h₂RS_{t−1} + h₃R_{t−1} + h₄ΔR*_t + h₅R*_{t−1}",
             published_form="NAM2026 Table 5.78 form (RSH on RNB and RSW)",
             regs=[("DR", "ΔR_t", ("0.951", "NAM2026 Table 5.78")), (Lg("RS", 1), "RS_{t−1}", ("−0.355", "NAM2026 Table 5.78")),
                   (Lg("R", 1), "R_{t−1}", ("0.293", "NAM2026 Table 5.78")), ("DRs", "ΔR*_t", ("0.254", "NAM2026 Table 5.78")), (Lg("Rs", 1), "R*_{t−1}", ("0.153", "NAM2026 Table 5.78"))],
             seasonals=[], candidates=COVID, start=cfg["start"]),
        dict(key="bridge", label="CPI-ATE bridge", lhs="Dpu", lhs_label="Δpu (quarterly CPI-ATE inflation)",
             form="Δpu_t = c + k₁Δp_t + k₂Δpe_t + k₃Δτ3_t + k₄Δpu_{t−1} + k₅Δpu_{t−4}",
             published_form="NAM2026 Table 5.36 form",
             regs=[("Dp", "Δp_t", ("0.91", "NAM2026 Table 5.36")), ("Dpen", "Δpe_t", ("−0.034", "NAM2026 Table 5.36")), ("Dt3", "Δτ3_t", ("0.174", "NAM2026 Table 5.36")),
                   (Lg("Dpu", 1), "Δpu_{t−1}", ("−0.034", "NAM2026 Table 5.36")), (Lg("Dpu", 4), "Δpu_{t−4}", ("0.119", "NAM2026 Table 5.36"))],
             seasonals=[], candidates=[], start="2004Q2"),
        dict(key="rule_est", label="Estimated reaction function (reference only)", lhs="DR", lhs_label="ΔR (policy rate)",
             form="ΔR_t = c + m₁R_{t−1} + m₂(Δ₄pu_t − π̄) + m₃ 100Δ₄y_t + m₄u_{t−1} + m₅ΔR*_t + m₆ΔR_{t−1}",
             published_form="BN2008 eq 46 / NAM2026 Table 5.77 form; NAM2026 §3.10: the weight on inflation 'has been reduced to zero after 2008q4' and the rate is best treated as exogenous",
             regs=[(Lg("R", 1), "R_{t−1}", ("−0.27", "BN2008 eq 46; NAM2026: −0.050")), ("pigap_u", "Δ₄pu_t − π̄", ("1.2 × 0.27 = 0.32", "BN2008 eq 46")),
                   ("g4y", "100Δ₄y_t", None), (Lg("u", 1), "u_{t−1}", ("−0.27 on U_{t−2}", "BN2008 eq 46")),
                   ("DRs", "ΔR*_t", ("0.193 on ΔRSW", "NAM2026 Table 5.77")), (Lg("DR", 1), "ΔR_{t−1}", ("0.394", "NAM2026 Table 5.77"))],
             seasonals=[], candidates=[], start="2004Q1"),
    ]
    return E

# ----------------------------------------------------------------------------------------------- estimation helpers

def ols(df: pd.DataFrame, y: str, X: list[str]):
    return sm.OLS(df[y], sm.add_constant(df[X], has_constant="add")).fit()


def chow_split(df: pd.DataFrame, y: str, X: list[str], date: str) -> dict | None:
    t = pd.Period(date, "Q")
    a, b = df[df.index < t], df[df.index >= t]; k = len(X) + 1
    if len(a) < k + 5 or len(b) < k + 5: return None
    rss = lambda s: float(ols(s, y, X).ssr)
    r0, r1, r2 = rss(df), rss(a), rss(b); T = len(df)
    F = ((r0 - r1 - r2) / k) / ((r1 + r2) / (T - 2 * k))
    return {"date": date, "F": round(F, 3), "df": [k, T - 2 * k], "p": round(float(1 - stats.f.cdf(F, k, T - 2 * k)), 4)}


def recursive(df: pd.DataFrame, y: str, X: list[str]) -> dict:
    """One-step recursive residuals with ±2 s.e., one-step Chow F and break-point (N↓) Chow F with 5% critical values."""
    k = len(X) + 1; n0 = k + 8; T = len(df)
    Xa = sm.add_constant(df[X], has_constant="add").values; ya = df[y].values
    dates, res, se, c1, c1cv, cN, cNcv = [], [], [], [], [], [], []
    rss_full = float(np.sum(sm.OLS(ya, Xa).fit().resid ** 2))
    for t in range(n0, T):
        m = sm.OLS(ya[:t], Xa[:t]).fit()
        xt = Xa[t]; e = float(ya[t] - xt @ m.params)
        var = float(m.scale * (1 + xt @ m.normalized_cov_params @ xt)) if m.df_resid > 0 else np.nan
        dates.append(str(df.index[t])); res.append(round(e, 6)); se.append(round(2 * math.sqrt(var), 6))
        F1 = e * e / var; c1.append(round(F1, 3)); c1cv.append(round(float(stats.f.ppf(0.95, 1, t - k)), 3))
        rss_t = float(m.ssr); h = T - t
        FN = ((rss_full - rss_t) / h) / (rss_t / (t - k)); cN.append(round(FN, 3)); cNcv.append(round(float(stats.f.ppf(0.95, h, t - k)), 3))
    return {"dates": dates, "resid": res, "band": se, "chow1": c1, "chow1_cv": c1cv, "chowN": cN, "chowN_cv": cNcv}


def diagnostics(m, df: pd.DataFrame, X: list[str]) -> dict:
    out = {}
    try:
        bg = acorr_breusch_godfrey(m, nlags=5); out["ar15"] = {"stat": round(float(bg[2]), 3), "p": round(float(bg[3]), 4), "label": "Breusch–Godfrey AR 1–5 F"}
    except Exception: pass
    try:
        a = het_arch(m.resid, nlags=4); out["arch14"] = {"stat": round(float(a[2]), 3), "p": round(float(a[3]), 4), "label": "ARCH 1–4 F"}
    except Exception: pass
    jb = jarque_bera(m.resid); out["norm"] = {"stat": round(float(jb[0]), 3), "p": round(float(jb[1]), 4), "label": "Jarque–Bera normality χ²(2)"}
    try:
        cont = [c for c in X if df[c].nunique() > 3]
        Z = sm.add_constant(pd.concat([df[cont], (df[cont] ** 2).add_suffix("_sq")], axis=1), has_constant="add")
        h = het_breuschpagan(m.resid, Z); out["het"] = {"stat": round(float(h[2]), 3), "p": round(float(h[3]), 4), "label": "Heteroskedasticity F (regressors and squares)"}
    except Exception: pass
    try:
        r = linear_reset(m, power=2, use_f=True); out["reset"] = {"stat": round(float(r.fvalue), 3), "p": round(float(r.pvalue), 4), "label": "RESET F (squared fitted values)"}
    except Exception: pass
    return out


def fit_equation(d: pd.DataFrame, eq: dict, end: str, exclude_covid: bool, split_date: str = "2001Q2") -> dict:
    y = eq["lhs"]; base = [c for c, _, _ in eq["regs"]] + eq["seasonals"]
    df = d.loc[eq["start"]:end, [y] + base + eq["candidates"]].dropna(subset=[y] + base)
    if exclude_covid:
        df = df[~df.index.isin(pd.period_range("2020Q1", "2021Q4", freq="Q"))]
    tried = {}; keep = []
    if eq["candidates"] and not exclude_covid:
        m0 = ols(df, y, base + eq["candidates"])
        for c in eq["candidates"]:
            tv = float(m0.tvalues[c]); tried[c] = round(tv, 2)
            if abs(tv) >= 2: keep.append(c)
    X = base + keep
    m = ols(df, y, X)
    labels = {c: lab for c, lab, _ in eq["regs"]}; pub = {c: p for c, _, p in eq["regs"]}
    coef = []
    for c in ["const"] + X:
        coef.append({"name": c, "label": labels.get(c, {"const": "constant"}.get(c, c)), "est": float(m.params[c]), "se": float(m.bse[c]), "mean": float(df[c].mean()) if c != "const" else 1.0,
                     "t": float(m.tvalues[c]), "p": float(m.pvalues[c]), "published": pub.get(c), "kind": "seasonal" if c in eq["seasonals"] else "dummy" if c in keep else "const" if c == "const" else "reg"})
    res = {"key": eq["key"], "label": eq["label"], "lhs": y, "lhs_label": eq["lhs_label"], "form": eq["form"], "published_form": eq["published_form"],
           "sample": [str(df.index[0]), str(df.index[-1])], "T": int(m.nobs), "sigma": float(math.sqrt(m.scale)), "r2": float(m.rsquared), "r2adj": float(m.rsquared_adj),
           "dw": float(durbin_watson(m.resid)), "coef": coef, "tests": diagnostics(m, df, X), "dummies_tried": tried,
           "chow_split": chow_split(df, y, X, split_date), "recursive": recursive(df, y, X),
           "dates": [str(t) for t in df.index], "actual": [round(float(v), 6) for v in df[y]], "fitted": [round(float(v), 6) for v in m.fittedvalues],
           "resid": [round(float(v), 10) for v in m.resid]}
    cov = np.asarray(m.cov_params()); cov = (cov + cov.T) / 2
    try:
        L = np.linalg.cholesky(cov + 1e-14 * np.eye(len(cov)))
    except np.linalg.LinAlgError:
        L = np.diag(np.sqrt(np.maximum(np.diag(cov), 0)))
    res["chol"] = {"names": ["const"] + X, "L": [[float(x) for x in row] for row in L],
                   "note": "Lower Cholesky factor of the OLS coefficient covariance (coefficients in the order of `names`); used for the parametric bootstrap of the +100 bp responses."}
    res["_model"] = m; res["_df"] = df; res["_X"] = X
    return res

# ----------------------------------------------------------------------------------------------- long-run checks

def deseason(x: pd.DataFrame) -> pd.DataFrame:
    q = np.array([t.quarter for t in x.index]); D = pd.get_dummies(q, drop_first=True).astype(float); D.index = x.index
    Z = sm.add_constant(D); out = x.copy()
    for c in x: out[c] = sm.OLS(x[c], Z).fit().resid + x[c].mean()
    return out


def johansen(x: pd.DataFrame, k: int = 4) -> dict:
    J = coint_johansen(deseason(x), 0, k)
    b = J.evec[:, 0] / J.evec[0, 0]
    return {"vars": list(x.columns), "sample": [str(x.index[0]), str(x.index[-1])], "T": len(x), "lags": k,
            "trace": [round(float(v), 2) for v in J.lr1], "trace_cv5": [round(float(v), 2) for v in J.cvt[:, 1]],
            "maxeig": [round(float(v), 2) for v in J.lr2], "maxeig_cv5": [round(float(v), 2) for v in J.cvm[:, 1]],
            "beta_first": [round(float(v), 3) for v in b],
            "note": "Johansen trace and max-eigenvalue statistics (unrestricted constant, 4 lags in differences, data de-seasonalised by quarterly dummies first; 5% critical values from statsmodels, which assume no exogenous variables). The first eigenvector is normalised on the first variable."}


def longrun_checks(d: pd.DataFrame, start: str, end: str) -> dict:
    out = {}
    # wage: (w - p), z, u  -> imposed w - p = z - 0.1u
    x = d.loc[start:end, ["w", "p", "z", "u"]].dropna(); X = pd.DataFrame({"w−p": x.w - x.p, "z": x.z, "u": x.u})
    jw = johansen(X); jw["imposed"] = {"z": 1.0, "u": -0.1, "source": "BJN2003 Table 1 Panel 4 (0.09 (0.02) on u; coefficient on z = 1 imposed); BN2008 eq 50; NAM2026 eq 3.33: 0.12 on LFS unemployment (manufacturing)"}
    # unrestricted EqCM: D4w on levels at t-4
    df = d.loc[start:end].copy(); df["wpz4"] = (d.w - d.p - d.z).shift(4); df["u4"] = d.u.shift(4)
    df = df[["D4w", "D4p_tgt", "D4z", "D4u", "wpz4", "u4"] + S].dropna()
    m = ols(df, "D4w", ["D4p_tgt", "D4z", "D4u", "wpz4", "u4"] + S)
    jw["unrestricted_eqcm"] = {"alpha": round(float(m.params.wpz4), 4), "alpha_t": round(float(m.tvalues.wpz4), 2), "gamma_u": round(float(-m.params.u4 / m.params.wpz4), 4),
                               "gamma_u_t": round(float(m.tvalues.u4), 2), "sample": [str(df.index[0]), str(df.index[-1])],
                               "note": "Wage equation with the levels (w − p − z)_{t−4} and u_{t−4} entered separately; γ_u = −(coefficient on u)/(coefficient on w − p − z)."}
    out["wage"] = jw
    # price: p, ulc = w + t1 - z, pi -> imposed p = 0.6 ulc + 0.4 pi (+ t3)
    x = d.loc[start:end, ["p", "w", "t1", "z", "pi", "t3"]].dropna(); X = pd.DataFrame({"p−τ3": x.p - x.t3, "w+τ1−z": x.w + x.t1 - x.z, "pi": x.pi})
    jp = johansen(X); jp["imposed"] = {"w+τ1−z": 0.6, "pi": 0.4, "source": "BJN2003 Table 1 Panel 4 (ϕ = 0.38 (0.02), 0.4 imposed; η = 1); ABE2005: 0.35; BN2008 eq 38: 0.3; NAM2026 Table 5.24: 0.38"}
    df = d.loc[start:end].copy(); df["ulc1"] = (d.w + d.t1 - d.z).shift(1); df["pi1"] = d.pi.shift(1); df["p1"] = (d.p - d.t3).shift(1)
    df = df[["Dp", "Dp_l4", "Dpi", "Dpen", "gap_l1", "p1", "ulc1", "pi1"] + S].dropna()
    m = ols(df, "Dp", ["Dp_l4", "Dpi", "Dpen", "gap_l1", "p1", "ulc1", "pi1"] + S)
    a = float(m.params.p1)
    jp["unrestricted_eqcm"] = {"alpha": round(a, 4), "alpha_t": round(float(m.tvalues.p1), 2), "phi_ulc": round(float(-m.params.ulc1 / a), 3), "phi_pi": round(float(-m.params.pi1 / a), 3),
                               "homogeneity_sum": round(float(-(m.params.ulc1 + m.params.pi1) / a), 3), "sample": [str(df.index[0]), str(df.index[-1])],
                               "note": "Price equation with p_{t−1}, (w + τ1 − z)_{t−1} and pi_{t−1} entered separately; the implied long-run weights are the ratios to the coefficient on p_{t−1}."}
    out["price"] = jp
    # output: free long run
    df = d.loc[start:end].copy()
    for c, k in [("y", 1), ("g", 1), ("rex", 1), ("rr", 1)]: lagcol(df, c, k)
    cols = ["Dy", "Dy_l1", "Dg", "y_l1", "g_l1", "rex_l1", "rr_l1"] + S + ["covidq2"]
    df = df[cols].dropna(); m = ols(df, "Dy", cols[1:]); a = float(m.params.y_l1)
    out["output"] = {"alpha": round(a, 4), "alpha_t": round(float(m.tvalues.y_l1), 2), "g": round(float(-m.params.g_l1 / a), 3), "rex": round(float(-m.params.rex_l1 / a), 3), "rr": round(float(m.params.rr_l1 / a), 4),
                     "imposed": {"g": 0.9, "rex": 0.16, "rr": 0.06, "source": "BN2008 eq 55"}, "sample": [str(df.index[0]), str(df.index[-1])],
                     "note": "Output equation with y_{t−1}, g_{t−1}, rex_{t−1}, (RS − π)_{t−1} entered separately (plus the 2020Q2 dummy); implied long-run coefficients are ratios to the coefficient on y_{t−1}."}
    # exchange rate: level term test is in the fx equation itself; import price: kappa from the equation
    return out

# ----------------------------------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="1996Q1"); ap.add_argument("--u", default="reg", choices=["reg", "lfs"])
    ap.add_argument("--pi", default="trad", choices=["trad", "total"]); ap.add_argument("--covid", default="dummies", choices=["dummies", "exclude"])
    ap.add_argument("--out", default=str(HERE / "estimates.json"))
    a = ap.parse_args(argv)
    cfg = {"start": a.start, "u": a.u, "pi": a.pi, "covid": a.covid}
    raw = pd.read_csv(HERE / "data.csv", index_col=0); raw.index = pd.PeriodIndex(raw.index, freq="Q")
    cols = pd.read_csv(HERE / "data_columns.csv")
    d, notes = build(raw, cfg)
    end = str(d[["w", "p", "y", "pi"]].dropna().index[-1])        # last quarter with the full QNA set
    print(f"sample {cfg['start']}–{end}; u={cfg['u']} pi={cfg['pi']} covid={cfg['covid']}")
    results = {}
    for eq in equations(d, cfg):
        r = fit_equation(d, eq, end, exclude_covid=(cfg["covid"] == "exclude"))
        results[eq["key"]] = r
        t = r["tests"]
        print(f"  {eq['key']:9s} {r['sample'][0]}–{r['sample'][1]} T={r['T']:3d} σ={r['sigma']:.5f} R²={r['r2']:.3f} DW={r['dw']:.2f} AR p={t.get('ar15', {}).get('p')} JB p={t['norm']['p']}  dummies {r['dummies_tried']}")
        for c in r["coef"]:
            if c["kind"] in ("reg", "dummy"): print(f"     {c['label'][:46]:46s} {c['est']:9.4f} (t {c['t']:6.2f})   published: {c['published'][0] if c['published'] else '—'}")
    # alternatives, for the page's comparison table
    alts = {}
    def alt(key, label, cfg2, eqkey):
        d2, _ = build(raw, cfg2); eqs = {e["key"]: e for e in equations(d2, cfg2)}
        r = fit_equation(d2, eqs[eqkey], end, exclude_covid=(cfg2["covid"] == "exclude"))
        alts[key] = {k: v for k, v in r.items() if not k.startswith("_") and k not in ("recursive", "dates", "actual", "fitted", "resid")}; alts[key]["alt_label"] = label
    alt("unemp_lfs" if cfg["u"] == "reg" else "unemp_reg", "LFS unemployment rate instead of registered" if cfg["u"] == "reg" else "Registered instead of LFS", {**cfg, "u": "lfs" if cfg["u"] == "reg" else "reg"}, "unemp")
    alt("wage_u_alt", "Wage equation with the other unemployment measure", {**cfg, "u": "lfs" if cfg["u"] == "reg" else "reg"}, "wage")
    alt("imp_total" if cfg["pi"] == "trad" else "imp_trad", "Total import deflator instead of traditional goods" if cfg["pi"] == "trad" else "Traditional-goods deflator", {**cfg, "pi": "total" if cfg["pi"] == "trad" else "trad"}, "imp")
    alt("price_pi_alt", "Price equation with the other import deflator", {**cfg, "pi": "total" if cfg["pi"] == "trad" else "trad"}, "price")
    alt("wage_2001", "Wage equation on 2001Q1–", {**cfg, "start": "2001Q1"}, "wage")
    alt("price_2001", "Price equation on 2001Q1–", {**cfg, "start": "2001Q1"}, "price")
    alt("wage_nocovid", "Wage equation with 2020Q1–2021Q4 excluded", {**cfg, "covid": "exclude"}, "wage")
    alt("price_nocovid", "Price equation with 2020Q1–2021Q4 excluded", {**cfg, "covid": "exclude"}, "price")
    # the quarterly-difference BJN wage form, for the record
    dq = d.copy(); lagcol(dq, "Dp", 1); lagcol(dq, "ecm_w", 1); lagcol(dq, "Dw", 4)
    eq_q = dict(key="wage_q", label="Wages, quarterly-difference form", lhs="Dw", lhs_label="Δw", form="Δw_t = c + Δp_t + Δp_{t−1} + Δz_t + Δu_t − α_w EqCM_{t−1} + Δw_{t−4} + seasonals",
                published_form="BJN2003 eq 18 / BN2008 eq 39 regressor set (OLS, Δp_t not instrumented)",
                regs=[("Dp", "Δp_t", ("0.56", "BN2008 eq 39")), ("Dp_l1", "Δp_{t−1}", ("0.43", "BN2008 eq 39")), ("Dz", "Δz_t", None), ("Du", "Δu_t", None), ("ecm_w_l1", "EqCM_w,t−1", ("−0.065", "BN2008 eq 39")), ("Dw_l4", "Δw_{t−4}", None)],
                seasonals=S, candidates=[], start=cfg["start"])
    r = fit_equation(dq, eq_q, end, False); alts["wage_q"] = {k: v for k, v in r.items() if not k.startswith("_") and k not in ("recursive", "dates", "actual", "fitted", "resid")}
    alts["wage_q"]["alt_label"] = "Quarterly-difference (BJN2003/BN2008) wage form on the same data"
    # system residual correlations
    keys = ["wage", "price", "imp", "fx", "unemp", "output"]
    R = pd.concat([results[k]["_model"].resid.rename(k) for k in keys], axis=1).dropna().corr()
    # long-run
    lr = longrun_checks(d, cfg["start"], end)
    # derived long-run quantities
    imp = results["imp"]; ai = -[c for c in imp["coef"] if c["name"] == "ecm_pi_l1"][0]["est"]; kr = [c for c in imp["coef"] if c["name"] == "rex_l1"][0]
    lr["imp"] = {"alpha": round(ai, 4), "kappa": round(kr["est"] / ai, 3) if ai else None, "kappa_t": round(kr["t"], 2), "imposed": {"v": 1, "pf": 1, "source": "BN2008 eq 48 (κ = 0.55)"}}
    fx = results["fx_level"]; av = [c for c in fx["coef"] if c["name"] == "ecm_v_l1"][0]
    lr["fx"] = {"alpha_v": round(av["est"], 4), "alpha_v_t": round(av["t"], 2), "note": "BN2008 eq 36 finds −0.042 (t −3.5) on 1994Q2–2007Q2; NAM2026 Table 5.44 has no level term. The simulation uses the equation without the level term unless the 'PPP anchor' switch is on."}
    un = results["unemp"]; au = -[c for c in un["coef"] if c["name"] == "u_l2"][0]["est"]
    g = lambda n: [c for c in un["coef"] if c["name"] == n][0]
    lr["unemp"] = {"alpha": round(au, 4), "theta_wage": round(g("Dwp_l2")["est"] / au, 2), "theta_rr": round(g("rr_l2")["est"] / au, 4), "theta_g4y": round(g("g4y_l2")["est"] / au, 4),
                   "published": {"theta_wage": 7.69, "theta_rr": 0.05, "source": "BN2008 eq 41"}}
    mm = results["mm"]; gm = lambda n: [c for c in mm["coef"] if c["name"] == n][0]["est"]; am = -gm("RS_l1")
    lr["mm"] = {"RS_on_R": round(gm("R_l1") / am, 3), "RS_on_Rs": round(gm("Rs_l1") / am, 3), "const": round(gm("const") / am, 3), "published": {"RS_on_R": round(0.293 / 0.355, 3), "RS_on_Rs": round(0.153 / 0.355, 3), "source": "NAM2026 Table 5.78"}}
    # sample means used by the page to re-centre an equation's constant when a long-run coefficient is moved
    sw = d.loc[results["wage"]["sample"][0]:results["wage"]["sample"][1]]; sp = d.loc[results["price"]["sample"][0]:results["price"]["sample"][1]]; sy = d.loc[results["output"]["sample"][0]:results["output"]["sample"][1]]
    lr["means"] = {"u_l4": float(sw.u.shift(4).mean()), "ulc_minus_pi_l1": float((sp.w + sp.t1 - sp.z - sp.pi).shift(1).mean()), "g_l1": float(sy.g.shift(1).mean()),
                   "rex_l1": float(sy.rex.shift(1).mean()), "rr_l1": float(sy.rr.shift(1).mean()),
                   "note": "Sample means of the long-run components (lagged as they enter), so that moving γ_u, ϕ or the output long-run coefficients on the page keeps the equation's mean fit (the constant is re-centred as re-estimation of the constant alone would do)."}
    # dynamic homogeneity in the wage equation is not testable in the Δ4 form with the EqCM (a₁ is a disequilibrium term); report a₁ only
    fs = HERE / "fetch_status.json"   # written by fetch_data.py; the date of the last (re)fetch is the data vintage
    vintage = json.loads(fs.read_text(encoding="utf-8")).get("fetched", "2026-10-31") if fs.exists() else "2026-10-31"
    out = {"built": pd.Timestamp.today().strftime("%Y-%m-%d"), "data_vintage": vintage, "config": cfg, "sample": [cfg["start"], end],
           "last_quarter": {"qna": end, "monthly": str(d.p.dropna().index[-1])},
           "equations": {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in results.items()},
           "alternatives": alts, "residual_correlation": {"keys": keys, "matrix": [[round(float(R.loc[i, j]), 3) for j in keys] for i in keys]},
           "longrun": lr, "construction_notes": notes,
           "estimator_note": "Every equation is estimated by OLS. The published versions use FIML for the wage–price block (BJN2003, ABE2005, BN2008); here no contemporaneous endogenous regressor remains in the wage equation (Δ₄p enters lagged) and the price equation conditions on Δpi_t and Δpe_t, so OLS is consistent if the import-price and CPI disturbances are uncorrelated — see the residual correlation matrix. NAM2026 also estimates its equations one by one (§5.1)."}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    print("residual correlations:\n", R.round(2).to_string()); print("written", a.out)
    return out


if __name__ == "__main__":
    main()
