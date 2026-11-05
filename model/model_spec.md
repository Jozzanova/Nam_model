# Model tab: specification of a small quarterly EqCM wage-price model of Norway

Written 2026-10-31 for the owner's review. Everything in Parts A–C is taken from the published record of
Bårdsen, Eitrheim, Jansen and Nymoen and successors, with the source tag (see `SOURCES.md`) and the equation or
table number given for every coefficient. Part D states what the dashboard will actually estimate and where it
departs from the published model; every departure is marked **DEPARTURE:** so the page can list them. Part E lists
the questions the owner has to decide. Part F records the forecast cross-checks.

Notation: lower-case letters are natural logarithms of the upper-case variables; Δ is the first difference,
Δ4 the four-quarter difference; t-ratios/standard errors in parentheses are those printed in the source;
"WP" after a value means the number is from a working-paper version, not from the journal/book version
(the OUP book itself could not be read, see `SOURCES.md` §1).

---

## Part A. Variables and definitions in the published model

### A.1 The BJN (1999/2003) core model, as printed in BJN2003-WP Appendix B ("all data are taken from RIMINI")

| Symbol | Definition (verbatim from BJN2003-WP App. B unless noted) | RIMINI code |
|---|---|---|
| W | "Nominal mainland hourly wages", constructed as W = (WIBA·TWIBA + WOTVJ·(TWTV + TWO + TWJ))/TWF; the text (§3.1) calls it "average hourly wages in the mainland economy, excluding the North-Sea oil producing sector and international shipping" | — |
| WC | "Nominal mainland hourly wage costs" | WCF |
| τ1 | "Employers tax rate. τ1 = WCF/WF − 1" (payroll tax) | — |
| τ2 | income tax rate; "omitted from the empirical model, since it is insignificant" (fn. 4) | — |
| τ3 | "Indirect tax rate" | T3 |
| P | "Consumer price index. 1991 = 1" | CPI |
| PI | "Deflator of total imports. 1991 = 1" | PB |
| PR | "Mainland economy value added per man hour at factor costs, fixed baseyear (1991) prices" | ZYF |
| U | "Rate of unemployment. Registered unemployed plus persons on active labour market programmes as a percentage of the labour force, calculated as employed wage earners plus unemployment"; u = ln U enters the equations | UTOT |
| V | "Effective import weighted value of the NOK. 1991 = 1" (v up = depreciation) | PBVAL |
| PCK | "Consumer prices abroad in foreign currency. 1991 = 1" | PCKONK |
| pf | import prices in foreign currency, defined through the identity pi = v + pf (eq. 12 text) | — |
| Y | "Total value added at market prices in the mainland economy. Fixed baseyear (1991) prices" | YF |
| gap | "log mainland GDP deviations from trend, where the trend is estimated by the HP-filter using λ = 1600" | — |
| RS | "3 month Euro-krone interest rate" | RS |
| RSECU | "ECU interest rate" (1967(1)–1986(3) NOK-basket weighted effective foreign bond rate; 1986(4)–1996(4) ECU-weighted) | R.BKUR / R.BECU |
| RB | nominal bond rate, "5 year maturity" (§4.2); RRB = RB − Δ4p | — |
| CO | "Public consumption expenditure, fixed 1991 prices" | CO |
| CR | "Real credit volume fixed 1991 prices", from Bårdsen and Klovland (2000) | — |
| YF | "Weighted average of GDP of trading countries, using share of Norwegian exports in 1985 as weights. 1991 = 1" | UEI |
| OIL | "Per barrel Brent-Blend oil-price. USD" | — |
| AMUN | labour-market-programme participation relative to total unemployment | AMUN |
| H | "Normal working hours per week" | NH |
| Dummies | Wdum (wage freeze: 1 in 1979.1, 1979.2, 1988.2, 1988.3); Pdum (price regulation: +1 in 1971.1, 1971.2, 1976.4, 1979.1, −1 in 1975.1, 1980.1, 1981.1, 1982.1); Vdum = i78q2 + 2·i82q3 + i86q4 + i87q4 (devaluations); i70q1 (VAT); i80q2; impulse dummies iyyqx | — |

Data are seasonally unadjusted; the marginal equations carry "a constant and three seasonal dummies" (§4.2, §4.4).

### A.2 The 2001-vintage model (ABE2005 Appendix B; "all time series have been extracted from the database of RIMINI")

E = "Effective import weighted value of the NOK; 1991 = 1" [CPIVAL]; P = CPI; P* = "Index for consumer prices in Norway's
trading partners in foreign currency" [PCKONK]; PE = electricity prices consumers face [CPIEL]; PH = housing prices;
PM = "Deflator of total imports" [PB]; PR = mainland value added per man hour [ZYF]; PU = "Underlying Consumer price
index" [KPIJAE]; r = "Euro-krone interest rate with 3 month maturity" [RS]; rl = bank lending rate [RLB]; rb = yield on
6-year government bonds [RB]; S = OSE stock index; τ1 = employers' tax rate [T1F]; τ2 = marginal household tax rate
[TMNI50]; τ3 = indirect tax rate [T3]; U = unemployment rate [UR2]; W = "Hourly wages in mainland Norway"; Y = mainland
GDP [YF]; Y* = trading-partner GDP, 1985 export weights [UEI]; cap = step dummy from 1990:3 for capital liberalisation.
"The econometric model is based on seasonally unadjusted quarterly data."

### A.3 NAM, 2008 vintage (BN2008-WP Appendix A; "The model employs seasonally unadjusted data ... taken from FPAS, the database of Norges Bank")

V trade-weighted nominal value of the krone (import shares); G government consumption, 1991 prices; L nominal credit;
R "Money market interest rate (3 month Euro-krone interest rate)"; R* ECU/foreign short rate; RL average bank loan rate;
RB 6-year government bond yield; RB* long foreign bond yield; P CPI; PC "core" CPI; P* consumer prices abroad;
PE CPI electricity, fuel and lubricants; PO USD Brent; PI import deflator; PI* producer price index, trading partners;
Y mainland GDP; Z mainland value added per man hour; T1 payroll tax rate; U **registered** rate of unemployment;
W "Nominal hourly wage COSTS in the mainland economy"; IT = 0 until 2001(1), 1 from 2001(2) (inflation-targeting step dummy).

### A.4 NAM, 2026 vintage (NAM2026 ch. 3–5 and Appendix D)

The current NAM is disaggregated (manufacturing WFP1, other goods WFP2, private services WFP3, government WO). Variables
used below: WFP1 hourly wage, WCFP1 hourly wage cost, T1FP1 payroll-tax rate, PYFP1 value-added deflator, ZYFP1 labour
productivity (all manufacturing and mining); CPI, CPIJAE (CPI-ATE), CPIEL (energy part of CPI); PYF mainland GDP deflator;
PB import price index; CPIVAL effective nominal exchange rate (import weights; up = depreciation); PCKONK and PPIKONK
trade-weighted foreign consumer and producer prices (constructed per App. D eqs D.1–D.2 from LSEG country series with
import weights from StatBank 08803); UAKU LFS unemployment rate = AKULED/AKUSTYRK·100 (eq 3.39), UR registered rate
= REGLED/AKUSTYRK·100 (eq 3.38); RNB sight-deposit (policy) rate; RSH 3-month money-market rate (LSEG NWIBK3M); RSW foreign
3-month rate (EIBOR3M); RBO/RBOTENY 5- and 10-year government yields; US10Y; SPOILUSD Brent (CRUDBFO); PAW world stock index
(MSCI); T3 indirect tax rate; π̄ "the inflation target rate". Monthly StatBank series are quarterly averages (App. D.2);
market data are quarterly averages of daily observations (App. D.4). Seasonal dummies S1–S3 (or centred CS1–CS3),
seasonal-break dummies KNRBREAKQ1–Q3 from 2015q1, Covid dummies COVIDQj (COVIDQ5 = 2021q1, so COVIDQ1 = 2020q1),
UKRW = 1 in 2022q1 (§5.1).

---

## Part B. The long-run (cointegrating) relations as published

### B.1 Theory (BJN2003-WP §2, eqs 1–7; identical in BN2008-WP §2.6 eqs 20–27 and NAM2026 App. C eqs C.12–C.17)

Price target (mark-up over normal unit labour costs, constant returns):  pp = m2 + w − pr + τ1  (BJN eq 1)
CPI definition: p ≡ (1 − ϕ)pp + ϕ pi + ητ3, 0 < ϕ < 1, 0 < η ≤ 1  (BJN eq 2); "due to the log-form, ϕ = is/(1 − is) where is is the
import share in private consumption" (BN2008-WP fn. 10).
Bargained wage: w = ι12 pp + ι13 pr − ι15 u − ι16 τ1 − ι17 τ2 + (1 − ι12)p  (BJN eq 3)
Substituting out pp gives the two "target equations" in w and p (BJN eqs 4–5, BN2008-WP eqs 25–26):

  w = (1 + ϕ d12) p + ι13 pr − ϕ d12 pi − ι15 u − ι16 τ1 − ι17 τ2 − η d12 τ3,   d12 = ι12/(1 − ϕ)
  p = (1 − ϕ)(w − pr + τ1) + ϕ pi + η τ3

Identification (BN2008-WP §2.6.2, NAM2026 C.4): "for the purpose of modelling the aggregate economy, we choose the
consumer price index p as the representative domestic price index by setting ι12 = 0", giving

  w = m_w + p + ι13 z − ι15 u − ι16 T1 + ecm^b   (BN2008-WP eq 27 / NAM2026 C.17)
  p = (1 − ϕ)m_q + (1 − ϕ){w + T1 − z} + ϕ pi + η T3 − (1 − ϕ)ecm^f   (BN2008-WP eq 26 / NAM2026 C.16)

Theory restrictions discussed: ι13 = 1 (productivity homogeneity, "implied theoretically by assuming bargaining power
on the part of unions"), ι15 ≈ 0.1 (the Blanchflower–Oswald wage curve), ι16 ∈ [0,1]. With ι13 = 1 the steady state has a
constant wage share and Δp = Δpi = steady-state imported inflation for any given u ("no NAIRU implied by the wage-price block",
BJN §2, BN2008-WP §2.6.4, BN2003-NB §2).

### B.2 Estimates, BJN2003-WP Table 1 (Johansen procedure, PcFiml 9.2; conditional system with 3 lags, sample 1966(4)–1996(4), T = 121; two cointegrating vectors: trace 82.73 and 30.20 vs 5% critical values 49.3 and 25.3 from Harbo et al. (1998) with 5 exogenous variables; restricted trend dropped, χ²(2) = 2.09 [0.35])

Panel 2 (nonlinear cross-equation restrictions of the theory), χ²(4) = 7.49 [0.11]:

  w = p + 0.85 pr − 0.08 u + 1.60 τ1 − 0.03 (p − pi + 2.66 τ3)
        (0.16)  (0.04)  (0.83)   (0.11)
  p = 0.64 (w + τ1 − pr) + 0.36 pi + 0.95 τ3
      (0.06)                        (0.29)

Panel 3 (no producer-price effect, full indirect-tax effect), χ²(6) = 7.59 [0.27]: w = p + 0.84pr − 0.08u + 1.51τ1;
p = 0.63(w + τ1 − pr) + 0.37pi + τ3.

**Panel 4 (maintained: full productivity effect, no payroll-tax effect on wages), χ²(8) = 10.48 [0.23]:**

  w = p + pr − 0.09 u                        (0.02)
  p = 0.62 (w + τ1 − pr) + 0.38 pi + τ3      (0.02)

Rounded and used for the dynamic model (BJN §3.1, last display): **w = p + pr − 0.1u; p = 0.6(w + τ1 − pr) + 0.4pi + τ3.**
"The estimated wage responsiveness to the rate of unemployment is approximately 0.1, which is close to the finding of
Johansen (1995) on manufacturing wages." Recursive estimates 1978(3)–1996(4) and recursive χ²(8) tests in Figure 1 show
constancy. The same values (0.09 / 0.62 / 0.38) appear in BJN1999-NB, so they are stable across the 1999 and 2001 versions.
Diagnostics of the unrestricted conditional subsystem: AR 1–5 F(20,150) = 1.25 [0.22]; normality χ²(4) = 1.05 [0.90];
heteroskedasticity F(66,183) = 0.49 [0.99].

### B.3 Later published values of the same two relations

| Vintage | Wage relation | Price relation | Source |
|---|---|---|---|
| 2001 model (to 2001:4) | ecm_w = (w − p − pr) + 0.1 u | ecm_p = p − 0.65(w − pr + τ1) − 0.35 pm − 0.5 τ3 (inside the price equation; the NKPC paper writes the "Bårdsen and Nymoen (2001)" version as p − 0.6(w − pr + τ1) − 0.4pb + 0.5τ3) | ABE2005 App. C.1; BJN2004-WP §5.2 |
| NAM 2008 | (w − p − z) = −0.1 u + μ_w   (eq 50) | p − 0.7(w − z) − (1 − 0.7)pi = μ_p   (eq 49); "ι12 = 0, ϕ = 0.7, ι15 = 0.1 and ι16 = 1 are taken as known parameters from the cointegration analysis documented in Bårdsen et al. (2005, Ch. 9.2)" (§2.6.5) | BN2008-WP (WP) |
| NAM 2026 (manufacturing) | ln(WFP1(1 + T1FP1)) = −0.12 ln(UAKU) + ln(PYFP1·ZYFP1) + const  (eq 3.33); i.e. wage **cost** share stable, unemployment elasticity −0.12, payroll-tax elasticity of the wage −1 | CPI: ECM_CPI = log(CPI/PYF) − 0.38 log(PB(1 + T3)/PYF) − 0.06 log(CPIEL/PYF) + 0.99·CPIDUM (Table 5.24 note): CPI homogeneous in the mainland GDP deflator, import prices incl. indirect taxes (weight 0.38) and energy (0.06) | NAM2026 |
| Manufacturing, annual 1964–94 | w − q − pr = −0.12 u + 0.3 rpr (eq 9; s.e. 0.013 and 0.06); wedge (p − q) drops out, χ²(1) = 1.65 [0.20] | — | BN2003-NB (WP) |

### B.4 Import prices and the exchange rate

BJN2003-WP: pi = v + pf is an **identity** ("the index of import prices in foreign currency is denoted pf", §2 eq 12 text;
§4.1), so pass-through is complete by construction and only v is modelled. The exchange-rate EqCM (§4.1):

  EqCM_v(t) = (RS_t − Δ4p_{t−1} − RSECU_t + Δ4pck_t) + (v − p + pck)_{t−1}

i.e. a real-exchange-rate (PPP) term plus a real-interest-differential term, building on Akram and Eitrheim (1999).

NAM 2008 (BN2008-WP eqs 47–48, WP): (v + p* − p) = 0.12[(R − π) − (R* − π*)] + μ_v (a "regressive expectations" real
exchange rate relation, implying about 8% per quarter adjustment of expected depreciation); and
(pi − v − pi*) − 0.55(p − v − p*) = μ_pi: long-run homogeneity of import prices in v and foreign producer prices pi*, plus
pricing-to-market ("a one percent real appreciation in terms of consumer prices is associated with only 0.55 percent
appreciation in terms of import prices").

NAM 2026 (Table 5.38): the import-price EqCM is log PB − log(CPIVAL·PPIKONK) with adjustment −0.30 (t = −6.6), plus two
real-exchange-rate levels log(PCKONK·CPIVAL/CPI) (−0.068) and log(PPIKONK·CPIVAL/CPI) (−0.049); "the partial long-term
elasticities are +1 for both variables" (§3.5). The 2026 exchange-rate equation (Table 5.44) has **no** level term.

### B.5 The interest-rate rules evaluated

(a) BJN2003-WP (§4, §5): "finding an empirically constant reaction function from inflation forecasts to interest rates is a
non-starter. We therefore treat the short-run interest rate as a policy variable." For the forecast-uncertainty comparison
they add "an equation for the short-term interest rate as a function of the lagged rates of domestic and foreign annual
inflation, of nominal exchange rate depreciation, and of the lagged output gap" (§5), coefficients not reported. The policy
experiment is a permanent +1 point (0.01) shock to RS: "a final reduction in annual inflation by around 0.4 percentage
point" (§6.1, Figure 8); a 1% permanent shock to y raises annual inflation one-for-one and "the signal rate has to be raised
by 1.7 points" to cancel it (§6.2, Figure 9).

(b) ABE2005 (the model "largely an extension of ... Bårdsen et al. (2003)", with the MSTE criterion of "Bårdsen et al.,
2005, Ch. 10"), general rule, eq (9):

  r_t = ρ_r r_{t−1} + (1 − ρ_r)(π̄ + r̄r) + θ_π(Δ4pu_t − π̄) + θ_y(Δ4y_t − ḡ_y) + θ_q0(q_t − q̄) + θ_q1(q_{t−1} − q̄) + θ_ph(Δ4ph_t − π̄_ph) + θ_s(Δ4s_t − ḡ_s)

with pu = underlying (CPI-ATE) inflation, output **growth** rather than the gap (fn. 5; Bernhardsen and Bårdsen (2004)
estimated a weight 0.6 on output growth and smoothing 0.7, fn. 6), q = real exchange rate. Table 1, steady-state values
π̄ + r̄r = 0.06, π̄ = 0.025, ḡ_y = 0.025, q̄ = 0, π̄_ph = 0.10, ḡ_s = 0.10 (r̄r = 3.5, π̄ = 2.5):

| Rule | ρ_r | θ_π | θ_y | θ_q0 | θ_q1 | θ_ph | θ_s |
|---|---|---|---|---|---|---|---|
| FLX (Taylor-type, "flexible") | 0 | 1.5 | 0.5 | | | | |
| SM (smoothing) | 0.75 | 1.5 | 0.5 | | | | |
| MCI (real exchange rate) | 0 | 1.5 | 0.5 | 0.33 | | | |
| PH (house prices) | 0 | 1.5 | 0.5 | | | 0.20 | |
| OSE (equity prices) | 0 | 1.5 | 0.5 | | | | 0.20 |
| CMP (composite) | 0.25 | 1.5 | 0.5 | 0.25 | −0.25 | 0.05 | 0.05 |

Loss function eq (10): L(λ, κ) = V[Δ4pu] + λV[Δ4y] + κV[Δr], evaluated by counterfactual simulation over 1995:1–2000:4.

(c) NAM 2008 estimated reaction function (BN2008-WP eq 46, OLS 1999(3)–2007(2), T = 32, σ̂ = 0.19, WP):

  ΔR_t = −0.27 [R_{t−1} − 5.6 − 1.2(π^C_t − π̄) + (U_{t−2} − Ū) − 0.86(R*_{t−2} − R̄*)] + 0.51 Δ²R*_t − 0.051 Δ²(V·P*/P)_t
         (0.047)                                                                       (0.088)        (0.013)
  π^C = 100·Δ4 ln PC (core CPI), π̄ = 2.5, Ū = 3.4 (average unemployment rate), R̄* = 3.5.
  F_AR(1–3)(3,22) = 1.62 [0.21]; F_ARCH(1–3)(3,19) = 0.60 [0.62]; χ²_norm(2) = 0.82 [0.67]; F_Het(12,12) = 0.59 [0.81].
  (The last regressor is read from the typeset symbol as the second difference of the real exchange rate; see SOURCES.)
  Implied long run: R = 5.6 + 1.2(π^C − 2.5) − (U − 3.4) + 0.86(R* − 3.5).

(d) NAM 2026 (Table 5.77, OLS 2001Q2–2025Q4, T = 99, σ̂ = 0.147; "not part of the default version of the operative model ...
kept for reference and for use in scenario analysis"; §3.10: "the weight on inflation has been reduced to zero after
2008q4", so "model users may find it practical to treat the policy interest rate as an exogenous variable"):

  D(RNB) = −0.050 (RNB_{−1} − IT − 1.38) + 0.394 D(RNB_{−1}) + 0.193 D(RSW) − 0.609 D²LOG(UR) + 0.976 RNBDUM
           (t = −4.2)                      (9.9)                (3.7)          (−8.1)              (12.0)
  with the note "IT = (@PCY(CPIJAE) − 0.7 INFTARG) − RSW(−1)" (printed as such; the exact bracketing is not fully legible
  in the PDF text and should be checked against the EViews program file).

### B.6 Other long-run relations of the small model (BN2008-WP eqs 51–56, WP)

z − 0.47(w − p) − 0.0029·Trend = 0.03u + μ_z (productivity); 0 = u − 7.7Δ(w − p) − 4.5[0.01(RL − π) − Δ4y] − μ_u
(steady-state unemployment depends on real-wage growth and on the real interest rate minus GDP growth, "see also Hendry
(2001b)"); RL = 0.41RB + 0.76R + μ_RL; RB = 0.43R + 0.57RB* + μ_RB; y − 0.9g − 0.16(v + p* − p) = −0.06(RL − π) + μ_y;
(l − p) − 2.65y + 0.04(RL − RB) = μ_lp. Steady-state growth: Δp = Δp* + Δv, Δw = Δp + Δz + Δv, Δpi = Δp + Δv (eqs 57–59).

---

## Part C. The short-run (EqCM) equations, estimation and testing as published

### C.1 The dynamic wage-price model of BJN2003-WP (eq 18; FIML; conditional subsystem for {Δw, Δp} given {Δpr, Δy, Δu_{t−1}, Δτ1, Δτ3}, gap_{t−1}, Δh, i80q2, i70q1, Wdum, Pdum, "with all variables entering with two additional lags"; the Panel 4 steady state imposed; sample 1966(4)–1996(4))

Read from the typeset matrix (pypdf extraction, cross-checked with Appendix A of the paper):

  Δw_t − Δp_t = −0.144 Δpi_t − Δτ1_{t−2} − 0.36 Δτ3_{t−2} − 0.08 [w_{t−2} − p_{t−2} − pr_{t−1} + 0.1 u_{t−2}] + (dummies, Δh_t)
                       (0.08 on the 0.36)                        (0.01)
  Δp_t − 0.13 Δw_t = 0.06 gap_{t−1} + 0.028 Δpi_t + 0.13 Δτ1_{t−2} + 0.07 Δτ3_{t−2}
         (0.05)      (0.02)                               (0.03)
                     − 0.08 [p_{t−1} − 0.6 w_{t−3} + 0.6 pr_{t−1} − 0.4 pi_{t−1} − 0.6 τ1_{t−1} − τ3_{t−3}] + (dummies)
                       (0.01)

The import-price terms are the theory restrictions of Appendix A: Δw_t = −0.36(0.4Δpi_t + Δτ3_{t−2}) + ... and
Δp_t = 0.07(0.4Δpi_t + Δτ3_{t−2}) + ..., with ϕ = 0.4 and η = 1 imposed from Table 1 (the "unweighted" price restriction
Δp = 0.4Δpi + Δτ3_{t−2} is rejected; the weighted-down version is accepted). The text (§3.2): "a one percent in the rate of
inflation raises wage growth by one percent"; "the change in normal working-time Δh_t enters the wage equation with a
negative coefficient"; the VAT dummy i70q1 is negative and Pdum positive in the wage equation. With ϕ = 0.38 the implied
wage elasticities with respect to Δpp and Δpi are 0.62 and 0.24, "the wage equation therefore implies that we do not have
a NAIRU model".

Table 2: conditional subsystem σ̂_Δw = 1.02%, σ̂_Δp = 0.42%, AR 1–5 F(20,190) = 1.43 [0.11], normality χ²(4) = 5.10 [0.28],
heteroskedasticity F(66,242) = 0.76 [0.90]. Model (18): σ̂_Δw = 1.01%, σ̂_Δp = 0.41%, residual correlation −0.5,
**overidentification χ²(9) = 9.92 [0.60]**, AR 1–5 F(20,200) = 1.20 [0.26], normality χ²(4) = 4.14 [0.39], heteroskedasticity
F(66,257) = 0.81 [0.84]. Figures 2–4: one-step residuals, recursive forecast Chow tests, recursive overidentification
(encompassing) tests, all inside the 5% bands. Weak exogeneity (Table 3): the EqCM terms are insignificant in the marginal
equations for Δy, Δpr, Δu, Δv (F-tests, p ≥ 0.09). Super-exogeneity/Lucas-critique test: the marginal models' break dummies
and the OILST terms are jointly insignificant in the wage and price equations, χ²(9) = 6.65 [0.67] and 13.33 [0.15].

### C.2 Marginal models in BJN2003-WP (OLS, "constant and three seasonal dummies" omitted; 1-step residuals in Figure 6)

Exchange rate (§4.1; T = 1972(1)–1996(4) = 100; σ̂ = 0.96%; AR 1–5 F(5,88) = 1.24 [0.30]; normality χ²(2) = 1.35 [0.50];
heteroskedasticity F(31,61) = 0.88 [0.64]):

  Δv_t = 0.27 Δ(v − p + pck)_{t−1} − 0.1 EqCM_v(t) − 0.13 Δoil_t·OILST_t − 0.03 Δoil_{t−2}·OILST_t − 0.02 Δoil_{t−1}·DOILST_t − 0.24 ΔRS_t + 0.02 Vdum_t
         (0.07)                      (0.04)          (0.02)                (0.007)                 (0.007)                  (0.08)      (0.004)
  OILST = 1/{1 + exp[4(OIL − 14.47)]}, DOILST = 1/[1 + exp(ΔOIL)] (smooth transitions: oil below 14 USD and falling oil prices
  depreciate the krone).

GDP (§4.2, adapted from the "AD" equation of Bårdsen and Klovland (2000); T = 100; σ̂ = 1.61%; AR F(5,86) = 1.44 [0.22];
normality 3.04 [0.22]; het. F(31,59) = 1.09 [0.38]):

  Δy_t = −0.71 Δy_{t−1} − 0.51 Δy_{t−2} − 0.32 EqCM_y(t) + 0.70 Δcr_{t−1} + 0.06[i85q1 + i86q2]_t
         (0.08)         (0.09)         (0.05)          (0.12)           (0.01)
  EqCM_y(t) = y_{t−3} − 0.5 co_{t−3} − 0.4 yf_{t−3} − 0.1(pi − p)_{t−2} + 0.9 RRB_{t−1},  RRB = RB − Δ4p.

Unemployment (§4.3; T = 1967(1)–1996(4) = 120; σ̂ = 0.081; AR F(5,99) = 1.42 [0.23]; normality 4.83 [0.09]; het. F(27,76) = 1.61 [0.06];
two sets of seasonals, constant omitted):

  Δu_t = 0.30 Δu_{t−1} − 0.24 u_{t−1} − 1.79 Δy_t − 1.13 Δy_{t−1} − 0.14 Δamun_t + 0.46 STU_{t−1} − 0.62 Δco·STU_{t−3} − 7.45 Δyf·STU_{t−3} − 0.76 Δ(pi − p)_{t−1}
         (0.07)         (0.04)        (0.37)      (0.22)         (0.04)        (0.08)        (0.32)              (3.08)              (0.33)
  STU = 1/(1 + exp(−125(U − 0.04))) (a threshold at 4% unemployment that shifts equilibrium unemployment down by 1.5 points).
  "The level of unemployment cannot be permanently influenced by fiscal policy or monetary policy ... since Δu_t is a function
  of GDP growth, not the level of GDP."

Productivity (§4.4; T = 120; σ̂ = 1.35%; AR F(5,107) = 3.14 [0.01]; normality 5.42 [0.07]; het. F(17,94) = 1.37 [0.17]):

  Δpr_t = −0.373 Δpr_{t−1} − 0.03 u_{t−1} − 0.08 i86(2)_t + 0.04[i79q2 − i91q3]_t
           (0.06)          (0.01)       (0.01)         (0.01)

Closing the model (§5): reaction functions for amun, for RB (reacting to RS with a lag) and for cr (output growth and the
cost of debt); identities for the EqCM terms, real wages, real exchange rate, real bond rate. Exogenous: yf, co, pf, pck,
oil, RS. Forecasts: dynamic ex-post forecasts 1995(1)–1996(4) from parameters estimated to 1994(4), conditional on actual
exogenous paths, with ±2 s.e. bands (standard error of annual inflation 0.9 points 4 quarters ahead, 1.2 points 8 ahead).

### C.3 The 2001-vintage system (ABE2005 Appendix C.1; "block recursive ... the simultaneous part of the model is estimated by FIML, while the equations constituting the recursive part are estimated by OLS"; seasonal and policy dummies suppressed; split-sample Chow tests, normality, AR and heteroskedasticity below each equation)

Wage growth and inflation (FIML, T = 117, 1972:4–2001:4; σ̂_w = 0.009, σ̂_p = 0.004; F_ar(1–5)(20,198) = 1.58 [0.06];
χ²_nd(4) = 4.36 [0.36]; F_het(135,186) = 1.25 [0.08]):

  Δw_t = 0.39 Δp_{t−1} + 0.37 Δp_{t−2} − 0.49 Δh_t − 0.09 [(w − p − pr)_{t−1} + 0.1 u_{t−2}]
         (0.095)        (0.097)        (0.110)    (0.012)
  Δp_t = 0.27 Δw_t + 0.13 Δw_{t−1} + 0.04 Δpm_t + 0.07 Δpe_t + 0.04 Δy_{t−1} − 0.06 [p_{t−3} − 0.65(w_{t−2} − pr_{t−1} + τ1_{t−1}) − 0.35 pm_{t−1} − 0.5 τ3_{t−1}]
         (0.031)     (0.021)        (0.009)     (0.008)     (0.012)       (0.006)

Nominal exchange rate (OLS, T = 116, 1973:1–2001:4, σ̂ = 0.015; F_Chow(1987:3)(58,50) = 0.46 [1.00]; F_Chow(1999:1)(12,96) = 0.63 [0.81];
F_ar(1–4) = 0.55 [0.70]; F_arch = 0.20 [0.94]; χ²_nd(2) = 10.1 [0.006]; F_het(14,101) = 0.81 [0.65]):

  Δe_t = 0.22 Δe_{t−1} − 0.14 (e − p + p*)_{t−1} − 0.28 Δp_t − 0.34 Δr_t − 0.21 (Δrb_{t−1} − Δp_{t−2}) − 0.13 Δoil_t/[1 + exp(4(OIL_t − 14.21))] − 0.14 (r_{t−1} − r*_t) − (e − .8e*)_{t−1}
         (0.077)       (0.032)                (0.173)   (0.101)   (0.144)                   (0.032)
  (the last two terms are printed without standard errors; the 2001 vintage thus keeps the PPP EqCM and the oil smooth transition of BJN).

Unemployment rate (OLS, T = 117, 1972:4–2001:4, σ̂ = 0.060; Chow tests [0.81], [0.62]; AR [0.88]; ARCH [0.48]; normality [0.28]; het. [0.02]):

  Δu_t = 0.34 Δu_{t−1} − 0.05 u_{t−1} − 1.87 Δ4y_t − 3.04 Δy_{t−2} + 1.22 Δ(w − p)_{t−1} + 1.68 ΔN1649AT_t
         (0.068)        (0.017)      (0.291)     (1.040)       (0.522)            (0.702)

Aggregate demand (OLS, T = 61, 1986:4–2001:4, σ̂ = 0.010): Δy_t = −0.39Δy_{t−1} + 0.024Δ(s − p)_{t−2} + 0.27Δg_t + 0.46 cap_t·Δ(e + p* − p)_t
− 0.3[y − 0.5g − 0.3y* + (rl(1 − τ2) − Δ4p) − 0.1(ph − p)]_{t−1} − 0.5Δ(e + p* − p)_{t−3}. Real credit, house prices and stock
prices equations are also printed (not needed here).

### C.4 NAM 2008 (BN2008-WP Tables 1–2; "estimated macroeconometric relationships in equilibrium correction form, with cointegration coefficients imposed as known"; Oxmetrics 5 estimation, EViews 6 simulation; seasonals and dummies omitted; WP)

Prices, wages, productivity (FIML, T = 1979(3)–2007(1) = 111; σ̂_P = 0.3%, σ̂_W = 0.6%, σ̂_Z = 1.2%; F_vec,AR(1–5)(45,250) = 1.07 [0.36];
F_vec,Het(354,224) = 1.11 [0.20]; χ²_vec,norm(6) = 7.02 [0.32]):

  Δp_t = −0.052 [p_{t−3} − 0.7(w − z)_{t−1} − 0.3 pi_{t−1} − μ_p] − 0.06 Δz_t + 0.29 Δp_{t−2} + 0.024 Δpi_t + 0.059 Δpe_t + 0.042 Δy_{t−1}     (38)
          (0.006)                                               (0.025)   (0.049)      (0.011)      (0.0038)     (0.014)
  Δw_t = −0.065 [(w_{t−1} − p_{t−2} − z_{t−1}) + 0.1 u_{t−4} − μ_w] + 0.56 Δp_t + 0.43 Δp_{t−1} − 0.039 (Δ²u_{t−1} + Δu_{t−3}) + 0.73 ΔT1_t     (39)
          (0.019)                                                (0.071)                  (0.0053)                     (0.023)
  Δz_t = −0.64 [z_{t−3} − 0.47(w − p)_{t−1} − 0.0029 Trend_t − 0.03 u_{t−2} − μ_z] + 0.24 Δ(w − p)_t − 0.83 Δ²z_{t−1}     (40)
          (0.062)                                                           (0.05)             (0.036)
  "the estimated wage equation (39) shows that â12(1) = 1, saying that dynamic homogeneity with respect to consumer price
  is a valid restriction"; "the t-values [of α11 and α22] are 8.6 and 3.8"; identification by zero restrictions on Δy in the
  wage equation and on Δu in the price equation.

Exchange rate (OLS, T = 1994(2)–2007(2) = 56, σ̂ = 1.6%; F_AR(1–4)(4,44) = 1.60 [0.19]; F_ARCH(1–4)(4,40) = 0.99 [0.42]; χ²_norm(2) = 0.07 [0.97]; F_x(6,41) = 0.59 [0.80]):

  Δv_t = −0.042 {(v + p* − p) − 0.12[(R − π) − (R* − π*)] − μ_v}_{t−1} − 0.0361 IT_t·Δ(R − R*)_t − 0.036 Δ²po_{t−1}     (36)
          (0.012)                                                     (0.00693)                  (0.015)
  π_t ≡ 100·Δ4P_t/P_{t−4}.

Import prices (OLS, T = 1990(1)–2007(1) = 69, σ̂ = 1.1%; F_AR = 1.78 [0.15]; F_ARCH = 0.99 [0.42]; χ²_norm = 0.81 [0.67]; F_Het(9,53) = 1.15 [0.34]):

  Δpi_t = −0.431 [(pi − v − pi*) − 0.55(p − v − p*) − μ_pi]_{t−1} + 0.429 Δv_t + 1.07 Δpi*_t     (37)
           (0.0806)                                          (0.0718)     (0.211)

Unemployment (OLS, T = 1981(1)–2007(2) = 106, σ̂ = 5.0% of U; F_AR(1–5)(5,92) = 1.04 [0.25]; F_ARCH = 0.48 [0.75]; χ²_norm = 0.50 [0.78]; F_Het(13,83) = 1.44 [0.16]):

  Δu_t = −0.078 {u_{t−1} − 7.69 Δ(w − p)_{t−2} − 0.05[(RL − π) − 100Δ4y]_{t−2} − μ_u} + 0.44 Δu_{t−1} + 0.49 Δu_{t−4} − 0.27 Δu_{t−5}     (41)
          (0.019)                                                            (0.071)       (0.059)       (0.074)

Interest rates (FIML, T = 1993(2)–2006(4) = 55; σ̂_RL = 0.10, σ̂_RB = 0.19): ΔRL_t = −0.33(RL − 0.41RB − 0.76R − μ)_{t−1} + 0.58ΔR_t (42);
ΔRB_t = −0.17(RB − 0.43R − 0.57RB* − μ)_{t−1} + 0.43ΔR_t + 0.97ΔRB*_t (43).
GDP (OLS, T = 1986(2)–2007(1) = 104, σ̂ = 1.4%): Δy_t = −0.21[y_{t−2} − 0.9g_{t−1} − 0.16(v + p* − p)_{t−1} + 0.06(RL − π)_{t−1} − μ_y]
− 0.74Δy_{t−1} + 0.42Δg_t + 0.67Δ(l − p)_{t−1} (44). Credit (OLS, 2000(1)–2007(2)): eq (45). Money-market rate: eq (46), Part B.5(c).

Stylized ("mean-dynamics") representation, eqs (60)–(69): Δv = −0.04Δ(R − R*) − 0.04{...}_{t−1}; Δ(pi − pi* − v) = 0.1Δv − 0.43[...]_{t−1};
Δp = 0.09Δz + 0.03Δpi + 0.08Δpe + 0.06Δy − 0.07[p − 0.7(w − z) − 0.3pi]_{t−1}; Δ(w − p) = −0.04Δu + 0.73ΔT1 − 0.07[(w − p − z) + 0.1u]_{t−1};
Δu = −0.23{u − 7.65Δ(w − p) − 4.46[0.01(RL − π) − Δ4y]}_{t−1}; Δy = 0.16Δg + 0.38Δ(l − p) − 0.12[...]_{t−1}.

Simulation practice: stochastic dynamic simulation 2007(4)–2035(4) with constant R and 2% foreign inflation (Figure 3;
inflation settles "just above 2.5%", "natural" unemployment about 3%); dynamic multipliers of a permanent +100 bp in R,
2007(1)–2012(4), with 95% bands (Figure 5: impact appreciation about 3%, steady-state appreciation 1.2%, inflation
multiplier reaching about −1 point); within-sample dynamic simulation 2003(3)–2007(3) with the estimated reaction function
(Figure 6); a −5% foreign-price shock (Figure 7).

### C.5 NAM 2026 (single equations by OLS/NLS in EViews, "treating the [cointegration] coefficient estimates as known" (§5.1); samples differ by equation)

Manufacturing wage (Table 5.25, OLS, 1996Q1–2025Q4, T = 120, σ̂ = 0.0228, R̄² = 0.63, DW = 1.85):

  Δ4 ln WFP1_t = −0.226 ECM_WFP1_{t−4} + 0.256 (Δ4 ln CPI_{t−1} − π̄) + 0.166 [Δ4 ln PYFP1_t + Δ4 ln ZYFP1_t] − 0.419 Δ ln WFP1_{t−4} + 1.00 WFP1DUM − 0.081 + S1..S3 + KNBREAKQ2/Q3
                 (t = −5.7)               (1.8)                            (3.9)                                       (−7.9)
  ECM_WFP1 = log(WCFP1/(ZYFP1·PYFP1)) + 0.12 log(UAKU).   Eq (3.34) in the text rounds this to −0.23, 0.26, 0.17.

Wage followers (Tables 5.26–5.27, eqs 3.35–3.37): Δ ln WFP2 = −0.58(ln WFP2 − ln WFP1)_{t−1} + 0.90 Δ ln WFP1 − 0.08 Δ3 ln WFP2_{t−1} − 0.004 ln UAKU_{t−1} + ...
(1972Q4–2025Q1); services −0.41 / 0.8; government −0.31 / 0.8 with −0.02 ln UAKU_{t−1} and 0.15Δ4 ln CPI_{t−1}.

CPI (Table 5.24, OLS, 1990Q1–2026Q2, T = 146, σ̂ = 0.00506, R̄² = 0.88, DW = 1.96):

  Δ log(CPI/PYF)_t = −0.195 ECM_CPI_{t−1} + 0.382 Δ log PYF_{t−1} + 0.058 Δ log(CPI/PYF)_{t−4}
                     (z = −10.3)            (14.7)                (5.1)
  ECM_CPI as in Part B.3. (The CPI is modelled relative to the mainland GDP deflator PYF, which NAM explains from the
  sectoral value-added deflators, Tables 5.19–5.23.)

CPI-ATE (Table 5.36, 2000Q1–2022Q1): Δ log CPIJAE = 0.91 Δ log CPI − 0.034 Δ log CPIEL − 0.0336 Δ log CPIJAE_{t−1} + 0.119 Δ log CPIJAE_{t−4} + 0.174 D(T3) − ... (bridge equation).

Import price (Table 5.38, LS, 1979Q2–2025Q1, T = 184, σ̂ = 0.0128, R̄² = 0.69, DW = 1.98):

  Δ log PB_t = −0.124 [Δ log PB_{t−1} − Δ log PB_{t−4}] − 0.300 [log PB − log(CPIVAL·PPIKONK)]_{t−1} − 0.068 [log(PCKONK·CPIVAL) − log CPI]_{t−1}
               (−4.4)                                   (−6.6)                                        (−5.2)
               − 0.049 [log(PPIKONK·CPIVAL) − log CPI]_{t−1} + 0.481 Δ log CPIVAL_t + 0.658 Δ log PPIKONK_t + 0.0038 log(SPOILUSD·SPUSD/PYF)_{t−1} + 1.00 PBDUM + S1..S3
               (−4.1)                                        (10.0)                 (8.3)                   (7.7)

Effective exchange rate (Table 5.44, LS, 2001Q1–2025Q2, T = 98, σ̂ = 0.0137, R̄² = 0.68, DW = 1.74):

  Δ log CPIVAL_t = −0.286 Δ log CPIVAL_{t−1} − 0.045 [D(RSH) − D(RSW)]_t − 0.088 Δ log SPOILUSD_t + 0.093 log(PAW_{t−4}/PAW_{t−5}) − 0.0071 (RBOTENY − US10Y)_t
                   (−4.6)                    (−8.6)                       (−8.1)                  (3.9)                        (−3.3)
                   + 0.049 CPIVAL08Q4 + 0.047 CPIVAL19Q4 − 0.065 COVIDQ2 − 0.023 COVIDQ6 + 0.052 CPIVAL23Q2

LFS unemployment (Table 5.58, 1987Q1–2025Q4; level of unemployed persons AKULED with a logistic switch at UAKU = 5.4 on the
sign-split annual change in employment N, AKULED_{t−1} (0.68), population–employment gap (0.047), seasonals, 2025q2 dummy);
registered unemployed (Table 5.59) bridged from AKULED. UAKU and UR then follow from eqs (3.38)–(3.39).

Money-market rate (Table 5.78, 1997Q2–2021Q3): D(RSH) = −0.23 − 0.355 RSH_{t−1} + 0.951 D(RNB) + 0.293 RNB_{t−1} + 0.254 D(RSW) + 0.153 RSW_{t−1} + dummies/steps.
Foreign short rate (Table 5.80, 1995Q1–2025Q4): D(RSW) = −0.103[RSW_{t−1} − US10Y − 0.6(100Δ log PCKONK − 2) + 2.1] − 1.44 CRISIS09Q1.

Forecasting procedure (§2.4): dynamic simulation from forecast origin T with exogenous variables extrapolated over T+1..T+H
(e.g. %FSTART 2025q3, %FSTOP 2030q4), stochastic simulation giving mean paths with 90% (or 95%) bands, ragged-edge fix of
endogenous variables by hand, annual tables (GDPSUPPLY/GDPDEMAND). Policy analysis (§2.5): shocks to exogenous variables
assuming one-way Granger causality and parameter invariance.

---

## Part D. What this dashboard implements and where it departs

### D.1 Design principle

The dashboard will estimate a **minimal, transparent** version of the BJN/NAM core in Python (statsmodels, OLS single
equations or SUR/FIML for the wage-price pair), with the long-run coefficients **imposed as known** from the published
cointegration results (exactly the two-step practice of BN2008-WP §2.5, §3.1 and NAM2026 §5.1) and, as a check, re-estimated
freely on the dashboard's own sample. The page will show, for each equation: the published long-run relation and coefficient
it imposes (with source tag), the estimated short-run coefficients with t-values, the residual standard error, and the
diagnostic battery the authors use (Breusch–Godfrey AR 1–4/1–5 F, ARCH 1–4, Jarque–Bera/Doornik–Hansen normality, White
heteroskedasticity, RESET, recursive one-step residuals and recursive Chow forecast tests, split-sample Chow tests), then a
dynamic simulation with ±2σ bands and the response to a permanent +100 bp shock to the policy rate under (i) exogenous rate
and (ii) each rule.

### D.2 The system (lower-case = logs; quarterly; seasonally unadjusted with seasonal dummies)

Endogenous: w, p (CPI), pu (CPI-ATE, bridge), pi (import prices), v (I-44), u (unemployment), y (mainland GDP), R (policy
rate), RS (3-month money-market rate). Exogenous: pf (foreign producer/consumer prices), p* (foreign CPI), R* (foreign
short rate), y* (trading-partner demand), z (productivity trend), oil (Brent USD), T1 (payroll-tax rate), T3 (indirect-tax
effect in CPI), g (public consumption), dummies.

1. **Wage equation** (BJN2003-WP eq 18 / ABE2005 C.1 / BN2008-WP eq 39 form)
   Δw_t = c + a0 Δp_t + a1 Δp_{t−1} + a2 Δz_t + a3 Δu_t − α_w [w − p − z + γ_u u]_{t−1} + seasonals + dummies,
   with **γ_u = 0.1 imposed** (BJN Table 1 Panel 4: 0.09 (0.02); BN2008 eq 50; NAM2026 eq 3.33 gives 0.12 for manufacturing);
   homogeneity w.r.t. p and z imposed in the level (Panel 4). Free alternative: estimate γ_u by Johansen on the dashboard sample
   and report both. Test dynamic homogeneity a0 + a1 = 1 (BN2008 §2.6.5) rather than impose it.
2. **Price equation**
   Δp_t = c + b0 Δw_t + b1 Δw_{t−1} + b2 Δpi_t + b3 gap_{t−1} (or Δy_{t−1}) + b4 Δpe_t − α_p [p − (1 − ϕ)(w + T1 − z) − ϕ pi − η T3]_{t−1} + seasonals + dummies,
   with **ϕ = 0.4 (1 − ϕ = 0.6) imposed** (BJN Panel 4: 0.38 (0.02); ABE2005: 0.35; BN2008: 0.3; NAM2026 Table 5.24: 0.38 on
   PB(1 + T3) relative to the GDP deflator). Free alternative: Johansen estimate of ϕ.
3. **Import-price equation** (BN2008-WP eq 37 form)
   Δpi_t = c + d0 Δv_t + d1 Δpf_t − α_pi [pi − v − pf − κ(p − v − p*)]_{t−1} + seasonals,
   long-run homogeneity in v and pf imposed; κ (pricing-to-market, 0.55 in BN2008) estimated freely and reported.
4. **Exchange-rate equation** (BN2008-WP eq 36 form, which nests the 2026 difference-only form when α_v = 0)
   Δv_t = c + e0 Δ(R − R*)_t + e1 Δoil_t + e2 Δv_{t−1} − α_v [(v + p* − p) − 0.12((R − π) − (R* − π*))]_{t−1} + dummies,
   α_v and e's estimated; the 0.12 real-interest-differential coefficient imposed from BN2008 eq 47 with a free alternative.
5. **Unemployment equation** (BN2008-WP eq 41 form, falling back to the BJN §4.3 growth form if the level term is insignificant)
   Δu_t = c + f1 Δu_{t−1} + f4 Δu_{t−4} − f5 Δy_t − f6 Δy_{t−1} − α_u [u − θ1 Δ(w − p) − θ2((RS − π) − 100Δ4y)]_{t−2} + seasonals.
6. **Output equation** (BN2008-WP eq 44 form without credit)
   Δy_t = c + g1 Δy_{t−1} + g2 Δg_t + g3 Δy*_t − α_y [y − 0.9 g − 0.16(v + p* − p) + 0.06(RS − π)]_{t−1} + seasonals + Covid dummies,
   long-run coefficients 0.9 / 0.16 / 0.06 imposed from BN2008 eq 55 with a free alternative.
7. **Policy rule**, three variants switchable on the page: (a) exogenous R (the BJN2003 practice and the NAM2026 default);
   (b) the ABE2005 Table 1 rules FLX and SM (θ_π = 1.5, θ_y = 0.5, ρ = 0 or 0.75, r̄r = 3.5, with π̄ = 2.5 before 2018Q1 and
   **2.0 from 2018Q1** — DEPARTURE below); (c) an estimated reaction function of the BN2008 eq 46 / NAM2026 Table 5.77 form on
   2001Q2–latest, shown with its recursive instability.
8. **Money-market rate**: RS_t = R_t + spread, spread modelled as in NAM2026 Table 5.78 (long-run RS on R and R*).
9. **Bridge** CPI-ATE: Δpu_t on Δp_t, Δpe_t, ΔT3_t (NAM2026 Table 5.36 form) so the rule can respond to CPI-ATE.
10. Identities: gap = HP(1600) of y (BJN App. B) or the output-growth variant of ABE2005; π = 100Δ4p; real rates; ecm terms.

### D.3 Departures from the published model (each to be listed on the page)

- **DEPARTURE: wage variable.** The originals use RIMINI/FPAS hourly wages (W) or wage costs (WC) for the mainland economy
  (BJN App. B; BN2008 App. A uses wage **costs**). The dashboard uses the quarterly national accounts: wages and salaries
  divided by hours worked for wage earners, Mainland Norway (StatBank 09175, the table NAM2026 App. D uses for its
  YWW/NWH series), available from 1995Q1. Wage **costs** (incl. employers' social contributions, YWC in 09175) give T1 =
  YWC/YWW − 1 exactly as BJN's τ1 = WCF/WF − 1. Before 1995 no quarterly hourly wage exists in StatBank; the wage index
  (lønnsindeks) is monthly earnings, not hourly, and starts later. The sample therefore starts in 1995Q1 at the earliest.
- **DEPARTURE: productivity.** z = ln(mainland value added, constant prices, 09171/09190) − ln(hours worked, 09175), i.e.
  value added per hour worked (BJN: "value added per man hour at factor costs, fixed 1991 prices", ZYF). Basic prices
  replace factor costs (SNA 2008). Not trend-filtered; the wage EqCM uses actual z as in the originals.
- **DEPARTURE: unemployment measure.** BJN use "total" registered unemployment incl. labour-market programmes (UTOT);
  BN2008 uses the registered rate; NAM2026 uses the LFS rate UAKU in the wage EqCM and registered UR in the policy rule.
  The dashboard carries both the registered rate (NAV via StatBank, longest history) and the LFS rate (StatBank 13760
  monthly, averaged), uses the **registered rate** in the wage equation by default (DEPARTURE from NAM2026, agreement with
  BN2008), and offers UAKU as a switch. The "total" rate incl. programme participants (NAV "bruttoledighet") is kept where
  StatBank provides it; see `data_map.md`. **Data finding**: SSB carries NAV's monthly registered rate only 1999M01–2014M12
  (table 10540) and persons 1990M01–2014M12 (10594); `data.csv` splices these with the quarterly, seasonally adjusted history
  in Norges Bank's MPR data file from 2015Q1 (NAV source), so `u_reg` has an NSA→SA seam at 2015Q1 that the page must state.
  The LFS rate (08518) is clean from 1972Q1 (breaks 2006, 2021) and is the safer default if the seam matters.
- **DEPARTURE: import prices and the identity pi = v + pf.** BJN treat pi = v + pf as an identity with pf unobserved. The
  dashboard uses the QNA import deflator (09190, current/constant-price imports) as PI, and estimates pass-through (eq 3) as
  NAM does, because no free trade-weighted foreign producer-price index exists: PPIKONK/PCKONK are built by NAM from LSEG
  country series (NAM2026 App. D.3). The dashboard's pf is a fixed-weight (2015–2024 import shares from StatBank 08803)
  index of the OECD/Eurostat producer-price indices of the main trading partners, or, if that fails, the euro-area PPI;
  p* likewise from OECD CPI. **Data finding**: `data.csv` carries the euro-area domestic PPI (Eurostat, 2000Q1–) as `pf`,
  the German PPI (1976Q1–) as a long proxy, the euro-area HICP (ECB, 1996Q1–) as p*, and OECD CPIs for SE/DE/UK/US; the
  fixed-weight trading-partner index is not yet built (open question 9). The import deflator `pi_defl` runs 1978Q1–.
- **DEPARTURE: exchange rate.** BJN's V is the import-weighted "effective ... value of the NOK" (PBVAL); NAM's CPIVAL is
  "an effective nominal exchange rate index (using trade data to construct the weights)". The dashboard uses Norges Bank's
  I-44 (import-weighted, 1995 = 100, up = depreciation), quarterly average of daily data — the same convention (up =
  weaker krone) as v in all vintages. **Data finding**: Norges Bank's open data give I-44 monthly from 1989-07 (1995 = 100)
  and the TWI from 1971-01 (1990 = 100), so v does not bind the sample; the wage data (1995Q1) do.
- **DEPARTURE: policy and money-market rates.** BJN/BN2008 use the 3-month Euro-krone rate RS as "the" instrument (BN2008
  fn. 15: the sight deposit rate is the instrument "in practice ... changes in the sight rate are transmitted to the money
  market rate immediately"). The dashboard uses Norges Bank's key policy rate (sight deposit rate, KPRA) as R, and for RS
  the 3-month NIBOR. **Data finding**: Norges Bank's API has no NIBOR at all (it stopped publishing it in 2013); the
  OECD short-term rate for Norway (IR3TIB, = 3-month NIBOR) is available monthly from 1980 and is used as `rs`; NOWA
  (2011Q4–) is carried for a check. The policy rate (sight deposit rate) exists from 1991-01-01; before that the D-loan
  (overnight lending) rate from 1982-04 is spliced in (`r_policy_spliced`). Foreign rate R*: 3-month EURIBOR (ECB, 1994Q1–)
  with the German 3-month rate (OECD, 1970–) before.
- **DEPARTURE: foreign demand y*.** BJN's YF (export-weighted trading-partner GDP, 1985 weights) is replaced by a
  fixed-weight index of trading-partner GDP from OECD QNA, or omitted from the output equation if coverage is poor (then
  the output equation is the BN2008 form, which has no y*).
- **DEPARTURE: indirect taxes T3 and the CPI/CPI-ATE pair.** τ3 (RIMINI T3) is not public. For 2001Q1 on, the dashboard
  constructs the cumulative tax contribution to the CPI from SSB's CPI-AT (CPI adjusted for tax changes): T3 ≈ ln(CPI) −
  ln(CPI-AT) rebased, and uses it with η = 1 in the price EqCM (BJN Panel 4) and as ΔT3 in the CPI-ATE bridge. **Data
  finding**: StatBank carries the CPI-AT and CPI-ATE index levels only from 2002M12 (table 14706; earlier tables hold only
  rates of change), so `t3` and `cpi_ate` start in 2003Q1; before that T3 is set to zero (constant), which is a departure
  only in the level of the constant, and CPI-ATE-based rules can only be simulated from 2003.
- **DEPARTURE: energy prices pe.** The 2001 and 2008 vintages have Δpe (CPI electricity, fuel) in the price equation. The
  dashboard uses the CPI sub-index 04.5 "Electricity, gas and other fuels" (and 07.2.2 fuels) from StatBank 14700,
  available from 2000M07 (2000Q3); for 1995–2000 the term is dropped or the CPI/CPI-excl.-energy ratio (KPI-JE, 1995M01–)
  is used instead. The 2021–23 energy and import-price burst then enters through Δpe and Δpi rather
  than through dummies; its adequacy is reported by recursive Chow tests, and 2022Q1 (UKRW, NAM2026 §5.1) is kept as a
  candidate impulse dummy.
- **DEPARTURE: oil price.** BJN's smooth-transition oil terms (OILST with threshold 14.47 USD) are specific to 1972–1996
  oil prices; the dashboard uses the linear Δoil term of BN2008 eq 36 / NAM2026 Table 5.44. Brent comes from the World
  Bank Pink Sheet (FRED is not reachable from the build machine).
- **DEPARTURE: no credit, house-price, stock-price or bond-rate equations.** The credit channel (BN2008 eqs 44–45, ABE2005)
  and the asset-price rules (PH, OSE) are omitted; only the FLX/SM/MCI rules and an estimated rule are offered. The real
  exchange rate and real short rate carry the transmission.
- **DEPARTURE: inflation target.** ABE2005/BN2008 use π̄ = 2.5. Norway's target was lowered to 2.0% on 2 March 2018; the
  dashboard uses π̄ = 2.5 to 2017Q4 and 2.0 from 2018Q1 in the rules and in the NAM2026-style wage term (Δ4p_{t−1} − π̄).
  (In NAM2026 π̄ "represents the inflation target rate"; whether it is time-varying is not stated in the documentation.)
- **DEPARTURE: estimator.** FIML for the wage-price pair (BJN, ABE2005, BN2008) is replaced by OLS on each equation with
  Δp_t in the wage equation and Δw_t in the price equation instrumented (2SLS with the system's predetermined variables),
  plus a SUR/FIML check if statsmodels' capabilities suffice; the page states which estimator produced the shown numbers.
  The Johansen rank/trace tests of BJN Table 1 are replicated with statsmodels' `coint_johansen` on the dashboard sample and
  reported, but the imposed long-run coefficients remain the published ones.
- **DEPARTURE: sample.** See D.4. The published samples start in 1966–1979; the dashboard cannot go before 1995Q1 with
  consistent wage data.
- **DEPARTURE: dummies.** None of the BJN income-policy, devaluation and VAT dummies falls in the dashboard sample. The
  dashboard uses: the inflation-targeting step IT (0 to 2001Q1, 1 from 2001Q2; BN2008 App. A); Covid impulses COVIDQ1–Q8
  (2020Q1–2021Q4) in the output, unemployment and exchange-rate equations only where significant; UKRW (2022Q1);
  seasonal-break dummies from 2015Q1 only if the seasonal residual pattern demands it. Every dummy that is kept is shown.
- **DEPARTURE: seasonal adjustment.** All vintages use unadjusted data with seasonal dummies. The dashboard does the same for
  CPI, wages, import prices, unemployment, and uses the **unadjusted** constant-price mainland GDP from 09190 (SSB also
  publishes a seasonally adjusted version; it is downloaded for the chart only, not used in estimation). Quarterly values of
  monthly series are averages (NAM2026 App. D.2); of daily series, averages of daily observations (App. D.4).

### D.4 Sample and regime choices

- Recommended **estimation sample 1995Q1/1996Q1–latest quarter** (the first quarter with 09175 hourly wages; NAM2026 Table
  5.25 itself starts in 1996Q1 for the wage equation and 1990Q1 for the CPI equation). With four lags the first usable
  observation is 1996Q1; the data collected on 2026-10-31 end in 2026Q2 (QNA) / 2026Q3 (monthly series), giving 122
  quarters. The import-price, exchange-rate, unemployment and output equations can be estimated from 1990Q1 (or 1979Q1 for
  the import deflator, 1978Q1 for GDP) as a longer-sample check, as NAM2026 does equation by equation. Long-run coefficients are imposed, so
  the short sample costs little in the levels and only affects the short-run dynamics.
- **Inflation targeting (29 March 2001)**: the BJN tests of invariance across the 1992 float are the authors' answer to the
  Lucas critique; the dashboard adds the IT step dummy in the exchange-rate (BN2008 eq 36 interacts IT with Δ(R − R*)) and
  policy-rate equations and reports a split-sample Chow test at 2001Q2 for the wage and price equations. An alternative
  **2001Q1–latest** sample (about 100 quarters) is offered as a switch; with γ_u and ϕ imposed it is long enough for the
  short-run coefficients, but recursive estimates will be unstable in the first 20 quarters.
- **Covid 2020–21**: impulse dummies as above; the wage and price equations are estimated with and without 2020Q2–2020Q3
  excluded and both shown.
- **2021–23 inflation burst**: no dummies in the price equation; the model has to explain it through Δpi, Δpe, Δw and the EqCM.
  The page shows the recursive one-step residuals so the owner can judge; the NAM2026 import-price and CPI equations are
  estimated through 2025–2026 without such dummies apart from PBDUM/CPIDUM (contents in the EViews file, not published).
- The 2018 target change (2.5 → 2.0) enters only the rules and the NAM-style wage term.

### D.5 Restrictions imposed vs. estimated freely (summary table)

| Relation | Imposed (source) | Estimated freely | Reported test |
|---|---|---|---|
| Wage level | w − p − z = −0.1 u (BJN T.1 P.4; BN2008 eq 50) | α_w, a0–a3, constant | Johansen γ_u on own sample; dynamic homogeneity a0 + a1 = 1 |
| Price level | p = 0.6(w + T1 − z) + 0.4 pi + T3 (BJN T.1 P.4) | α_p, b0–b4 | Johansen ϕ; restriction b2 = 0.4·b_pp (BJN App. A) |
| Import price | pi = v + pf (+κ·rex) | α_pi, κ, d0, d1 | homogeneity test |
| Exchange rate | 0.12 on real-rate differential (BN2008 eq 47) | α_v, e0–e2 | α_v = 0 (the NAM2026 form) |
| Unemployment | none | all | level-term significance |
| Output | 0.9, 0.16, 0.06 (BN2008 eq 55) | α_y, g1–g3 | free long run |
| Policy rule | θ_π = 1.5, θ_y = 0.5, ρ ∈ {0, 0.75}, r̄r = 3.5 (ABE2005 T.1) | estimated variant | recursive Chow |
| Money-market spread | none | all | — |

### D.6 Simulation and reporting

Dynamic (deterministic) simulation of the full system from an origin quarter with exogenous variables held at actual values
(within sample) or extrapolated at stated growth rates (forecast), as in BJN §5 and NAM2026 §2.3–2.4; bootstrap or
Gaussian stochastic simulation for bands (NAM2026 reports 90%/95% bands; BJN ±2 s.e.). Shock analysis: permanent +100 bp to
R from a chosen quarter, reporting the multipliers for Δ4p, Δ4pu, u, Δ4y, v and Δ(w − p) over 48 quarters, in the layout of
BJN Figure 8 and BN2008 Figure 5, under each rule variant. All numbers shown on the page carry the estimation sample and the
date of the data vintage.

### D.7 As implemented (decisions of 2026-10-31; this list is what the page shows as "departures")

- **Sample.** 1996Q1–2026Q2, 122 quarters, for every equation except the CPI-ATE bridge (2004Q2–) and the reference reaction function (2004Q1–). The quarterly hourly wage from the national accounts (StatBank 09175) starts in 1995Q1 and binds; the originals start in 1966–1979. The same equations on 2001Q1– are reported beside the defaults.
- **Wage equation in four-quarter differences.** The quarterly-difference form of BJN2003 eq 18 / BN2008 eq 39 is replaced by the annual-difference form of NAM2026 eq 3.33 (Table 5.25): Δ₄w on (Δ₄p₋₁ − π̄), Δ₄z, Δ₄u and the EqCM lagged four quarters. The national-accounts hourly wage has a seasonal swing of about ±11% (holiday pay, hours); on this sample the quarterly form leaves a residual standard error of 3.1%, residual autocorrelation (AR 1–5 p < 0.001) and wrong-signed price terms, while the annual-difference form gives 2.3% and clean residuals. Both are reported.
- **Wage and productivity variables.** Hourly wages = wages and salaries ÷ employees' hours, Mainland Norway (09175); τ1 = ln(wage costs/wages) from SSB's seasonally adjusted series (the unadjusted ratio has a ±2 pp seasonal). Productivity z = value added per hour at basic prices (09171/09175), not trend-filtered. Both share the hours series in the denominator, which is one reason the Δ₄z coefficient is near one.
- **Unemployment.** The registered rate, as in BN2008 (NAM2026 uses the LFS rate in the wage equation): SSB/NAV unadjusted to 2014Q4, Norges Bank's seasonally adjusted NAV history from 2015Q1, so the unemployment equation uses seasonal dummies only up to 2014Q4. The LFS alternative is reported; its residuals are better behaved.
- **Import prices.** The deflator of traditional-goods imports from the quarterly national accounts (09190), in both the price EqCM and the import-price equation; the total-import deflator (ships, platforms, services) fits worse and is reported as the alternative. Pass-through is estimated (BN2008 eq 37 form), not the identity pi = v + pf of BJN2003.
- **Foreign prices.** pf = euro-area producer prices (Eurostat, 2000Q1–) extended backwards with the German PPI; p* = euro-area HICP (1996Q1–) extended with the German CPI. No trade-weighted index (NAM's PPIKONK/PCKONK are built from proprietary country series).
- **Exchange rate.** Norges Bank's I-44 (import-weighted, up = weaker krone). The default equation has no level term, as in NAM2026 Table 5.44: on this sample the BN2008 eq 36 PPP/real-rate term has the wrong sign and is insignificant (+0.004, t 0.6, against −0.042 (t −3.5) on 1994–2007). The BN2008 version is estimated and can be switched on ("PPP anchor"); without it the model has no long-run anchor for the real exchange rate, and the forecast inherits the drift implied by the interest-rate paths.
- **Energy prices.** A composite of CPI 04.5 (electricity, gas, other fuels; weight 0.63) and 07.2.2 (fuels and lubricants; 0.37), StatBank 14700 from 2000Q3, backcast to 1995 from ln(CPI) − ln(CPI excl. energy) with an estimated energy share of 0.072. BN2008 used a single CPI energy index.
- **Oil.** A linear Δoil term (BN2008 eq 36, NAM2026 Table 5.44) instead of BJN2003's smooth-transition oil terms; Brent from the World Bank Pink Sheet.
- **Interest rates.** R = Norges Bank's sight deposit rate (D-loan rate before 1991); RS = 3-month NIBOR (OECD); R* = 3-month EURIBOR (German rate before 1994). BJN2003/BN2008 use the 3-month rate as the instrument; here the rules set R and RS follows the money-market equation.
- **Indirect taxes.** τ3 = ln(CPI) − ln(CPI-AT), available from 2003Q1 and set to zero before; η = 1 imposed as in BJN2003.
- **Output gap.** Hodrick–Prescott (λ = 1600) on log mainland GDP over the whole sample; in forecasts the trend is continued at its mean growth of the last ten years, so the gap is y − trend.
- **No credit, house-price or bond-rate equations.** The BN2008 credit channel and the ABE2005 house-price and equity rules are omitted; only FLX, SM and the estimated reaction function are offered, the last for reference (NAM2026 §3.10 treats the policy rate as exogenous).
- **Inflation target.** π̄ = 2.5 to 2017Q4, 2.0 from 2018Q1, in the rules and in the wage term; ABE2005 and BN2008 use 2.5 throughout.
- **Estimator.** OLS equation by equation (NAM2026 §5.1 practice) where the originals use FIML for the wage–price block. No contemporaneous endogenous regressor remains in the wage equation; the price equation conditions on Δpi and Δpe; the residual correlation matrix is reported.
- **Dummies.** Covid impulses 2020Q1–2020Q4 were tried in the exchange-rate, unemployment, output and money-market equations and kept where |t| ≥ 2 (the kept ones are listed under each equation); UKRW (2022Q1) was tried in the price equation and not kept (t 0.7). None of the 1970s–1990s dummies of the originals falls in the sample. The 2021–23 inflation burst is left to the equations.
- **Long-run coefficients.** Imposed from the papers (γ_u = 0.1, ϕ = 0.4, η = 1; 0.12 in the exchange-rate term; 0.9/0.16/0.06 in the output term) with free estimates on the dashboard sample reported beside them. The free wage-curve coefficient has the wrong sign on 1996–2026 (the labour share fell while unemployment was low in 2022–24), the free price weights are 0.5/0.5 with homogeneity 0.99, and the free output long run has an implausible sign on the real exchange rate.
- **Simulation.** Deterministic dynamic simulation; forecast bands from 500 bootstrap draws of the residual vectors (no coefficient uncertainty); exogenous assumptions listed on the page; the policy rate follows Norges Bank's published path unless a rule is selected. Moving a coefficient on the page re-centres that equation's constant so that its mean fit over the sample is unchanged; nothing is re-estimated in the browser.

### D.8 Additions beyond the published model (2026-11-01; the page lists these as "additions")

- **Forecasting record.** A rolling pseudo-out-of-sample evaluation in the design of Eitrheim, Husebø and Nymoen (1999) and Eitrheim, Jansen and Nymoen (2002): from every origin 2007Q1–2026Q1 the equations are re-estimated on the data to the origin (expanding window, same specification and dummy rule) and the system is simulated eight quarters ahead conditional on the actual exogenous variables and policy rate. Compared with the same system with every level term dropped (the dVAR of EHN1999), an intercept-corrected version (each equation's last residual carried through the horizon), a no-change forecast and a univariate AR(4); RMSFE, bias and Diebold–Mariano tests (HAC, Harvey–Leybourne–Newbold), with and without the Covid target quarters 2020Q1–2021Q4. Current data vintage, not real-time vintages, and no comparison with Norges Bank's historical projections. Script: model/forecast_eval.py.
- **Loss function for the policy-rate settings.** ABE2005 eq (10), L = V[Δ₄pu] + λV[Δ₄y] + κV[Δr], computed by stochastic simulation (500 bootstrap draws of the residual vectors, 24 quarters, identical draws under every setting) rather than by ABE's counterfactual simulation over 1995–2000; the variance is pooled over quarters and draws, and the mean squared deviation of CPI-ATE inflation from the target is shown beside it because the variance ignores a biased path. λ and κ are set on the page. The settings are ABE's FLX and SM rules with their parameters, Norges Bank's published path and the estimated reaction function; no coefficient uncertainty.
- **Equilibrium unemployment implied by the wage–price block.** u* = [μ_p + ητ3 + (1 − ϕ)(μ_w + τ1) − ϕ(p − pi)] / ((1 − ϕ)γ_u), the rate at which the imposed wage curve and price mark-up hold at the same time (BJN2003 §2.3; Bårdsen, Eitrheim, Jansen and Nymoen 2005, ch. 6), with μ_w and μ_p the steady-state values of the two EqCM terms implied by the estimated wage and price equations at inflation on target and productivity growing at the assumed rate. Computed for the actual wedge p − pi and tax rates 1996Q1–2026Q2 and for whatever coefficients are set on the page. It is the wage-share-consistent rate, not a NAIRU estimate: with γ_u = 0.1 it moves 0.4/(0.6·0.1) = 6.7% of its level for every 1% change in the real import price.
- **Indicator saturation.** Impulse-indicator saturation (two blocks) and step-indicator saturation (four blocks) at α = 0.01 with backward elimination (Hendry, Johansen and Santos 2008; Castle, Doornik and Hendry 2012) on every core equation without its hand-picked Covid dummies, so that the data locate outliers and level shifts; retained dates, σ̂ before and after, and the shifts in the estimated coefficients are reported beside the hand-picked dummies. A split-half implementation in Python, not Autometrics; no joint IIS+SIS and no selection over the regressors. Script: model/robustness.py.
- **Super-exogeneity tests.** Hendry and Santos (2010): IIS and SIS on AR(4) marginal models of the policy rate, the exchange rate and each equation's conditioning variables; the retained indicators are added to the conditional equation and tested jointly by F. Applied to the wage, price, import-price, unemployment and output equations against (i) their conditioning variables and (ii) the policy-rate and exchange-rate processes, the latter being the Lucas-critique check of BEJN2005 ch. 9. Power depends on the breaks the marginal models reveal.
- **New Keynesian Phillips curve and encompassing.** The hybrid NKPC of Galí and Gertler, estimated by 2SLS with lags as instruments (Newey–West standard errors, Sargan test, first-stage F), with the wage share and the output gap as forcing variables, and the two encompassing tests of Bårdsen, Jansen and Nymoen (2004, Oxford Bulletin): the NKPC with the EqCM's variables added (does the lead survive?) and the EqCM with the instrumented lead added (does the lead add anything?). Quarterly CPI inflation with seasonals; the Wald test of the EqCM block is in the homoskedastic F form.
- **Recursive cointegration.** Johansen trace statistics and the first cointegrating vector of the wage system (w − p, z, u) and the price system (p − τ3, w + τ1 − z, pi) re-estimated on samples ending at every quarter from 2005Q4 (the Z-representation of Hansen and Johansen 1999), shown as ratios to the 5% critical values and as coefficient paths; the critical values ignore the de-seasonalisation and the short samples.
- **Coefficient uncertainty of the +100 bp responses.** Parametric bootstrap: in each of 1000 draws every estimated equation's coefficients are drawn from its OLS sampling distribution (Cholesky factor of the covariance; imposed long-run coefficients fixed; draws independent across equations, so cross-equation covariance is ignored), the baseline and the shocked path are simulated with the same draw and the difference collected; 25–75% and 5–95% ranges, exogenous-rate case, recomputed in the browser for other coefficient settings. Residual bootstrap would give no width because the system is linear in logs.
- **2SLS checks.** For the equations with a contemporaneous endogenous regressor (price: Δpi; import prices: Δv; unemployment: Δy), 2SLS with lagged and exogenous instruments and Newey–West standard errors beside OLS, with the first-stage F and a Durbin–Wu–Hausman test (control-function t). The originals' FIML for the wage–price block is not reproduced.

---

## Part E. Open questions for the owner

1. **Which unemployment rate in the wage EqCM**: registered (BN2008, longest series) or LFS (NAM2026)? And should the
   programme participants be added (BJN's UTOT) where NAV/StatBank provide "bruttoledighet"?
2. **Impose or estimate the long-run coefficients?** The specification imposes γ_u = 0.1 and ϕ = 0.4 (BJN Panel 4). NAM2026
   finds 0.12 (manufacturing) and 0.38 (CPI vs import prices incl. taxes). Should the page default to the imposed values with
   the free estimates as a check (as written), or the reverse?
3. **Wage concept**: hourly wages (BJN) or hourly wage costs (BN2008, NAM2026's ECM uses WCFP1)? With T1 in the price EqCM
   and γ_T1 = 0 in the wage level (Panel 4) the two coincide in the long run only if T1 is constant. Default: wages, with T1
   from 09175 in the price relation; alternative: wage costs throughout, which removes T1 from the system.
4. **Aggregate (BJN/BN2008) or wage-leader structure (NAM2026)?** The minimal system is aggregate (mainland). A manufacturing
   wage-leader equation (eq 3.33–3.34) with followers is possible from 09175/09171 by industry but doubles the equations.
5. **Sample start** 1995Q1/1996Q1 (data-limited) vs 2001Q1 (regime-limited); and whether to show both.
6. **Policy rate vs money-market rate as instrument** in the rules; and whether the estimated reaction function should be shown
   at all given NAM2026's own verdict that it is unstable after 2008Q4 and not part of the operative model.
7. **Inflation target in the rules**: 2.5 → 2.0 switch at 2018Q1 (as written) or a constant 2.0 (or 2.5)?
8. **Covid handling**: impulse dummies (NAM2026 practice) vs excluding 2020Q2–2021Q1 from estimation.
9. **Foreign prices**: fixed-weight OECD-based trading-partner PPI/CPI (closest to PPIKONK/PCKONK) vs euro-area indices
   (simplest, one source). The data script builds the fixed-weight index if the OECD API answers; the fallback is the euro area.
10. **Output gap**: HP(1600) on mainland GDP (BJN App. B) — with the end-point problem on the forecast horizon — or output
    growth in the rules (ABE2005 fn. 5)? Default: growth in the rules, HP gap in the price equation.
11. Whether to display the NAM2026 manufacturing wage equation (3.34) re-estimated on the dashboard's data as a side panel,
    since it is the authors' current specification, even though the dashboard's core follows the 2003/2008 aggregate form.
12. Whether the owner can obtain the OUP book chapters 6, 9 and 10 (or the EViews program file of NAM, which defines the
    dummies CPIDUM, PBDUM, WFP1DUM) so that the chapter-level citations can be checked against the book text rather than
    against the authors' working papers.

---

## Part F. Cross-checks: NAM's own forecasts and Norges Bank's projections

Collected 2026-10-31 into `nam_forecasts.json` (10 publications, each with URL, date, horizon, variables, exogenous
assumptions and a `verified` flag) and `norges_bank_projections.json` (MPR 3/26, parsed from Norges Bank's xlsx). The
dashboard will plot its own dynamic-simulation path next to these two, each labelled with its publication date and
forecast origin.

### F.1 Do Bårdsen and Nymoen still publish NAM forecasts? Essentially no, not under their own name.

- **normetrics.no**: the last forecast posts are from May–June 2017 (mainland GDP growth about 2% for 2017, 30 May 2017;
  registered unemployment 2.7% in 2017Q2, 3 June 2017; house prices 7.4 / 0.6 / 0.7 / 1.9% for 2017–2020 under the MPR 1/17
  rate path, 21 June 2017), each with a fan chart (70% bands) from NAM. The last reports are Rapport 1/2019 (municipal
  wages 2019–2023, for KS) and Rapport 2/2019 (pension assumptions 2019–2035 for KLP, five-year averages of CPI inflation,
  wage growth and the 5-year yield, e.g. wages 3.38% p.a. 2026–30, 3.64% 2031–35; 5-year yield 3.70% 2031–35). Posts since
  2025 are research notices; the NAM*.pdf uploads of 2025–2026 are successive versions of the model documentation, not
  forecast reports. One orphaned image, `wp-content/uploads/2025/12/fan_rnb.jpg` (uploaded 18 Dec 2025, linked from no
  page), is a "NAM forecast with estimated 90% uncertainty interval" for the policy rate against the MPR 3/2025 path: the
  NAM mean falls from about 4.3 (2025Q3) to a trough near 3.7 in mid-2026 and then runs flat at 3.8–3.85 to 2028, with a
  90% band of roughly 2.5–5.1 by 2028 (chart-read, approximate; flagged as such in the JSON).
- **Nymoen (UiO/NVA)**: "Makroøkonomiske prognoser 2013-2016" (KLP conference, 2012), "NAM ... Om store prognosefeil"
  (Ministry of Finance model committee, 2015), "NAM-prognoser januar 2016" (Ministry of Finance seminar) are lecture records
  without files (checked through the NVA API).
- **Bårdsen (NTNU)**: publication lists only. **Norges Bank Watch**: no edition authored by either.
- **Where NAM forecasts do appear**: (i) **LO's Samfunnsnotat "Konjunkturutsiktene"**, explicitly produced with NAM
  ("LO/NAM"): nr. 1/2026 (March 2026) and nr. 3/2026 (May 2026), annual tables 2025–2028 copied in full into the JSON;
  (ii) Finanstilsynet's *Finansielt utsyn* / stress tests, which use NAM-FT (NAM plus a bank module) for baseline and stress
  scenarios (2017–, incl. 2025 and June 2026) — noted, not transcribed; (iii) Samfunnsøkonomisk Analyse, "Norsk økonomi –
  boligmarkedet til 2028" (24 Nov 2025), house-price forecasts with NAM — noted.

Latest NAM-based numbers (LO/NAM, May 2026; 2026 / 2027 / 2028): mainland GDP growth 1.5 / 1.5 / 1.3; LFS unemployment
4.5 / 4.5 / 4.5; CPI inflation 3.2 / 2.4 / 2.2; CPI-ATE 3.1 / 2.6 / 2.2; policy rate (assumed, = MPR 1/26 path) 4.2 / 4.2 / 3.7;
I-44 change −4.9 / −0.5 / 0.0 (krone stronger); household consumption 2.0 / 1.9 / 2.0; employment 0.4 / 0.5 / 0.5.
Stated exogenous assumptions: Brent 92 / 80 / 77 USD; I-44 frozen at the 1–19 April 2026 average; public demand +1.5–2%;
two rate increases in 2026 then a decline toward 3.5%. The March 2026 round had GDP 1.8 / 1.7 / 1.5, LFS 4.4 / 4.3 / 4.3,
CPI 3.0 / 2.6 / 2.4, CPI-ATE 3.1 / 2.4 / 2.2, policy rate 3.9 / 3.7 / 3.4, oil 61 / 62 / 63. (The investment rows of the May
PDF were misaligned by the text extraction; check before use. LO's tables carry no wage growth, registered unemployment
or house prices.) **How produced**: per the NAM documentation (§2.4), dynamic stochastic simulation from the forecast origin
with the exogenous variables (foreign prices and demand, foreign rates, oil, fiscal variables, the policy-rate path) set by
the user; the rate path is taken from Norges Bank's MPR; model version = the documentation vintage in force.

### F.2 How far back the NAM forecast archive goes; track record

Public material starts with the DN / Samfunnsøkonomene forecasting competition ("Norges beste spåmenn"): Bårdsen and
Nymoen won for their 2012 forecasts made with NAM (the judge noted NAM had been among the weakest for 2011); the DN
articles are paywalled so the submitted numbers could not be read, and no participation after about 2013 was found. Then the
2012–2016 lectures (no files), the 2017 normetrics posts and the 2017–2019 reports, and after 2019 only the third-party uses
above and the December 2025 fan chart. **No table of NAM forecasts against realised outcomes is published.** The evaluation
material is Bårdsen, Kolsrud and Nymoen (2017), "Forecast robustness in macroeconometric models", *Journal of Forecasting*
(DOI 10.1002/for.2459; summarised at normetrics.no/nam/nam-and-forecast-robustness-in-macroeconometric-models/ with a figure
of NAM forecasts vs actuals 2007Q1–2011Q4: the interest-rate forecasts failed after the financial crisis, the others "not so
bad"), Bårdsen, Jansen and Nymoen (2002) on inflation-forecast uncertainty, and Falch and Nymoen (2011) on the accuracy of a
forecast-targeting central bank. A track-record comparison on the dashboard is therefore limited to: the 2017 posts (three
variables, 2017–2020, now fully realised), Rapport 2/2019 (five-year averages, partly realised), and the 2026 LO/NAM tables
(to be compared with outcomes as they arrive). The dashboard should store each NAM-based table with its date so that the
archive grows from 2026 on.

### F.3 Norges Bank, Monetary Policy Report 3/2026

Published 24 September 2026 (cut-off 18 September; decision 23 September: policy rate raised from 4.25 to 4.50%, unanimous).
Report: https://www.norges-bank.no/en/news-events/publications/Monetary-Policy-Report/2026/mpr-32026/ ; data file
(all numbers below parsed from it): https://www.norges-bank.no/contentassets/1462461ecf6a423eb7bc3e89c1cb0d2b/data-mpr-3-26.xlsx.
Annual (2025 / 2026 / 2027 / 2028 / 2029): CPI 3.0 / 3.3 / 2.6 / 2.3 / 2.1; CPI-ATE 3.1 / 3.0 / 2.7 / 2.4 / 2.1; annual wages
4.9 / 4.4 / 4.0 / 3.6 / 3.4; mainland GDP 1.7 / 0.9 / 1.0 / 1.0 / 1.3; output gap 0.1 / −0.3 / −0.8 / −1.1 / −1.0; registered
unemployment 2.1 / 2.1 / 2.3 / 2.4 / 2.4; house prices 5.9 / 3.0 / 3.6 / 6.2 / 6.9; policy rate 4.3 / 4.2 / 4.6 / 4.2 / 3.7;
I-44 119.6 / 112.3 / 110 / 110 / 110. Quarterly paths from 2026Q3: policy rate 4.27, 4.51, 4.57, 4.60 (peak 2027Q2), 4.58,
4.46, 4.38, 4.28, 4.14, 3.99, 3.83, 3.70, 3.59, 3.49, 3.39, 3.28 (2030Q2); CPI 3.25, 3.46, 2.72, 2.95, 2.62, 2.24 … 1.96;
CPI-ATE 2.88, 2.76, 2.61, 2.66, 2.82, 2.73 … 1.96; output gap −0.38 → −1.10 (2028Q3) → −0.72; I-44 111.77 then 110 flat;
registered unemployment 2.05 → 2.38 (2028Q4) → 2.33. Monthly Sep–Dec 2026: CPI 3.5 / 3.8 / 3.4 / 3.2, CPI-ATE 2.9 / 2.7 /
2.8 / 2.7. Not in the file: LFS unemployment (omitted) and quarterly wage growth (annual only). Quarterly mainland GDP and
house-price growth are four-quarter growth rates derived from the published level series (flagged "derived" in the JSON).

### F.4 How the dashboard will use them

The model path (origin = last data quarter; exogenous paths: the MPR 3/26 policy-rate path or a rule, the MPR foreign
assumptions where published, oil flat or forward) is drawn next to the MPR 3/26 quarterly path and the LO/NAM May 2026
annual numbers for CPI, CPI-ATE, the policy rate, unemployment (registered vs MPR; LFS vs LO/NAM), I-44 and mainland GDP,
with the dates. When a newer MPR or LO/NAM note appears, the JSON files are extended, never overwritten, so the archive
accumulates from 2026 on.
