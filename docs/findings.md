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
10. **File B bulk layer (FY2024).** Account × program activity × object class
    breakdown: **58,282 rows × 49 columns**, 0 null obligation rows, 2,053
    negative rows (deobligations/netting — kept, documented). Total FY2024
    obligations **$9.519T**, reconciling with the agency series (78.5% ×
    ~$12.1T budgetary resources ≈ $9.5T) (`notebooks/06_fileb_analysis.py`).
11. **Three object classes dominate federal obligations.** Insurance claims and
    indemnities 32.1%, grants/subsidies/contributions 25.1%, interest and
    dividends 12.1% — the top 5 classes absorb **76.0%** of all FY2024
    obligations (`notebooks/06_fileb_analysis.py`).
12. **The single largest program activities are entitlements and debt
    service.** Federal Old-Age and Survivors Insurance Trust Fund (Direct)
    13.8%, interest on Treasury debt securities 11.9%, Medicaid vendor
    payments 6.9%, Medicare SMI/HI benefit payments ~9.5% combined
    (`notebooks/06_fileb_analysis.py`).

## Interpretation (not proven by this data)

- The year-end rush plus falling obligation rates is consistent with
  "use-it-or-lose-it" incentives, but the data cannot prove motive — only timing.
- Low single-year obligation rates at DOD/HUD partly reflect multi-year and
  no-year budget authority **by design**. Ranking "execution" without
  separating one-year from multi-year authority misleads.
- Unobligated balances are not waste by default: this dataset cannot split
  balances that **lapse** from balances that **carry forward**.
- File B (findings 10–12) shows the federal budget is overwhelmingly
  transfers, insurance, and debt service — 76% of obligations sit in 5 object
  classes. Discretionary procurement ("Equipment", "Supplies", "Other
  services") is a single-digit share. Debates about "government spending"
  that ignore this composition mislead. File B records obligation *activity*,
  not budget authority — it cannot by itself split expiring from no-year
  balances.

## Recommendations

- **For analysts reusing this work:** always split one-year vs multi-year/no-year
  authority before ranking agencies; treat sub-$100M agencies separately.
- **For oversight:** the year-end obligation spike (finding 3) is the cheapest
  place to look for low-quality rushed spending — it is large, significant,
  and persistent.
- **Next iteration of this repo:** File B (the 100k+ row layer) is now pulled
  and analyzed (findings 10–12). Next: split expiring vs no-year balances at
  the account level, and extend the forecast with policy-event indicators.

## Limitations

- Agency-reported financial systems data; restatements occur.
- Outlay rates trail obligations by construction (cash timing).
- Current FY excluded from trends (partial year).
- Findings describe patterns; they do not judge whether spending was effective.
