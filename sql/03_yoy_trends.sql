-- 03_yoy_trends.sql
-- Year-over-year change in budget execution per agency (window functions).
-- Run from the repo root, e.g.:  duckdb -csv < sql/03_yoy_trends.sql

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
        END AS outlay_rate
    FROM base
),
yoy AS (
    SELECT
        *,
        LAG(obligation_rate) OVER (
            PARTITION BY toptier_code ORDER BY fiscal_year
        ) AS prev_obligation_rate,
        LAG(outlay_rate) OVER (
            PARTITION BY toptier_code ORDER BY fiscal_year
        ) AS prev_outlay_rate,
        LAG(agency_budgetary_resources) OVER (
            PARTITION BY toptier_code ORDER BY fiscal_year
        ) AS prev_resources
    FROM metrics
)
SELECT
    fiscal_year,
    abbreviation,
    agency_name,
    ROUND(obligation_rate, 4)                    AS obligation_rate,
    ROUND(obligation_rate - prev_obligation_rate, 4)
                                                AS yoy_obligation_rate_change,
    ROUND(outlay_rate, 4)                        AS outlay_rate,
    ROUND(outlay_rate - prev_outlay_rate, 4)     AS yoy_outlay_rate_change,
    ROUND(
        (agency_budgetary_resources - prev_resources)
        / NULLIF(prev_resources, 0), 4
    )                                           AS yoy_resources_change
FROM yoy
WHERE prev_obligation_rate IS NOT NULL  -- drop first year per agency (no prior)
ORDER BY yoy_obligation_rate_change DESC;
