# Data map for the Model tab

Every series used by `fetch_data.py`, with the exact request. All endpoints were queried on 2026-10-31. Quarterly
values of monthly series are averages of the months (NAM2026 App. D.2); of daily series, averages of the daily
observations (App. D.4); a quarter is kept only when all its months (or at least 40 business days) are present.
`python -X utf8 model/fetch_data.py` caches each raw response under `model/raw/` and never refetches unless `--refresh`
is given; `model/data_columns.csv` lists every output column with its description, unit, seasonal-adjustment status,
source, request and first/last quarter.

Install: `pip install -r model/requirements.txt` (pandas 2.2.3, numpy 2.2.1, requests 2.32.3, statsmodels 0.14.6,
openpyxl 3.1.5; Python 3.13 was used).

## 1. SSB StatBank (PxWeb API v1)

- Metadata: `GET https://data.ssb.no/api/v0/en/table/<id>`; data: `POST` to the same URL with
  `{"query":[{"code":<dim>,"selection":{"filter":"item","values":[...]}}, ..., {"code":"Tid","selection":{"filter":"all","values":["*"]}}],"response":{"format":"json-stat2"}}`.
  The alias `api.ssb.no/v0/...` returns 404; use `data.ssb.no`. API v2 (`data.ssb.no/api/pxwebapi/v2/tables/<id>/data?lang=en&valueCodes[...]`)
  also works but v1 is used. json-stat2: `id` gives the dimension order, `dimension[d].category.index` the code positions,
  `value` a flat row-major list with `Tid` fastest; time labels `2024M01` (monthly), `2024K1` (quarterly; K not Q), `2024` (annual).
- The script sleeps 1.5 s between POSTs; about 20 requests are needed for a full fetch.
- **2026 change**: SSB rebased the CPI to 2025 = 100 in January 2026. The old tables 03013 (CPI 2015 = 100, 1979M01–2025M12),
  05327 (CPI-ATE), 06444 (SA), 03014, 08981 are "closed series" frozen at 2025M12. Successors used here: 14710, 14706, 14708, 14700.

| Column(s) | Table | Query (the `query` list; `Tid` = all) | Codes | Coverage | Notes |
|---|---|---|---|---|---|
| `cpi` | 14710 Consumer price index (2025=100) | `[{"code":"ContentsCode","selection":{"filter":"item","values":["KpiIndMnd"]}}]` | single series | 1920M03–2026M09 → 1970Q1–2026Q3 in data.csv | NSA. Old 03013: `Konsumgrp` = `TOTAL`, `ContentsCode` = `KpiIndMnd` (2015 = 100), 1979M01–2025M12. |
| `cpi_ate`, `cpi_at`, `cpi_xe` | 14706 Derived series from CPI (2025=100) | `[{"code":"KPIavledetSerie","selection":{"filter":"item","values":["KPI","KPI-JAE","KPI-JA","KPI-JE"]}},{"code":"ContentsCode","selection":{"filter":"item","values":["KPIJustIndMnd"]}}]` | `KPI-JAE` = CPI-ATE, `KPI-JA` = CPI adjusted for tax changes, `KPI-JE` = CPI excl. energy; other codes `KPI-JEL`, `KPI-XADM`, `KPI-JA-XADM`, `KPI-JAE-XADM` | KPI-JAE and KPI-JA **from 2002M12** (→ 2003Q1); KPI-JE from 1995M01 | Index levels of CPI-ATE before 2002M12 are not on StatBank (older tables 11447, 04488/04493 only carry rates of change). Old 05327: `Konsumgrp` = `JAE_TOTAL` / `JA_TOTAL`. |
| `cpi_sa`, `cpi_ate_sa` | 14708 Seasonally adjusted CPI (2025=100) | `[{"code":"KPIavledetSerie","selection":{"filter":"item","values":["KPI","KPI-JAE"]}},{"code":"ContentsCode","selection":{"filter":"item","values":["KPIsesong"]}}]` | | KPI 1985M01–, KPI-JAE 2002M12– | SSB's own seasonal adjustment; used for charts only. |
| `cpi_elgas`, `cpi_fuel` | 14700 CPI by consumption group (COICOP, 2025=100) | `[{"code":"VareTjenesteGrp","selection":{"filter":"item","values":["04.5","07.2.2"]}},{"code":"ContentsCode","selection":{"filter":"item","values":["KpiIndMnd"]}}]` | `04.5` Electricity, gas and other fuels; `07.2.2` Fuels and lubricants for personal transport equipment; sub-codes `04.5.1` Electricity, `04.5.5` other heating energy | 2000M01– in the table, but the 04.5 and 07.2.2 indices are null before 2000M07, so the first full quarter is 2000Q3 | The `pe` energy indicator (CPIEL in NAM; "CPI electricity, fuel and lubricants" PE in BN2008). |
| `gdp_ml`, `gdp_ml_sa`, `gdp_ml_cur`, `gdp_ml_basic`, `gdp_total`, `gov_cons`, `imp_cur`, `imp_const`, `imp_trad_cur`, `imp_trad_const` | 09190 Final expenditure and gross domestic product, quarterly | `[{"code":"Makrost","selection":{"filter":"item","values":["bnpb.nr23_9fn","bnpb.nr23_6fn","bnpb.nr23_9","imp.nrtot","imp.nrtradvare","koo.nroff"]}},{"code":"ContentsCode","selection":{"filter":"item","values":["Priser","Faste","PriserSesJust","FastePriserSesJust","PrisIndex"]}}]` | `bnpb.nr23_9fn` GDP Mainland Norway market values; `bnpb.nr23_6fn` basic values; `bnpb.nr23_9` total GDP; `imp.nrtot` total imports; `imp.nrtradvare` traditional goods imports; `koo.nroff` general government final consumption (label truncated to "governmen" in the metadata). `Priser` current prices; `Faste` constant prices (base year 2023 at collection — it moves with each main revision); `PriserSesJust`/`FastePriserSesJust` seasonally adjusted; `PrisIndex` SA price index 2023 = 100 | 1978K1–2026K2 | NSA levels are used for estimation (`Faste`), SA for charts. Derived: `pi_defl` = imp_cur/imp_const (import deflator, RIMINI PB), `pi_trad_defl`, `py_ml` = gdp_ml_cur/gdp_ml. |
| `va_ml`, `va_ml_cur`, `va_man`, `va_man_cur` | 09171 Production account by industry, quarterly | `[{"code":"NACE","selection":{"filter":"item","values":["nr23_6fn","nr23ind","nr23_6"]}},{"code":"ContentsCode","selection":{"filter":"item","values":["BNPB","BNPB2","BNPB2ses"]}}]` | `nr23_6fn` Mainland Norway, `nr23ind` manufacturing, `nr23_6` total; `BNPB` value added current prices, `BNPB2` constant prices, `BNPB2ses` constant SA | 1978K1–2026K2 | Derived: `py_man` = va_man_cur/va_man (PYFP1 counterpart). |
| `wages_*`, `wcost_*`, `hours_*`, `hours_emp_*`, `employees_*` (`ml` = Mainland, `man` = manufacturing), `wages_ml_sa`, `wcost_ml_sa` | 09175 Wages, employment and hours worked by industry, quarterly | `[{"code":"NACE","selection":{"filter":"item","values":["nr23_6fn","nr23ind","nr23_6"]}},{"code":"ContentsCode","selection":{"filter":"item","values":["Lonn","LKostnader","Timeverk","TimeverkL","SysselsatteLonn","Lonn2","LKostnader2","TimeverkSesJust"]}}]` | `Lonn` wages and salaries; `LKostnader` compensation of employees; `Timeverk` hours worked, employees + self-employed; `TimeverkL` hours worked, employees; `SysselsatteLonn` employees; `Lonn2`/`LKostnader2`/`TimeverkSesJust` SA | **1995K1**–2026K2 | This is the table NAM2026 App. D uses for its YWW/YWC/NWH series. Nothing quarterly before 1995 exists in StatBank; the annual table 09174 (1970–) could be interpolated (not done). Derived: `w_hour` = wages_ml/hours_emp_ml (W), `wc_hour` (WC), `t1` = wcost/wages − 1 (τ1 = WCF/WF − 1 in BJN; includes pension contributions, seasonal), `t1_sa`, `z_ml` = va_ml/hours_ml (Z), manufacturing counterparts `w_hour_man`, `wc_hour_man`, `z_man`. |
| `u_lfs`, `u_lfs_persons` | 08518 LFS unemployed persons by sex and age, quarterly | `[{"code":"Kjonn","selection":{"filter":"item","values":["0"]}},{"code":"Alder","selection":{"filter":"item","values":["15-74"]}},{"code":"ContentsCode","selection":{"filter":"item","values":["Prosent","Personer"]}}]` | `Prosent` = rate, `Personer` = 1000 persons | 1972K1–2026K2 | NSA; LFS breaks in 2006 (age 15–74, age at reference week) and 2021 (new EU regulation). NAM's UAKU. |
| `lf_lfs` | 03777 LFS labour force | same `Kjonn`/`Alder`; `ContentsCode` chosen from the metadata by the label "labour force" | | 1972K1–2026K2 | NAM's AKUSTYRK. |
| `u_lfs_sa` | 14483 (2009K1–) spliced with 07458 (1997K1–2024K4) | 14483: `[{"code":"Kjonn",...["0"]},{"code":"Alder",...["15-74"]},{"code":"Justering",...["S"]},{"code":"ContentsCode",...["ArbledProsArbstyrk"]}]`; 07458: `Alder` = `15-74`, `ContentsCode` = `ArbeidslauseStyrken` (plus `Kjonn` = `0` if the table has it) | `Justering`: `S` SA, `IS` NSA, `T` trend | 1997Q1–2026Q2 | SSB's seasonal adjustment; monthly SA alternative 13760 (2006M01–, 3-month moving average) not used. |
| `u_reg_ssb`, `u_reg_persons` | 10540 Registered unemployed, per cent of labour force (1999M01–); 10594 persons (1990M01–) | 10540: `[{"code":"Region",...["0"]},{"code":"Alder",...["15-74"]},{"code":"ContentsCode",...["RegHeltLedige"]}]`; 10594: `[{"code":"Region",...["0"]},{"code":"Kjonn",...["0"]},{"code":"ContentsCode",...["Registrerte1"]}]` | | monthly **only to 2014M12**; afterwards only November (and some March) values, which the quarterly rule drops | SSB stopped carrying NAV's monthly series after 2014 (10593 holds only 2014M06–2015M08) and all NAV data after 2020M11. |
| `u_reg_nb` | Norges Bank MPR 3/26 data file, sheet "Data G" (`Registrert ledighet samlet (rate)`) | `https://www.norges-bank.no/contentassets/1462461ecf6a423eb7bc3e89c1cb0d2b/data-mpr-3-26.xlsx` (URL taken from `norges_bank_projections.json` → `tables_url`; the file is cached as `raw/nb_mpr_data.xlsx`) | quarterly, seasonally adjusted, NAV source | 2015Q1–2026Q2 (projections from the MPR's first projection quarter are excluded) | Replaces the SSB series after 2014. The URL changes with every MPR; update `norges_bank_projections.json`. |
| `u_reg` | spliced | 1990Q1–1998Q4: 10594 persons ÷ LFS labour force (03777) × 100; 1999Q1–2014Q4: 10540; 2015Q1–: `u_reg_nb` | | 1990Q1–2026Q2 | **The seam at 2014Q4/2015Q1 is NSA → SA**; the registered rate has a small seasonal (winter peak). NAV's own monthly files at nav.no ("Helt ledige ... Tidsserie måned") carry only the current year; the historical files (`Hl_Fy_mnd_51-60.xlsx` … `81-90.xlsx`) are monthly counts by county 1951–1990 and could extend the series backwards by hand. |
| `pm_trade` | 08241 External trade in commodities, indices of volume and price (2000=100), quarterly | `[{"code":"ImpEks",...["1"]},{"code":"ImpEkspGr",...["-"]},{"code":"ContentsCode",...["Prisindeks"]}]` | `ImpEks` 1 = imports; `ImpEkspGr` `-` = total (SITC groups available); 05987 is the same by BEC end-use | 1989K1–2026K3 | Unit-value based; alternative import price measure. |
| `pif_imp`, `pif_all` | 03675 Price index of first-hand domestic sales (2021=100), monthly | `[{"code":"Marked",...["4","3"]},{"code":"SITC",...["SITCT"]},{"code":"ContentsCode",...["Indeksniva"]}]` | `Marked` 4 = import market (from 2000M12), 3 = domestic + import (1926M01–), 2 = domestic (1977M01–) | 2001Q1– / 1970Q1– | |

Not used but verified: 09174 (annual wages, hours, value added per hour, 1970–2025); 11654 earnings index 2016K1– (`NACE2007` `10-33`, `ContentsCode` `GjMdTotalIndeks`), 07219 (2000K1–2018K1, closed) and 06787 (1998K1–2018K1, closed, last value 0) for a monthly-earnings index; 09178 imports by product; 14483 `IS` for NSA LFS; 08931 (`Arbeidslause6` SA registered unemployed 2006M02–2020M12); 03769 SA LFS 1989M01–2005M11.

## 2. Norges Bank open data (SDMX REST, `https://data.norges-bank.no/api/data/<FLOW>/<key>?format=csv`)

CSV is semicolon-separated, one row per observation, columns = dimension codes and labels, then `TIME_PERIOD;OBS_VALUE`.
`startPeriod`, `endPeriod`, `lastNObservations` work. There is **no quarterly frequency** in EXR (404); the script averages.

| Column | Flow / key | URL | Coverage | Notes |
|---|---|---|---|---|
| `policy_rate` | IR / `B.KPRA.SD.` | `https://data.norges-bank.no/api/data/IR/B.KPRA.SD.?format=csv&startPeriod=1980-01-01` | daily 1991-01-01– (quarterly 1991Q1–) | Key policy rate = sight deposit rate (styringsrente); `KPRA` is the only instrument, tenors `SD` sight deposit, `OL` overnight lending (D-loan), `RR` reserve rate. Monthly `M.KPRA.SD.` and annual also exist. No `FOLIO`/`DLAAN` codes. |
| `dloan_rate` | IR / `M.KPRA.OL.` | `https://data.norges-bank.no/api/data/IR/M.KPRA.OL.?format=csv` | 1982-04– (gaps 1982-05..07) | Pre-1991 proxy for the policy rate (`r_policy_spliced`). |
| `nowa` | SHORT_RATES / `M.NOWA.ON.R` | `https://data.norges-bank.no/api/data/SHORT_RATES/M.NOWA.ON.R?format=csv` | 2011-10– | Daily `B.NOWA.ON.R` from 2011-09-30; `UNIT_MEASURE` V volume, T transactions; `NOWA_AVERAGE` 1M/3M/6M from 2020. |
| `i44` | EXR / `M.I44.NOK.SP` | `https://data.norges-bank.no/api/data/EXR/M.I44.NOK.SP?format=csv` | 1989-07– (daily `B.I44.NOK.SP` from 1989-07-03) | Import-weighted index, 1995 average = 100 (verified), higher = weaker krone — same convention as v in BJN/NAM. |
| `twi` | EXR / `M.TWI.NOK.SP` | `https://data.norges-bank.no/api/data/EXR/M.TWI.NOK.SP?format=csv` | 1971-01– | Trade-weighted index, 1990 = 100; longer-sample check for v. |
| `eurnok`, `usdnok` | EXR / `M.EUR.NOK.SP`, `M.USD.NOK.SP` | same pattern | 1999-01– / 1960-01– | |
| NIBOR | — | not in the API (`IR/M.NIBOR..` 404; `MONEY_MARKET` is post-2020 transaction data). Norges Bank stopped publishing NIBOR in 2013. | — | See OECD `IR3TIB` for NOR below. |

## 3. Foreign series

| Column | Source | URL | Coverage | Notes |
|---|---|---|---|---|
| `hicp_ea` | ECB Data Portal, dataflow HICP (successor of ICP, which is discontinued since 4 Feb 2026 and frozen at 2025-12) | `https://data-api.ecb.europa.eu/service/data/HICP/M.U2.N.000000.4D0.INX?format=csvdata` | 1996-01– (rows 1990–1995 are empty) | 2025 = 100; data-provider code `4D0`. Eurostat alternative: `https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/prc_hicp_minr/M.I15.TOTAL.EA?format=SDMX-CSV` (1996-01–, 2015 = 100). p* for the real exchange rate. |
| `euribor3m` | ECB FM | `https://data-api.ecb.europa.eu/service/data/FM/M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA?format=csvdata` | 1994-01– | Foreign short rate R* (BN2008: ECU rate). |
| `ppi_ea` | Eurostat sts_inppd_m | `https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/sts_inppd_m/M.PRC_PRR_DOM.B-E36.NSA.I21.EA20?format=SDMX-CSV` | 2000-01– | Domestic output prices, industry B–E36, 2021 = 100; the `pf` proxy (NAM's PPIKONK is a trade-weighted index built from LSEG country series, App. D.3, not public). `INDIC_BT` codes: `PRC_PRR_DOM`, `PRC_PRR`, `PRC_IMP`, … |
| `ppi_de` | Eurostat sts_inppd_m | `.../sts_inppd_m/M.PRC_PRR_DOM.B-E36.NSA.I21.DE?format=SDMX-CSV` | 1976-01– | Long `pf` proxy for samples before 2000. |
| `cpi_se`, `cpi_de`, `cpi_uk`, `cpi_us`, `cpi_ea_oecd` | OECD SDMX, DF_PRICES_ALL | `https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/SWE+DEU+GBR+USA+NOR+EA20.M.N.CPI.IX._T.N.?format=csvfilewithlabels&startPeriod=1960-01` | DEU/GBR/USA 1970– to 2026; SWE, EA20 national-methodology series end 2025-12 | Key order REF_AREA.FREQ.METHODOLOGY.MEASURE.UNIT_MEASURE.EXPENDITURE.ADJUSTMENT.TRANSFORMATION; leave the last dimension empty (`GY` → 404). A fixed-weight trading-partner CPI (PCKONK analogue) can be built from these with StatBank 08803 import shares — not done yet. |
| `nibor3m` (= `rs`), `ir3_ea`, `ir3_de`, `ir3_se`, `ir3_us` | OECD SDMX, DF_FINMARK | `https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_FINMARK,4.0/EA20+SWE+GBR+USA+DEU+NOR.M.IR3TIB.PA.....?format=csvfilewithlabels&startPeriod=1970-01` | NOR 1979Q1– in the combined file (a single-country request starts 1980-01); EA20 1994-01– | NOR IR3TIB = 3-month NIBOR; the money-market rate RS of BJN/BN2008 (their RS was the 3-month Euro-krone rate). |
| `oil_brent` | World Bank Pink Sheet (monthly xlsx), link discovered from `https://www.worldbank.org/en/research/commodity-markets` by regex `CMO-Historical-Data-Monthly.xlsx` (doc-id changes every release; the URL used is saved in `raw/wb_pink_sheet_url.txt`) | sheet "Monthly Prices", header row 5, column "Crude oil, Brent" | 1960M01– | **FRED is not reachable from this machine** (connection reset on fredgraph.csv and alfred; api.stlouisfed.org needs a key); EIA needs a key. |

## 4. Derived columns in `data.csv` (all defined in `fetch_data.py`, section 9)

`l_<x>` natural logs: `l_w` (w), `l_wc`, `l_p` (CPI), `l_pu` (CPI-ATE), `l_pe`, `l_pi` (import deflator), `l_pitrad`, `l_pm`, `l_z`, `l_y`
(mainland GDP NSA), `l_ysa`, `l_g`, `l_py`, `l_v` (I-44), `l_vtwi`, `l_pstar` (euro-area HICP), `l_pf` (euro-area PPI), `l_pfde`,
`l_u` (log registered unemployment rate), `l_ulfs`, `l_oil`, `l_wman`, `l_zman`, `l_qman`; `t3` = ln CPI − ln CPI-AT (indirect-tax
proxy, from 2003Q1); `ecm_w` = (w − p − z) + 0.1u; `ecm_p` = p − 0.6(w + ln(1 + τ1) − z) − 0.4pi − τ3 (τ3 set to 0 where missing);
`rex` = v + p* − p; `ecm_pi` = pi − v − pf; `infl4`, `infl4_ate`, `infl4_ea` (four-quarter inflation, per cent); `rs` (NIBOR 3m);
`r_policy_spliced`; `infl_target` (2.5 from 2001Q2, 2.0 from 2018Q1); dummies `d_it` (1 from 2001Q2), `covidq1`–`covidq8`
(2020Q1–2021Q4), `ukrw` (2022Q1), `s1`–`s3`, `cs1`–`cs3` (centred, 0.75/−0.25 as in NAM2026 §5.1 fn. 2).

## 5. Coverage at collection (2026-10-31)

Core model variables and their first usable quarter: `cpi` 1970Q1; `cpi_ate` 2003Q1; `w_hour`, `z_ml`, `t1` 1995Q1; `pi_defl`,
`gdp_ml`, `gov_cons` 1978Q1; `u_reg` 1990Q1 (seam 2015Q1); `u_lfs` 1972Q1; `policy_rate` 1991Q1 (`r_policy_spliced` 1982Q3);
`nibor3m` 1979Q1; `i44` 1989Q3 (`twi` 1971Q1); `hicp_ea` 1996Q1; `euribor3m` 1994Q1; `ppi_ea` 2000Q1 (`ppi_de` 1976Q1);
`oil_brent` 1970Q1; `cpi_elgas` 2000Q3; `t3` 2003Q1. Last quarter: QNA 2026Q2; monthly/daily series 2026Q3. The
**binding constraint is the wage block (1995Q1)**, then CPI-ATE/τ3 (2003Q1) if the rule or the price EqCM is to use them.

## 6. Missing or replaced relative to the published model

| Original variable | Status | Replacement in data.csv |
|---|---|---|
| RIMINI/FPAS hourly wages W, wage costs WCF (mainland) | not public | `w_hour`, `wc_hour` from QNA 09175 (1995Q1–) |
| τ1 payroll-tax rate (RIMINI T1F) | not public | `t1` = LKostnader/Lonn − 1 (incl. pension contributions) |
| τ3 indirect-tax rate (RIMINI T3) | not public | `t3` = ln CPI − ln CPI-AT (2003Q1–) |
| UTOT registered unemployed + programme participants | discontinued on StatBank; NAV annual file "HL065 Helt ledige og arbeidssøkere på tiltak. Fylke. Tidsserie år" exists (annual) | `u_reg` (registered only), `u_lfs` |
| PBVAL / CPIVAL effective exchange rate | Norges Bank I-44 is the public import-weighted index | `i44` (1989Q3–), `twi` (1971Q1–) |
| PCKONK, PPIKONK (trade-weighted foreign CPI/PPI built by NAM from LSEG) | not public | `hicp_ea`, `ppi_ea`, `ppi_de`, OECD CPIs; fixed-weight index not yet built |
| RS 3-month Euro-krone rate | not public | `nibor3m` (OECD IR3TIB NOR) |
| RSECU / R* ECU rate | — | `euribor3m` (1994Q1–), `ir3_de` before |
| YF / UEI trading-partner GDP | not fetched (OECD QNA would do) | — (output equation uses BN2008 form without y*) |
| Real credit CR, house prices PH, OSE | not fetched | — |
| Bond rates RB, RL | not fetched (Norges Bank GOVT_* flows and StatBank 07200 exist) | — |
