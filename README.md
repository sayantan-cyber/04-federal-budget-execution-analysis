# Federal Budget Execution Analysis

How well do U.S. federal agencies actually execute the budgets they are given?

## Business question

Congress grants federal agencies budget authority, but granting money is not the same as spending it well. This project measures **budget execution**: which agencies obligate and spend their full budget authority, where money lapses unspent, how execution has changed over time, and whether agencies rush obligations at fiscal year-end.

## Key metrics

| Metric | Definition |
|---|---|
| Obligation rate | Total obligated ÷ total budgetary resources |
| Outlay rate | Total outlayed ÷ total obligated |
| Unobligated balance | Budgetary resources − obligations |
| YoY execution change | Year-over-year change in obligation/outlay rates by agency |
| Q4 obligation share | Share of annual obligations recorded in the final quarter (year-end rush indicator) |

## Dataset

**USAspending.gov — Agency Budgetary Resources & Account Data**

- Publisher: U.S. Department of the Treasury, Bureau of the Fiscal Service
- Source: <https://www.usaspending.gov> · API docs: <https://api.usaspending.gov/docs/endpoints>
- License: U.S. federal public domain (17 U.S.C. § 105 — no copyright restriction)
- Access: public API (no key required) + bulk Custom Account Data download
- Full documentation: [`data/README.md`](data/README.md) · Column reference: [`docs/data_dictionary.md`](docs/data_dictionary.md)

## Methods

1. **SQL** — CTEs and window functions: agency execution rankings, YoY trends, obligation-rate tiers
2. **Python** — validation pipeline (schema checks, null audits, totals reconciliation), quarterly obligation patterns, statistical tests with effect sizes
3. **Forecasting** — quarterly obligation time series with temporal holdout, benchmarked against naive baselines
4. **Excel** — dashboard of top-15 agency execution (PivotTables, documented formulas)
5. **Power BI** — star schema (`dim_agency`, `dim_fiscal_year`, `fact_budget_execution`) with documented DAX

## Repository structure

```text
├── README.md            # this file
├── data/
│   └── README.md        # dataset documentation (raw data is gitignored; reproducible via scripts)
├── sql/                 # analysis queries (CTEs, window functions)
├── notebooks/           # Python analysis (validation, stats, forecasting)
├── visuals/             # exported charts
├── excel/               # Excel dashboard workbook + formula documentation
├── docs/
│   ├── data_dictionary.md
│   └── methodology.md
├── requirements.txt
└── .gitignore
```

## Status

🚧 **In progress.** This commit contains the project scaffold, dataset documentation, and methodology only. Analysis code lands in the next commits, and **no findings are reported until the code has actually run on the real data.**

## Limitations (known upfront)

- Figures are agency-reported financial systems data; reporting timing lags exist between obligation and outlay.
- The current fiscal year is partial-year data and is excluded from YoY comparisons.
- Bulk account-level data is requested asynchronously and processed separately from the API agency series.
- This analysis describes execution patterns; it does not evaluate whether spending was effective or appropriate.
