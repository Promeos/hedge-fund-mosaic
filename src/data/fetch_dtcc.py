"""
DTCC Swap Data Repository Downloader

Downloads daily cumulative swap reports from DTCC's Public Price Dissemination API.
Covers 5 asset classes: Rates, Credits, Commodities, Equities, Forex.
Data available from 2025-03-13 onward (trade-level OTC derivative transactions).

Each daily file is a ZIP containing a CSV with ~30K+ individual swap trades and 110 columns
including notional amounts, counterparty types, clearing status, and pricing details.
"""

import os
import time
import requests
from datetime import datetime, timedelta

SAVE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 'dtcc')

BASE_URL = "https://pddata.dtcc.com/ppd/api/report/cumulative/cftc"

ASSET_CLASSES = ["RATES", "CREDITS", "COMMODITIES", "EQUITIES", "FOREX"]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.3.1 Safari/605.1.15',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://pddata.dtcc.com/ppd/cftcdashboard',
}

# Data starts from this date
EARLIEST_DATE = datetime(2025, 3, 13)


def generate_business_dates(start_date=None, end_date=None):
    """Generate weekday dates from start to end (DTCC reports on business days only)."""
    if start_date is None:
        start_date = EARLIEST_DATE
    if end_date is None:
        end_date = datetime.now() - timedelta(days=1)  # Yesterday (latest available)

    dates = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Monday=0 through Friday=4
            dates.append(current)
        current += timedelta(days=1)
    return dates


def download_report(date, asset_class, save_dir):
    """Download a single cumulative report for a given date and asset class."""
    filename = f"CFTC_CUMULATIVE_{asset_class}_{date.year}_{date.month:02d}_{date.day:02d}.zip"
    filepath = os.path.join(save_dir, filename)

    if os.path.exists(filepath):
        return "cached"

    url = f"{BASE_URL}/{filename}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=60)
        if resp.status_code == 200 and len(resp.content) > 500:
            # Verify it's a ZIP file
            if resp.content[:2] == b'PK':
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
                return "downloaded"
            else:
                return "not_zip"
        elif resp.status_code == 404:
            return "not_found"
        else:
            return "failed"
    except requests.RequestException:
        return "failed"


def fetch_all_dtcc_reports(asset_classes=None, start_date=None, end_date=None):
    """Download all available cumulative reports."""
    os.makedirs(SAVE_DIR, exist_ok=True)

    if asset_classes is None:
        asset_classes = ASSET_CLASSES

    dates = generate_business_dates(start_date, end_date)
    total = len(dates) * len(asset_classes)
    print(f"Checking {len(dates)} dates × {len(asset_classes)} asset classes = {total} reports...")

    stats = {"cached": 0, "downloaded": 0, "not_found": 0, "failed": 0, "not_zip": 0}
    count = 0

    for date in dates:
        for asset_class in asset_classes:
            count += 1
            result = download_report(date, asset_class, SAVE_DIR)
            stats[result] += 1

            if result == "downloaded":
                print(f"  [{count}/{total}] {asset_class} {date.strftime('%Y-%m-%d')}")
                time.sleep(0.2)
            elif result == "failed":
                print(f"  [{count}/{total}] FAILED {asset_class} {date.strftime('%Y-%m-%d')}")

        # Progress every 20 dates
        if count % (len(asset_classes) * 20) == 0:
            total_files = len([f for f in os.listdir(SAVE_DIR) if f.endswith('.zip')])
            print(f"  --- Progress: {count}/{total} checked, {total_files} files on disk ---")

    print(f"\nDone! Downloaded: {stats['downloaded']}, Cached: {stats['cached']}, "
          f"Not found: {stats['not_found']}, Failed: {stats['failed']}")
    total_files = len([f for f in os.listdir(SAVE_DIR) if f.endswith('.zip')])
    print(f"Files in {SAVE_DIR}: {total_files}")


if __name__ == '__main__':
    fetch_all_dtcc_reports()
