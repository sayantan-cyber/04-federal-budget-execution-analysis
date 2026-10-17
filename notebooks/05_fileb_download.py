"""
Download the File B (account breakdown by program activity & object class)
bulk data for FY2024 from USAspending.

The bulk download is asynchronous: this script polls the status endpoint
until the file is ready, then downloads the zip into data/raw/.

Usage:  python notebooks/05_fileb_download.py   (run from repo root)
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

STATUS_URL = ("https://api.usaspending.gov/api/v2/download/status"
              "?file_name=FY2024P01-P12_All_FA_AccountBreakdownByPA-OC_2026-10-17_H07M42S35143377.zip")
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

POLL_SECONDS = 60
MAX_POLLS = 90  # ~90 minutes


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] polling for File B bulk download...")
    for i in range(1, MAX_POLLS + 1):
        r = requests.get(STATUS_URL, timeout=30)
        r.raise_for_status()
        info = r.json()
        status = info.get("status", "unknown")
        print(f"  poll {i}: status={status} "
              f"total_rows={info.get('total_rows')} total_columns={info.get('total_columns')}")
        if status == "ready" and info.get("file_url"):
            url = info["file_url"]
            dest = RAW / url.rsplit("/", 1)[-1]
            print(f"  ready — downloading {url}")
            with requests.get(url, stream=True, timeout=300) as dl:
                dl.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in dl.iter_content(chunk_size=1 << 20):
                        f.write(chunk)
            size_mb = dest.stat().st_size / 1e6
            print(f"  saved {dest} ({size_mb:.1f} MB)")
            (RAW / "fileb_download_log.json").write_text(json.dumps({
                "finished_utc": datetime.now(timezone.utc).isoformat(),
                "file_name": dest.name,
                "size_mb": round(size_mb, 1),
                "total_rows": info.get("total_rows"),
                "total_columns": info.get("total_columns"),
                "status_url": STATUS_URL,
            }, indent=2))
            print("DONE")
            return
        if status in ("failed", "error"):
            raise SystemExit(f"bulk download failed: {info}")
        time.sleep(POLL_SECONDS)
    raise SystemExit("timed out waiting for bulk download")


if __name__ == "__main__":
    main()
