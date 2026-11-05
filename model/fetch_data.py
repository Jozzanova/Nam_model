#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fetch_data.py - build the quarterly dataset for the Model tab (EqCM wage-price model of Norway).

    python -X utf8 model/fetch_data.py            # fetch what is not cached under model/raw, build model/data.csv
    python -X utf8 model/fetch_data.py --refresh  # refetch everything

Every raw response is cached under model/raw/ (never refetched unless --refresh). The exact request for every
series is listed in model/data_map.md; this script is the executable version of that document. Output:

    model/data.csv          one row per quarter ("1978Q1" ...), levels and logs as defined in model_spec.md Part D
    model/data_columns.csv  one row per column: description, unit, seasonal adjustment, source, request, first/last quarter

Dependencies: pandas, numpy, requests, openpyxl (pip install -r model/requirements.txt). statsmodels is not needed
here; it is pinned for the estimation step.
"""
import io
import json
import re
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
RAW.mkdir(exist_ok=True)
REFRESH = "--refresh" in sys.argv
HEADERS = {"User-Agent": "eitrheim-dashboard model/fetch_data.py (python-requests)"}
TIMEOUT = 120

SSB = "https://data.ssb.no/api/v0/en/table/{}"
NB = "https://data.norges-bank.no/api/data/{}/{}?format=csv"
ECB = "https://data-api.ecb.europa.eu/service/data/{}/{}?format=csvdata"
EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{}/{}?format=SDMX-CSV"
OECD = "https://sdmx.oecd.org/public/rest/data/{}/{}?format=csvfilewithlabels&startPeriod={}"
WB_PAGE = "https://www.worldbank.org/en/research/commodity-markets"

COLUMNS = []   # (column, description, unit, seasonal adjustment, source, request)
warnings.simplefilter("ignore", category=pd.errors.PerformanceWarning)
_last_ssb_call = 0.0


# ----------------------------------------------------------------------------------------------------------------
# generic helpers
# ----------------------------------------------------------------------------------------------------------------
def log(msg):
    print(msg, flush=True)


KEPT = []   # raw files whose refetch failed and whose cached copy was used instead (reported at the end, written to fetch_status.json)


def cached_bytes(name, fetch):
    """Return cached raw bytes for `name`, calling fetch() (returns bytes) if not cached.
    With --refresh a failed fetch falls back to the cached copy (and is listed in KEPT) so one source that is down
    does not remove a series from data.csv."""
    path = RAW / name
    if path.exists() and not REFRESH:
        return path.read_bytes()
    try:
        data = fetch()
    except Exception as e:
        if path.exists():
            log(f"  !! {name}: refetch failed ({repr(e)[:160]}); keeping the cached copy")
            KEPT.append(name)
            return path.read_bytes()
        raise
    path.write_bytes(data)
    return data


def http_get(url, params=None):
    r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.content


def ssb_post(table, query):
    """POST a PxWeb v1 query, polite to SSB's rate limit."""
    global _last_ssb_call
    wait = 1.5 - (time.time() - _last_ssb_call)
    if wait > 0:
        time.sleep(wait)
    r = requests.post(SSB.format(table), json={"query": query, "response": {"format": "json-stat2"}},
                      headers=HEADERS, timeout=TIMEOUT)
    _last_ssb_call = time.time()
    r.raise_for_status()
    return r.content


def ssb_meta(table):
    raw = cached_bytes(f"ssb_{table}_meta.json", lambda: http_get(SSB.format(table)))
    return json.loads(raw.decode("utf-8"))


def ssb_code(table, dim, pattern, first=True):
    """Find the value code(s) of dimension `dim` in `table` whose label matches regex `pattern` (case-insensitive)."""
    meta = ssb_meta(table)
    for v in meta["variables"]:
        if v["code"] == dim:
            hits = [c for c, t in zip(v["values"], v["valueTexts"]) if re.search(pattern, t, re.I)]
            if not hits:
                raise KeyError(f"table {table}: no value of {dim} matches /{pattern}/; labels: {v['valueTexts'][:20]}")
            return hits[0] if first else hits
    raise KeyError(f"table {table}: no dimension {dim}")


def jsonstat_to_series(js):
    """json-stat2 -> pandas Series with a MultiIndex over all dimensions (codes)."""
    ids, sizes = js["id"], js["size"]
    cats = []
    for d in ids:
        idx = js["dimension"][d]["category"]["index"]
        codes = sorted(idx, key=idx.get) if isinstance(idx, dict) else list(idx)
        cats.append(codes)
    vals = js["value"]
    n = int(np.prod(sizes))
    if isinstance(vals, dict):
        arr = np.full(n, np.nan)
        for k, v in vals.items():
            arr[int(k)] = np.nan if v is None else v
    else:
        arr = np.array([np.nan if v is None else v for v in vals], dtype=float)
    index = pd.MultiIndex.from_product(cats, names=ids)
    return pd.Series(arr, index=index)


def ssb_series(table, name, query):
    """Run a StatBank query (list of {code, selection}) and return the json-stat2 Series. Cached as raw/ssb_<table>_<name>.json."""
    raw = cached_bytes(f"ssb_{table}_{name}.json", lambda: ssb_post(table, query))
    return jsonstat_to_series(json.loads(raw.decode("utf-8")))


def ssb_item(code, values):
    return {"code": code, "selection": {"filter": "item", "values": values if isinstance(values, list) else [values]}}


SSB_ALL_TIME = {"code": "Tid", "selection": {"filter": "all", "values": ["*"]}}


def ssb_period_index(labels):
    """'2024M01' -> monthly Period, '2024K1' -> quarterly Period, '2024' -> annual Period."""
    out = []
    for s in labels:
        if "M" in s:
            out.append(pd.Period(s.replace("M", "-"), freq="M"))
        elif "K" in s:
            y, q = s.split("K")
            out.append(pd.Period(f"{y}Q{q}", freq="Q"))
        else:
            out.append(pd.Period(s, freq="Y"))
    return pd.PeriodIndex(out)


def pick(series, **sel):
    """Select one cell per time period from a json-stat2 Series; returns a Series indexed by Period."""
    s = series
    for dim, code in sel.items():
        s = s.xs(code, level=dim)
    if isinstance(s.index, pd.MultiIndex):
        s = s.droplevel([l for l in s.index.names if l != "Tid"])
    s.index = ssb_period_index(list(s.index))
    return s.sort_index().dropna()


def to_quarterly_mean(s, min_count=None):
    """Average a monthly or daily Period/Datetime-indexed Series to quarters. Incomplete quarters are dropped."""
    s = s.dropna()
    if isinstance(s.index, pd.PeriodIndex):
        if s.index.freqstr.startswith("Q"):
            return s
        q = s.index.asfreq("Q")
        expected = 3 if s.index.freqstr.startswith("M") else None
    else:
        q = pd.PeriodIndex(s.index, freq="Q")
        expected = None
    g = s.groupby(q)
    m, c = g.mean(), g.count()
    if min_count is None:
        min_count = expected if expected else 40  # daily data: at least 40 business-day observations
    return m[c >= min_count]


def csv_series(text, time_col, value_col, sep=","):
    df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str)
    df = df[[time_col, value_col]].dropna()
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna()
    t = df[time_col].str.strip()
    if t.str.len().max() == 10:                                  # daily 'YYYY-MM-DD'
        idx = pd.to_datetime(t)
    elif t.str.match(r"^\d{4}-\d{2}$").all():                   # monthly 'YYYY-MM'
        idx = pd.PeriodIndex(t, freq="M")
    elif t.str.match(r"^\d{4}-Q\d$").all():
        idx = pd.PeriodIndex(t.str.replace("-", ""), freq="Q")
    else:
        idx = pd.PeriodIndex(t, freq="Y")
    return pd.Series(df[value_col].values, index=idx).sort_index()


def nb_series(flow, key, name, extra=""):
    raw = cached_bytes(f"nb_{name}.csv", lambda: http_get(NB.format(flow, key) + extra))
    return csv_series(raw.decode("utf-8"), "TIME_PERIOD", "OBS_VALUE", sep=";")


def ecb_series(flow, key, name):
    raw = cached_bytes(f"ecb_{name}.csv", lambda: http_get(ECB.format(flow, key)))
    return csv_series(raw.decode("utf-8"), "TIME_PERIOD", "OBS_VALUE")


def eurostat_series(dataset, key, name):
    raw = cached_bytes(f"eurostat_{name}.csv", lambda: http_get(EUROSTAT.format(dataset, key)))
    text = raw.decode("utf-8")
    if text.lstrip().startswith("<?xml"):
        raise RuntimeError(f"Eurostat {dataset}/{key}: {text[:200]}")
    return csv_series(text, "TIME_PERIOD", "OBS_VALUE")


def oecd_frame(flow, key, name, start="1970-01"):
    raw = cached_bytes(f"oecd_{name}.csv", lambda: http_get(OECD.format(flow, key, start)))
    text = raw.decode("utf-8")
    if "NoRecordsFound" in text[:200] or "NoResultsFound" in text[:200]:
        raise RuntimeError(f"OECD {flow}/{key}: no records")
    df = pd.read_csv(io.StringIO(text), dtype=str)
    df["OBS_VALUE"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    return df


def oecd_series(df, ref_area):
    d = df[df["REF_AREA"] == ref_area].dropna(subset=["OBS_VALUE"])
    idx = pd.PeriodIndex(d["TIME_PERIOD"], freq="M")
    return pd.Series(d["OBS_VALUE"].values, index=idx).sort_index()


def add(frame, col, series, desc, unit, sa, source, request):
    """Attach a quarterly Series to the frame and record its documentation."""
    if isinstance(series, pd.Series):
        s = series.copy()
        s.index = pd.PeriodIndex(s.index, freq="Q")
        s = s.reindex(frame.index)
    else:  # array-like aligned with the frame (dummies)
        s = pd.Series(np.asarray(series, dtype=float), index=frame.index)
    frame[col] = s
    COLUMNS.append((col, desc, unit, sa, source, request))


# ----------------------------------------------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------------------------------------------
def main():
    failures = []

    def attempt(label, fn):
        try:
            fn()
        except Exception as e:  # keep going; report at the end
            failures.append((label, repr(e)[:300]))
            log(f"  !! {label}: {repr(e)[:300]}")

    quarters = pd.period_range("1970Q1", pd.Timestamp.today().to_period("Q"), freq="Q")
    D = pd.DataFrame(index=quarters)
    D.index.name = "quarter"

    # ---------------- 1. CPI (SSB 14710 total 1920-; 14706 derived series CPI-ATE/CPI-AT 1995-/2002M12-; 14708 SA; 14700 COICOP) ----
    def cpi():
        q = [ssb_item("ContentsCode", "KpiIndMnd"), SSB_ALL_TIME]
        s = pick(ssb_series("14710", "total", q), ContentsCode="KpiIndMnd")
        add(D, "cpi", to_quarterly_mean(s), "Consumer price index, all items, quarterly average of monthly index", "index 2025=100",
            "NSA", "SSB StatBank 14710", json.dumps(q))
        q = [ssb_item("KPIavledetSerie", ["KPI", "KPI-JAE", "KPI-JA", "KPI-JE"]), ssb_item("ContentsCode", "KPIJustIndMnd"), SSB_ALL_TIME]
        s = ssb_series("14706", "derived", q)
        add(D, "cpi_ate", to_quarterly_mean(pick(s, KPIavledetSerie="KPI-JAE", ContentsCode="KPIJustIndMnd")),
            "CPI-ATE (KPI-JAE: adjusted for tax changes and excluding energy products), quarterly average", "index 2025=100", "NSA",
            "SSB StatBank 14706", json.dumps(q))
        add(D, "cpi_at", to_quarterly_mean(pick(s, KPIavledetSerie="KPI-JA", ContentsCode="KPIJustIndMnd")),
            "CPI-AT (KPI-JA: adjusted for tax changes), quarterly average", "index 2025=100", "NSA", "SSB StatBank 14706", json.dumps(q))
        add(D, "cpi_xe", to_quarterly_mean(pick(s, KPIavledetSerie="KPI-JE", ContentsCode="KPIJustIndMnd")),
            "CPI excluding energy products (KPI-JE), quarterly average", "index 2025=100", "NSA", "SSB StatBank 14706", json.dumps(q))
        q = [ssb_item("KPIavledetSerie", ["KPI", "KPI-JAE"]), ssb_item("ContentsCode", "KPIsesong"), SSB_ALL_TIME]
        s = ssb_series("14708", "sa", q)
        add(D, "cpi_sa", to_quarterly_mean(pick(s, KPIavledetSerie="KPI", ContentsCode="KPIsesong")),
            "CPI seasonally adjusted (SSB), quarterly average", "index 2025=100", "SA (SSB)", "SSB StatBank 14708", json.dumps(q))
        add(D, "cpi_ate_sa", to_quarterly_mean(pick(s, KPIavledetSerie="KPI-JAE", ContentsCode="KPIsesong")),
            "CPI-ATE seasonally adjusted (SSB), quarterly average", "index 2025=100", "SA (SSB)", "SSB StatBank 14708", json.dumps(q))
        q = [ssb_item("VareTjenesteGrp", ["04.5", "07.2.2"]), ssb_item("ContentsCode", "KpiIndMnd"), SSB_ALL_TIME]
        s = ssb_series("14700", "energy", q)
        add(D, "cpi_elgas", to_quarterly_mean(pick(s, VareTjenesteGrp="04.5", ContentsCode="KpiIndMnd")),
            "CPI 04.5 Electricity, gas and other fuels (the 'pe' / CPIEL energy price indicator), quarterly average", "index 2025=100", "NSA",
            "SSB StatBank 14700", json.dumps(q))
        add(D, "cpi_fuel", to_quarterly_mean(pick(s, VareTjenesteGrp="07.2.2", ContentsCode="KpiIndMnd")),
            "CPI 07.2.2 Fuels and lubricants for personal transport equipment, quarterly average", "index 2025=100", "NSA",
            "SSB StatBank 14700", json.dumps(q))
    log("1. CPI"); attempt("CPI", cpi)

    # ---------------- 2. Quarterly national accounts: expenditure side (09190, 1978Q1-) ------------------------------------------
    def qna_exp():
        gov = ssb_code("09190", "Makrost", r"^Final consumption expenditure of general governmen")  # label is truncated in StatBank metadata ("koo.nroff")
        q = [ssb_item("Makrost", ["bnpb.nr23_9fn", "bnpb.nr23_6fn", "bnpb.nr23_9", "imp.nrtot", "imp.nrtradvare", gov]),
             ssb_item("ContentsCode", ["Priser", "Faste", "PriserSesJust", "FastePriserSesJust", "PrisIndex"]), SSB_ALL_TIME]
        s = ssb_series("09190", "exp", q)
        src = "SSB StatBank 09190"
        add(D, "gdp_ml", pick(s, Makrost="bnpb.nr23_9fn", ContentsCode="Faste"), "GDP Mainland Norway, market values, constant prices (base year moves with revisions; 2023 at collection)", "NOK million, constant prices", "NSA", src, json.dumps(q))
        add(D, "gdp_ml_sa", pick(s, Makrost="bnpb.nr23_9fn", ContentsCode="FastePriserSesJust"), "GDP Mainland Norway, market values, constant prices, seasonally adjusted (SSB)", "NOK million, constant prices", "SA (SSB)", src, json.dumps(q))
        add(D, "gdp_ml_cur", pick(s, Makrost="bnpb.nr23_9fn", ContentsCode="Priser"), "GDP Mainland Norway, market values, current prices", "NOK million", "NSA", src, json.dumps(q))
        add(D, "gdp_ml_basic", pick(s, Makrost="bnpb.nr23_6fn", ContentsCode="Faste"), "GDP Mainland Norway, basic values, constant prices", "NOK million, constant prices", "NSA", src, json.dumps(q))
        add(D, "gdp_total", pick(s, Makrost="bnpb.nr23_9", ContentsCode="Faste"), "GDP total, market values, constant prices", "NOK million, constant prices", "NSA", src, json.dumps(q))
        add(D, "gov_cons", pick(s, Makrost=gov, ContentsCode="Faste"), "Final consumption expenditure of general government, constant prices (g)", "NOK million, constant prices", "NSA", src, json.dumps(q))
        add(D, "imp_cur", pick(s, Makrost="imp.nrtot", ContentsCode="Priser"), "Total imports, current prices", "NOK million", "NSA", src, json.dumps(q))
        add(D, "imp_const", pick(s, Makrost="imp.nrtot", ContentsCode="Faste"), "Total imports, constant prices", "NOK million, constant prices", "NSA", src, json.dumps(q))
        add(D, "imp_trad_cur", pick(s, Makrost="imp.nrtradvare", ContentsCode="Priser"), "Imports of traditional goods, current prices", "NOK million", "NSA", src, json.dumps(q))
        add(D, "imp_trad_const", pick(s, Makrost="imp.nrtradvare", ContentsCode="Faste"), "Imports of traditional goods, constant prices", "NOK million, constant prices", "NSA", src, json.dumps(q))
        add(D, "pi_defl", D["imp_cur"] / D["imp_const"] * 100, "Implicit deflator of total imports (PI = 'Deflator of total imports' [RIMINI PB]); base year = QNA constant-price base", "index, base year = 100", "NSA", src + " (derived)", "imp_cur / imp_const")
        add(D, "pi_trad_defl", D["imp_trad_cur"] / D["imp_trad_const"] * 100, "Implicit deflator of traditional goods imports", "index", "NSA", src + " (derived)", "imp_trad_cur / imp_trad_const")
        add(D, "py_ml", D["gdp_ml_cur"] / D["gdp_ml"] * 100, "Implicit deflator of Mainland GDP, market values (NAM PYF counterpart)", "index", "NSA", src + " (derived)", "gdp_ml_cur / gdp_ml")
    log("2. QNA expenditure"); attempt("QNA 09190", qna_exp)

    # ---------------- 3. Value added by industry (09171, 1978Q1-) and wages/hours by industry (09175, 1995Q1-) ----------------
    def qna_ind():
        q = [ssb_item("NACE", ["nr23_6fn", "nr23ind", "nr23_6"]), ssb_item("ContentsCode", ["BNPB", "BNPB2", "BNPB2ses"]), SSB_ALL_TIME]
        s = ssb_series("09171", "va", q)
        src = "SSB StatBank 09171"
        add(D, "va_ml", pick(s, NACE="nr23_6fn", ContentsCode="BNPB2"), "Value added Mainland Norway, basic values, constant prices", "NOK million, constant prices", "NSA", src, json.dumps(q))
        add(D, "va_ml_cur", pick(s, NACE="nr23_6fn", ContentsCode="BNPB"), "Value added Mainland Norway, basic values, current prices", "NOK million", "NSA", src, json.dumps(q))
        add(D, "va_man", pick(s, NACE="nr23ind", ContentsCode="BNPB2"), "Value added manufacturing, constant prices", "NOK million, constant prices", "NSA", src, json.dumps(q))
        add(D, "va_man_cur", pick(s, NACE="nr23ind", ContentsCode="BNPB"), "Value added manufacturing, current prices", "NOK million", "NSA", src, json.dumps(q))
        q = [ssb_item("NACE", ["nr23_6fn", "nr23ind", "nr23_6"]),
             ssb_item("ContentsCode", ["Lonn", "LKostnader", "Timeverk", "TimeverkL", "SysselsatteLonn", "Lonn2", "LKostnader2", "TimeverkSesJust"]), SSB_ALL_TIME]
        s = ssb_series("09175", "wages", q)
        src = "SSB StatBank 09175"
        for nace, tag, lab in [("nr23_6fn", "ml", "Mainland Norway"), ("nr23ind", "man", "manufacturing")]:
            add(D, f"wages_{tag}", pick(s, NACE=nace, ContentsCode="Lonn"), f"Wages and salaries, {lab}", "NOK million", "NSA", src, json.dumps(q))
            add(D, f"wcost_{tag}", pick(s, NACE=nace, ContentsCode="LKostnader"), f"Compensation of employees (wage costs incl. employers' social contributions), {lab}", "NOK million", "NSA", src, json.dumps(q))
            add(D, f"hours_{tag}", pick(s, NACE=nace, ContentsCode="Timeverk"), f"Hours worked, employees and self-employed, {lab}", "million hours", "NSA", src, json.dumps(q))
            add(D, f"hours_emp_{tag}", pick(s, NACE=nace, ContentsCode="TimeverkL"), f"Hours worked, employees, {lab}", "million hours", "NSA", src, json.dumps(q))
            add(D, f"employees_{tag}", pick(s, NACE=nace, ContentsCode="SysselsatteLonn"), f"Employees, {lab}", "1000 persons", "NSA", src, json.dumps(q))
        add(D, "wages_ml_sa", pick(s, NACE="nr23_6fn", ContentsCode="Lonn2"), "Wages and salaries Mainland Norway, seasonally adjusted (SSB)", "NOK million", "SA (SSB)", src, json.dumps(q))
        add(D, "wcost_ml_sa", pick(s, NACE="nr23_6fn", ContentsCode="LKostnader2"), "Compensation of employees Mainland Norway, seasonally adjusted (SSB)", "NOK million", "SA (SSB)", src, json.dumps(q))
        # derived wage-block variables (model_spec Part D.3)
        add(D, "w_hour", D["wages_ml"] / D["hours_emp_ml"], "Hourly wage, Mainland Norway = wages and salaries / hours worked by employees (W)", "NOK per hour", "NSA", "derived 09175", "wages_ml / hours_emp_ml")
        add(D, "wc_hour", D["wcost_ml"] / D["hours_emp_ml"], "Hourly wage cost, Mainland Norway (WC)", "NOK per hour", "NSA", "derived 09175", "wcost_ml / hours_emp_ml")
        add(D, "t1", D["wcost_ml"] / D["wages_ml"] - 1, "Payroll-tax proxy tau1 = WC/W - 1 (employers' social contributions incl. pensions over wages; BJN: tau1 = WCF/WF - 1)", "ratio", "NSA (seasonal)", "derived 09175", "wcost_ml / wages_ml - 1")
        add(D, "t1_sa", D["wcost_ml_sa"] / D["wages_ml_sa"] - 1, "tau1 from SSB seasonally adjusted wages and wage costs", "ratio", "SA (SSB)", "derived 09175", "wcost_ml_sa / wages_ml_sa - 1")
        add(D, "w_hour_man", D["wages_man"] / D["hours_emp_man"], "Hourly wage, manufacturing (WFP1 counterpart)", "NOK per hour", "NSA", "derived 09175", "wages_man / hours_emp_man")
        add(D, "wc_hour_man", D["wcost_man"] / D["hours_emp_man"], "Hourly wage cost, manufacturing (WCFP1 counterpart)", "NOK per hour", "NSA", "derived 09175", "wcost_man / hours_emp_man")
        add(D, "z_ml", D["va_ml"] / D["hours_ml"], "Labour productivity Mainland Norway = constant-price value added / hours worked (Z, ZYF)", "constant NOK per hour", "NSA", "derived 09171/09175", "va_ml / hours_ml")
        add(D, "z_man", D["va_man"] / D["hours_man"], "Labour productivity manufacturing (ZYFP1 counterpart)", "constant NOK per hour", "NSA", "derived 09171/09175", "va_man / hours_man")
        add(D, "py_man", D["va_man_cur"] / D["va_man"] * 100, "Value-added deflator manufacturing (PYFP1 counterpart)", "index", "NSA", "derived 09171", "va_man_cur / va_man")
    log("3. QNA industry, wages, hours"); attempt("QNA 09171/09175", qna_ind)

    # ---------------- 4. Unemployment -----------------------------------------------------------------------------------------
    def unemployment():
        q = [ssb_item("Kjonn", "0"), ssb_item("Alder", "15-74"), ssb_item("ContentsCode", ["Prosent", "Personer"]), SSB_ALL_TIME]
        s = ssb_series("08518", "lfs", q)
        add(D, "u_lfs", pick(s, Kjonn="0", Alder="15-74", ContentsCode="Prosent"), "LFS unemployment rate, 15-74 (UAKU); breaks 2006 and 2021", "per cent of labour force", "NSA", "SSB StatBank 08518", json.dumps(q))
        add(D, "u_lfs_persons", pick(s, Kjonn="0", Alder="15-74", ContentsCode="Personer"), "LFS unemployed persons, 15-74 (AKULED)", "1000 persons", "NSA", "SSB StatBank 08518", json.dumps(q))
        # labour force 03777 (metadata-driven ContentsCode)
        lf_code = ssb_code("03777", "ContentsCode", r"labour force")
        q = [ssb_item("Kjonn", "0"), ssb_item("Alder", "15-74"), ssb_item("ContentsCode", lf_code), SSB_ALL_TIME]
        s = ssb_series("03777", "lf", q)
        add(D, "lf_lfs", pick(s, Kjonn="0", Alder="15-74", ContentsCode=lf_code), "LFS labour force, 15-74 (AKUSTYRK)", "1000 persons", "NSA", "SSB StatBank 03777", json.dumps(q))
        # seasonally adjusted LFS rate: 14483 (2009Q1-) spliced with 07458 (1997Q1-2024Q4)
        q1 = [ssb_item("Kjonn", "0"), ssb_item("Alder", "15-74"), ssb_item("Justering", "S"), ssb_item("ContentsCode", "ArbledProsArbstyrk"), SSB_ALL_TIME]
        s1 = pick(ssb_series("14483", "lfs_sa", q1), Kjonn="0", Alder="15-74", Justering="S", ContentsCode="ArbledProsArbstyrk")
        meta = ssb_meta("07458")
        dims = [v["code"] for v in meta["variables"]]
        q2 = [ssb_item("Alder", "15-74"), ssb_item("ContentsCode", "ArbeidslauseStyrken"), SSB_ALL_TIME]
        sel = {"Alder": "15-74", "ContentsCode": "ArbeidslauseStyrken"}
        if "Kjonn" in dims:
            q2.insert(0, ssb_item("Kjonn", "0")); sel["Kjonn"] = "0"
        s2 = pick(ssb_series("07458", "lfs_sa_old", q2), **sel)
        spliced = pd.concat([s2[s2.index < s1.index.min()], s1]).sort_index()
        add(D, "u_lfs_sa", spliced, "LFS unemployment rate, seasonally adjusted: 14483 (2009Q1-) with 07458 before 2009", "per cent", "SA (SSB)", "SSB StatBank 14483 + 07458", json.dumps(q1) + " ; " + json.dumps(q2))
        # registered unemployment (NAV): SSB 10540 rate 1999M01-2020M11, 10594 persons 1990M01-2020M11, then Norges Bank MPR data 2015Q1-
        q = [ssb_item("Region", "0"), ssb_item("Alder", "15-74"), ssb_item("ContentsCode", "RegHeltLedige"), SSB_ALL_TIME]
        s_rate = to_quarterly_mean(pick(ssb_series("10540", "reg_rate", q), Region="0", Alder="15-74", ContentsCode="RegHeltLedige"))
        q2 = [ssb_item("Region", "0"), ssb_item("Kjonn", "0"), ssb_item("ContentsCode", "Registrerte1"), SSB_ALL_TIME]
        s_pers = to_quarterly_mean(pick(ssb_series("10594", "reg_persons", q2), Region="0", Kjonn="0", ContentsCode="Registrerte1"))
        add(D, "u_reg_persons", s_pers, "Registered wholly unemployed (NAV via SSB), quarterly average of monthly; monthly only to 2014M12 (afterwards only November values, dropped)", "persons", "NSA", "SSB StatBank 10594", json.dumps(q2))
        add(D, "u_reg_ssb", s_rate, "Registered unemployment rate (NAV via SSB), quarterly average of monthly; monthly only 1999M01-2014M12 (afterwards only November/March values, dropped)", "per cent of labour force", "NSA", "SSB StatBank 10540", json.dumps(q))
        # Norges Bank MPR data file, sheet 'Data G': quarterly registered unemployment rate (history + projections)
        mpr = json.loads((ROOT / "norges_bank_projections.json").read_text(encoding="utf-8")) if (ROOT / "norges_bank_projections.json").exists() else {}
        s_nb = None
        if mpr.get("tables_url"):
            raw = cached_bytes("nb_mpr_data.xlsx", lambda: http_get(mpr["tables_url"]))
            xl = pd.read_excel(io.BytesIO(raw), sheet_name=None, header=None)
            for name, df in xl.items():
                txt = " ".join(str(x) for x in df.iloc[:12].values.ravel() if pd.notna(x))
                if "Registrert ledighet" in txt and "Dato" in txt:
                    hdr = df.index[df.iloc[:, 0].astype(str).str.strip() == "Dato"][0]
                    body = df.iloc[hdr + 2:, :2].dropna()
                    body = body[pd.to_datetime(body.iloc[:, 0], errors="coerce").notna()]
                    idx = pd.PeriodIndex(pd.to_datetime(body.iloc[:, 0]), freq="Q")
                    s_nb = pd.Series(pd.to_numeric(body.iloc[:, 1]).values, index=idx)
                    break
        if s_nb is not None:
            m = re.search(r"(\d{4}Q[1-4])", str(mpr.get("projection_start", "")))
            start = pd.Period(m.group(1) if m else "2026Q3", freq="Q")
            hist = s_nb[s_nb.index < start]
            add(D, "u_reg_nb", hist, "Registered unemployment rate, Norges Bank MPR data file (NAV source; history up to the MPR cut-off, projections excluded)", "per cent of labour force", "SA (Norges Bank)", "Norges Bank " + mpr.get("report", "MPR"), mpr["tables_url"])
            # before 1999: persons / LFS labour force; 1999-2020M11: SSB rate; after: Norges Bank history (NSA/SA mismatch flagged)
            early = (D["u_reg_persons"] / 1000.0 / D["lf_lfs"] * 100)
            early = early[early.index < s_rate.index.min()]
            spliced = pd.concat([early.dropna(), s_rate, hist[hist.index > s_rate.index.max()]]).sort_index()
            add(D, "u_reg", spliced, "Registered unemployment rate, spliced: 1990Q1-1998Q4 persons/LFS labour force (10594/03777), 1999Q1-2014Q4 SSB 10540 (NSA), 2015Q1- Norges Bank MPR data-file history (NAV source, SA). No overlap; the 2014/2015 seam is NSA->SA.", "per cent", "mixed (NSA to 2014Q4, SA after)", "derived", "see components")
        else:
            add(D, "u_reg", s_rate, "Registered unemployment rate (SSB 10540 only)", "per cent", "NSA", "SSB StatBank 10540", json.dumps(q))
    log("4. Unemployment"); attempt("unemployment", unemployment)

    # ---------------- 5. External trade price index (08241), first-hand import prices (03675) --------------------------------
    def trade_prices():
        q = [ssb_item("ImpEks", "1"), ssb_item("ImpEkspGr", "-"), ssb_item("ContentsCode", "Prisindeks"), SSB_ALL_TIME]
        s = pick(ssb_series("08241", "imp_price", q), ImpEks="1", ImpEkspGr="-", ContentsCode="Prisindeks")
        add(D, "pm_trade", s, "External trade in commodities, price index of imports, total (unit-value based)", "index 2000=100", "NSA", "SSB StatBank 08241", json.dumps(q))
        q = [ssb_item("Marked", ["4", "3"]), ssb_item("SITC", "SITCT"), ssb_item("ContentsCode", "Indeksniva"), SSB_ALL_TIME]
        s = ssb_series("03675", "pif", q)
        add(D, "pif_imp", to_quarterly_mean(pick(s, Marked="4", SITC="SITCT", ContentsCode="Indeksniva")), "Price index of first-hand domestic sales, import market, all commodities (from 2000M12)", "index 2021=100", "NSA", "SSB StatBank 03675", json.dumps(q))
        add(D, "pif_all", to_quarterly_mean(pick(s, Marked="3", SITC="SITCT", ContentsCode="Indeksniva")), "Price index of first-hand domestic sales, domestic + import market, all commodities", "index 2021=100", "NSA", "SSB StatBank 03675", json.dumps(q))
    log("5. Trade prices"); attempt("trade prices", trade_prices)

    # ---------------- 6. Norges Bank: policy rate, D-loan rate, NOWA, I-44, TWI, EUR, USD -------------------------------------
    def norges_bank():
        s = nb_series("IR", "B.KPRA.SD.", "kpra_sd_daily", "&startPeriod=1980-01-01")
        add(D, "policy_rate", to_quarterly_mean(s), "Norges Bank key policy rate (sight deposit rate, KPRA SD), quarterly average of daily end-of-day values; from 1991-01-01", "per cent", "n/a", "Norges Bank open data IR", NB.format("IR", "B.KPRA.SD.") + "&startPeriod=1980-01-01")
        s = nb_series("IR", "M.KPRA.OL.", "kpra_ol_monthly")
        add(D, "dloan_rate", to_quarterly_mean(s, min_count=2), "Overnight lending (D-loan) rate, KPRA OL, quarterly average of monthly; from 1982-04 (gaps in 1982)", "per cent", "n/a", "Norges Bank open data IR", NB.format("IR", "M.KPRA.OL."))
        s = nb_series("SHORT_RATES", "M.NOWA.ON.R", "nowa_monthly")
        add(D, "nowa", to_quarterly_mean(s), "NOWA overnight rate, quarterly average of monthly; from 2011-10", "per cent", "n/a", "Norges Bank open data SHORT_RATES", NB.format("SHORT_RATES", "M.NOWA.ON.R"))
        s = nb_series("EXR", "M.I44.NOK.SP", "i44_monthly")
        add(D, "i44", to_quarterly_mean(s), "Import-weighted exchange rate index I-44, quarterly average of monthly averages; 1995 = 100; higher = weaker NOK (V)", "index 1995=100", "n/a", "Norges Bank open data EXR", NB.format("EXR", "M.I44.NOK.SP"))
        s = nb_series("EXR", "M.TWI.NOK.SP", "twi_monthly")
        add(D, "twi", to_quarterly_mean(s), "Trade-weighted exchange rate index TWI, quarterly average; 1990 = 100; higher = weaker NOK; from 1971", "index 1990=100", "n/a", "Norges Bank open data EXR", NB.format("EXR", "M.TWI.NOK.SP"))
        s = nb_series("EXR", "M.EUR.NOK.SP", "eurnok_monthly")
        add(D, "eurnok", to_quarterly_mean(s), "NOK per EUR, quarterly average", "NOK", "n/a", "Norges Bank open data EXR", NB.format("EXR", "M.EUR.NOK.SP"))
        s = nb_series("EXR", "M.USD.NOK.SP", "usdnok_monthly")
        add(D, "usdnok", to_quarterly_mean(s), "NOK per USD, quarterly average", "NOK", "n/a", "Norges Bank open data EXR", NB.format("EXR", "M.USD.NOK.SP"))
    log("6. Norges Bank"); attempt("Norges Bank", norges_bank)

    # ---------------- 7. Foreign prices and rates: ECB, Eurostat, OECD ------------------------------------------------------
    def foreign():
        s = ecb_series("HICP", "M.U2.N.000000.4D0.INX", "hicp_ea")
        add(D, "hicp_ea", to_quarterly_mean(s), "Euro area HICP all items, quarterly average (ECB HICP dataflow, successor of ICP)", "index 2025=100", "NSA", "ECB Data Portal", ECB.format("HICP", "M.U2.N.000000.4D0.INX"))
        s = ecb_series("FM", "M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA", "euribor3m")
        add(D, "euribor3m", to_quarterly_mean(s), "3-month EURIBOR, quarterly average of monthly (foreign short rate R*)", "per cent", "n/a", "ECB Data Portal FM", ECB.format("FM", "M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA"))
        try:
            s = eurostat_series("sts_inppd_m", "M.PRC_PRR_DOM.B-E36.NSA.I21.EA20", "ppi_ea")
            add(D, "ppi_ea", to_quarterly_mean(s), "Euro area producer prices, domestic output, industry B-E36 (foreign producer price pf proxy)", "index 2021=100", "NSA", "Eurostat sts_inppd_m", EUROSTAT.format("sts_inppd_m", "M.PRC_PRR_DOM.B-E36.NSA.I21.EA20"))
        except Exception as e:
            failures.append(("Eurostat PPI", repr(e)[:200]))
        try:
            s = eurostat_series("sts_inppd_m", "M.PRC_PRR_DOM.B-E36.NSA.I21.DE", "ppi_de")
            add(D, "ppi_de", to_quarterly_mean(s), "Germany producer prices, domestic output, industry B-E36 (longer pf proxy)", "index 2021=100", "NSA", "Eurostat sts_inppd_m", EUROSTAT.format("sts_inppd_m", "M.PRC_PRR_DOM.B-E36.NSA.I21.DE"))
        except Exception as e:
            failures.append(("Eurostat PPI DE", repr(e)[:200]))
        key = "SWE+DEU+GBR+USA+NOR+EA20.M.N.CPI.IX._T.N."
        df = oecd_frame("OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0", key, "cpi", "1960-01")
        for area, col in [("SWE", "cpi_se"), ("DEU", "cpi_de"), ("GBR", "cpi_uk"), ("USA", "cpi_us"), ("EA20", "cpi_ea_oecd")]:
            try:
                add(D, col, to_quarterly_mean(oecd_series(df, area)), f"CPI all items {area} (OECD), quarterly average", "index 2015=100", "NSA", "OECD SDMX DF_PRICES_ALL", OECD.format("OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0", key, "1960-01"))
            except Exception as e:
                failures.append((col, repr(e)[:200]))
        key = "EA20+SWE+GBR+USA+DEU+NOR.M.IR3TIB.PA....."
        df = oecd_frame("OECD.SDD.STES,DSD_STES@DF_FINMARK,4.0", key, "ir3", "1970-01")
        for area, col, desc in [("NOR", "nibor3m", "Norway 3-month interbank rate (NIBOR 3m; OECD IR3TIB NOR) - the money-market rate RS"),
                                ("EA20", "ir3_ea", "Euro area 3-month interbank rate (OECD)"), ("DEU", "ir3_de", "Germany 3-month interbank rate (OECD)"),
                                ("SWE", "ir3_se", "Sweden 3-month interbank rate (OECD)"), ("USA", "ir3_us", "US 3-month rate (OECD)")]:
            try:
                add(D, col, to_quarterly_mean(oecd_series(df, area)), desc + ", quarterly average of monthly", "per cent", "n/a", "OECD SDMX DF_FINMARK", OECD.format("OECD.SDD.STES,DSD_STES@DF_FINMARK,4.0", key, "1970-01"))
            except Exception as e:
                failures.append((col, repr(e)[:200]))
    log("7. Foreign"); attempt("foreign", foreign)

    # ---------------- 8. Oil: World Bank Pink Sheet (FRED is not reachable from this network) -------------------------------
    def oil():
        def fetch_xlsx():
            page = http_get(WB_PAGE).decode("utf-8", "ignore")
            m = re.search(r"https://thedocs\.worldbank\.org/[^\"' ]*CMO-Historical-Data-Monthly\.xlsx", page)
            if not m:
                raise RuntimeError("World Bank monthly Pink Sheet link not found on " + WB_PAGE)
            (RAW / "wb_pink_sheet_url.txt").write_text(m.group(0), encoding="utf-8")
            return http_get(m.group(0))
        raw = cached_bytes("wb_pink_sheet_monthly.xlsx", fetch_xlsx)
        df = pd.read_excel(io.BytesIO(raw), sheet_name="Monthly Prices", header=4)
        col = [c for c in df.columns if str(c).strip().lower().startswith("crude oil, brent")][0]
        t = df.iloc[:, 0].astype(str).str.strip()
        ok = t.str.match(r"^\d{4}M\d{2}$")
        s = pd.Series(pd.to_numeric(df.loc[ok, col], errors="coerce").values, index=pd.PeriodIndex(t[ok].str.replace("M", "-"), freq="M")).dropna()
        url = (RAW / "wb_pink_sheet_url.txt").read_text(encoding="utf-8") if (RAW / "wb_pink_sheet_url.txt").exists() else WB_PAGE
        add(D, "oil_brent", to_quarterly_mean(s), "Brent crude oil, USD per barrel, quarterly average of monthly (World Bank Pink Sheet)", "USD/bbl", "n/a", "World Bank Commodity Markets", url)
    log("8. Oil"); attempt("oil", oil)

    # ---------------- 9. Logs, model variables, dummies ---------------------------------------------------------------------
    def derived():
        L = lambda c: np.log(D[c])
        logs = {
            "w": ("w_hour", "log hourly wage, Mainland Norway"), "wc": ("wc_hour", "log hourly wage cost, Mainland Norway"),
            "p": ("cpi", "log CPI"), "pu": ("cpi_ate", "log CPI-ATE"), "pe": ("cpi_elgas", "log CPI electricity, gas and other fuels"),
            "pi": ("pi_defl", "log import deflator (total imports)"), "pitrad": ("pi_trad_defl", "log import deflator, traditional goods"),
            "pm": ("pm_trade", "log external-trade import price index"), "z": ("z_ml", "log productivity Mainland Norway"),
            "y": ("gdp_ml", "log Mainland GDP, constant prices, NSA"), "ysa": ("gdp_ml_sa", "log Mainland GDP, constant prices, SA"),
            "g": ("gov_cons", "log government consumption, constant prices"), "py": ("py_ml", "log Mainland GDP deflator"),
            "v": ("i44", "log I-44 (up = depreciation)"), "vtwi": ("twi", "log TWI"), "pstar": ("hicp_ea", "log euro-area HICP (p*)"),
            "pf": ("ppi_ea", "log euro-area PPI (pf proxy)"), "pfde": ("ppi_de", "log German PPI (long pf proxy)"), "u": ("u_reg", "log registered unemployment rate (u, BN2008 definition)"),
            "ulfs": ("u_lfs", "log LFS unemployment rate (UAKU)"), "oil": ("oil_brent", "log Brent USD"),
            "wman": ("w_hour_man", "log hourly wage manufacturing"), "zman": ("z_man", "log productivity manufacturing"), "qman": ("py_man", "log value-added deflator manufacturing"),
        }
        for col, (src, desc) in logs.items():
            if src in D.columns:
                add(D, "l_" + col, L(src), desc, "log", sa_of(src), "derived", f"ln({src})")
        if "cpi_at" in D.columns:
            add(D, "t3", np.log(D["cpi"]) - np.log(D["cpi_at"]), "Indirect-tax proxy tau3 = ln(CPI) - ln(CPI-AT): cumulative contribution of tax changes to the CPI since the CPI-AT base (2002M12); level is relative to 2025 = 100", "log points", "NSA", "derived 14710/14706", "ln(cpi) - ln(cpi_at)")
        if {"l_w", "l_p", "l_z"} <= set(D.columns):
            add(D, "ecm_w", D["l_w"] - D["l_p"] - D["l_z"] + 0.1 * D["l_u"], "Wage EqCM term (w - p - z) + 0.1 u, BJN Table 1 Panel 4 / BN2008 eq 50 (constant not removed)", "log", "NSA", "derived", "l_w - l_p - l_z + 0.1*l_u")
        if {"l_p", "l_w", "l_z", "l_pi", "t1"} <= set(D.columns):
            add(D, "ecm_p", D["l_p"] - 0.6 * (D["l_w"] + np.log1p(D["t1"]) - D["l_z"]) - 0.4 * D["l_pi"] - D["t3"].fillna(0), "Price EqCM term p - 0.6(w + ln(1+tau1) - z) - 0.4 pi - tau3, BJN Table 1 Panel 4 (constant not removed)", "log", "NSA", "derived", "l_p - 0.6*(l_w + ln(1+t1) - l_z) - 0.4*l_pi - t3")
        if {"l_v", "l_pstar", "l_p"} <= set(D.columns):
            add(D, "rex", D["l_v"] + D["l_pstar"] - D["l_p"], "Real exchange rate v + p* - p (up = real depreciation)", "log", "NSA", "derived", "l_v + l_pstar - l_p")
        if {"l_pi", "l_v", "l_pf"} <= set(D.columns):
            add(D, "ecm_pi", D["l_pi"] - D["l_v"] - D["l_pf"], "Import-price EqCM term pi - v - pf (homogeneity imposed)", "log", "NSA", "derived", "l_pi - l_v - l_pf")
        add(D, "infl4", 100 * (D["cpi"] / D["cpi"].shift(4) - 1), "CPI inflation, four-quarter, per cent (pi_t)", "per cent", "NSA", "derived", "100*(cpi/cpi(-4)-1)")
        if "cpi_ate" in D.columns:
            add(D, "infl4_ate", 100 * (D["cpi_ate"] / D["cpi_ate"].shift(4) - 1), "CPI-ATE inflation, four-quarter, per cent", "per cent", "NSA", "derived", "100*(cpi_ate/cpi_ate(-4)-1)")
        if "hicp_ea" in D.columns:
            add(D, "infl4_ea", 100 * (D["hicp_ea"] / D["hicp_ea"].shift(4) - 1), "Euro-area HICP inflation, four-quarter", "per cent", "NSA", "derived", "100*(hicp_ea/hicp_ea(-4)-1)")
        # money-market rate RS: NIBOR 3m (OECD) ; policy rate spliced back with the D-loan rate before 1991
        if "nibor3m" in D.columns:
            add(D, "rs", D["nibor3m"], "Money-market rate RS = NIBOR 3m (OECD IR3TIB NOR)", "per cent", "n/a", "derived", "nibor3m")
        if {"policy_rate", "dloan_rate"} <= set(D.columns):
            r = D["policy_rate"].copy()
            early = D["dloan_rate"][D["dloan_rate"].index < r.dropna().index.min()]
            add(D, "r_policy_spliced", pd.concat([early, r.dropna()]).sort_index(), "Policy rate spliced: D-loan rate (KPRA OL) before 1991Q1, sight deposit rate after", "per cent", "n/a", "derived", "dloan_rate before 1991Q1, policy_rate after")
        # inflation target (per cent): 2.5 from 2001Q2 (29 March 2001), 2.0 from 2018Q1 (2 March 2018)
        tgt = pd.Series(np.nan, index=D.index)
        tgt[D.index >= pd.Period("2001Q2", freq="Q")] = 2.5
        tgt[D.index >= pd.Period("2018Q1", freq="Q")] = 2.0
        add(D, "infl_target", tgt, "Inflation target: 2.5 from 2001Q2, 2.0 from 2018Q1 (NaN before inflation targeting)", "per cent", "n/a", "Norges Bank regulation 2001/2018", "hand-coded")
        add(D, "d_it", (D.index >= pd.Period("2001Q2", freq="Q")).astype(int), "Inflation-targeting step dummy IT: 0 to 2001Q1, 1 from 2001Q2 (BN2008 App. A)", "0/1", "n/a", "BN2008-WP App. A", "hand-coded")
        for j in range(1, 9):
            per = pd.Period("2020Q1", freq="Q") + (j - 1)
            add(D, f"covidq{j}", (D.index == per).astype(int), f"Covid impulse dummy COVIDQ{j} = 1 in {per} (NAM2026 convention: COVIDQ5 = 2021Q1)", "0/1", "n/a", "NAM2026 §5.1", "hand-coded")
        add(D, "ukrw", (D.index == pd.Period("2022Q1", freq="Q")).astype(int), "Ukraine-war impulse dummy UKRW = 1 in 2022Q1 (NAM2026 §5.1)", "0/1", "n/a", "NAM2026 §5.1", "hand-coded")
        for k in range(1, 4):
            add(D, f"s{k}", (D.index.quarter == k).astype(int), f"Seasonal dummy S{k} (quarter {k})", "0/1", "n/a", "NAM2026 §5.1", "hand-coded")
        for k in range(1, 4):
            add(D, f"cs{k}", np.where(D.index.quarter == k, 0.75, -0.25), f"Centred seasonal dummy CS{k} (0.75 in quarter {k}, -0.25 otherwise)", "0/1", "n/a", "NAM2026 §5.1 fn. 2", "hand-coded")
    log("9. Derived variables"); attempt("derived", derived)

    # ---------------- write --------------------------------------------------------------------------------------------------
    hand = [c for c, *_ in COLUMNS if _[-1] == "hand-coded"]
    D = D.loc[D.drop(columns=hand).notna().any(axis=1)]   # drop quarters that only have dummies
    D.index = D.index.astype(str)
    D.to_csv(ROOT / "data.csv", float_format="%.6f")
    rows = []
    for col, desc, unit, sa, source, request in COLUMNS:
        s = D[col].dropna() if col in D.columns else pd.Series(dtype=float)
        rows.append({"column": col, "description": desc, "unit": unit, "seasonal_adjustment": sa, "source": source,
                     "request": request, "first": s.index.min() if len(s) else "", "last": s.index.max() if len(s) else "", "n": len(s)})
    cols = pd.DataFrame(rows)
    cols.to_csv(ROOT / "data_columns.csv", index=False)

    log("\nCoverage (first / last quarter, n):")
    for r in rows:
        log(f"  {r['column']:<16} {str(r['first']):<7} {str(r['last']):<7} {r['n']:>4}   {r['description'][:80]}")
    log(f"\nWrote {ROOT / 'data.csv'} ({D.shape[0]} quarters x {D.shape[1]} columns) and {ROOT / 'data_columns.csv'}")
    if KEPT:
        log("\nKEPT FROM CACHE (refetch failed, cached raw file used): " + ", ".join(KEPT))
    if failures:
        log("\nFAILURES (series missing from data.csv):")
        for label, err in failures:
            log(f"  - {label}: {err}")
    status = {"fetched": pd.Timestamp.today().strftime("%Y-%m-%d"), "refresh": REFRESH, "kept_from_cache": KEPT,
              "failures": [{"series": label, "error": err} for label, err in failures]}
    (ROOT / "fetch_status.json").write_text(json.dumps(status, indent=1), encoding="utf-8")
    return 1 if failures else 0


def sa_of(col):
    """Seasonal-adjustment note recorded for an existing column."""
    for c, desc, unit, sa, source, request in COLUMNS:
        if c == col:
            return sa
    return ""


if __name__ == "__main__":
    sys.exit(main())
