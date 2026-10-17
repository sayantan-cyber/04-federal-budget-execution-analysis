"""
Validate the downloaded USAspending agency data before any analysis trusts it.

Checks: schema conformance, null audit, negative amounts, FY completeness,
totals reconciliation, obligation-rate sanity, cumulative-period monotonicity.

Usage:  python notebooks/02_validation.py
Exits non-zero if any HARD check fails.
"""

import json
import sys
from pathlib import Path

import duckdb

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
YEAR_CSV = RAW / "agency_budgetary_resources.csv"
PERIOD_CSV = RAW / "agency_obligation_periods.csv"
EXPECTED_FYS = list(range(2017, 2025))

failures, warnings = [], []


def check(name, condition, detail="", hard=True):
    status = "PASS" if condition else ("FAIL" if hard else "WARN")
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        (failures if hard else warnings).append(name)


def main():
    for p in (YEAR_CSV, PERIOD_CSV):
        check(f"file exists: {p.name}", p.exists(), f"missing {p}", hard=True)
    if failures:
        return 1
    con = duckdb.connect()

    # 1. schema conformance (DESCRIBE returns (name, type, ...); name is r[0])
    year_cols = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{YEAR_CSV}'").fetchall()}
    expected = {"toptier_code", "agency_name", "abbreviation", "fiscal_year",
                "agency_budgetary_resources", "agency_total_obligated",
                "agency_total_outlayed", "total_budgetary_resources"}
    check("year schema has expected columns", expected <= year_cols,
          f"missing {expected - year_cols}")
    period_cols = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{PERIOD_CSV}'").fetchall()}
    check("period schema has expected columns",
          {"toptier_code", "fiscal_year", "period", "obligated"} <= period_cols)

    n_year = con.execute(f"SELECT COUNT(*) FROM '{YEAR_CSV}'").fetchone()[0]
    n_agencies = con.execute(f"SELECT COUNT(DISTINCT toptier_code) FROM '{YEAR_CSV}'").fetchone()[0]
    print(f"\n  rows: {n_year} agency-years across {n_agencies} agencies")
    check("non-trivial row count", n_year >= n_agencies * len(EXPECTED_FYS) * 0.9,
          f"only {n_year} rows")

    # 2. null audit on key measures — small agencies/temporary commissions
    #    (e.g. 400 Years of African-American History Commission) report nulls;
    #    they are documented and excluded from rate calculations, not dropped.
    nulls = con.execute(f"""
        SELECT COUNT(*) FROM '{YEAR_CSV}'
        WHERE agency_budgetary_resources IS NULL
           OR agency_total_obligated IS NULL
           OR agency_total_outlayed IS NULL
    """).fetchone()[0]
    check("no nulls in key measures", nulls == 0, f"{nulls} rows with nulls (small agencies; excluded from rates)",
          hard=False)

    # 3. negative dollar amounts — legitimate federal accounting: offsetting
    #    collections can make net obligations/outlays negative (e.g. FDIC
    #    insurance premiums). Documented, not treated as errors.
    negs = con.execute(f"""
        SELECT COUNT(*) FROM '{YEAR_CSV}'
        WHERE agency_budgetary_resources < 0 OR agency_total_obligated < 0
           OR agency_total_outlayed < 0
    """).fetchone()[0]
    check("no negative dollar amounts", negs == 0,
          f"{negs} rows negative (offsetting collections, e.g. FDIC)", hard=False)

    # 4. FY completeness per agency
    missing = con.execute(f"""
        WITH want AS (
            SELECT DISTINCT y.toptier_code, f.fy
            FROM (SELECT DISTINCT toptier_code FROM '{YEAR_CSV}') y
            CROSS JOIN (SELECT UNNEST({EXPECTED_FYS}) AS fy) f
        )
        SELECT COUNT(*) FROM want
        WHERE (toptier_code, fy) NOT IN
              (SELECT toptier_code, fiscal_year FROM '{YEAR_CSV}')
    """).fetchone()[0]
    check("every agency has all FY2017-2024", missing == 0,
          f"{missing} agency-year gaps", hard=False)

    # 5. totals reconciliation: government-wide total must be constant within an FY,
    #    and the sum of agency resources should approximate it
    rec = con.execute(f"""
        SELECT fiscal_year,
               COUNT(DISTINCT total_budgetary_resources) AS distinct_totals,
               SUM(agency_budgetary_resources) AS sum_agency,
               MAX(total_budgetary_resources) AS reported_total
        FROM '{YEAR_CSV}' GROUP BY fiscal_year ORDER BY fiscal_year
    """).fetchall()
    for fy, distinct_totals, sum_agency, reported_total in rec:
        check(f"FY{fy}: single reported government total", distinct_totals == 1,
              f"{distinct_totals} distinct totals", hard=False)
        if reported_total:
            diff = abs(sum_agency - reported_total) / reported_total
            check(f"FY{fy}: agency sum reconciles to reported total (<0.1% diff)",
                  diff < 0.001, f"diff={diff:.4%}", hard=False)

    # 6. obligation-rate sanity: obligations should not exceed budgetary resources
    over = con.execute(f"""
        SELECT COUNT(*) FROM '{YEAR_CSV}'
        WHERE agency_budgetary_resources > 0
          AND agency_total_obligated / agency_budgetary_resources > 1.001
    """).fetchone()[0]
    check("obligations <= budgetary resources", over == 0,
          f"{over} rows exceed 100.1%", hard=False)

    # 7. period cumulative obligations non-decreasing within agency x FY
    decreases = con.execute(f"""
        SELECT COUNT(*) FROM (
            SELECT toptier_code, fiscal_year, period, obligated,
                   LAG(obligated) OVER (PARTITION BY toptier_code, fiscal_year
                                       ORDER BY period) AS prev
            FROM '{PERIOD_CSV}'
        ) WHERE prev IS NOT NULL AND obligated < prev
    """).fetchone()[0]
    check("cumulative obligations never decrease within FY", decreases == 0,
          f"{decreases} decreases", hard=False)

    # download log cross-check
    log_path = RAW / "download_log.json"
    if log_path.exists():
        log = json.loads(log_path.read_text())
        check("download log reports zero errors", len(log.get("errors", [])) == 0,
              f"{len(log.get('errors', []))} errors logged")

    print(f"\nValidation complete: {len(failures)} FAILED, {len(warnings)} warnings")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
