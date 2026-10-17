-- 02_rankings.sql
-- Agency execution rankings and performance tiers within each fiscal year.
-- Run from the repo root, e.g.:  duckdb -csv < sql/02_rankings.sql

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
ranked AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY fiscal_year ORDER BY obligation_rate DESC
        ) AS execution_rank,
        NTILE(4) OVER (
            PARTITION BY fiscal_year ORDER BY obligation_rate DESC
        ) AS execution_quartile  -- 1 = top 25% executors
    FROM metrics
)
SELECT
    fiscal_year,
    execution_rank,
    execution_quartile,
    abbreviation,
    agency_name,
    ROUND(obligation_rate, 4) AS obligation_rate,
    ROUND(outlay_rate, 4)     AS outlay_rate,
    ROUND((agency_budgetary_resources - agency_total_obligated) / 1e9, 2)
        AS unobligated_balance_bn
FROM ranked
ORDER BY fiscal_year, execution_rank;
