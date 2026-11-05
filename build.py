"""Build site/index.html for the NAM-type model dashboard.

    python -X utf8 model/run_model.py            # estimate, check, simulate, forecast evaluation, robustness, JS-twin test
    python -X utf8 model/run_model.py --refresh  # ... refetching the data first
    python -X utf8 build.py                      # then this: inject the model outputs and modelsim.js into template.html
    python -X utf8 build.py --open               # ... and open the page

Deploy: npx wrangler deploy (wrangler.jsonc serves ./site). The page is self-contained: all data is embedded in index.html."""
import json, re, sys, webbrowser
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"


def model_block() -> dict | None:
    """estimates.json, simulation.json, forecast_eval.json and robustness.json from model/ (built by model/run_model.py), the
    as-implemented departures (model_spec.md D.7) and additions (D.8), and the sources list. None when the model has not been run."""
    mdir = ROOT / "model"
    if not (mdir / "estimates.json").exists() or not (mdir / "simulation.json").exists():
        return None
    est = json.loads((mdir / "estimates.json").read_text(encoding="utf-8"))
    sim = json.loads((mdir / "simulation.json").read_text(encoding="utf-8"))
    keys = ["wage", "price", "imp", "fx", "unemp", "output", "mm", "bridge"]   # the same eight as simulate.py's bootstrap
    common = sorted(set.intersection(*[set(est["equations"][k]["dates"]) for k in keys]))
    sim["bands"]["resid_matrix"] = {"keys": keys, "dates": common,
                                    "rows": [[round(est["equations"][k]["resid"][est["equations"][k]["dates"].index(q)], 8) for k in keys] for q in common]}
    for grp in (est["equations"], est["alternatives"]):
        for eq in grp.values():
            eq.pop("resid", None)
            if "recursive" in eq:
                eq["recursive"] = {k: ([round(x, 5) for x in v] if k != "dates" else v) for k, v in eq["recursive"].items()}
    deps = []
    spec = (mdir / "model_spec.md").read_text(encoding="utf-8")
    sec = spec.split("### D.7", 1)[1].split("\n---", 1)[0] if "### D.7" in spec else ""
    for para in re.split(r"\n(?=- \*\*)", sec):
        m = re.match(r"- \*\*(.+?)\*\*\s*(.*)", para.strip(), re.S)
        if m:
            deps.append({"title": m.group(1).rstrip("."), "text": re.sub(r"\s+", " ", m.group(2)).strip()})
    adds = []
    sec8 = spec.split("### D.8", 1)[1].split("\n---", 1)[0] if "### D.8" in spec else ""
    for para in re.split(r"\n(?=- \*\*)", sec8):
        m = re.match(r"- \*\*(.+?)\*\*\s*(.*)", para.strip(), re.S)
        if m:
            adds.append({"title": m.group(1).rstrip("."), "text": re.sub(r"\s+", " ", m.group(2)).strip()})
    fe = json.loads((mdir / "forecast_eval.json").read_text(encoding="utf-8")) if (mdir / "forecast_eval.json").exists() else None
    rb = json.loads((mdir / "robustness.json").read_text(encoding="utf-8")) if (mdir / "robustness.json").exists() else None
    sources = [
        {"tag": "BJN2003", "text": "Bårdsen, G., Jansen, E. S. and Nymoen, R. (2003), 'Econometric inflation targeting', Econometrics Journal 6, 429–460; read in the working-paper versions (Norges Bank Arbeidsnotat 2002/5 / UiO Memorandum 15/2002).", "url": "https://www.norges-bank.no/en/news-events/publications/Working-Papers/2002/wp-20025/"},
        {"tag": "ABE2005", "text": "Akram, Q. F., Bårdsen, G. and Eitrheim, Ø. (2005), 'Monetary policy and asset prices: to respond or not?', Norges Bank Working Paper 2005/9 (the public counterpart of the policy chapter of Bårdsen, Eitrheim, Jansen and Nymoen, The Econometrics of Macroeconomic Modelling, Oxford University Press 2005).", "url": "https://www.norges-bank.no/en/news-events/publications/Working-Papers/2005/wp-20059/"},
        {"tag": "BN2008", "text": "Bårdsen, G. and Nymoen, R. (2009), 'Macroeconometric modelling for policy', in Palgrave Handbook of Econometrics vol. 2; working-paper version 'Macroeconometric modeling for policy' (2008), whose header asks that it not be quoted without permission — coefficients are cited for comparison only.", "url": "https://www.normetrics.no/"},
        {"tag": "NAM2026", "text": "Bårdsen, G. and Nymoen, R., Norwegian Aggregate Model (NAM): documentation, 5 October 2026 version, normetrics.no.", "url": "https://www.normetrics.no/"},
        {"tag": "Data", "text": "Statistics Norway StatBank tables 14710, 14706, 14708, 14700, 09190, 09171, 09175, 08518, 03777, 10540, 10594; Norges Bank open data (IR, EXR, SHORT_RATES) and the MPR 3/26 data file; ECB (HICP, EURIBOR); Eurostat (PPI); OECD (CPI, short rates); World Bank Pink Sheet (Brent).", "url": None},
        {"tag": "Robustness", "text": "Hendry, D. F., Johansen, S. and Santos, C. (2008), 'Automatic selection of indicators in a fully saturated regression', Computational Statistics 23; Castle, J. L., Doornik, J. A. and Hendry, D. F. (2012), 'Model selection when there are multiple breaks', Journal of Econometrics 169; Hendry, D. F. and Santos, C. (2010), 'An automatic test of super exogeneity', in Volatility and Time Series Econometrics (OUP); Castle, Doornik, Hendry and Nymoen (2014), 'Mis-specification testing: non-invariance of expectations models of inflation', Econometric Reviews 33; Bårdsen, G., Jansen, E. S. and Nymoen, R. (2004), 'Econometric evaluation of the New Keynesian Phillips curve', Oxford Bulletin of Economics and Statistics 66; Hansen, H. and Johansen, S. (1999), 'Some tests for parameter constancy in cointegrated VAR-models', Econometrics Journal 2.", "url": None},
        {"tag": "Comparators", "text": "Norges Bank, Monetary Policy Report 3/2026 (24 September 2026); LO, Konjunkturutsiktene (Samfunnsnotat 1/2026 and 3/2026), forecasts made with NAM.", "url": sim.get("norges_bank", {}).get("url")},
    ]
    sources.insert(4, {"tag": "EHN1999", "text": "Eitrheim, Ø., Husebø, T. A. and Nymoen, R. (1999), 'Equilibrium-correction vs. differencing in macroeconometric forecasting', Economic Modelling 16, 515–544; and Eitrheim, Ø., Jansen, E. S. and Nymoen, R. (2002), 'Progress from forecast failure — the Norwegian consumption function', Econometrics Journal 5, 40–64: the forecast-evaluation design (EqCM against dVAR, intercept correction).", "url": "https://doi.org/10.1016/S0264-9993(99)00013-6"})
    # data status for the Overview box: the last check (model/data_check.json, written by check_data.py) and the last data update
    ds = json.loads((mdir / "data_check.json").read_text(encoding="utf-8")) if (mdir / "data_check.json").exists() else {}
    data_status = {k: ds.get(k) for k in ("checked", "fetched", "outcome", "summary", "last_update", "kept_from_cache", "failures", "last_quarter")}
    data_status["schedule"] = "on Tuesday and Friday mornings"
    return {"estimates": est, "simulation": sim, "departures": deps, "additions": adds, "forecast_eval": fe, "robustness": rb, "sources": sources,
            "data_status": data_status}


def main():
    md = model_block()
    if md is None:
        sys.exit("model/estimates.json or model/simulation.json missing: run python -X utf8 model/run_model.py first")
    md["generated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    SITE.mkdir(exist_ok=True)
    template = (ROOT / "template.html").read_text(encoding="utf-8")
    payload = json.dumps(md, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = template.replace("/*__DATA__*/null", payload)
    msim = ROOT / "model" / "modelsim.js"
    page = page.replace("/*__MODELSIM__*/", msim.read_text(encoding="utf-8").replace("</", "<\\/") if msim.exists() else "const modelSim = null;")
    (SITE / "index.html").write_text(page, encoding="utf-8")
    print(f"wrote {SITE / 'index.html'} ({len(page) // 1024} kB)")
    if "--open" in sys.argv:
        webbrowser.open((SITE / "index.html").as_uri())


if __name__ == "__main__":
    main()
