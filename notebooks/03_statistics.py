"""
Statistical analysis for the Federal Budget Execution project.

Test 1 — Year-end rush: do agencies obligate disproportionately in the final
         periods of the fiscal year? One-sample Wilcoxon signed-rank test of
         each agency-year's year-end obligation share against the uniform
         baseline, with rank-biserial effect size.
Test 2 — Size vs execution: does agency size predict execution rates?
         Spearman rank correlation (robust to outliers such as the FEC FY2020
         reporting artifact), with a sensitivity check excluding rates > 200%.

All tests report assumptions, effect sizes, and limitations. No causal claims.

Usage:  python notebooks/03_statistics.py   (run from repo root)
"""

import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

# Materiality filter: tiny agencies with sparse period data distort shares.
MIN_RESOURCES_USD = 100_000_000
MIN_PERIODS = 8
# Periods 2..12 observed (11 periods); "year-end" = periods 10-12 (3 periods).
UNIFORM_BASELINE = 3 / 11


def load_year_end_shares(con):
    """One row per agency-year with its year-end obligation share."""
    return con.execute("""
        WITH periods AS (
            SELECT toptier_code, fiscal_year, period, obligated
            FROM read_csv('%s')
            WHERE obligated IS NOT NULL
        ),
        increments AS (
            SELECT *,
                   obligated - LAG(obligated) OVER (
                       PARTITION BY toptier_code, fiscal_year ORDER BY period
                   ) AS inc,
                   MAX(obligated) OVER (
                       PARTITION BY toptier_code, fiscal_year
                   ) AS annual
            FROM periods
        ),
        agg AS (
            SELECT toptier_code, fiscal_year,
                   SUM(CASE WHEN period >= 10 THEN inc ELSE 0 END) AS ye_inc,
                   SUM(inc) AS total_inc,
                   COUNT(*) AS n_periods
            FROM increments
            WHERE inc IS NOT NULL
            GROUP BY toptier_code, fiscal_year
        )
        SELECT a.toptier_code, a.fiscal_year,
               a.ye_inc / NULLIF(a.total_inc, 0) AS year_end_share,
               a.n_periods,
               y.agency_name, y.abbreviation,
               y.agency_budgetary_resources
        FROM agg a
        JOIN read_csv('%s') y
          USING (toptier_code, fiscal_year)
        WHERE a.total_inc > 0
          AND y.agency_budgetary_resources >= %d
          AND a.n_periods >= %d
    """ % (RAW / "agency_obligation_periods.csv",
           RAW / "agency_budgetary_resources.csv",
           MIN_RESOURCES_USD, MIN_PERIODS)).fetchdf()


def load_execution(con):
    """Agency-year execution metrics for the size-vs-execution test."""
    return con.execute("""
        SELECT toptier_code, fiscal_year, abbreviation, agency_name,
               agency_budgetary_resources,
               agency_total_obligated / agency_budgetary_resources
                   AS obligation_rate,
               CASE WHEN agency_total_obligated > 0
                    THEN agency_total_outlayed / agency_total_obligated
               END AS outlay_rate
        FROM read_csv('%s')
        WHERE agency_budgetary_resources > 0
          AND agency_total_obligated IS NOT NULL
          AND agency_total_outlayed IS NOT NULL
    """ % (RAW / "agency_budgetary_resources.csv",)).fetchdf()


def rank_biserial(wilcoxon_z, n):
    """Rank-biserial correlation effect size from Wilcoxon z."""
    return abs(wilcoxon_z) / np.sqrt(n)


def test_year_end_rush(df):
    print("=" * 64)
    print("TEST 1 — Year-end obligation rush")
    print("=" * 64)
    print(f"Sample: {len(df)} agency-years "
          f"(resources >= ${MIN_RESOURCES_USD/1e6:.0f}M, >= {MIN_PERIODS} periods)")
    print(f"Uniform baseline year-end share: {UNIFORM_BASELINE:.4f} "
          f"(3 of 11 observed periods)")
    med = df["year_end_share"].median()
    mean = df["year_end_share"].mean()
    print(f"Observed median year-end share: {med:.4f} | mean: {mean:.4f}")

    # Wilcoxon signed-rank against the uniform baseline (one-sided: greater)
    diff = df["year_end_share"].dropna() - UNIFORM_BASELINE
    diff = diff[diff != 0]
    res = stats.wilcoxon(diff, alternative="greater")
    z = stats.norm.ppf(1 - res.pvalue)  # one-sided z from p
    r_rb = rank_biserial(z, len(diff))
    print(f"Wilcoxon signed-rank (H1: share > uniform): "
          f"statistic={res.statistic:.0f}, p={res.pvalue:.4g}")
    print(f"Effect size (rank-biserial r): {r_rb:.3f} "
          f"({'negligible' if r_rb < 0.1 else 'small' if r_rb < 0.3 else 'medium' if r_rb < 0.5 else 'large'})")
    print("Assumptions/limits: periods are reporting periods, not exact quarters; "
          "deobligations kept as negative increments; small agencies excluded by design.")
    return {"median_share": med, "p": res.pvalue, "r_rb": r_rb, "n": len(diff)}


def test_size_vs_execution(df):
    print("=" * 64)
    print("TEST 2 — Agency size vs execution rates")
    print("=" * 64)
    d = df.dropna(subset=["obligation_rate", "outlay_rate"]).copy()
    d["log_resources"] = np.log10(d["agency_budgetary_resources"])
    print(f"Sample: {len(d)} agency-years")

    for col in ["obligation_rate", "outlay_rate"]:
        rho, p = stats.spearmanr(d["log_resources"], d[col])
        print(f"Spearman log10(resources) vs {col}: rho={rho:.3f}, p={p:.4g} "
              f"(n={len(d)})")

    # Sensitivity: drop likely reporting artifacts (rate > 200%)
    d2 = d[d["obligation_rate"] <= 2.0]
    rho2, p2 = stats.spearmanr(d2["log_resources"], d2["obligation_rate"])
    print(f"Sensitivity (obligation_rate <= 200%, n={len(d2)}): "
          f"rho={rho2:.3f}, p={p2:.4g}")
    print("Note: correlation only — size does not cause execution behavior; "
          "budget structure (mandatory vs discretionary) is an unmeasured confounder.")
    return {"rho": rho, "p": p}


def main():
    con = duckdb.connect()
    shares = load_year_end_shares(con)
    exec_df = load_execution(con)
    print(f"\nLoaded {len(shares)} agency-years for rush test, "
          f"{len(exec_df)} for size test\n")
    r1 = test_year_end_rush(shares)
    print()
    r2 = test_size_vs_execution(exec_df)
    print("\nDone.")
    return r1, r2


if __name__ == "__main__":
    main()
