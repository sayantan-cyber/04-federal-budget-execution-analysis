"""
Quarterly obligation forecast with temporal holdout.

Data reality (see docstring of 04_quarterly_pattern.sql): the API's reporting
granularity changed over time — FY2017-2021 is mostly quarterly
(periods {3,6,9,12}), FY2022-2024 mostly monthly (periods {2..12}).
To get a consistent series, quarterly increments are derived from the
cumulative obligations at periods 3, 6, 9, 12 (present in both regimes).

For each material agency: quarterly increment series -> 4-quarter holdout ->
compare naive vs seasonal-naive (lag 4) vs linear trend on MAE and sMAPE.

Usage:  python notebooks/04_forecast.py   (run from repo root)
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
HOLDOUT = 4
SEASON_LAG = 4
MIN_QUARTERS = 24
N_AGENCIES = 8
QUARTERS = [3, 6, 9, 12]


def smape(actual, forecast):
    actual, forecast = np.asarray(actual, float), np.asarray(forecast, float)
    denom = (np.abs(actual) + np.abs(forecast)) / 2
    mask = denom > 0
    return float(np.mean(np.abs(actual[mask] - forecast[mask]) / denom[mask]) * 100)


def mae(actual, forecast):
    return float(np.mean(np.abs(np.asarray(actual, float) - np.asarray(forecast, float))))


def load_quarterly(con):
    """Quarterly obligation increments per agency (derived, both regimes)."""
    df = con.execute("""
        WITH q AS (
            SELECT toptier_code, fiscal_year, period, obligated
            FROM read_csv('%s')
            WHERE period IN (3, 6, 9, 12) AND obligated IS NOT NULL
        ),
        -- keep agency-years with all four quarters for clean increments
        four_q AS (
            SELECT toptier_code, fiscal_year
            FROM q GROUP BY toptier_code, fiscal_year HAVING COUNT(*) = 4
        ),
        inc AS (
            SELECT q.*,
                   obligated - LAG(obligated) OVER (
                       PARTITION BY toptier_code, fiscal_year ORDER BY period
                   ) AS q_increment
            FROM q JOIN four_q USING (toptier_code, fiscal_year)
        )
        SELECT i.toptier_code, i.fiscal_year, i.period AS quarter_period,
               CASE WHEN i.period = 3 THEN i.obligated ELSE i.q_increment END
                   AS q_increment,
               MAX(y.agency_name) AS agency_name,
               MAX(y.abbreviation) AS abbreviation
        FROM inc i
        JOIN read_csv('%s') y USING (toptier_code, fiscal_year)
        GROUP BY i.toptier_code, i.fiscal_year, i.period, i.obligated,
                 i.q_increment
        ORDER BY i.toptier_code, i.fiscal_year, i.period
    """ % (RAW / "agency_obligation_periods.csv",
           RAW / "agency_budgetary_resources.csv")).fetchdf()
    return df


def forecast_one(y):
    train, test = y[:-HOLDOUT], y[-HOLDOUT:]
    t_train = np.arange(len(train))
    naive = np.full(HOLDOUT, train[-1])
    seas = [train[len(train) - SEASON_LAG + h - 1]
            if len(train) - SEASON_LAG + h - 1 >= 0 else np.mean(train)
            for h in range(1, HOLDOUT + 1)]
    coef = np.polyfit(t_train, train, 1)
    trend = np.polyval(coef, np.arange(len(train), len(train) + HOLDOUT))
    return {"actual": test, "naive": naive,
            "seasonal_naive": np.array(seas), "trend": trend}


def main():
    con = duckdb.connect()
    df = load_quarterly(con)

    counts = df.groupby(["toptier_code", "agency_name", "abbreviation"]).size()
    totals = (df.groupby(["toptier_code", "agency_name", "abbreviation"])
                ["q_increment"].sum())
    cand = pd.DataFrame({"n_q": counts, "total": totals}).reset_index()
    cand = cand[cand["n_q"] >= MIN_QUARTERS].nlargest(N_AGENCIES, "total")
    print(f"Quarterly series built: {df['toptier_code'].nunique()} agencies, "
          f"{len(df)} quarters")
    print(f"Forecasting {len(cand)} agencies (>= {MIN_QUARTERS} quarters each)\n")

    rows = []
    for _, a in cand.iterrows():
        y = df[df["toptier_code"] == a["toptier_code"]]["q_increment"].to_numpy(float)
        fc = forecast_one(y)
        row = {"agency": a["abbreviation"], "n_q": len(y)}
        for m in ("naive", "seasonal_naive", "trend"):
            row[f"{m}_MAE"] = mae(fc["actual"], fc[m])
            row[f"{m}_sMAPE"] = smape(fc["actual"], fc[m])
        rows.append(row)
        print(f"{a['abbreviation']:>12}: " +
              " | ".join(f"{m} sMAPE={row[f'{m}_sMAPE']:.1f}%"
                         for m in ("naive", "seasonal_naive", "trend")))

    res = pd.DataFrame(rows)
    print("\nMean across agencies:")
    summary = {m: (res[f"{m}_MAE"].mean(), res[f"{m}_sMAPE"].mean())
               for m in ("naive", "seasonal_naive", "trend")}
    for m, (m_mae, m_smape) in summary.items():
        print(f"  {m:>14}: mean MAE=${m_mae/1e9:.2f}B  mean sMAPE={m_smape:.1f}%")
    print(f"\nWinner on holdout sMAPE: {min(summary, key=lambda m: summary[m][1])}")
    print("Limits: quarterly derivation assumes no intra-quarter revisions; "
          "policy shocks unmodeled; 4-quarter holdout is short by necessity; "
          "agencies with incomplete quarter coverage are excluded.")
    return res


if __name__ == "__main__":
    main()
