"""
CFTC Weekly Swaps Report Downloader

Downloads all weekly swap reports (2013-2026) from the CFTC archive.
Reports are Excel files (~80KB each) containing interest rate, credit, and FX swap data.

Note: No reports exist for Dec 22 2018 - Jan 26 2019 due to government shutdown.
Early reports (2013-2014) use inconsistent naming (lowercase, 2-digit years, random IDs).
"""

import os
import time
from datetime import datetime, timedelta

import requests

SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "swaps")

BASE = "https://www.cftc.gov"

# URL patterns — CFTC changed paths multiple times over the years
# Order matters: most common patterns first
URL_PATTERNS = [
    # 2024-2026 style
    "/sites/default/files/{year}-{month:02d}/CFTC_Swaps_Report_{month:02d}_{day:02d}_{year}.xlsx",
    "/sites/default/files/idc/groups/public/%40swapsreport/documents/file/CFTC_Swaps_Report_{month:02d}_{day:02d}_{year}.xlsx",
    "/sites/default/files/CFTC_Swaps_Report_{month:02d}_{day:02d}_{year}.xlsx",
    # Early years — lowercase
    "/sites/default/files/idc/groups/public/%40swapsreport/documents/file/cftc_swaps_report_{month:02d}_{day:02d}_{year}.xlsx",
    # 2-digit year variant
    "/sites/default/files/idc/groups/public/%40swapsreport/documents/file/cftc_swaps_report_{month:02d}_{day:02d}_{year_short}.xlsx",
    "/sites/default/files/idc/groups/public/%40swapsreport/documents/file/CFTC_Swaps_Report_{month:02d}_{day:02d}_{year_short}.xlsx",
    # 2019-2023 common pattern
    "/sites/default/files/{year}-{month:02d}/cftc_swaps_report_{month:02d}_{day:02d}_{year}.xlsx",
]

HEADERS = {
    "User-Agent": "HedgeFundIndustryAnalysis admin@financialresearch.dev",
    "Accept": "*/*",
}

# Government shutdown: no reports issued
SHUTDOWN_START = datetime(2018, 12, 22)
SHUTDOWN_END = datetime(2019, 1, 26)


def generate_report_dates(start_year=2013, end_year=None):
    """Generate all Monday dates (report dates) from start to current year."""
    if end_year is None:
        end_year = datetime.now().year
    dates = []
    current = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)

    while current.weekday() != 0:
        current += timedelta(days=1)

    while current <= end and current <= datetime.now():
        if SHUTDOWN_START <= current <= SHUTDOWN_END:
            current += timedelta(days=7)
            continue
        dates.append(current)
        current += timedelta(days=7)

    return dates


def download_report(date, save_dir):
    """Download a single weekly swap report, trying multiple URL patterns."""
    filename = f"CFTC_Swaps_Report_{date.month:02d}_{date.day:02d}_{date.year}.xlsx"
    filepath = os.path.join(save_dir, filename)

    if os.path.exists(filepath):
        return "cached"

    year_short = str(date.year)[-2:]

    for pattern in URL_PATTERNS:
        url = BASE + pattern.format(year=date.year, month=date.month, day=date.day, year_short=year_short)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200 and len(resp.content) > 1000:
                # Verify it's not an HTML error page
                if resp.content[:4] == b"PK\x03\x04" or resp.content[:4] == b"\x50\x4b\x03\x04":
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
                    return "downloaded"
        except requests.RequestException:
            continue

    return "failed"


def fetch_all_swaps_reports():
    """Download all available weekly swap reports."""
    os.makedirs(SAVE_DIR, exist_ok=True)

    dates = generate_report_dates()
    print(f"Checking {len(dates)} weekly report dates...")

    stats = {"cached": 0, "downloaded": 0, "failed": 0}
    failed_dates = []

    for i, date in enumerate(dates):
        result = download_report(date, SAVE_DIR)
        stats[result] += 1

        if result == "downloaded":
            print(f"  [{i + 1}/{len(dates)}] Downloaded {date.strftime('%Y-%m-%d')}")
            time.sleep(0.3)
        elif result == "failed":
            # Reports aren't always on Mondays — try nearby days
            found = False
            for offset in [1, -1, 2, -2, 3, 4, 5, 6]:
                alt_date = date + timedelta(days=offset)
                alt_result = download_report(alt_date, SAVE_DIR)
                if alt_result == "downloaded":
                    print(f"  [{i + 1}/{len(dates)}] Downloaded {alt_date.strftime('%Y-%m-%d')} (offset {offset:+d})")
                    stats["downloaded"] += 1
                    stats["failed"] -= 1
                    found = True
                    time.sleep(0.3)
                    break
                elif alt_result == "cached":
                    stats["cached"] += 1
                    stats["failed"] -= 1
                    found = True
                    break
            if not found:
                failed_dates.append(date.strftime("%Y-%m-%d"))

        # Progress update every 50
        if (i + 1) % 50 == 0:
            total_files = len([f for f in os.listdir(SAVE_DIR) if f.endswith(".xlsx")])
            print(f"  --- Progress: {i + 1}/{len(dates)} checked, {total_files} files on disk ---")

    print(f"\nDone! Downloaded: {stats['downloaded']}, Cached: {stats['cached']}, Failed: {stats['failed']}")
    total_files = len([f for f in os.listdir(SAVE_DIR) if f.endswith(".xlsx")])
    print(f"Files in {SAVE_DIR}: {total_files}")

    if failed_dates:
        print(f"\nFailed dates ({len(failed_dates)}):")
        for d in failed_dates[:20]:
            print(f"  {d}")
        if len(failed_dates) > 20:
            print(f"  ... and {len(failed_dates) - 20} more")


if __name__ == "__main__":
    fetch_all_swaps_reports()
