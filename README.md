# A NAM-type model of Norway: dashboard

A standalone dashboard of the small quarterly equilibrium-correction model of Norway built in the tradition of
Bårdsen, Eitrheim, Jansen and Nymoen (BJN2003, ABE2005, BN2008, NAM2026), re-estimated on public data from
Statistics Norway, Norges Bank, the ECB, Eurostat, the OECD and the World Bank. It began as the "NAM-type model" tab
of the Øyvind Eitrheim dashboard (`C:\claude_code\eitrheim`) and is the same model, reorganised into tabs.

Live: https://nam-type-model.jskjeltorp.workers.dev (private: Cloudflare Access, invited emails only; `src/worker.js` refuses
any request that did not come through Access before serving the page, the same fail-closed design as the equity factors
dashboard. The Access application "NAM-type model of Norway" and its invited list are managed in Cloudflare Zero Trust.)

## Tabs

| Tab | Hash | What is on it |
|---|---|---|
| Overview | `#overview` | What the model is and is not, the sample, data vintage and estimation choices, a guide to the tabs |
| Forecast | `#forecast` | Dynamic simulation from the last national-accounts quarter under Norges Bank's rate path or a policy rule (FLX, SM, estimated reaction function), bootstrap bands computed in the browser, annual averages against Norges Bank's MPR and LO/NAM projections; side panel for the rate setting and the exogenous assumptions |
| Policy | `#policy` | A permanent +100 bp with coefficient-uncertainty bands; the ABE2005 loss function by stochastic simulation; side panel with every coefficient, the rule parameters and the imposed long-run coefficients on sliders (they also drive the Forecast tab) |
| Equations | `#equations` | One card per equation: published form, estimates with standard errors, diagnostics, recursive tests, fitted path; residual correlations; imposed against free long-run relations; the equilibrium unemployment rate u* implied by the wage–price block |
| Robustness | `#robustness` | Indicator saturation (IIS/SIS), super-exogeneity tests, the New Keynesian Phillips curve against the EqCM, recursive cointegration, OLS against 2SLS |
| Forecasting record | `#record` | In-sample dynamic simulation ("how far the system drifts on its own") and the rolling pseudo-out-of-sample evaluation from 77 origins against a dVAR, intercept correction, no change and an AR(4) |
| Notes & sources | `#notes` | Departures from the published model (spec D.7), additions beyond it (D.8), sources and files |

## Rebuild

```
python -X utf8 model/run_model.py            # estimate, check, simulate, forecast evaluation, robustness, JS twin test
python -X utf8 model/run_model.py --refresh  # ... refetching all data first
python -X utf8 build.py                      # inject the model outputs and modelsim.js into template.html -> site/index.html
npx wrangler deploy                          # Cloudflare Workers static assets, worker "nam-type-model"
```

`model/` is the whole pipeline and is self-contained: `fetch_data.py` (raw cache in `model/raw`), `estimate.py`,
`check_sim.py`, `simulate.py`, `forecast_eval.py`, `robustness.py`, `modelsim.js` (the browser twin of `simulate.py`,
checked by `js_twin_test.js`), `run_model.py`. The specification with every assumption is `model/model_spec.md`; the
data requests are in `model/data_map.md`; what was read of the sources is in `model/SOURCES.md`.

`build.py` reads `estimates.json`, `simulation.json`, `forecast_eval.json`, `robustness.json` and `data_check.json`, parses
D.7 and D.8 of the spec, and writes one self-contained `site/index.html` (about 575 kB; Plotly from a CDN). No network
access is needed to build.

## Automatic data updates

A scheduled cloud agent (playbook: `UPDATE.md`) runs on Tuesday and Friday mornings. It runs `model/check_data.py`, which
refetches every source and compares the result with the dataset the model was last estimated on; when new observations
or revisions have arrived it re-runs `model/run_model.py`, rebuilds, deploys and commits. The Overview tab shows the last
check and the most recent data update (`model/data_check.json`, `model/data_updates.json`). A source that is down keeps
its cached raw file (`fetch_status.json` lists what was kept). Norges Bank's projections (`model/norges_bank_projections.json`)
are updated by hand; the agent only reports when a newer Monetary Policy Report is out.

The repository is `https://github.com/Jozzanova/nam_model`; `model/raw` (about 5 MB) is versioned so that a fresh clone
has a baseline and a cached copy of every source.

## Keeping the two copies in step

The Eitrheim dashboard still carries its own copy of `model/` and renders the same material as one tab. Changes to the
model code should be made in one place and copied to the other (`model/` is identical except for the final message of
`run_model.py` and the header comment of `modelsim.js`, which name `build.py` here and `update.py` there). The page code
(`template.html`) differs: here the blocks are split over seven tabs and the simulation state is shared between the
Forecast, Policy and Equations tabs.
