"""
File B analysis: FY2024 account breakdown by program activity & object class.

This is the 100k+ row layer of the project — every federal account's
obligations and outlays broken down by program activity and object class.

The script is schema-defensive: it detects key columns by keyword because
USAspending occasionally renames fields between releases.

Usage:  python notebooks/06_fileb_analysis.py   (run from repo root,
        after 05_fileb_download.py has fetched the zip)
"""

import glob
import zipfile
from pathlib import Path

import duckdb

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def find_column(cols, *keywords):
    """First column whose lowercase name contains all keywords."""
    for c in cols:
        lc = c.lower()
        if all(k in lc for k in keywords):
            return c
    return None


def main():
    zips = glob.glob(str(RAW / "*AccountBreakdownByPA-OC*.zip"))
    if not zips:
        raise SystemExit("File B zip not found in data/raw/ — run 05_fileb_download.py first")
    zpath = zips[0]
    print(f"Reading {Path(zpath).name}")

    con = duckdb.connect()
    # Extract the CSV once (DuckDB's zip:// path syntax is unreliable
    # across builds) and read the extracted file.
    with zipfile.ZipFile(zpath) as z:
        csv_name = [n for n in z.namelist() if n.endswith(".csv")][0]
        csv_path = RAW / csv_name
        if not csv_path.exists():
            z.extract(csv_name, RAW)
            print(f"Extracted {csv_name} ({csv_path.stat().st_size/1e6:.1f} MB)")
    rel = f"read_csv('{csv_path}', auto_detect=true, sample_size=200000)"
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {rel} LIMIT 0").fetchall()]
    print(f"Columns ({len(cols)}):")
    for c in cols:
        print(f"  - {c}")

    n = con.execute(f"SELECT COUNT(*) FROM {rel}").fetchone()[0]
    print(f"\nRows: {n:,}")

    c_oblig = find_column(cols, "obligations_incurred")
    c_outlay = find_column(cols, "gross_outlay")
    c_oc = find_column(cols, "object_class_name") or find_column(cols, "object_class")
    c_pa = find_column(cols, "program_activity_name") or find_column(cols, "program_activity")
    c_fa = find_column(cols, "federal_account_name") or find_column(cols, "federal_account")
    print(f"\nDetected: obligations={c_oblig} | outlays={c_outlay} | "
          f"object_class={c_oc} | program_activity={c_pa} | account={c_fa}")
    if not c_oblig:
        raise SystemExit("Could not detect obligations column — inspect columns above")

    # Validation
    null_oblig = con.execute(
        f"SELECT COUNT(*) FROM {rel} WHERE \"{c_oblig}\" IS NULL").fetchone()[0]
    neg_oblig = con.execute(
        f"SELECT COUNT(*) FROM {rel} WHERE \"{c_oblig}\" < 0").fetchone()[0]
    print(f"Validation: {null_oblig:,} null obligation rows, "
          f"{neg_oblig:,} negative (deobligations/netting — kept, documented)")

    total = con.execute(
        f"SELECT SUM(\"{c_oblig}\") FROM {rel}").fetchone()[0]
    print(f"Total FY2024 obligations in file: ${total/1e12:.3f}T")

    def top10(group_col, label):
        print(f"\n--- Top 10 {label} by obligations ---")
        df = con.execute(f"""
            SELECT "{group_col}" AS name,
                   COUNT(*) AS rows,
                   SUM("{c_oblig}") AS obligations
            FROM {rel}
            GROUP BY 1 ORDER BY obligations DESC LIMIT 10
        """).fetchdf()
        df["share"] = df["obligations"] / total
        print(df.to_string(index=False,
                           formatters={"obligations": "${:,.0f}".format,
                                       "share": "{:.2%}".format}))
        return df

    if c_oc:
        oc = top10(c_oc, "object classes")
        print(f"\nTop-5 object-class concentration: {oc['share'][:5].sum():.2%} of all obligations")
    if c_pa:
        top10(c_pa, "program activities")
    if c_fa:
        top10(c_fa, "federal accounts")

    print("\nDone. Interpret with care: File B is obligation activity, not "
          "budget authority — rates vs the agency series need not match.")


if __name__ == "__main__":
    main()
