"""End-to-end pipeline: fetch data, parse all sources, compute metrics, run analysis.

Usage:
    python -m src.pipeline              # run everything
    python -m src.pipeline --fetch      # fetch only
    python -m src.pipeline --parse      # parse only
    python -m src.pipeline --analyze    # analyze only
    python -m src.pipeline --artifacts  # regenerate public figures, reports, notebook
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import pandas as pd
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(ROOT_DIR, "data", "processed")


def step_fetch() -> None:
    """Fetch raw data from all external sources."""
    from fredapi import Fred

    from src.data.fetch import (
        HEDGE_FUND_CIKS,
        HEDGE_FUND_SERIES,
        fetch_13f_holdings,
        fetch_all_fund_profiles,
        fetch_cftc_data,
        fetch_hedge_fund_data,
        fetch_vix_data,
        rebuild_13f_aggregate,
    )
    from src.data.fetch_dtcc import fetch_all_dtcc_reports
    from src.data.fetch_fcm import fetch_all_fcm_reports
    from src.data.fetch_swaps import fetch_all_swaps_reports

    load_dotenv()
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        print("ERROR: FRED_API_KEY not found in .env")
        sys.exit(1)

    fred = Fred(api_key=api_key)
    os.makedirs(RAW_DIR, exist_ok=True)

    print("[1/7] FRED — Hedge Fund Balance Sheet")
    fetch_hedge_fund_data(
        fred, HEDGE_FUND_SERIES, cache_path=os.path.join(RAW_DIR, "hedge_fund_balance_sheet_fred.csv")
    )

    print("\n[2/7] FRED — VIX")
    fetch_vix_data(fred, cache_path=os.path.join(RAW_DIR, "vix_quarterly.csv"))

    print("\n[3/7] SEC EDGAR — 13F Holdings")
    for fund_name, cik in HEDGE_FUND_CIKS.items():
        df = fetch_13f_holdings(cik, fund_name, cache_dir=RAW_DIR)
        if df.empty:
            print(f"  No 13F holdings captured for {fund_name}")
        time.sleep(0.2)
    rebuilt = rebuild_13f_aggregate(RAW_DIR, expected_funds=HEDGE_FUND_CIKS)
    if rebuilt.empty:
        print("  Could not rebuild aggregate 13F cache from fetched per-fund files")

    print("\n[4/7] CFTC — Commitments of Traders")
    fetch_cftc_data(cache_path=os.path.join(RAW_DIR, "cftc_cot.csv"))

    print("\n[5/7] SEC EDGAR — Fund Profiles")
    fetch_all_fund_profiles(cache_dir=RAW_DIR)

    print("\n[6/7] CFTC — Weekly Swaps Reports")
    fetch_all_swaps_reports()

    print("\n[7/7] DTCC + FCM Reports")
    fetch_all_dtcc_reports()
    fetch_all_fcm_reports()


def step_parse() -> None:
    """Parse all raw data into processed CSVs."""
    from src.data.parse_dtcc import parse_all_dtcc
    from src.data.parse_fcm import parse_all_fcm
    from src.data.parse_form_pf import parse_all_form_pf
    from src.data.parse_swaps import parse_all_swaps

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    parsers = [
        ("Form PF", parse_all_form_pf),
        ("FCM", parse_all_fcm),
        ("DTCC", parse_all_dtcc),
        ("Swaps", parse_all_swaps),
    ]
    failures = []
    for i, (name, fn) in enumerate(parsers, 1):
        print(f"[{i}/{len(parsers)}] Parsing {name}")
        try:
            fn()
        except Exception as e:
            print(f"  WARNING: {name} parsing failed — {e}")
            failures.append(name)
    if failures:
        raise RuntimeError(f"Parsing failed for: {', '.join(failures)}")


def step_analyze() -> dict[str, object]:
    """Compute derived metrics and run analysis reports used by public artifacts."""
    from src.analysis.advanced import run_all_advanced
    from src.analysis.cross_source import run_full_analysis
    from src.analysis.metrics import compute_derived_metrics

    balance_sheet_path = os.path.join(RAW_DIR, "hedge_fund_balance_sheet_fred.csv")
    if os.path.exists(balance_sheet_path):
        print("[1/3] Computing derived metrics")
        df = pd.read_csv(balance_sheet_path, index_col=0, parse_dates=True)
        df = compute_derived_metrics(df)
        canonical_path = os.path.join(PROCESSED_DIR, "hedge_fund_analysis.csv")
        legacy_path = os.path.join(PROCESSED_DIR, "hedge_fund_metrics.csv")
        df.to_csv(canonical_path)
        df.to_csv(legacy_path)
        print(f"  Saved {len(df)} quarters to data/processed/hedge_fund_analysis.csv")
        print("  Saved compatibility copy to data/processed/hedge_fund_metrics.csv")
    else:
        print("[1/3] Skipped metrics — no balance sheet data found. Run --fetch first.")

    print("\n[2/3] Cross-source analysis")
    try:
        cross_results = run_full_analysis(save=True)
    except Exception as e:
        print(f"  ERROR: Cross-source analysis failed — {e}")
        raise

    print("\n[3/3] Advanced analysis")
    try:
        advanced_results = run_all_advanced(save=True)
    except Exception as e:
        print(f"  ERROR: Advanced analysis failed — {e}")
        raise

    return {
        "cross_source": cross_results,
        "advanced": advanced_results,
    }


def step_artifacts(analysis_results: dict[str, object] | None = None) -> object:
    """Regenerate public figures, rendered notebook, and provenance artifacts."""
    from src.artifacts import refresh_public_artifacts

    print("[1/1] Public artifacts")
    return refresh_public_artifacts(analysis_results=analysis_results)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Hedge Fund Mosaic pipeline")
    parser.add_argument("--fetch", action="store_true", help="Fetch raw data only")
    parser.add_argument("--parse", action="store_true", help="Parse raw data only")
    parser.add_argument("--analyze", action="store_true", help="Run analysis only")
    parser.add_argument("--artifacts", action="store_true", help="Regenerate public figures, reports, and notebook")
    args = parser.parse_args(argv)

    # If no flags, run everything
    run_all = not (args.fetch or args.parse or args.analyze or args.artifacts)

    print("=" * 60)
    print("HEDGE FUND MOSAIC PIPELINE")
    print("=" * 60)

    analysis_results = None

    if run_all or args.fetch:
        print("\n>>> FETCH\n")
        step_fetch()

    if run_all or args.parse:
        print("\n>>> PARSE\n")
        step_parse()

    if run_all or args.analyze:
        print("\n>>> ANALYZE\n")
        analysis_results = step_analyze()

    if run_all or args.artifacts:
        print("\n>>> ARTIFACTS\n")
        step_artifacts(analysis_results=analysis_results)

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
