# Data-update routine

This file is the playbook for the scheduled cloud agent that keeps the NAM-type model current. You start with a fresh
clone of this repository and no other context; read this file first, then do the steps in order. Do not end the run
before step 5 is done.

## 1. Set up

    git pull --rebase origin main
    pip install -r model/requirements.txt       # pandas, numpy, statsmodels, scipy, requests, openpyxl

Node is needed only for the JavaScript twin test inside the model run; if `node` is missing the run skips it and says so.

## 2. Check whether new data is available

    python -X utf8 model/check_data.py          # refetches every source and compares; 3-6 minutes, give it a 15-minute timeout

The script refetches all series from Statistics Norway, Norges Bank, the ECB, Eurostat, the OECD and the World Bank into
`model/raw`, rebuilds `model/data.csv`, compares it with the dataset the model was last estimated on, and writes
`model/data_check.json` (and, when something changed, an entry in `model/data_updates.json`). The last line of its
output starts with `DATA CHECK` and says what changed. The exit code decides what to do next:

| Exit code | Meaning | What to do |
|---|---|---|
| 0 | New observations and/or revisions | Step 3, then 4 and 5 |
| 3 | Nothing changed | Skip step 3; do step 4 (so the page shows today's check) and step 5 |
| 2 | A series was lost: a source failed and had no cached copy; the previous data was restored | Skip step 3; do step 4 and 5 and say in the report which series and why |

A source that is down but has a cached copy is not an error: the cached copy is used and listed under
`kept_from_cache` in `model/data_check.json`; mention it in the commit message and the report. A fetch that fails with
`403 Forbidden` from the proxy means the cloud environment's network allowlist does not include that host; say so in the
report so the allowlist can be extended.

## 3. Re-estimate (only when the data changed)

    python -X utf8 model/run_model.py           # estimate, check, simulate (500 bootstrap replications), forecast evaluation, robustness, JS twin test; 5-10 minutes, 20-minute timeout

Do not pass `--refresh`: step 2 has already fetched the data. The run must end with `model pipeline done`. If a step fails,
read the error; if it is a data problem you can see in `model/data.csv` (a series ending early, a gap), restore the data
files with `git checkout -- model/data.csv model/data_columns.csv model/raw` and treat the run as "unchanged" (step 4
and 5 still happen, and the report must say what went wrong). Never edit the model code to make the run pass.

## 4. Rebuild and deploy the page

    python -X utf8 build.py
    npx wrangler deploy                         # uses CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID from the environment; never write them into the repository

`build.py` reads the model outputs and `model/data_check.json`, so the Overview box shows today's check and the most
recent data update. `npx wrangler deploy` must print the deployed address `https://nam-type-model.jskjeltorp.workers.dev`.

## 5. Commit and push

When the data changed, commit everything the run touched: `model/raw`, `model/data.csv`, `model/data_columns.csv`,
`model/fetch_status.json`, `model/data_check.json`, `model/data_updates.json` and the model outputs
(`model/estimates.json`, `model/simulation.json`, `model/forecast_eval.json`, `model/robustness.json`). Commit message:
`Data update YYYY-MM-DD: <the summary line from data_check.json>`.

When nothing changed (exit code 3 or 2), discard the refetched files so the history does not fill with identical data
(`git checkout -- model/raw model/data.csv model/data_columns.csv model/fetch_status.json`) and commit only
`model/data_check.json` with the message `Data check YYYY-MM-DD: no new data` (or `...: <series> lost, previous data kept`).

    git add -A
    git commit -m "<message>"
    git pull --rebase origin main && git push origin main

## 6. Norges Bank's projections (report only)

`model/norges_bank_projections.json` records which Monetary Policy Report the comparison paths and the registered-unemployment
history come from (`report`, `published`). Norges Bank publishes a report in March, May, June, September and December. Open
https://www.norges-bank.no/en/news-events/publications/Monetary-Policy-Report/ and check whether a report newer than
`published` is out. If so, do not change the file; say in the report which report is out and its date, so the projections
can be updated by hand.

## 7. Report

End with a short report: the data check's summary line, whether the model was re-estimated, the deployed address, the
commit, any source kept from cache or lost, and whether a newer Monetary Policy Report is out.
