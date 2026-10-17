# DAX measures — documented

All measures live in `fact_budget_execution` unless noted. `DIVIDE` is used
throughout so division by zero yields BLANK, never an error.

```dax
Total Budgetary Resources =
SUM ( fact_budget_execution[budgetary_resources] )

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

-- Year-over-year change in execution discipline, in percentage points
YoY Obligation Rate Change =
[Obligation Rate]
    - CALCULATE (
        [Obligation Rate],
        SAMEPERIODLASTYEAR ( dim_fiscal_year[fiscal_year] )
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
