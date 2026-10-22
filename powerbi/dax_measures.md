# DAX measures — documented

All measures live in `fact_budget_execution` unless noted. `DIVIDE` is used
throughout so division by zero yields BLANK, never an error.

```dax
Total Budgetary Resources =
SUM ( fact_budget_execution[budgetary_resources] )
-- NEVER SUM total_budgetary_resources: it is the government-wide total
-- REPEATED on every row (for share calculations). If that column is loaded
-- into the model, delete it in Power Query — summing it multiplies the
-- government-wide total by the row count. Only agency-level columns get summed.

Total Obligated =
SUM ( fact_budget_execution[obligated] )

Total Outlayed =
SUM ( fact_budget_execution[outlayed] )

-- Share of available budget that agencies legally committed
Obligation Rate =
DIVIDE ( [Total Obligated], [Total Budgetary Resources] )

-- Share of committed funds actually disbursed as cash
Outlay Rate =
DIVIDE ( [Total Outlayed], [Total Obligated] )

-- Funds left uncommitted at year-end (lapse risk)
Unobligated Balance =
[Total Budgetary Resources] - [Total Obligated]

-- Year-over-year change in execution discipline, in percentage points.
-- NOTE: SAMEPERIODLASTYEAR cannot be used here. Time-intelligence functions
-- need a proper date table; dim_fiscal_year's key is an INTEGER fiscal year,
-- so SAMEPERIODLASTYEAR returns blank and the measure silently breaks.
-- This FILTER + ALL version does the same job on an integer year column.
YoY Obligation Rate Change =
VAR CurrentFY =
    SELECTEDVALUE ( dim_fiscal_year[fiscal_year] )
RETURN
    [Obligation Rate]
        - CALCULATE (
            [Obligation Rate],
            FILTER (
                ALL ( dim_fiscal_year ),
                dim_fiscal_year[fiscal_year] = CurrentFY - 1
            )
        )

-- Agencies below the 90% obligation bar (filter context aware)
Agencies Below 90 Pct =
COUNTROWS (
    FILTER (
        VALUES ( dim_agency[agency_name] ),
        [Obligation Rate] < 0.90
    )
)
```

Year-end rush (on `fact_quarterly`):

```dax
-- Share of annual obligations recorded in periods 10-12
Year End Share =
DIVIDE (
    CALCULATE (
        SUM ( fact_quarterly[period_increment] ),
        dim_period[period_key] >= 10
    ),
    SUM ( fact_quarterly[period_increment] )
)
```

Formatting: rates as %, currency as $bn (divide by 1e9 in a display measure
when needed). Every visual must use these measures — no drag-and-drop
implicit aggregations.
