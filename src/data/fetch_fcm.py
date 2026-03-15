"""
CFTC FCM Financial Reports Downloader

Downloads monthly Futures Commission Merchant financial data from CFTC.
Reports include adjusted net capital, excess capital, customer segregated funds,
and cleared swap segregation for every registered FCM.

Data available: January 2022 – present (monthly).
Reports are uploaded ~2 months after the data month.
"""

import os
import time
import calendar
import requests

SAVE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 'fcm')

BASE = "https://www.cftc.gov/sites/default/files"

HEADERS = {
    'User-Agent': 'HedgeFundIndustryAnalysis admin@financialresearch.dev',
    'Accept': '*/*',
}

# CFTC uses inconsistent filename formats across years
FILENAME_PATTERNS = [
    "01%20-%20FCM%20Webpage%20Update%20-%20{month}%20{year}.xlsx",
    "01-%20FCM%20Webpage%20Update%20-%20{month}%20{year}.xlsx",
    "01%20-%20FCM%20Webpage%20Update%20-%20{month}%20{year}%20.xlsx",
]


def generate_report_months(start_year=2022, start_month=1, end_year=2026, end_month=1):
    """Generate (data_year, data_month, upload_year, upload_month) tuples."""
    months = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        upload_month = month + 2
        upload_year = year
        if upload_month > 12:
            upload_month -= 12
            upload_year += 1
        months.append((year, month, upload_year, upload_month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def download_report(data_year, data_month, upload_year, upload_month, save_dir):
    """Download a single FCM monthly report, trying multiple filename patterns."""
    out_filename = f"fcm_{data_year}_{data_month:02d}.xlsx"
    filepath = os.path.join(save_dir, out_filename)

    if os.path.exists(filepath):
        return "cached"

    month_name = calendar.month_name[data_month]

    for pattern in FILENAME_PATTERNS:
        filename = pattern.format(month=month_name, year=data_year)
        url = f"{BASE}/{upload_year}-{upload_month:02d}/{filename}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200 and len(resp.content) > 1000:
                if resp.content[:4] == b'PK\x03\x04':
                    with open(filepath, 'wb') as f:
                        f.write(resp.content)
                    return "downloaded"
        except requests.RequestException:
            continue

    # Try upload_month +/- 1 in case timing is off
    for offset in [-1, 1]:
        alt_upload_month = upload_month + offset
        alt_upload_year = upload_year
        if alt_upload_month > 12:
            alt_upload_month -= 12
            alt_upload_year += 1
        elif alt_upload_month < 1:
            alt_upload_month += 12
            alt_upload_year -= 1

        for pattern in FILENAME_PATTERNS:
            filename = pattern.format(month=month_name, year=data_year)
            url = f"{BASE}/{alt_upload_year}-{alt_upload_month:02d}/{filename}"
            try:
                resp = requests.get(url, headers=HEADERS, timeout=30)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    if resp.content[:4] == b'PK\x03\x04':
                        with open(filepath, 'wb') as f:
                            f.write(resp.content)
                        return "downloaded"
            except requests.RequestException:
                continue

    return "failed"


def fetch_all_fcm_reports():
    """Download all available FCM monthly reports."""
    os.makedirs(SAVE_DIR, exist_ok=True)

    months = generate_report_months()
    print(f"Checking {len(months)} monthly FCM reports...")

    stats = {"cached": 0, "downloaded": 0, "failed": 0}
    failed_months = []

    for i, (dy, dm, uy, um) in enumerate(months):
        result = download_report(dy, dm, uy, um, SAVE_DIR)
        stats[result] += 1

        month_name = calendar.month_name[dm]
        if result == "downloaded":
            print(f"  [{i+1}/{len(months)}] Downloaded {month_name} {dy}")
            time.sleep(0.3)
        elif result == "failed":
            failed_months.append(f"{month_name} {dy}")

    print(f"\nDone! Downloaded: {stats['downloaded']}, Cached: {stats['cached']}, Failed: {stats['failed']}")
    total_files = len([f for f in os.listdir(SAVE_DIR) if f.endswith('.xlsx')])
    print(f"Files in {SAVE_DIR}: {total_files}")

    if failed_months:
        print(f"\nFailed months ({len(failed_months)}):")
        for m in failed_months:
            print(f"  {m}")


if __name__ == '__main__':
    fetch_all_fcm_reports()
