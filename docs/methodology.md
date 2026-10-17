# Methodology

## Analysis plan

### 1. Validation (Python, `notebooks/01_validation.py`)
- Schema conformance: expected columns, types, no silent renames
- Null audit on all measure columns; negative-value checks on dollar amounts
- Reconciliation: agency obligations/outlays vs. reported government-wide totals
- Fiscal-year completeness: flag partial current year, exclude from YoY

### 2. Core execution analysis (SQL, `sql/`)
- `01_agency_execution.sql` — obligation rate, outlay rate, unobligated balances per agency × FY (CTEs)
- `02_rankings.sql` — agency rankings and execution tiers via window functions (`RANK`, `NTILE`)
- `03_yoy_trends.sql` — YoY change in execution rates (`LAG`), agencies with largest improvements/declines
- `04_quarterly_pattern.sql` — quarterly obligation shares; year-end rush measurement

### 3. Statistical analysis (Python, `notebooks/02_statistics.py`)
- Correlation between agency size (budgetary resources) and execution rates, with effect sizes
- Test: do agencies exhibit a Q4 obligation rush? (paired comparison of Q4 share vs. uniform baseline, with effect size)
- All tests report assumptions checked and limitations; no causal claims from correlations

### 4. Forecasting (Python, `notebooks/03_forecast.py`)
- Quarterly obligation time series for top agencies
- Temporal holdout: train on earlier quarters, evaluate on the most recent 4
- Models benchmarked against naive (repeat-last-quarter) baseline; error reported as MAPE/MAE

### 5. Excel dashboard (`excel/`)
- Top-15 agency execution table: PivotTables, documented formulas, conditional formatting
- Workbook built from the validated CSV extracts; every formula documented in `excel/formulas.md`

### 6. Power BI (`powerbi/` to be added)
- Star schema: `dim_agency`, `dim_fiscal_year`, `fact_budget_execution`
- DAX measures: Obligation Rate, Outlay Rate, Unobligated Balance, YoY Execution Change — each documented with its formula

## Honesty rules

- Findings are written only after code runs on real data.
- Facts, interpretation, and recommendations are kept in separate sections.
- Limitations are documented alongside every result, not in an appendix nobody reads.
