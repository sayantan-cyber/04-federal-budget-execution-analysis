-- 04_quarterly_pattern.sql
-- Within-year obligation timing: do agencies rush obligations at year-end?
--
-- The API reports CUMULATIVE obligations per period (2..12). Period increments
-- are derived; a negative increment is a deobligation (real, kept as-is).
-- "Year-end share" = increments in periods 10-12 / annual obligations.
-- Assumption documented: periods 10-12 proxy the final quarter of the FY.
--
-- Run from the repo root, e.g.:  duckdb -csv < sql/04_quarterly_pattern.sql

WITH periods AS (
    SELECT
        toptier_code,
        fiscal_year,
        period,
        obligated
    FROM read_csv('data/raw/agency_obligation_periods.csv')
    WHERE obligated IS NOT NULL
),
increments AS (
    SELECT
        *,
        obligated - LAG(obligated) OVER (
            PARTITION BY toptier_code, fiscal_year ORDER BY period
        ) AS period_increment,
        MAX(obligated) OVER (
            PARTITION BY toptier_code, fiscal_year
        ) AS annual_obligated
    FROM periods
),
shares AS (
    SELECT
        toptier_code,
        fiscal_year,
        period,
        CASE WHEN annual_obligated > 0
             THEN period_increment / annual_obligated
        END AS period_share,
        CASE WHEN period >= 10 AND annual_obligated > 0
             THEN period_increment / annual_obligated
             ELSE 0
        END AS year_end_increment_share
    FROM increments
    WHERE period_increment IS NOT NULL  -- first observed period has no prior
)
SELECT
    s.fiscal_year,
    y.abbreviation,
    y.agency_name,
    ROUND(SUM(s.year_end_increment_share), 4) AS year_end_share_p10_12,
    ROUND(AVG(s.period_share), 4)             AS avg_period_share,
    ROUND(MAX(s.period_share), 4)             AS max_single_period_share,
    COUNT(*)                                  AS periods_observed
FROM shares s
JOIN (
    SELECT DISTINCT toptier_code, abbreviation, agency_name
    FROM read_csv('data/raw/agency_budgetary_resources.csv')
) y USING (toptier_code)
GROUP BY s.fiscal_year, y.abbreviation, y.agency_name
HAVING SUM(s.year_end_increment_share) IS NOT NULL
ORDER BY year_end_share_p10_12 DESC;
