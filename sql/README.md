# SQL analysis

Queries run against the validated agency × fiscal-year dataset (loaded into DuckDB).

Planned queries:

| File | Purpose |
|---|---|
| `01_agency_execution.sql` | Obligation rate, outlay rate, unobligated balances per agency × FY (CTEs) |
| `02_rankings.sql` | Agency execution rankings and tiers (`RANK`, `NTILE`) |
| `03_yoy_trends.sql` | YoY execution change per agency (`LAG`) |
| `04_quarterly_pattern.sql` | Quarterly obligation shares; year-end rush measurement |

Style: one statement per file, CTEs named for business logic, no `SELECT *`.
