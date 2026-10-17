-- 01_agency_execution.sql
-- Core budget execution metrics per agency x fiscal year.
-- Run from the repo root, e.g.:  duckdb -csv < sql/01_agency_execution.sql
--
-- Filters: agencies with null or non-positive budgetary resources are excluded
-- from rate calculations (see 02_validation.py: small agencies report nulls;
-- FDIC-style offsetting collections produce negatives).

WITH base AS (
    SELECT
        toptier_code,
        agency_name,
        abbreviation,
        fiscal_year,
        agency_budgetary_resources,
        agency_total_obligated,
        agency_total_outlayed
    FROM read_csv('data/raw/agency_budgetary_resources.csv')
    WHERE agency_budgetary_resources > 0
      AND agency_total_obligated IS NOT NULL
      AND agency_total_outlayed IS NOT NULL
),
metrics AS (
    SELECT
        *,
        agency_total_obligated / agency_budgetary_resources
            AS obligation_rate,
        CASE WHEN agency_total_obligated > 0
             THEN agency_total_outlayed / agency_total_obligated
        END AS outlay_rate,
        agency_budgetary_resources - agency_total_obligated
            AS unobligated_balance
    FROM base
)
SELECT
    fiscal_year,
    abbreviation,
    agency_name,
    ROUND(agency_budgetary_resources / 1e9, 2)  AS budgetary_resources_bn,
    ROUND(agency_total_obligated / 1e9, 2)       AS obligated_bn,
    ROUND(agency_total_outlayed / 1e9, 2)        AS outlayed_bn,
    ROUND(obligation_rate, 4)                   AS obligation_rate,
    ROUND(outlay_rate, 4)                       AS outlay_rate,
    ROUND(unobligated_balance / 1e9, 2)         AS unobligated_balance_bn
FROM metrics
ORDER BY fiscal_year, obligation_rate DESC;
