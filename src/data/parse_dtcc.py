"""
DTCC Swap Data Repository Parser

Parses daily cumulative swap reports from DTCC's Public Price Dissemination API.
Each ZIP contains a CSV with ~30K+ individual OTC derivative transactions and 110 columns.
Produces daily and quarterly summaries by asset class, clearing status, and product type.

Data: ~1,825 daily files across 5 asset classes (2025-03-13 onward).
"""

import csv
import gc
import os
import sys
import zipfile
from datetime import datetime

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "dtcc")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")


def _extract_date_from_filename(filename):
    """Extract date from CFTC_CUMULATIVE_{CLASS}_{YYYY}_{MM}_{DD}.zip"""
    parts = filename.replace(".zip", "").split("_")
    try:
        year, month, day = int(parts[-3]), int(parts[-2]), int(parts[-1])
        return datetime(year, month, day)
    except (ValueError, IndexError):
        return None


def _extract_asset_class(filename):
    """Extract asset class from filename."""
    parts = filename.replace(".zip", "").split("_")
    # CFTC_CUMULATIVE_{CLASS}_{Y}_{M}_{D}
    return parts[2] if len(parts) >= 6 else "UNKNOWN"


def parse_single_zip(filepath):
    """Parse one DTCC cumulative ZIP file and return aggregated summary.

    Uses Python's csv module (not pandas) to stream rows without loading the
    entire file into memory. This keeps peak memory under ~5 MB per file
    even for 30K+ row CSVs.
    """
    import csv as csv_mod
    import io

    filename = os.path.basename(filepath)
    date = _extract_date_from_filename(filename)
    asset_class = _extract_asset_class(filename)

    if date is None:
        return None

    try:
        with zipfile.ZipFile(filepath, "r") as zf:
            csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
            if not csv_names:
                return None

            with zf.open(csv_names[0]) as csv_file:
                reader = csv_mod.reader(io.TextIOWrapper(csv_file, encoding="utf-8"))
                header = next(reader, None)
                if not header:
                    return None

                # Find column indices for the 5 fields we need
                col_idx = {}
                for i, col in enumerate(header):
                    col = col.strip()
                    if col == "Notional amount-Leg 1":
                        col_idx["notional"] = i
                    elif col == "Notional currency-Leg 1":
                        col_idx["currency"] = i
                    elif col == "Cleared":
                        col_idx["cleared"] = i
                    elif col == "Prime brokerage transaction indicator":
                        col_idx["pb"] = i
                    elif col == "Block trade election indicator":
                        col_idx["block"] = i

                # Single-pass aggregation
                trade_count = 0
                total_notional = 0.0
                usd_notional = 0.0
                cleared_count = 0
                cleared_notional = 0.0
                pb_count = 0
                block_count = 0

                notional_idx = col_idx.get("notional")
                currency_idx = col_idx.get("currency")
                cleared_idx = col_idx.get("cleared")
                pb_idx = col_idx.get("pb")
                block_idx = col_idx.get("block")

                for row in reader:
                    trade_count += 1

                    # Parse notional (cap at $100B to filter DTCC data errors)
                    notional_val = 0.0
                    if notional_idx is not None and notional_idx < len(row):
                        raw = row[notional_idx].replace(",", "").strip()
                        if raw:
                            try:
                                notional_val = float(raw)
                                if notional_val > 1e11:
                                    print(
                                        f"  WARN: notional {notional_val:.0f} exceeds $100B cap, zeroed",
                                        file=sys.stderr,
                                    )
                                    notional_val = 0.0
                            except ValueError:
                                pass
                    total_notional += notional_val

                    # Cleared
                    if cleared_idx is not None and cleared_idx < len(row):
                        cl = row[cleared_idx].strip().upper()
                        if cl in ("Y", "I", "TRUE"):
                            cleared_count += 1
                            cleared_notional += notional_val

                    # USD notional
                    if currency_idx is not None and currency_idx < len(row):
                        if row[currency_idx].strip() == "USD":
                            usd_notional += notional_val

                    # Prime brokerage
                    if pb_idx is not None and pb_idx < len(row):
                        if row[pb_idx].strip().upper() in ("TRUE", "Y"):
                            pb_count += 1

                    # Block trade
                    if block_idx is not None and block_idx < len(row):
                        if row[block_idx].strip().upper() in ("TRUE", "Y"):
                            block_count += 1

        if trade_count == 0:
            return None

        summary = {
            "date": date,
            "asset_class": asset_class,
            "trade_count": trade_count,
            "total_notional_bn": total_notional / 1e9,
            "usd_notional_bn": usd_notional / 1e9,
            "cleared_count": cleared_count,
            "cleared_notional_bn": cleared_notional / 1e9,
            "uncleared_notional_bn": (total_notional - cleared_notional) / 1e9,
            "cleared_pct": cleared_count / trade_count if trade_count > 0 else 0,
            "pb_count": pb_count,
            "pb_pct": pb_count / trade_count if trade_count > 0 else 0,
            "block_count": block_count,
            "block_pct": block_count / trade_count if trade_count > 0 else 0,
            "avg_trade_size_bn": (total_notional / 1e9) / trade_count if trade_count > 0 else 0,
        }

        return summary

    except Exception as e:
        print(f"  WARNING: {os.path.basename(filepath)}: {e}")
        return None


SUMMARY_FIELDS = [
    "date",
    "asset_class",
    "trade_count",
    "total_notional_bn",
    "usd_notional_bn",
    "cleared_count",
    "cleared_notional_bn",
    "uncleared_notional_bn",
    "cleared_pct",
    "cleared_notional_pct",
    "pb_count",
    "pb_pct",
    "block_count",
    "block_pct",
    "avg_trade_size_bn",
]

LEGACY_SUMMARY_FIELDS = [
    "date",
    "asset_class",
    "trade_count",
    "total_notional_bn",
    "usd_notional_bn",
    "cleared_count",
    "cleared_notional_bn",
    "uncleared_notional_bn",
    "cleared_pct",
    "pb_count",
    "pb_pct",
    "block_count",
    "block_pct",
    "cleared_notional_pct",
]


def _canonicalize_summary_row(row):
    """Map legacy or current DTCC summary rows onto the canonical schema."""
    if len(row) == len(SUMMARY_FIELDS):
        return dict(zip(SUMMARY_FIELDS, row))

    if len(row) == len(LEGACY_SUMMARY_FIELDS):
        data = dict(zip(LEGACY_SUMMARY_FIELDS, row))
        trade_count = pd.to_numeric(data.get("trade_count"), errors="coerce")
        total_notional = pd.to_numeric(data.get("total_notional_bn"), errors="coerce")
        data["avg_trade_size_bn"] = total_notional / trade_count if pd.notna(trade_count) and trade_count > 0 else 0
        return {field: data.get(field, "") for field in SUMMARY_FIELDS}

    return None


def _load_summary_rows(summary_path):
    """Read a possibly mixed-schema DTCC summary CSV without failing on old rows."""
    if not os.path.exists(summary_path):
        return []

    rows = []
    with open(summary_path, newline="") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # header
        for row in reader:
            canonical = _canonicalize_summary_row(row)
            if canonical is not None:
                rows.append(canonical)

    return rows


def _clean_existing_summary(summary_path):
    """Deduplicate resume state by (date, asset_class) and backfill derived columns."""
    if not os.path.exists(summary_path):
        return pd.DataFrame(columns=SUMMARY_FIELDS)

    rows = _load_summary_rows(summary_path)
    daily = pd.DataFrame(rows, columns=SUMMARY_FIELDS)
    if daily.empty:
        return daily

    numeric_cols = [col for col in SUMMARY_FIELDS if col not in {"date", "asset_class"}]
    for col in numeric_cols:
        daily[col] = pd.to_numeric(daily[col], errors="coerce")
    daily = daily.sort_values(["date", "asset_class"])
    daily = daily.drop_duplicates(subset=["date", "asset_class"], keep="last")
    if "cleared_notional_pct" not in daily.columns:
        daily["cleared_notional_pct"] = daily["cleared_notional_bn"] / daily["total_notional_bn"]
    if "avg_trade_size_bn" not in daily.columns:
        daily["avg_trade_size_bn"] = daily["total_notional_bn"] / daily["trade_count"]
    daily.to_csv(summary_path, index=False, columns=SUMMARY_FIELDS)
    return daily


def _validate_row(summary):
    """Validate a parsed summary row. Returns list of warnings (empty = OK)."""
    warnings = []
    if summary["trade_count"] <= 0:
        warnings.append("zero trades")
    if summary["total_notional_bn"] < 0:
        warnings.append(f"negative notional: {summary['total_notional_bn']:.2f}")
    if not (0 <= summary["cleared_pct"] <= 1):
        warnings.append(f"cleared_pct out of range: {summary['cleared_pct']:.3f}")
    if not (0 <= summary["pb_pct"] <= 1):
        warnings.append(f"pb_pct out of range: {summary['pb_pct']:.3f}")
    return warnings


def parse_all_dtcc(data_dir=None, output_dir=None):
    """Parse all DTCC cumulative ZIP files, streaming rows directly to CSV."""
    if data_dir is None:
        data_dir = DATA_DIR
    if output_dir is None:
        output_dir = OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)

    files = sorted([f for f in os.listdir(data_dir) if f.endswith(".zip")])
    print(f"Parsing {len(files)} DTCC cumulative reports...", flush=True)

    summary_path = os.path.join(output_dir, "dtcc_daily_summary.csv")
    error_path = os.path.join(output_dir, "dtcc_parse_errors.log")

    # Resume support: normalize any pre-existing file before appending.
    existing_keys = set()
    existing = _clean_existing_summary(summary_path)
    if not existing.empty:
        for _, row in existing.iterrows():
            existing_keys.add((str(row["date"])[:10], row["asset_class"]))
        print(f"  Resuming: {len(existing_keys)} rows already saved", flush=True)

    write_header = len(existing_keys) == 0
    parsed = 0
    failed = 0
    skipped = 0
    warned = 0

    with open(summary_path, "a", newline="") as csvfile, open(error_path, "a") as errlog:
        writer = csv.DictWriter(csvfile, fieldnames=SUMMARY_FIELDS)
        if write_header:
            writer.writeheader()

        for i, f in enumerate(files):
            date = _extract_date_from_filename(f)
            asset_class = _extract_asset_class(f)
            if date and (date.strftime("%Y-%m-%d"), asset_class) in existing_keys:
                skipped += 1
                continue

            filepath = os.path.join(data_dir, f)
            summary = parse_single_zip(filepath)

            if summary is None:
                failed += 1
                errlog.write(f"FAIL: {f}\n")
                continue

            # Validate before writing
            warnings = _validate_row(summary)
            if warnings:
                warned += 1
                errlog.write(f"WARN: {f}: {'; '.join(warnings)}\n")

            # Stream write — one row at a time, no memory accumulation
            summary["date"] = summary["date"].strftime("%Y-%m-%d")
            summary["cleared_notional_pct"] = (
                summary["cleared_notional_bn"] / summary["total_notional_bn"] if summary["total_notional_bn"] > 0 else 0
            )
            writer.writerow(summary)
            csvfile.flush()
            parsed += 1

            if (i + 1) % 50 == 0:
                gc.collect()
                print(
                    f"  [{i + 1}/{len(files)}] {parsed} parsed, {skipped} skipped, {failed} failed, {warned} warnings",
                    flush=True,
                )

    total_rows = parsed + len(existing_keys)
    if total_rows == 0:
        print("No DTCC data parsed!")
        return

    print(f"  Saved dtcc_daily_summary.csv ({total_rows} rows)", flush=True)

    # --- Quarterly aggregation (lightweight read of the flat CSV) ---
    daily = _clean_existing_summary(summary_path)

    daily["date"] = pd.to_datetime(daily["date"])
    daily["quarter"] = daily["date"].dt.to_period("Q").astype(str)
    quarter_end = (
        daily.sort_values(["asset_class", "date"])
        .groupby(["quarter", "asset_class"], as_index=False)
        .last()
        .rename(
            columns={
                "date": "quarter_end_date",
                "trade_count": "quarter_end_trade_count",
                "total_notional_bn": "quarter_end_total_notional_bn",
                "usd_notional_bn": "quarter_end_usd_notional_bn",
                "cleared_count": "quarter_end_cleared_count",
                "cleared_notional_bn": "quarter_end_cleared_notional_bn",
                "uncleared_notional_bn": "quarter_end_uncleared_notional_bn",
                "cleared_pct": "quarter_end_cleared_pct",
                "cleared_notional_pct": "quarter_end_cleared_notional_pct",
                "pb_pct": "quarter_end_pb_pct",
                "block_pct": "quarter_end_block_pct",
            }
        )
    )
    trading_days = daily.groupby(["quarter", "asset_class"]).agg(trading_days=("date", "nunique")).reset_index()
    quarterly = trading_days.merge(quarter_end, on=["quarter", "asset_class"], how="left")
    quarterly.to_csv(os.path.join(output_dir, "dtcc_quarterly.csv"), index=False)
    print(f"  Saved dtcc_quarterly.csv ({len(quarterly)} rows)", flush=True)

    # --- Summary ---
    print(
        f"\nDone! {len(files)} files: {parsed} parsed, {skipped} resumed, {failed} failed, {warned} warnings.",
        flush=True,
    )
    if failed > 0:
        print(f"  See {error_path} for details", flush=True)
    for ac in daily["asset_class"].unique():
        ac_data = daily[daily["asset_class"] == ac]
        print(
            f"  {ac}: {len(ac_data)} days, {ac_data['trade_count'].sum():,.0f} total trades, "
            f"quarter-end cleared notional {ac_data['cleared_notional_pct'].iloc[-1]:.1%}",
            flush=True,
        )


if __name__ == "__main__":
    parse_all_dtcc()
