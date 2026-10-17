# Power BI model

## Star schema

```text
dim_agency (1) ──< fact_budget_execution >── (1) dim_fiscal_year
                        │
                        └──── (1) dim_period (for quarterly analysis)
```

| Table | Key | Columns |
|---|---|---|
| `dim_agency` | `agency_key` (= toptier_code) | agency_name, abbreviation |
| `dim_fiscal_year` | `fy_key` (= fiscal_year, integer) | fiscal_year |
| `dim_period` | `period_key` (= period) | period |
| `fact_budget_execution` | composite | agency_key, fy_key, budgetary_resources, obligated, outlayed |
| `fact_quarterly` | composite | agency_key, fy_key, period_key, obligated_cumulative, period_increment |

Relationships are single-direction, one-to-many from dimensions to facts.
`fact_quarterly.period_increment` is precomputed exactly as in
`sql/04_quarterly_pattern.sql` (cumulative difference; negatives kept).

## Build steps

1. Power Query: load the two validated CSVs; set currency columns to Fixed
   Decimal Number; drop rows where `agency_budgetary_resources` is null.
2. Model view: create the relationships above; hide key columns from report view.
3. Add the measures in `dax_measures.md` — each is documented with its
   business meaning. No implicit measures; every visual uses explicit DAX.
4. Report pages: (1) Executive — KPI cards + obligation-rate bar chart by
   agency; (2) Trends — YoY lines; (3) Year-end rush — period-share columns.
