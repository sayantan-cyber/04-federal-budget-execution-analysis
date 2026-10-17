# Excel dashboard — formula documentation

Workbook: `federal_budget_execution_dashboard.xlsx`, built from the validated
CSV extracts (`data/raw/agency_budgetary_resources.csv`,
`data/raw/agency_obligation_periods.csv`). Every non-trivial formula below
states what it computes and why.

## Sheet: `data_agency` (raw extract, one row per agency × FY)

| Column | Contents |
|---|---|
| A–H | `toptier_code, agency_name, abbreviation, fiscal_year,` `agency_budgetary_resources, agency_total_obligated,` `agency_total_outlayed, total_budgetary_resources` (pasted from CSV) |
| I | **Obligation rate** `=IF(E2>0, F2/E2, NA())` — NA (not 0) when resources are missing/non-positive, so bad rows never silently average in |
| J | **Outlay rate** `=IF(F2>0, G2/F2, NA())` |
| K | **Unobligated balance** `=E2-F2` |
| L | **YoY obligation-rate change** `=IFERROR(I2-XLOOKUP(B2&"|"&(D2-1), $B$2:$B$900&"|"&$D$2:$D$900, $I$2:$I$900), NA())` — looks up the same agency's prior FY; NA when absent |

## Sheet: `kpi` (government-wide KPIs per FY)

Assumes an FY selector in `$B$1` (data validation list 2017–2024).

- **Total budgetary resources** `=SUMIFS(data_agency!E:E, data_agency!D:D, $B$1)`
- **Total obligated** `=SUMIFS(data_agency!F:F, data_agency!D:D, $B$1)`
- **Total outlayed** `=SUMIFS(data_agency!G:G, data_agency!D:D, $B$1)`
- **Govt-wide obligation rate** `=IFERROR(B3/B2, NA())` (obligated ÷ resources)
- **Govt-wide outlay rate** `=IFERROR(B4/B3, NA())`
- **Agencies below 90% obligation** `=COUNTIFS(data_agency!D:D, $B$1, data_agency!I:I, "<0.9")`

## Sheet: `top15` (top-15 agencies by resources, selected FY)

- Agency list via `=SORTN(FILTER(...))` or a PivotTable sorted by resources desc, Top 15.
- Conditional formatting on obligation-rate column: red `<0.90`, amber `0.90–0.97`, green `>0.97`.
- Sparklines in the trend column from the FY series per agency.

## Sheet: `quarterly` (year-end rush view)

- PivotTable on the periods extract: rows = agency, columns = period, values = sum of period increments (increments computed as in `sql/04_quarterly_pattern.sql`).
- **Year-end share** `=SUM(periods 10:12 increments) / SUM(all increments)` per agency.

## Refresh procedure

1. Re-run `notebooks/01_download.py`, copy the two CSVs into `data_agency` / `data_periods`.
2. Extend all structured ranges; PivotTables → Refresh All.
3. Update the "data as of" cell and this file if any formula changed.
