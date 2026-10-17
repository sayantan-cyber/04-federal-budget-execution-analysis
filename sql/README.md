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

## Known quirks these queries surfaced (documented, not hidden)

- **Rates above 100% are real source data, not bugs.** FCC shows obligation
  rates up to ~152%: the FCC funds itself largely through offsetting
  collections (e.g. spectrum auctions), which the API nets against resources.
- **FEC FY2020 shows an obligation rate of ~106x** — obligations recorded far
  in excess of that year's reported budgetary resources. Treated as a likely
  reporting artifact (multi-year/no-year authority timing), flagged wherever
  rankings are presented.
- **Small agencies dominate naive extremes.** Commissions with only 3 reported
  periods or near-zero resources produce 95%+ "year-end shares" and wild YoY
  swings. Findings focus on material agencies; small-agency rows are kept in
  the data but called out when they top a ranking.
