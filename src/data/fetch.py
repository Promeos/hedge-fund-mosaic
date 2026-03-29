"""Data fetching functions for all external sources.

Fetches and caches data from 5 sources:
- Federal Reserve FRED (Z.1 balance sheet, VIX)
- SEC EDGAR (13F holdings, Form ADV submissions)
- CFTC Commitments of Traders (equity index futures positioning)

All data is cached to data/raw/ to avoid redundant API calls.
Rate limits: 0.2s FRED, 0.15s SEC EDGAR.
"""

import argparse
import json
import os
import re
import time
import warnings
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO

import pandas as pd
import requests
from dotenv import load_dotenv

try:
    from fredapi import Fred
except ImportError:  # pragma: no cover - exercised indirectly in test collection
    Fred = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# FRED series ID mapping for B.101.f (Balance Sheet of Domestic Hedge Funds)
HEDGE_FUND_SERIES = {
    # Assets
    "Total assets": "BOGZ1FL624090005Q",
    "Foreign currency; asset": "BOGZ1FL623091003Q",
    "Deposits; asset": "BOGZ1FL623039003Q",
    "Other cash and cash equivalents; asset": "BOGZ1FL623039013Q",
    "Money market fund shares; asset": "BOGZ1FL623034003Q",
    "Security repurchase agreements; asset": "BOGZ1FL622051003Q",
    "Total debt securities; asset": "BOGZ1FL624022005Q",
    "Treasury securities; asset": "BOGZ1FL623061103Q",
    "Corporate and foreign bonds; asset": "BOGZ1FL623063003Q",
    "Total loans; asset": "BOGZ1FL623069005Q",
    "Leveraged loans; asset": "BOGZ1FL623069503Q",
    "Other loans; asset": "BOGZ1FL623069003Q",
    "Corporate equities; asset": "BOGZ1FL623064103Q",
    "Miscellaneous assets; asset": "BOGZ1FL623093005Q",
    # Liabilities
    "Total liabilities": "BOGZ1FL624190005Q",
    "Total security repurchase agreements; liability": "BOGZ1FL622151005Q",
    "Security repurchase agreements with domestic institutions; liability": "BOGZ1FL622151013Q",
    "Security repurchase agreements with foreign institutions; liability": "BOGZ1FL622151063Q",
    "Total loans; liability": "BOGZ1FL624123005Q",
    "Loans, total secured borrowing via prime brokerage; liability": "BOGZ1FL624123035Q",
    "Loans, secured borrowing via domestic prime brokerages; liability": "BOGZ1FL623167003Q",
    "Loans, secured borrowing via foreign prime brokerages; liability": "BOGZ1FL623169533Q",
    "Loans, total other secured borrowing; liability": "BOGZ1FL624123015Q",
    "Loans, other secured borrowing from domestic institutions; liability": "BOGZ1FL623168013Q",
    "Loans, other secured borrowing from foreign institutions; liability": "BOGZ1FL623169513Q",
    "Loans, total unsecured borrowing; liability": "BOGZ1FL623168023Q",
    "Miscellaneous liabilities; liability": "BOGZ1FL623193005Q",
    # Net assets and memo items
    "Total net assets": "BOGZ1FL622000003Q",
    "Derivatives (long value)": "BOGZ1FL623098003Q",
}

SEC_HEADERS = {
    "User-Agent": "HedgeFundIndustryAnalysis admin@financialresearch.dev",
    "Accept-Encoding": "gzip, deflate",
}

HEDGE_FUND_CIKS = {
    "Citadel Advisors": "0001423053",
    "Bridgewater Associates": "0001350694",
    "Renaissance Technologies": "0001037389",
    "Point72 Asset Management": "0001603466",
    "Two Sigma Investments": "0001179392",
    "D.E. Shaw": "0001009207",
    "Millennium Management": "0001273087",
    "AQR Capital Management": "0001167557",
}

FORM_13F_DOLLAR_CUTOFF = pd.Timestamp("2022-10-17")
THIRTEENF_WINDOW_RE = re.compile(r"^13f_(?P<fund>.+)_(?P<start>\d{8})_(?P<end>\d{8})\.csv$")


def normalize_13f_holdings(df):
    """Backfill a canonical dollar-denominated value column for 13F holdings.

    The SEC changed the XML ``value`` element from thousands to nearest dollar
    in the October 17, 2022 Form 13F technical specification update. Older
    holdings need to be scaled by 1,000; newer filings should not.
    """
    if df.empty:
        return df.copy()

    out = df.copy()
    raw_col = "value_thousands" if "value_thousands" in out.columns else "value"
    if raw_col not in out.columns:
        return out

    raw_values = pd.to_numeric(out[raw_col], errors="coerce")
    if "filing_date" in out.columns:
        filing_dates = pd.to_datetime(out["filing_date"], errors="coerce")
    else:
        filing_dates = pd.Series(pd.NaT, index=out.index)

    if "value_unit" in out.columns:
        value_units = out["value_unit"].astype(str).str.lower()
        reported_in_dollars = value_units.eq("usd")
        reported_in_thousands = value_units.eq("thousands")
    else:
        reported_in_dollars = filing_dates >= FORM_13F_DOLLAR_CUTOFF
        reported_in_thousands = ~reported_in_dollars
        reported_in_thousands = reported_in_thousands.fillna(False)

    if "value_usd" not in out.columns:
        out["value_usd"] = pd.Series(index=out.index, dtype="float64")

    missing_value_usd = pd.to_numeric(out["value_usd"], errors="coerce").isna()
    out.loc[missing_value_usd & reported_in_dollars, "value_usd"] = raw_values[missing_value_usd & reported_in_dollars]
    out.loc[missing_value_usd & reported_in_thousands, "value_usd"] = (
        raw_values[missing_value_usd & reported_in_thousands] * 1000
    )

    if "value_unit" not in out.columns:
        inferred = pd.Series("unknown", index=out.index, dtype="object")
        inferred.loc[reported_in_dollars] = "usd"
        inferred.loc[reported_in_thousands] = "thousands"
        out["value_unit"] = inferred

    return out


def _select_best_13f_window(cache_dir, expected_funds=None):
    """Choose the newest complete per-fund 13F cache window available on disk."""
    if not os.path.isdir(cache_dir):
        return []

    groups = {}
    for filename in os.listdir(cache_dir):
        match = THIRTEENF_WINDOW_RE.match(filename)
        if not match:
            continue
        tags = (match.group("start"), match.group("end"))
        groups.setdefault(tags, []).append(os.path.join(cache_dir, filename))

    if not groups:
        return []

    expected_count = len(expected_funds) if expected_funds else None

    def score(item):
        (start_tag, end_tag), paths = item
        count = len(paths)
        complete = int(expected_count is not None and count >= expected_count)
        return (complete, count, end_tag, start_tag)

    _, paths = max(groups.items(), key=score)
    return sorted(paths)


def load_best_13f_holdings(cache_dir="data/raw", expected_funds=None):
    """Load the newest coherent 13F holdings snapshot available locally.

    Prefer the latest complete set of per-fund window caches over the aggregate
    ``13f_all_holdings.csv`` file, which can become stale if only the per-fund
    caches are refreshed.
    """
    per_fund_paths = _select_best_13f_window(cache_dir, expected_funds=expected_funds)
    if per_fund_paths:
        frames = [normalize_13f_holdings(pd.read_csv(path)) for path in per_fund_paths]
        return pd.concat(frames, ignore_index=True)

    aggregate_path = os.path.join(cache_dir, "13f_all_holdings.csv")
    if os.path.exists(aggregate_path):
        return normalize_13f_holdings(pd.read_csv(aggregate_path))

    processed_path = os.path.join(os.path.dirname(cache_dir), "processed", "13f_holdings.csv")
    if os.path.exists(processed_path):
        return normalize_13f_holdings(pd.read_csv(processed_path))

    return pd.DataFrame()


def rebuild_13f_aggregate(cache_dir="data/raw", expected_funds=None):
    """Rebuild ``13f_all_holdings.csv`` from the newest local per-fund caches."""
    holdings = load_best_13f_holdings(cache_dir=cache_dir, expected_funds=expected_funds)
    if holdings.empty:
        return holdings

    aggregate_path = os.path.join(cache_dir, "13f_all_holdings.csv")
    holdings.to_csv(aggregate_path, index=False)
    return holdings


# ---------------------------------------------------------------------------
# FRED — Hedge Fund Balance Sheet
# ---------------------------------------------------------------------------


def fetch_hedge_fund_data(fred_client, series_map, cache_path=None):
    """Fetch all hedge fund balance sheet series from FRED and combine into a DataFrame."""
    if cache_path and os.path.exists(cache_path):
        print(f"Loading cached data from {cache_path}")
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        print(f"  Loaded {len(df)} quarters, {df.index.min().date()} to {df.index.max().date()}")
        return df

    print(f"Fetching {len(series_map)} series from FRED...")
    data = {}
    failed = []
    for name, series_id in series_map.items():
        try:
            s = fred_client.get_series(series_id)
            data[name] = s
            print(f"  OK: {name} ({series_id}) — {len(s)} observations")
        except Exception as e:
            print(f"  FAILED: {name} ({series_id}) — {e}")
            failed.append(name)
        time.sleep(0.2)

    df = pd.DataFrame(data)
    df.index.name = "Date"

    # Convert to billions (FRED returns millions for Z.1 data)
    df = df / 1000.0

    if cache_path:
        df.to_csv(cache_path)
        print(f"\nSaved to {cache_path}")

    if failed:
        print(f"\nWARNING: {len(failed)} series failed: {failed}")

    print(f"Fetched {len(df)} quarters, {df.index.min().date()} to {df.index.max().date()}")
    return df


# ---------------------------------------------------------------------------
# FRED — VIX Volatility Index
# ---------------------------------------------------------------------------


def fetch_vix_data(fred_client, cache_path=None):
    """Fetch VIX daily data from FRED, aggregate to quarterly."""
    if cache_path and os.path.exists(cache_path):
        print(f"Loading cached VIX data from {cache_path}")
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        return df

    print("Fetching VIX data from FRED (VIXCLS)...")
    vix = fred_client.get_series("VIXCLS")
    vix = vix.dropna()

    df = (
        vix.resample("QE")
        .agg(VIX_mean="mean", VIX_max="max", VIX_min="min", VIX_end="last", VIX_std="std")
        .rename_axis("Date")
    )

    if cache_path:
        df.to_csv(cache_path)
        print(f"Saved to {cache_path}")

    print(f"VIX data: {len(df)} quarters, {df.index.min().date()} to {df.index.max().date()}")
    return df


# ---------------------------------------------------------------------------
# SEC EDGAR — 13F Holdings
# ---------------------------------------------------------------------------


def fetch_13f_holdings(cik, fund_name, cache_dir="data/raw", start_date=None, end_date=None):
    """Fetch 13F-HR filing data from SEC EDGAR for a given fund.

    Args:
        start_date: Earliest filing date to fetch holdings for (inclusive).
                    Defaults to 2 years ago.
        end_date: Latest filing date to fetch holdings for (inclusive).
                  Defaults to today.
    """
    if end_date is None:
        end_date = pd.Timestamp.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_date = (pd.Timestamp.now() - pd.DateOffset(years=2)).strftime("%Y-%m-%d")
    # Cache key includes date window so different queries don't collide
    start_tag = start_date.replace("-", "")
    end_tag = end_date.replace("-", "")
    cache_path = os.path.join(cache_dir, f"13f_{fund_name.replace(' ', '_').lower()}_{start_tag}_{end_tag}.csv")
    if os.path.exists(cache_path):
        df_cached = normalize_13f_holdings(pd.read_csv(cache_path))
        # Only use cache if it contains actual holdings data
        if "value_thousands" in df_cached.columns:
            if "value_usd" not in df_cached.columns or "value_unit" not in df_cached.columns:
                df_cached.to_csv(cache_path, index=False)
            print(f"  Cached: {fund_name} ({len(df_cached)} holdings)")
            return df_cached
        else:
            # Stale metadata-only cache — re-fetch
            os.remove(cache_path)
            print(f"  Stale cache removed for {fund_name}, re-fetching...")

    submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    try:
        resp = requests.get(submissions_url, headers=SEC_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accessions = filings.get("accessionNumber", [])
        primary_docs = filings.get("primaryDocument", [])

        records = []
        for i, form in enumerate(forms):
            if form in ("13F-HR", "13F-HR/A"):
                records.append(
                    {
                        "fund": fund_name,
                        "form": form,
                        "filing_date": dates[i],
                        "accession": accessions[i],
                        "primary_doc": primary_docs[i] if i < len(primary_docs) else None,
                    }
                )

        if not records:
            print(f"  No 13F filings found for {fund_name}")
            return pd.DataFrame()

        df_filings = pd.DataFrame(records)
        print(f"  Found {len(df_filings)} 13F filings for {fund_name} (latest: {df_filings['filing_date'].iloc[0]})")

        window = df_filings[(df_filings["filing_date"] >= start_date) & (df_filings["filing_date"] <= end_date)].copy()

        # Deduplicate amendments: keep 13F-HR/A over 13F-HR for same quarter
        # Derive report_period from filing_date (filings are due ~45 days after quarter-end)
        window["report_quarter"] = pd.to_datetime(window["filing_date"]).apply(
            lambda d: (d - pd.DateOffset(months=2)).to_period("Q").strftime("%YQ%q")
        )
        window = window.sort_values("form", ascending=False)  # 13F-HR/A sorts after 13F-HR
        window = window.drop_duplicates(subset=["fund", "report_quarter"], keep="first")

        all_holdings = []
        for _, filing in window.iterrows():
            acc_no = filing["accession"].replace("-", "")
            acc_dash = filing["accession"]
            cik_stripped = cik.lstrip("0")
            base_url = f"https://www.sec.gov/Archives/edgar/data/{cik_stripped}/{acc_no}/"

            try:
                # Try index.json first, fall back to HTML scraping
                info_file = None
                try:
                    idx_resp = requests.get(
                        f"https://data.sec.gov/Archives/edgar/data/{cik_stripped}/{acc_no}/index.json",
                        headers=SEC_HEADERS,
                        timeout=15,
                    )
                    idx_resp.raise_for_status()
                    idx_data = idx_resp.json()
                    for item in idx_data.get("directory", {}).get("item", []):
                        name = item.get("name", "").lower()
                        if "infotable" in name or "information" in name:
                            info_file = item["name"]
                            break
                        # Broader: any XML that's not primary_doc.xml
                        if name.endswith(".xml") and name != "primary_doc.xml" and info_file is None:
                            info_file = item["name"]
                except Exception as e:
                    warnings.warn(f"13F index.json unavailable for {acc_no}: {e}")

                # Fallback: scrape HTML index for INFORMATION TABLE typed files
                if not info_file:
                    import re

                    idx_url = f"{base_url}{acc_dash}-index.htm"
                    idx_resp = requests.get(idx_url, headers=SEC_HEADERS, timeout=15)
                    if idx_resp.status_code == 200:
                        matches = re.findall(
                            r'href="[^"]*?/([^/"]+\.xml)"[^<]*</a>\s*</td>\s*<td[^>]*>\s*INFORMATION TABLE',
                            idx_resp.text,
                            re.IGNORECASE,
                        )
                        if matches:
                            info_file = matches[0]
                        else:
                            # Any non-primary XML
                            xml_files = re.findall(r'href="[^"]*?/([^/"]+\.xml)"', idx_resp.text)
                            xml_files = [f for f in xml_files if f != "primary_doc.xml"]
                            if xml_files:
                                info_file = xml_files[0]

                if info_file:
                    xml_url = base_url + info_file
                    xml_resp = requests.get(xml_url, headers=SEC_HEADERS, timeout=15)
                    xml_resp.raise_for_status()

                    root = ET.fromstring(xml_resp.content)
                    ns = ""
                    if root.tag.startswith("{"):
                        ns = root.tag.split("}")[0] + "}"

                    for entry in root.findall(f".//{ns}infoTable"):
                        name_of_issuer = entry.findtext(f"{ns}nameOfIssuer", "")
                        title = entry.findtext(f"{ns}titleOfClass", "")
                        cusip = entry.findtext(f"{ns}cusip", "")
                        value = entry.findtext(f"{ns}value", "0")
                        shares_node = entry.find(f"{ns}shrsOrPrnAmt")
                        shares = shares_node.findtext(f"{ns}sshPrnamt", "0") if shares_node else "0"
                        share_type = shares_node.findtext(f"{ns}sshPrnamtType", "") if shares_node else ""
                        put_call = entry.findtext(f"{ns}putCall", "")

                        value_raw = int(value) if value else 0
                        filing_ts = pd.to_datetime(filing["filing_date"], errors="coerce")
                        reported_in_dollars = pd.notna(filing_ts) and filing_ts >= FORM_13F_DOLLAR_CUTOFF
                        value_usd = value_raw if reported_in_dollars else value_raw * 1000

                        all_holdings.append(
                            {
                                "fund": fund_name,
                                "filing_date": filing["filing_date"],
                                "report_period": filing.get("report_quarter", filing["filing_date"][:7]),
                                "issuer": " ".join(name_of_issuer.split()),
                                "title": " ".join(title.split()),
                                "cusip": cusip,
                                # Preserve the historical column name for compatibility, but
                                # also emit a canonical dollar-denominated value column.
                                "value_thousands": value_raw,
                                "value_unit": "usd" if reported_in_dollars else "thousands",
                                "value_usd": value_usd,
                                "shares": int(shares) if shares else 0,
                                "share_type": share_type,
                                "put_call": put_call,
                            }
                        )

                time.sleep(0.15)
            except Exception as e:
                print(f"    Could not parse holdings for {filing['filing_date']}: {e}")
                continue

        if all_holdings:
            df_h = normalize_13f_holdings(pd.DataFrame(all_holdings))
            df_h.to_csv(cache_path, index=False)
            print(f"  Saved {len(df_h)} holdings to {cache_path}")
            return df_h
        else:
            # Do NOT cache metadata-only results — they poison future runs
            print(f"  No holdings parsed for {fund_name} (XML extraction failed)")
            return df_filings

    except Exception as e:
        print(f"  Error fetching {fund_name}: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# CFTC — Commitments of Traders
# ---------------------------------------------------------------------------


def fetch_cftc_data(cache_path=None):
    """Fetch CFTC Traders in Financial Futures report for equity index futures."""
    if cache_path and os.path.exists(cache_path):
        print(f"Loading cached CFTC data from {cache_path}")
        return pd.read_csv(cache_path, parse_dates=["date"])

    print("Fetching CFTC Commitments of Traders data...")

    # CFTC provides historical compressed ZIPs with proper headers per year
    base_url = "https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
    current_year = pd.Timestamp.now().year
    years = range(current_year - 2, current_year + 1)  # 3 years of data

    frames = []
    for year in years:
        url = base_url.format(year=year)
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            z = zipfile.ZipFile(BytesIO(resp.content))
            with z.open(z.namelist()[0]) as f:
                df = pd.read_csv(f)
            frames.append(df)
            print(f"  {year}: {len(df)} records")
            time.sleep(0.3)
        except Exception as e:
            print(f"  {year}: skipped ({e})")

    if not frames:
        print("Error: could not fetch any CFTC data")
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    equity_keywords = ["S&P 500", "E-MINI S&P", "DJIA", "DOW JONES", "NASDAQ", "RUSSELL"]
    mask = (
        df["Market_and_Exchange_Names"]
        .str.upper()
        .apply(lambda x: any(k in x.upper() for k in equity_keywords) if pd.notna(x) else False)
    )
    df_equity = df[mask].copy()

    if df_equity.empty:
        print("  No equity index futures found, keeping all data")
        df_equity = df.copy()

    result = pd.DataFrame(
        {
            "date": pd.to_datetime(df_equity["Report_Date_as_YYYY-MM-DD"]),
            "market": df_equity["Market_and_Exchange_Names"],
            "lev_fund_long": pd.to_numeric(df_equity.get("Lev_Money_Positions_Long_All", 0), errors="coerce"),
            "lev_fund_short": pd.to_numeric(df_equity.get("Lev_Money_Positions_Short_All", 0), errors="coerce"),
            "lev_fund_spreading": pd.to_numeric(df_equity.get("Lev_Money_Positions_Spread_All", 0), errors="coerce"),
        }
    )
    result["lev_fund_net"] = result["lev_fund_long"] - result["lev_fund_short"]
    result = result.sort_values("date").reset_index(drop=True)

    if cache_path:
        result.to_csv(cache_path, index=False)
        print(f"Saved {len(result)} records to {cache_path}")

    print(f"CFTC data: {len(result)} records, {result['date'].min().date()} to {result['date'].max().date()}")
    return result


# ---------------------------------------------------------------------------
# SEC EDGAR — Form ADV (Investment Adviser Registration)
# ---------------------------------------------------------------------------


def fetch_form_adv(cik, fund_name, cache_dir="data/raw"):
    """Fetch Form ADV data from SEC EDGAR for a given fund.

    Form ADV contains: AUM, employee count, types of clients,
    fee structures, disciplinary history, and office locations.
    """
    cache_path = os.path.join(cache_dir, "form_adv", f"adv_{fund_name.replace(' ', '_').lower()}.json")
    if os.path.exists(cache_path):
        print(f"  Cached: {fund_name} ADV")
        with open(cache_path) as f:
            return json.load(f)

    # Use the submissions API to find ADV filings
    submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    adv_headers = {
        "User-Agent": SEC_HEADERS["User-Agent"],
        "Accept-Encoding": "gzip, deflate",
    }

    try:
        resp = requests.get(submissions_url, headers=adv_headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # Extract company info
        company_info = {
            "name": data.get("name"),
            "cik": cik,
            "sic": data.get("sic"),
            "sicDescription": data.get("sicDescription"),
            "stateOfIncorporation": data.get("stateOfIncorporation"),
            "addresses": data.get("addresses"),
        }

        # Find all filing types and dates
        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accessions = filings.get("accessionNumber", [])
        primary_docs = filings.get("primaryDocument", [])

        # Collect all filings (not just 13F)
        filing_records = []
        for i, form in enumerate(forms):
            filing_records.append(
                {
                    "form": form,
                    "filing_date": dates[i],
                    "accession": accessions[i],
                    "primary_doc": primary_docs[i] if i < len(primary_docs) else None,
                }
            )

        # Summary by filing type
        from collections import Counter

        form_counts = Counter(forms)

        result = {
            "company_info": company_info,
            "filing_type_counts": dict(form_counts),
            "total_filings": len(filing_records),
            "filing_date_range": {
                "earliest": dates[-1] if dates else None,
                "latest": dates[0] if dates else None,
            },
            "all_filings": filing_records,
        }

        # Look for ADV filings specifically
        adv_filings = [f for f in filing_records if "ADV" in f["form"]]
        result["adv_filings"] = adv_filings
        result["adv_count"] = len(adv_filings)

        # Try to get IAPD (Investment Adviser Public Disclosure) data
        # CIK and IAPD numbers are different — IAPD uses SEC file numbers
        iapd_numbers = []
        for i, form in enumerate(forms):
            if "ADV" in form:
                iapd_numbers.append(accessions[i])
        result["iapd_accessions"] = iapd_numbers[:10]  # Keep recent ones

        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"  Saved {fund_name} ADV data ({len(filing_records)} total filings, {len(adv_filings)} ADV)")

        return result

    except Exception as e:
        print(f"  Error fetching ADV for {fund_name}: {e}")
        return {}


def fetch_all_fund_profiles(cache_dir="data/raw"):
    """Fetch submission profiles for all tracked hedge funds."""
    print("Fetching fund profiles from SEC EDGAR Submissions API...")
    profiles = {}
    for fund_name, cik in HEDGE_FUND_CIKS.items():
        profile = fetch_form_adv(cik, fund_name, cache_dir=cache_dir)
        if profile:
            profiles[fund_name] = profile
            counts = profile.get("filing_type_counts", {})
            adv_count = profile.get("adv_count", 0)
            total = profile.get("total_filings", 0)
            date_range = profile.get("filing_date_range", {})
            print(f"    {fund_name}: {total} filings ({date_range.get('earliest')} to {date_range.get('latest')})")
            print(
                f"      ADV: {adv_count}, 13F: {counts.get('13F-HR', 0)}, "
                f"SC 13G: {counts.get('SC 13G', 0) + counts.get('SC 13G/A', 0)}"
            )
        time.sleep(0.15)
    return profiles


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Hedge Fund Mosaic source data")
    parser.add_argument("--13f", action="store_true", dest="fetch_13f_only", help="Fetch or rebuild only 13F holdings")
    args = parser.parse_args()

    load_dotenv()
    FRED_API_KEY = os.getenv("FRED_API_KEY")
    raw_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)

    if args.fetch_13f_only:
        print("=" * 60)
        print("FETCHING 13F HOLDINGS")
        print("=" * 60)

        holdings_list = []
        for fund_name, cik in HEDGE_FUND_CIKS.items():
            df_fund = fetch_13f_holdings(cik, fund_name, cache_dir=raw_dir)
            if not df_fund.empty and "value_thousands" in df_fund.columns:
                holdings_list.append(df_fund)
            time.sleep(0.2)

        if holdings_list:
            df_13f = pd.concat(holdings_list, ignore_index=True)
            df_13f = normalize_13f_holdings(df_13f)
            df_13f.to_csv(os.path.join(raw_dir, "13f_all_holdings.csv"), index=False)
            print(f"Total 13F holdings: {len(df_13f)} records across {df_13f['fund'].nunique()} funds")
        else:
            rebuilt = rebuild_13f_aggregate(cache_dir=raw_dir, expected_funds=HEDGE_FUND_CIKS)
            if rebuilt.empty:
                print("No 13F holdings available to rebuild aggregate cache.")
            else:
                print(
                    "Rebuilt aggregate 13F cache from local per-fund files: "
                    f"{len(rebuilt)} rows across {rebuilt['fund'].nunique()} funds"
                )
        exit(0)

    if Fred is None:
        print("ERROR: fredapi is not installed. Run `pip install -r requirements.txt`.")
        exit(1)

    if not FRED_API_KEY:
        print("ERROR: FRED_API_KEY not found in .env")
        exit(1)

    fred = Fred(api_key=FRED_API_KEY)

    print("=" * 60)
    print("FETCHING ALL DATA SOURCES")
    print("=" * 60)

    # 1. FRED hedge fund balance sheet
    print("\n[1/4] FRED — Hedge Fund Balance Sheet")
    fetch_hedge_fund_data(
        fred, HEDGE_FUND_SERIES, cache_path=os.path.join(raw_dir, "hedge_fund_balance_sheet_fred.csv")
    )

    # 2. VIX
    print("\n[2/4] FRED — VIX Volatility Index")
    fetch_vix_data(fred, cache_path=os.path.join(raw_dir, "vix_quarterly.csv"))

    # 3. SEC 13F
    print("\n[3/4] SEC EDGAR — 13F Holdings")
    holdings_list = []
    for fund_name, cik in HEDGE_FUND_CIKS.items():
        df_fund = fetch_13f_holdings(cik, fund_name, cache_dir=raw_dir)
        if not df_fund.empty and "value_thousands" in df_fund.columns:
            holdings_list.append(df_fund)
        time.sleep(0.2)

    if holdings_list:
        df_13f = normalize_13f_holdings(pd.concat(holdings_list, ignore_index=True))
        df_13f.to_csv(os.path.join(raw_dir, "13f_all_holdings.csv"), index=False)
        print(f"Total 13F holdings: {len(df_13f)} records across {df_13f['fund'].nunique()} funds")

    # 4. CFTC
    print("\n[4/5] CFTC — Commitments of Traders")
    fetch_cftc_data(cache_path=os.path.join(raw_dir, "cftc_cot.csv"))

    # 5. Fund profiles (Form ADV + submission history)
    print("\n[5/5] SEC EDGAR — Fund Profiles (Submissions API)")
    fetch_all_fund_profiles(cache_dir=raw_dir)

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)
