"""
Build dashboard.xlsx with native Excel charts (xlsxwriter).

Sheets:
  - 'Raw Data'           agency x FY execution table (validated rows only)
  - 'Aggregated Metrics' government-wide KPIs per FY + top-15 agencies FY2024
  - 'Dashboard'          FY2024 KPI cards + 3 embedded native Excel charts

Usage:  python notebooks/07_generate_excel_dashboard.py   (run from repo root)
Output: excel/dashboard.xlsx
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "excel" / "dashboard.xlsx"
BN = 1e9


def load():
    df = pd.read_csv(RAW / "agency_budgetary_resources.csv")
    v = df[(df["agency_budgetary_resources"] > 0)
           & df["agency_total_obligated"].notna()
           & df["agency_total_outlayed"].notna()].copy()
    v["obligation_rate"] = v["agency_total_obligated"] / v["agency_budgetary_resources"]
    v["outlay_rate"] = (v["agency_total_outlayed"]
                        / v["agency_total_obligated"].where(
                            v["agency_total_obligated"] > 0))
    v["unobligated"] = (v["agency_budgetary_resources"]
                        - v["agency_total_obligated"])
    return v


def main():
    v = load()
    govt = (v.groupby("fiscal_year")
             .agg(resources=("agency_budgetary_resources", "sum"),
                  obligated=("agency_total_obligated", "sum"),
                  outlayed=("agency_total_outlayed", "sum"))
             .reset_index())
    govt["obligation_rate"] = govt["obligated"] / govt["resources"]
    govt["outlay_rate"] = govt["outlayed"] / govt["obligated"]
    govt["unobligated"] = govt["resources"] - govt["obligated"]
    fys = govt["fiscal_year"].tolist()
    n_fy = len(fys)

    top15 = (v[v["fiscal_year"] == fys[-1]]
             .nlargest(15, "agency_budgetary_resources")
             [["abbreviation", "agency_name", "agency_budgetary_resources",
               "agency_total_obligated", "obligation_rate", "unobligated"]])

    with pd.ExcelWriter(OUT, engine="xlsxwriter") as writer:
        wb = writer.book
        # ---- formats ----
        title_fmt = wb.add_format({"bold": True, "font_size": 16,
                                   "font_color": "#1F3864"})
        sub_fmt = wb.add_format({"bold": True, "font_size": 12,
                                 "font_color": "#2E75B6"})
        hdr_fmt = wb.add_format({"bold": True, "bg_color": "#1F3864",
                                 "font_color": "white", "border": 1})
        money_fmt = wb.add_format({"num_format": '$#,##0.0,, "B"', "border": 1})
        pct_fmt = wb.add_format({"num_format": "0.0%", "border": 1})
        kpi_lbl = wb.add_format({"bold": True, "font_size": 11})
        kpi_money = wb.add_format({"num_format": '$#,##0.0,, "B"',
                                   "font_size": 14, "bold": True,
                                   "font_color": "#1F3864"})
        kpi_pct = wb.add_format({"num_format": "0.0%", "font_size": 14,
                                 "bold": True, "font_color": "#1F3864"})
        note_fmt = wb.add_format({"italic": True, "font_color": "#595959",
                                  "font_size": 9})

        # ---- 1. Raw Data ----
        raw = v[["fiscal_year", "abbreviation", "agency_name",
                 "agency_budgetary_resources", "agency_total_obligated",
                 "agency_total_outlayed", "obligation_rate", "outlay_rate",
                 "unobligated"]].copy()
        for c in ["agency_budgetary_resources", "agency_total_obligated",
                  "agency_total_outlayed", "unobligated"]:
            raw[c] = raw[c] / BN
        raw.columns = ["FY", "Abbrev", "Agency", "Resources ($B)",
                       "Obligated ($B)", "Outlayed ($B)", "Obligation Rate",
                       "Outlay Rate", "Unobligated ($B)"]
        raw.to_excel(writer, sheet_name="Raw Data", index=False)
        ws = writer.sheets["Raw Data"]
        for col, w in zip(range(9), [8, 10, 42, 15, 15, 14, 15, 12, 16]):
            ws.set_column(col, col, w)
        for c in range(9):
            ws.write(0, c, raw.columns[c], hdr_fmt)
        ws.conditional_format(1, 6, len(raw), 6,
                              {"type": "cell", "criteria": "<",
                               "value": 0.9, "format":
                               wb.add_format({"bg_color": "#FFC7CE"})})
        ws.freeze_panes(1, 0)
        ws.autofilter(0, 0, len(raw), 8)

        # ---- 2. Aggregated Metrics ----
        ws2 = wb.add_worksheet("Aggregated Metrics")
        writer.sheets["Aggregated Metrics"] = ws2
        ws2.write("A1", "Government-wide execution by fiscal year", sub_fmt)
        gcols = ["FY", "Resources ($B)", "Obligated ($B)", "Outlayed ($B)",
                 "Obligation Rate", "Outlay Rate", "Unobligated ($B)"]
        for c, h in enumerate(gcols):
            ws2.write(1, c, h, hdr_fmt)
        for r, (_, row) in enumerate(govt.iterrows(), start=2):
            ws2.write(r, 0, int(row["fiscal_year"]))
            ws2.write(r, 1, row["resources"] / BN, money_fmt)
            ws2.write(r, 2, row["obligated"] / BN, money_fmt)
            ws2.write(r, 3, row["outlayed"] / BN, money_fmt)
            ws2.write(r, 4, row["obligation_rate"], pct_fmt)
            ws2.write(r, 5, row["outlay_rate"], pct_fmt)
            ws2.write(r, 6, row["unobligated"] / BN, money_fmt)
        ws2.set_column(0, 0, 8)
        ws2.set_column(1, 3, 16)
        ws2.set_column(4, 5, 15)
        ws2.set_column(6, 6, 16)

        t2_row = n_fy + 4
        ws2.write(t2_row, 0,
                  f"Top 15 agencies by budgetary resources — FY{fys[-1]}",
                  sub_fmt)
        h2 = ["Abbrev", "Agency", "Resources ($B)", "Obligated ($B)",
              "Obligation Rate", "Unobligated ($B)"]
        for c, h in enumerate(h2):
            ws2.write(t2_row + 1, c, h, hdr_fmt)
        for r, (_, row) in enumerate(top15.iterrows(), start=t2_row + 2):
            ws2.write(r, 0, row["abbreviation"])
            ws2.write(r, 1, row["agency_name"])
            ws2.write(r, 2, row["agency_budgetary_resources"] / BN, money_fmt)
            ws2.write(r, 3, row["agency_total_obligated"] / BN, money_fmt)
            ws2.write(r, 4, row["obligation_rate"], pct_fmt)
            ws2.write(r, 5, row["unobligated"] / BN, money_fmt)
        ws2.set_column(1, 1, 42)
        # named ranges for charts: govt table rows 3..(2+n_fy) in 1-indexed Excel
        er1, er2 = 3, 2 + n_fy
        tr1, tr2 = t2_row + 3, t2_row + 2 + len(top15)  # top15 data rows

        # ---- 3. Dashboard ----
        ws3 = wb.add_worksheet("Dashboard")
        writer.sheets["Dashboard"] = ws3
        ws3.write("A1", "Federal Budget Execution — Dashboard (FY2017–2024)",
                  title_fmt)
        ws3.write("A2", "Source: USAspending.gov (U.S. Dept. of the Treasury). "
                        "Validated rows only; see data/README.md.", note_fmt)
        fy = fys[-1]
        g = govt[govt["fiscal_year"] == fy].iloc[0]
        ws3.write("A4", f"FY{fy} key figures", sub_fmt)
        kpis = [("Budgetary resources", g["resources"] / BN, kpi_money),
                ("Obligated", g["obligated"] / BN, kpi_money),
                ("Outlayed", g["outlayed"] / BN, kpi_money),
                ("Obligation rate", g["obligation_rate"], kpi_pct),
                ("Unobligated balance", g["unobligated"] / BN, kpi_money)]
        for i, (lbl, val, fmt) in enumerate(kpis, start=5):
            ws3.write(f"A{i}", lbl, kpi_lbl)
            ws3.write(f"B{i}", val, fmt)
        ws3.set_column("A:A", 24)
        ws3.set_column("B:B", 18)

        agg = "'Aggregated Metrics'"
        # Chart 1: obligation rate trend (column)
        c1 = wb.add_chart({"type": "column"})
        c1.add_series({"name": "Obligation rate",
                       "categories": f"={agg}!$A${er1}:$A${er2}",
                       "values": f"={agg}!$E${er1}:$E${er2}",
                       "fill": {"color": "#2E75B6"}})
        c1.set_title({"name": "Government-wide obligation rate by FY"})
        c1.set_y_axis({"num_format": "0%", "min": 0.7})
        c1.set_legend({"none": True})
        ws3.insert_chart("A11", c1, {"x_scale": 1.15, "y_scale": 1.0})

        # Chart 2: top-10 unobligated balances FY2024 (bar)
        top10_unob_sorted = top15.nlargest(10, "unobligated")
        c2 = wb.add_chart({"type": "bar"})
        # write a small helper range on Dashboard for the sorted top10
        ws3.write("D4", "Top-10 unobligated helper (hidden)", note_fmt)
        for i, (_, row) in enumerate(top10_unob_sorted.iterrows()):
            ws3.write(5 + i, 3, row["abbreviation"])
            ws3.write(5 + i, 4, row["unobligated"] / BN)
        c2.add_series({"name": f"Unobligated ($B), FY{fy}",
                       "categories": "=Dashboard!$D$6:$D$15",
                       "values": "=Dashboard!$E$6:$E$15",
                       "fill": {"color": "#C55A5B"}})
        c2.set_title({"name": f"Top 10 unobligated balances — FY{fy}"})
        c2.set_legend({"none": True})
        ws3.insert_chart("A27", c2, {"x_scale": 1.15, "y_scale": 1.0})

        # Chart 3: unobligated balance trend (line)
        c3 = wb.add_chart({"type": "line"})
        c3.add_series({"name": "Unobligated ($B)",
                       "categories": f"={agg}!$A${er1}:$A${er2}",
                       "values": f"={agg}!$G${er1}:$G${er2}",
                       "line": {"color": "#548235", "width": 2.5},
                       "marker": {"type": "circle"}})
        c3.set_title({"name": "Unobligated balances trend ($B)"})
        c3.set_legend({"none": True})
        ws3.insert_chart("J11", c3, {"x_scale": 1.15, "y_scale": 1.0})
        ws3.set_column("D:E", 14)

    print(f"Wrote {OUT} ({OUT.stat().st_size/1e3:.0f} KB)")


if __name__ == "__main__":
    main()
