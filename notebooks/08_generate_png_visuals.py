"""
Generate 5 recruiter-ready PNG charts into visuals/ (matplotlib + seaborn).

  01_yoy_execution_trends.png      govt-wide obligation & outlay rates by FY
  02_top_agencies_obligation_rate.png  top-12 agencies (FY2024) by obligation rate
  03_q4_rush_effect.png            year-end share distribution vs uniform baseline
  04_unobligated_concentration.png top-10 unobligated balances, FY2024
  05_forecast_holdout.png          HHS holdout: actual vs 3 models

Usage:  python notebooks/08_generate_png_visuals.py   (run from repo root)
"""

from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

matplotlib.use("Agg")
sns.set_theme(style="whitegrid", palette="deep")

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
VIS = ROOT / "visuals"
VIS.mkdir(exist_ok=True)
DPI = 150
SRC = "Source: USAspending.gov (U.S. Dept. of the Treasury), FY2017–2024"


def finalize(fig, title, fname):
    fig.suptitle(title, fontsize=13, fontweight="bold", y=0.98)
    fig.text(0.01, 0.005, SRC, fontsize=7, color="#666666")
    fig.tight_layout(rect=[0, 0.03, 1, 0.94])
    out = VIS / fname
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    print(f"  saved {out.name}")


def load_valid(con):
    return con.execute("""
        SELECT *, agency_total_obligated / agency_budgetary_resources AS obligation_rate,
               agency_total_outlayed / NULLIF(agency_total_obligated, 0) AS outlay_rate,
               agency_budgetary_resources - agency_total_obligated AS unobligated
        FROM read_csv('%s')
        WHERE agency_budgetary_resources > 0 AND agency_total_obligated IS NOT NULL
    """ % (RAW / "agency_budgetary_resources.csv",)).fetchdf()


def c1_yoy(con):
    df = load_valid(con)
    g = (df.groupby("fiscal_year")
           .agg(res=("agency_budgetary_resources", "sum"),
                obl=("agency_total_obligated", "sum"),
                out=("agency_total_outlayed", "sum")).reset_index())
    g["obligation_rate"] = g["obl"] / g["res"]
    g["outlay_rate"] = g["out"] / g["obl"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(g["fiscal_year"], g["obligation_rate"] * 100, marker="o",
            label="Obligation rate", linewidth=2.5)
    ax.plot(g["fiscal_year"], g["outlay_rate"] * 100, marker="s",
            label="Outlay rate", linewidth=2.5)
    ax.set_ylabel("Rate (%)")
    ax.set_xlabel("Fiscal year")
    ax.set_ylim(70, 100)
    ax.legend()
    finalize(fig, "Government-wide budget execution is drifting down",
             "01_yoy_execution_trends.png")


def c2_top_rates(con):
    df = load_valid(con)
    d = (df[df["fiscal_year"] == 2024]
         .nlargest(12, "agency_budgetary_resources")
         .sort_values("obligation_rate"))
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ["#C55A5B" if x < 0.9 else "#2E75B6" for x in d["obligation_rate"]]
    ax.barh(d["abbreviation"], d["obligation_rate"] * 100, color=colors)
    ax.axvline(90, color="red", linestyle="--", linewidth=1,
               label="90% benchmark")
    ax.set_xlabel("Obligation rate, FY2024 (%)")
    ax.legend()
    finalize(fig, "Largest agencies by obligation rate, FY2024 "
                  "(red = below 90%)",
             "02_top_agencies_obligation_rate.png")


def c3_rush(con):
    shares = con.execute("""
        WITH p AS (
            SELECT toptier_code, fiscal_year, period, obligated
            FROM read_csv('%s') WHERE obligated IS NOT NULL
        ),
        inc AS (
            SELECT *, obligated - LAG(obligated) OVER (
                PARTITION BY toptier_code, fiscal_year ORDER BY period) AS d
            FROM p
        ),
        a AS (
            SELECT toptier_code, fiscal_year,
                   SUM(CASE WHEN period >= 10 THEN d ELSE 0 END) AS ye,
                   SUM(d) AS tot, COUNT(*) AS n
            FROM inc WHERE d IS NOT NULL
            GROUP BY 1, 2
        )
        SELECT a.ye / NULLIF(a.tot, 0) AS share
        FROM a JOIN read_csv('%s') y USING (toptier_code, fiscal_year)
        WHERE a.tot > 0 AND y.agency_budgetary_resources >= 1e8 AND a.n >= 8
    """ % (RAW / "agency_obligation_periods.csv",
           RAW / "agency_budgetary_resources.csv")).fetchdf()["share"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(shares * 100, bins=20, color="#2E75B6", edgecolor="white")
    ax.axvline(3 / 11 * 100, color="red", linestyle="--", linewidth=2,
               label=f"Uniform baseline ({3/11:.1%})")
    ax.axvline(shares.median() * 100, color="darkgreen", linestyle="-",
               linewidth=2, label=f"Observed median ({shares.median():.1%})")
    ax.set_xlabel("Share of annual obligations in final 3 periods (%)")
    ax.set_ylabel("Agency-years")
    ax.legend()
    finalize(fig, "Agencies rush obligations into year-end "
                  "(n=198 agency-years)",
             "03_q4_rush_effect.png")


def c4_unobligated(con):
    df = load_valid(con)
    d = (df[df["fiscal_year"] == 2024]
         .nlargest(10, "unobligated").sort_values("unobligated"))
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(d["abbreviation"], d["unobligated"] / 1e9, color="#548235")
    ax.set_xlabel("Unobligated balance, FY2024 ($B)")
    finalize(fig, "Unobligated balances concentrate in a few large agencies",
             "04_unobligated_concentration.png")


def c5_forecast(con):
    # HHS quarterly increments, 4-quarter holdout, 3 models
    q = con.execute("""
        WITH p AS (
            SELECT toptier_code, fiscal_year, period, obligated
            FROM read_csv('%s')
            WHERE period IN (3,6,9,12) AND obligated IS NOT NULL
              AND toptier_code = '075'
        ),
        f AS (
            SELECT toptier_code, fiscal_year FROM p
            GROUP BY 1, 2 HAVING COUNT(*) = 4
        ),
        inc AS (
            SELECT p.*, obligated - LAG(obligated) OVER (
                PARTITION BY fiscal_year ORDER BY period) AS d
            FROM p JOIN f USING (toptier_code, fiscal_year)
        )
        SELECT fiscal_year, period,
               CASE WHEN period = 3 THEN obligated ELSE d END AS qinc
        FROM inc ORDER BY fiscal_year, period
    """ % (RAW / "agency_obligation_periods.csv",)).fetchdf()["qinc"].to_numpy(float)
    H = 4
    train, test = q[:-H], q[-H:]
    t = np.arange(len(train))
    fc = {"Naive": np.full(H, train[-1]),
          "Seasonal naive": np.array([train[len(train) - 4 + h - 1]
                                      for h in range(1, H + 1)]),
          "Trend": np.polyval(np.polyfit(t, train, 1),
                              np.arange(len(train), len(train) + H))}
    x = np.arange(len(q))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, q / 1e9, color="black", linewidth=2, label="Actual")
    xh = np.arange(len(train), len(train) + H)
    for name, y in fc.items():
        ax.plot(xh, y / 1e9, marker="o", linestyle="--", label=name)
    ax.axvline(len(train) - 0.5, color="gray", linestyle=":",
               label="Holdout starts")
    ax.set_xlabel("Quarter (sequential)")
    ax.set_ylabel("Obligations per quarter ($B)")
    ax.legend()
    finalize(fig, "HHS quarterly obligations: holdout forecast vs actuals",
             "05_forecast_holdout.png")


def main():
    print("Generating PNG visuals...")
    con = duckdb.connect()
    c1_yoy(con)
    c2_top_rates(con)
    c3_rush(con)
    c4_unobligated(con)
    c5_forecast(con)
    print("Done.")


if __name__ == "__main__":
    main()
