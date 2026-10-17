# Data documentation

## Dataset

**USAspending.gov — Agency Budgetary Resources & Account Data**

| Item | Detail |
|---|---|
| Title | USAspending.gov Agency Budgetary Resources & Account Data |
| Source URL | <https://www.usaspending.gov> |
| API | <https://api.usaspending.gov/docs/endpoints> (public, no key required) |
| Publisher | U.S. Department of the Treasury, Bureau of the Fiscal Service |
| License | U.S. federal public domain (17 U.S.C. § 105) |
| Coverage | All top-tier federal agencies (~100), fiscal years 2017–2024 (complete years) |
| Grain (API series) | One row per agency × fiscal year, plus quarterly cumulative obligation periods |
| Grain (bulk series) | One row per federal account × program activity × object class (100k+ rows; requested via Custom Account Data download) |

## How the data is obtained (reproducible)

1. **Agency series (API):**
   - `GET /api/v2/references/toptier_agencies/` — agency list with budget authority, obligations, outlays
   - `GET /api/v2/agency/{toptier_code}/budgetary_resources/?fiscal_year={FY}` — budgetary resources, obligations, outlays, and quarterly `agency_obligation_by_period`
2. **Account series (bulk):** `POST /api/v2/download/accounts/` with fiscal-year filters → asynchronous CSV download → validated and loaded with DuckDB.

Raw downloads are **not committed** (see `.gitignore`); the download scripts reproduce them exactly.

## Known limitations

- Agency-reported data from federal financial systems; corrections and restatements occur.
- Timing lags between obligation and outlay mean outlay rates trail obligation rates by construction.
- Current fiscal year is partial and excluded from trend comparisons.
- Bulk downloads are generated asynchronously; row counts are recorded in the download log when fulfilled.
- See [`../docs/data_dictionary.md`](../docs/data_dictionary.md) for column definitions.
