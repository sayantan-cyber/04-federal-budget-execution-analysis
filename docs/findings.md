# Findings — Federal Budget Execution Analysis

All figures below were computed from the validated USAspending dataset
(888 agency-years, 111 agencies, FY2017–2024). Code that produced each number
is referenced. Facts, interpretation, and recommendations are separated
deliberately.

## Facts

1. **Scale.** 888 agency-years across 111 agencies (FY2017–2024), 5,325
   quarterly obligation periods, 2,824 derived quarters. Zero download errors;
   validation passed with 12 documented warnings (`notebooks/02_validation.py`).
2. **Government-wide obligation rates drifted down.** 84.3% (2017) → 78.5%
   (2024). Unobligated balances rose from **$1.10T to $2.60T** over the same
   period (`sql/01_agency_execution.sql`).
3. **The year-end rush is real and large.** Median 33.3% of annual obligations
   land in the final 3 reporting periods vs 27.3% under a uniform baseline
   (n=198 agency-years; Wilcoxon p=3.4e-14; rank-biserial r=0.53, large)
   (`notebooks/03_statistics.py`).
4. **Size does not predict execution.** Agency size vs obligation rate:
   Spearman rho=-0.03, p=0.37. Vs outlay rate: rho=-0.10, p=0.004 —
   statistically detectable but operationally negligible
   (`notebooks/03_statistics.py`).
5. **Unobligated balances concentrate.** FY2024 top three: DOD $598B (69.9%
   obligated), Treasury $430B (80.5%), HHS $346B (87.9%)
   (`sql/01_agency_execution.sql`).
6. **Lowest FY2024 obligation rates among large agencies:** PBGC 25.9%, HUD
   31.2%, DOC 39.7% (`sql/02_rankings.sql`).
7. **Obligations are seasonal — and forecastable.** Seasonal-naive (same
   quarter last year) beat naive and trend models on a 4-quarter holdout
   (mean sMAPE 26.7% vs 29.5%/28.2%). SSA is highly predictable (~5% sMAPE);
   Education is volatile (~85–102%, student-loan policy swings)
   (`notebooks/04_forecast.py`).
8. **The source changed its own reporting.** USAspending shifted from quarterly
   to monthly period reporting around FY2022 — any long time series must
   harmonize granularity first (found during forecast construction).
9. **Quirks, not errors:** FCC obligation rates up to ~152% (spectrum-auction
   offsetting collections); FEC FY2020 ~106x rate (likely reporting artifact,
   excluded from headline findings); 67 null rows at tiny commissions; 5
   negative rows from net collections (FDIC).

## Interpretation (not proven by this data)

- The year-end rush plus falling obligation rates is consistent with
  "use-it-or-lose-it" incentives, but the data cannot prove motive — only timing.
- Low single-year obligation rates at DOD/HUD partly reflect multi-year and
  no-year budget authority **by design**. Ranking "execution" without
  separating one-year from multi-year authority misleads.
- Unobligated balances are not waste by default: this dataset cannot split
  balances that **lapse** from balances that **carry forward**.

## Recommendations

- **For analysts reusing this work:** always split one-year vs multi-year/no-year
  authority before ranking agencies; treat sub-$100M agencies separately.
- **For oversight:** the year-end obligation spike (finding 3) is the cheapest
  place to look for low-quality rushed spending — it is large, significant,
  and persistent.
- **Next iteration of this repo:** pull File B account-level bulk data to split
  expiring vs no-year balances (the 100k+ row layer), and extend the forecast
  with policy-event indicators.

## Limitations

- Agency-reported financial systems data; restatements occur.
- Outlay rates trail obligations by construction (cash timing).
- Current FY excluded from trends (partial year).
- Findings describe patterns; they do not judge whether spending was effective.
