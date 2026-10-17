# Data dictionary

## Agency budgetary resources series (API)

One row per agency × fiscal year.

| Column | Type | Description |
|---|---|---|
| `toptier_code` | string | 3-digit agency identifier (e.g. `020` = Department of the Treasury) |
| `agency_name` | string | Full agency name |
| `agency_slug` | string | URL-safe agency identifier |
| `abbreviation` | string | Agency abbreviation (e.g. `TREAS`, `HHS`) |
| `fiscal_year` | integer | Federal fiscal year (Oct 1 – Sep 30) |
| `agency_budgetary_resources` | numeric (USD) | Total budgetary resources available to the agency |
| `agency_total_obligated` | numeric (USD) | Total obligations (legally committed funds) |
| `agency_total_outlayed` | numeric (USD) | Total outlays (cash actually disbursed) |
| `total_budgetary_resources` | numeric (USD) | Government-wide budgetary resources (for share calculations) |

### Quarterly obligation periods (nested per agency × fiscal year)

| Column | Type | Description |
|---|---|---|
| `period` | integer | Reporting period within the fiscal year (2–11 in observed responses) |
| `obligated` | numeric (USD) | Cumulative obligations through that period |

## Top-tier agency reference fields

`agency_id`, `congressional_justification_url`, `active_fy`, `active_fq`, `outlay_amount`, `obligated_amount`, `budget_authority_amount`, `current_total_budget_authority_amount`, `percentage_of_total_budget_authority`.

## Bulk account series (File B — documented after download)

Columns will be recorded here once the Custom Account Data download is fulfilled. Expected grain: federal account × program activity × object class, with gross outlays, obligations incurred, and unobligated balances.

## Derived metrics (computed, not sourced)

- `obligation_rate = agency_total_obligated / agency_budgetary_resources`
- `outlay_rate = agency_total_outlayed / agency_total_obligated`
- `unobligated_balance = agency_budgetary_resources - agency_total_obligated`
- `q4_obligation_share` = obligations in final periods ÷ annual obligations
