"""
Download agency budgetary resources from the USAspending API.

Source: U.S. Department of the Treasury, Bureau of the Fiscal Service
(https://www.usaspending.gov). Public domain (17 U.S.C. 105). No API key needed.

Produces (in data/raw/, gitignored):
  - agency_budgetary_resources.csv  (one row per agency x fiscal year)
  - agency_obligation_periods.csv   (one row per agency x fiscal year x period)
  - download_log.json               (run metadata for reproducibility)

Usage:  python notebooks/01_download.py
"""

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://api.usaspending.gov/api/v2"
FISCAL_YEARS = list(range(2017, 2025))  # complete fiscal years only
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "federal-budget-execution-analysis/1.0 (academic project)"})


def get_json(url, params=None, retries=4):
    """GET with exponential backoff; raises on final failure."""
    for attempt in range(retries):
        try:
            r = SESSION.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            wait = 2 ** attempt
            print(f"  retry {attempt + 1}/{retries} after {wait}s: {e}")
            time.sleep(wait)
    raise RuntimeError(f"GET failed after {retries} attempts: {url}")


def main():
    started = datetime.now(timezone.utc).isoformat()

    print("Fetching top-tier agency list...")
    agencies = get_json(f"{BASE}/references/toptier_agencies/")["results"]
    print(f"  {len(agencies)} agencies found")

    year_rows, period_rows = [], []
    errors = []
    n_calls = 0
    for i, a in enumerate(agencies, 1):
        code = a["toptier_code"]
        for fy in FISCAL_YEARS:
            try:
                d = get_json(f"{BASE}/agency/{code}/budgetary_resources/",
                             params={"fiscal_year": fy})
                n_calls += 1
                for rec in d.get("agency_data_by_year", []):
                    if rec.get("fiscal_year") != fy:
                        continue
                    year_rows.append({
                        "toptier_code": code,
                        "agency_name": a["agency_name"],
                        "abbreviation": a.get("abbreviation"),
                        "fiscal_year": fy,
                        "agency_budgetary_resources": rec.get("agency_budgetary_resources"),
                        "agency_total_obligated": rec.get("agency_total_obligated"),
                        "agency_total_outlayed": rec.get("agency_total_outlayed"),
                        "total_budgetary_resources": rec.get("total_budgetary_resources"),
                    })
                    for p in rec.get("agency_obligation_by_period") or []:
                        period_rows.append({
                            "toptier_code": code,
                            "fiscal_year": fy,
                            "period": p.get("period"),
                            "obligated": p.get("obligated"),
                        })
            except Exception as e:  # noqa: BLE001 - logged, run continues
                errors.append({"toptier_code": code, "fiscal_year": fy, "error": str(e)})
            time.sleep(0.15)  # be polite to the public API
        if i % 10 == 0:
            print(f"  {i}/{len(agencies)} agencies done")

    year_path = RAW / "agency_budgetary_resources.csv"
    period_path = RAW / "agency_obligation_periods.csv"
    with open(year_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(year_rows[0].keys()))
        w.writeheader()
        w.writerows(year_rows)
    with open(period_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(period_rows[0].keys()))
        w.writeheader()
        w.writerows(period_rows)

    log = {
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "source": "https://api.usaspending.gov/api/v2",
        "fiscal_years": FISCAL_YEARS,
        "agencies_requested": len(agencies),
        "api_calls": n_calls,
        "year_rows": len(year_rows),
        "period_rows": len(period_rows),
        "errors": errors,
    }
    with open(RAW / "download_log.json", "w") as f:
        json.dump(log, f, indent=2)

    print(f"\nWrote {len(year_rows)} agency-year rows -> {year_path}")
    print(f"Wrote {len(period_rows)} obligation-period rows -> {period_path}")
    print(f"Errors: {len(errors)}")
    if errors:
        raise SystemExit(f"FAILED with {len(errors)} download errors - see download_log.json")


if __name__ == "__main__":
    main()
