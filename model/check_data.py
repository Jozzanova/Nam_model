#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_data.py - is there new data? Refetch every source and compare with the dataset the model was last estimated on.

    python -X utf8 model/check_data.py            # refetch, compare, write model/data_check.json, exit code says what to do
    python -X utf8 model/check_data.py --compare  # no refetch: compare the current data.csv with the committed copy (git show HEAD)

Exit codes (the update routine branches on them):
    0  the data changed (new quarters and/or revisions): re-estimate (model/run_model.py), rebuild, deploy, commit
    3  nothing changed: discard the refetched raw files, keep model/data_check.json (the check date), rebuild, deploy
    2  a series was lost (a source failed and had no cached copy): the old data.csv is restored; report, do not re-estimate

What is compared: every source column of data.csv (data_columns.csv rows whose source is not "derived" and whose request is
not "hand-coded"). A column whose last quarter moved forward is a new observation; a column whose last quarter moved back
is "shortened" (a source dropped a quarter; counts as a change, flagged); cells that differ by more than 1e-6 relative over
the common sample are revisions. The result is written to model/data_check.json; when the data changed an entry is also
appended to model/data_updates.json (the log the page shows as "most recent data update").
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA, COLS = HERE / "data.csv", HERE / "data_columns.csv"
CHECK, UPDATES, STATUS = HERE / "data_check.json", HERE / "data_updates.json", HERE / "fetch_status.json"
REL_TOL = 1e-6
KEY = ["gdp_ml", "cpi", "cpi_ate", "w_hour", "u_reg", "pi_defl", "i44", "policy_rate", "nibor3m", "hicp_ea", "ppi_ea", "oil_brent"]


def load(data_path, cols_path):
    d = pd.read_csv(data_path, index_col=0)
    c = pd.read_csv(cols_path).fillna("")
    src = [r.column for r in c.itertuples() if r.source != "derived" and r.request != "hand-coded" and r.column in d.columns]
    return d, c.set_index("column"), src


def compare(old, new):
    d0, c0, src0 = old
    d1, c1, src1 = new
    out = {"new_quarters": {}, "shortened": {}, "revised": {}, "dropped": [c for c in src0 if c not in src1], "added": [c for c in src1 if c not in src0]}
    for col in src0:
        if col not in src1:
            continue
        a, b = d0[col].dropna(), d1[col].dropna()
        la, lb = (str(a.index[-1]) if len(a) else ""), (str(b.index[-1]) if len(b) else "")
        if lb > la:
            out["new_quarters"][col] = [la, lb]
        elif lb < la:
            out["shortened"][col] = [la, lb]
        common = a.index.intersection(b.index)
        if len(common):
            x, y = a.loc[common].to_numpy(float), b.loc[common].to_numpy(float)
            rel = np.abs(y - x) / np.maximum(np.abs(x), 1e-9)
            n = int((rel > REL_TOL).sum())
            if n:
                k = int(np.argmax(rel))
                out["revised"][col] = {"cells": n, "first": str(common[np.argmax(rel > REL_TOL)]), "max_rel": float(rel[k]), "at": str(common[k])}
    out["changed"] = bool(out["new_quarters"] or out["shortened"] or out["revised"] or out["added"])
    return out


FAMILY = [   # (column prefixes, readable name) in order of precedence; the page shows families, the JSON keeps the columns
    (("cpi_se", "cpi_de", "cpi_uk", "cpi_us", "cpi_ea_oecd"), "foreign consumer prices (OECD)"),
    (("cpi",), "consumer prices (Statistics Norway)"),
    (("gdp", "gov_cons", "imp_", "pi_defl", "pi_trad", "py_ml", "va_"), "national accounts (Statistics Norway)"),
    (("wages", "wcost", "hours", "employees", "w_hour", "wc_hour", "t1", "z_", "py_man"), "wages and productivity (Statistics Norway)"),
    (("u_lfs", "lf_lfs"), "labour force survey (Statistics Norway)"),
    (("u_reg_nb",), "registered unemployment (Norges Bank MPR file)"),
    (("u_reg",), "registered unemployment (Statistics Norway)"),
    (("pm_trade", "pif"), "import prices (Statistics Norway)"),
    (("policy_rate", "dloan_rate", "nowa"), "Norges Bank interest rates"),
    (("i44", "twi", "eurnok", "usdnok"), "exchange rates (Norges Bank)"),
    (("hicp_ea", "euribor3m"), "euro-area prices and rates (ECB)"),
    (("ppi_",), "producer prices (Eurostat)"),
    (("nibor3m", "ir3_"), "money-market rates (OECD)"),
    (("oil_brent",), "Brent oil (World Bank)"),
]


def family(col):
    for prefixes, name in FAMILY:
        if any(col.startswith(p) for p in prefixes):
            return name
    return col


def families(cols):
    seen = []
    for c in cols:
        f = family(c)
        if f not in seen:
            seen.append(f)
    return ", ".join(seen)


def describe(res, d1):
    """One sentence per kind of change, in source families, for the page and the commit message."""
    parts = []
    if res["new_quarters"]:
        by_q = {}
        for col, (la, lb) in res["new_quarters"].items():
            by_q.setdefault(lb, []).append(col)
        parts.append("new observations: " + "; ".join(f"{q} for {families(sorted(cols))}" for q, cols in sorted(by_q.items())))
    if res["revised"]:
        parts.append("revisions in " + families(sorted(res["revised"])))
    if res["shortened"]:
        parts.append("shortened: " + ", ".join(f"{c} ({a} to {b})" for c, (a, b) in res["shortened"].items()))
    if res["added"]:
        parts.append("added: " + ", ".join(res["added"]))
    return ". ".join(parts) + ("." if parts else "no change")


def main():
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    compare_only = "--compare" in sys.argv
    tmp = Path(tempfile.mkdtemp(prefix="nam_check_"))
    try:
        if compare_only:   # the committed copy is the baseline
            for name in ("data.csv", "data_columns.csv"):
                (tmp / name).write_bytes(subprocess.run(["git", "show", f"HEAD:model/{name}"], cwd=ROOT, capture_output=True, check=True).stdout)
        else:
            shutil.copy(DATA, tmp / "data.csv"); shutil.copy(COLS, tmp / "data_columns.csv")
            print("+ fetch_data.py --refresh", flush=True)
            r = subprocess.run([sys.executable, "-X", "utf8", str(HERE / "fetch_data.py"), "--refresh"], cwd=ROOT)
            print(f"fetch_data.py exit code {r.returncode}", flush=True)
        old = load(tmp / "data.csv", tmp / "data_columns.csv")
        new = load(DATA, COLS)
        res = compare(old, new)
        status = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
        d1 = new[0]
        res.update({"checked": today, "fetched": status.get("fetched", today), "kept_from_cache": status.get("kept_from_cache", []),
                    "failures": status.get("failures", []),
                    "last_quarter": {c: str(d1[c].dropna().index[-1]) for c in KEY if c in d1.columns},
                    "summary": describe(res, d1)})
        previous = json.loads(CHECK.read_text(encoding="utf-8")) if CHECK.exists() else {}
        if res["dropped"]:   # a source failed without a cache: restore the previous dataset, do not re-estimate
            shutil.copy(tmp / "data.csv", DATA); shutil.copy(tmp / "data_columns.csv", COLS)
            res["outcome"] = "series lost, previous data restored: " + ", ".join(res["dropped"])
            res["last_update"] = previous.get("last_update")
            CHECK.write_text(json.dumps(res, indent=1), encoding="utf-8")
            print("\nDATA CHECK: " + res["outcome"]); return 2
        updates = json.loads(UPDATES.read_text(encoding="utf-8")) if UPDATES.exists() else []
        if res["changed"]:
            entry = {"date": today, "summary": res["summary"], "new_quarters": res["new_quarters"], "revised": sorted(res["revised"]),
                     "last_quarter": res["last_quarter"]}
            updates.append(entry)
            UPDATES.write_text(json.dumps(updates, indent=1), encoding="utf-8")
            res["last_update"] = entry; res["outcome"] = "changed"
        else:
            res["last_update"] = updates[-1] if updates else previous.get("last_update"); res["outcome"] = "unchanged"
        CHECK.write_text(json.dumps(res, indent=1), encoding="utf-8")
        print("\nDATA CHECK " + today + ": " + res["summary"])
        if res["kept_from_cache"]:
            print("kept from cache (source down): " + ", ".join(res["kept_from_cache"]))
        return 0 if res["changed"] else 3
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
