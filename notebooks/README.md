# Python analysis

Planned scripts (each runnable end-to-end, printing a validation summary):

| File | Purpose |
|---|---|
| `01_download.py` | Pull agency budgetary resources from the USAspending API; save raw JSON/CSV to `data/raw/` |
| `02_validation.py` | Schema checks, null audit, totals reconciliation, FY completeness flags |
| `03_statistics.py` | Size-vs-execution correlation, Q4-rush test, effect sizes |
| `04_forecast.py` | Quarterly obligation forecast with temporal holdout vs. naive baseline |

Every script asserts its assumptions and fails loudly instead of producing silent garbage.
