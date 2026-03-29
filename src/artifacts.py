"""Public artifact generation for portfolio-ready figures, reports, and provenance."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "financial_data_mpl"))

import nbformat
import pandas as pd
from nbclient import NotebookClient

from src.data.fetch import HEDGE_FUND_CIKS, load_best_13f_holdings
from src.visualization.plots import (
    plot_asset_composition,
    plot_balance_sheet_overview,
    plot_borrowing_patterns,
    plot_clearing_rate,
    plot_concentration_trend,
    plot_correlation_heatmap,
    plot_cross_source_leverage,
    plot_debt_securities,
    plot_derivative_exposure,
    plot_dtcc_summary,
    plot_fcm_capital,
    plot_fcm_concentration,
    plot_form_pf_leverage,
    plot_granger_heatmap,
    plot_impulse_response,
    plot_liability_structure,
    plot_liquidity_mismatch_detail,
    plot_monte_carlo,
    plot_strategy_allocation,
    plot_strategy_hhi,
    plot_structural_breaks,
    plot_swaps_notional,
    plot_total_assets,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
OUTPUT_DIR = ROOT_DIR / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
REPORTS_DIR = OUTPUT_DIR / "reports"
NOTEBOOK_PATH = ROOT_DIR / "notebooks" / "hedge_fund_analysis.ipynb"

PUBLIC_FIGURES = [
    "total_assets.png",
    "asset_composition.png",
    "debt_securities.png",
    "liability_structure.png",
    "balance_sheet_overview.png",
    "derivative_exposure.png",
    "borrowing_patterns.png",
    "correlation_heatmap.png",
    "form_pf_leverage.png",
    "strategy_allocation.png",
    "concentration_trend.png",
    "swaps_notional.png",
    "clearing_rate.png",
    "fcm_capital.png",
    "fcm_concentration.png",
    "dtcc_summary.png",
    "cross_source_leverage.png",
    "granger_causality_heatmap.png",
    "var_impulse_response.png",
    "monte_carlo_z1_total_assets.png",
    "monte_carlo_z1_total_net_assets.png",
    "structural_breaks_pf_gav_nav_ratio.png",
    "structural_breaks_swap_ir_cleared_pct.png",
    "structural_breaks_vix_mean.png",
    "strategy_hhi.png",
    "liquidity_mismatch_detail.png",
]

PUBLIC_REPORTS = [
    "advanced_analysis.txt",
    "cross_source_aligned.csv",
    "cross_source_metrics.csv",
    "cross_source_tests.csv",
    "executive_summary.md",
    "granger_causality_matrix.csv",
    "var_impulse_response.csv",
    "var_fevd.csv",
    "strategy_rotation_hhi.csv",
    "monte_carlo_summary.csv",
    "claims_ledger.csv",
    "run_manifest.json",
]

PUBLIC_CLAIMS = [
    {
        "claim_id": "z1_total_assets_latest_b",
        "claim_label": "Fed Z.1 hedge fund assets (latest, $B)",
        "source_files": ["data/processed/hedge_fund_analysis.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"${m['z1_total_assets_latest_b']:.1f}B",
    },
    {
        "claim_id": "z1_total_assets_yoy_pct",
        "claim_label": "Fed Z.1 hedge fund assets YoY growth (latest, %)",
        "source_files": ["data/processed/hedge_fund_analysis.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"{m['z1_total_assets_yoy_pct']:.1%}",
    },
    {
        "claim_id": "form_pf_hedge_fund_gav_latest_b",
        "claim_label": "Form PF hedge fund gross asset value (latest, $B)",
        "source_files": ["data/processed/form_pf_gav_nav.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"${m['form_pf_hedge_fund_gav_latest_b']:.0f}B",
    },
    {
        "claim_id": "form_pf_derivatives_latest_b",
        "claim_label": "Form PF hedge fund derivative value (latest, $B)",
        "source_files": ["data/processed/form_pf_derivatives.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"${m['form_pf_derivatives_latest_b']:.0f}B",
    },
    {
        "claim_id": "form_pf_derivatives_to_nav_latest_x",
        "claim_label": "Form PF hedge fund derivative-to-NAV ratio (latest, x)",
        "source_files": ["data/processed/form_pf_derivatives.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"{m['form_pf_derivatives_to_nav_latest_x']:.1f}x",
    },
    {
        "claim_id": "form_pf_all_private_gav_latest_b",
        "claim_label": "Form PF all private funds gross asset value (latest, $B)",
        "source_files": ["data/processed/form_pf_gav_nav.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"${m['form_pf_all_private_gav_latest_b']:.0f}B",
    },
    {
        "claim_id": "form_pf_all_private_nav_latest_b",
        "claim_label": "Form PF all private funds net asset value (latest, $B)",
        "source_files": ["data/processed/form_pf_gav_nav.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"${m['form_pf_all_private_nav_latest_b']:.0f}B",
    },
    {
        "claim_id": "form_pf_all_private_gav_nav_latest_x",
        "claim_label": "Form PF all private funds GAV/NAV ratio (latest, x)",
        "source_files": ["data/processed/form_pf_gav_nav.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"{m['form_pf_all_private_gav_nav_latest_x']:.2f}x",
    },
    {
        "claim_id": "form_pf_top10_nav_share_latest_pct",
        "claim_label": "Form PF Top 10 fund concentration (latest, % of NAV)",
        "source_files": ["data/processed/form_pf_concentration.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"{m['form_pf_top10_nav_share_latest_pct']:.1%}",
    },
    {
        "claim_id": "form_pf_top500_nav_share_latest_pct",
        "claim_label": "Form PF Top 500 fund concentration (latest, % of NAV)",
        "source_files": ["data/processed/form_pf_concentration.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"{m['form_pf_top500_nav_share_latest_pct']:.1%}",
    },
    {
        "claim_id": "swaps_ir_total_latest_b",
        "claim_label": "CFTC weekly swaps interest-rate notional outstanding (latest, $B)",
        "source_files": ["data/processed/swaps_weekly.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"${m['swaps_ir_total_latest_b'] / 1000:.1f}T",
    },
    {
        "claim_id": "thirteenf_total_rows",
        "claim_label": "13F amendment-deduped rows in bundled snapshot",
        "source_files": ["data/processed/13f_holdings.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"{int(m['thirteenf_total_rows']):,}",
    },
    {
        "claim_id": "thirteenf_long_positions_total",
        "claim_label": "13F long equity/ETF rows in bundled snapshot",
        "source_files": ["data/processed/13f_holdings.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"{int(m['thirteenf_long_positions_total']):,}",
    },
    {
        "claim_id": "thirteenf_latest_long_value_b",
        "claim_label": "13F combined long equity value in latest quarter ($B)",
        "source_files": ["data/processed/13f_holdings.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"${m['thirteenf_latest_long_value_b']:.0f}B",
    },
    {
        "claim_id": "thirteenf_nvidia_value_b",
        "claim_label": "13F combined NVIDIA value in latest quarter ($B)",
        "source_files": ["data/processed/13f_holdings.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"${m['thirteenf_nvidia_value_b']:.1f}B",
    },
    {
        "claim_id": "thirteenf_top_issuer_value_b",
        "claim_label": "13F top issuer value in latest quarter ($B)",
        "source_files": ["data/processed/13f_holdings.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"${m['thirteenf_top_issuer_value_b']:.1f}B",
    },
    {
        "claim_id": "dtcc_max_daily_trades",
        "claim_label": "DTCC maximum summed daily trade count",
        "source_files": ["data/processed/dtcc_daily_summary.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"{int(m['dtcc_max_daily_trades']):,}",
    },
    {
        "claim_id": "z1_prime_brokerage_share_latest_pct",
        "claim_label": "Prime brokerage share of hedge fund borrowing (latest, %)",
        "source_files": ["data/processed/hedge_fund_analysis.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"{m['z1_prime_brokerage_share_latest_pct']:.1%}",
    },
    {
        "claim_id": "form_pf_us_financial_share_latest_pct",
        "claim_label": "Form PF U.S. financial creditor share (latest, %)",
        "source_files": ["data/processed/form_pf_borrowing_creditor.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"{m['form_pf_us_financial_share_latest_pct']:.1%}",
    },
    {
        "claim_id": "form_pf_non_us_financial_share_latest_pct",
        "claim_label": "Form PF non-U.S. financial creditor share (latest, %)",
        "source_files": ["data/processed/form_pf_borrowing_creditor.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"{m['form_pf_non_us_financial_share_latest_pct']:.1%}",
    },
    {
        "claim_id": "liquidity_30d_mean_gap_pct",
        "claim_label": "Form PF 30-day portfolio-minus-investor liquidity gap (mean, %)",
        "source_files": ["data/processed/form_pf_liquidity.csv", "outputs/reports/advanced_analysis.txt"],
        "generation_step": "advanced_analysis",
        "display": lambda m: f"{m['liquidity_30d_mean_gap_pct']:.1%}",
    },
    {
        "claim_id": "liquidity_30d_dangerous_quarters",
        "claim_label": "Form PF dangerous 30-day liquidity quarters (< -20%)",
        "source_files": ["data/processed/form_pf_liquidity.csv", "outputs/reports/advanced_analysis.txt"],
        "generation_step": "advanced_analysis",
        "display": lambda m: str(int(m["liquidity_30d_dangerous_quarters"])),
    },
    {
        "claim_id": "leverage_adf_pvalue",
        "claim_label": "ADF p-value for Z.1 leverage ratio",
        "source_files": ["outputs/reports/cross_source_tests.csv"],
        "generation_step": "cross_source_analysis",
        "display": lambda m: f"{m['leverage_adf_pvalue']:.4f}",
    },
    {
        "claim_id": "fcm_capital_adequacy_ratio_latest",
        "claim_label": "FCM industry capital adequacy ratio (latest)",
        "source_files": ["data/processed/fcm_monthly_industry.csv"],
        "generation_step": "artifact_metrics",
        "display": lambda m: f"{m['fcm_capital_adequacy_ratio_latest']:.2f}x",
    },
]


def _quarter_sort_value(value):
    return pd.Period(str(value), freq="Q")


def _relative_path(path: Path) -> str:
    return path.relative_to(ROOT_DIR).as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


def _copy_if_exists(src: Path, dest: Path) -> Path | None:
    if not src.exists():
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def snapshot_public_inputs(raw_dir: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR) -> list[Path]:
    """Refresh processed snapshots that public artifacts depend on."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    refreshed = []

    for filename in ("vix_quarterly.csv", "cftc_cot.csv"):
        copied = _copy_if_exists(raw_dir / filename, processed_dir / filename)
        if copied is not None:
            refreshed.append(copied)
        elif (processed_dir / filename).exists():
            refreshed.append(processed_dir / filename)

    holdings_path = processed_dir / "13f_holdings.csv"
    holdings = load_best_13f_holdings(str(raw_dir), expected_funds=HEDGE_FUND_CIKS)
    if not holdings.empty:
        holdings.to_csv(holdings_path, index=False)
    if holdings_path.exists():
        refreshed.append(holdings_path)

    return refreshed


def _load_indexed_frame(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def load_public_data(processed_dir: Path = PROCESSED_DIR) -> tuple[dict[str, pd.DataFrame], list[Path]]:
    """Load the tracked processed snapshot used by the public artifact pipeline."""
    files = {
        "z1": processed_dir / "hedge_fund_analysis.csv",
        "form_pf_gav_nav": processed_dir / "form_pf_gav_nav.csv",
        "form_pf_derivatives": processed_dir / "form_pf_derivatives.csv",
        "form_pf_strategy": processed_dir / "form_pf_strategy.csv",
        "form_pf_notional": processed_dir / "form_pf_notional.csv",
        "form_pf_concentration": processed_dir / "form_pf_concentration.csv",
        "form_pf_liquidity": processed_dir / "form_pf_liquidity.csv",
        "form_pf_borrowing_detail": processed_dir / "form_pf_borrowing_detail.csv",
        "form_pf_borrowing_creditor": processed_dir / "form_pf_borrowing_creditor.csv",
        "swaps_weekly": processed_dir / "swaps_weekly.csv",
        "fcm_monthly_industry": processed_dir / "fcm_monthly_industry.csv",
        "fcm_concentration": processed_dir / "fcm_concentration.csv",
        "dtcc_daily_summary": processed_dir / "dtcc_daily_summary.csv",
        "dtcc_quarterly": processed_dir / "dtcc_quarterly.csv",
        "vix": processed_dir / "vix_quarterly.csv",
        "cot": processed_dir / "cftc_cot.csv",
        "thirteenf": processed_dir / "13f_holdings.csv",
    }

    data = {"z1": _load_indexed_frame(files["z1"])}
    for key, path in files.items():
        if key == "z1":
            continue
        data[key] = pd.read_csv(path, low_memory=False) if path.exists() else pd.DataFrame()

    if "fund_type" in data["form_pf_gav_nav"].columns:
        data["pf_hf"] = data["form_pf_gav_nav"][data["form_pf_gav_nav"]["fund_type"] == "Hedge Fund"].copy()
    else:
        data["pf_hf"] = data["form_pf_gav_nav"].copy()

    existing_paths = [path for path in files.values() if path.exists()]
    return data, existing_paths


def compute_public_metrics(
    data: dict[str, pd.DataFrame],
    cross_results: dict | None = None,
    advanced_results: dict | None = None,
) -> dict[str, float | int | str]:
    """Compute the headline metrics used across public artifacts."""
    metrics = {}

    z1 = data["z1"].copy()
    z1_valid = z1[z1["Total assets"] > 0].copy()
    latest_z1 = z1_valid.iloc[-1]
    first_z1 = z1_valid.iloc[0]
    years = len(z1_valid) / 4
    prior_year_assets = z1_valid["Total assets"].shift(4).iloc[-1]

    metrics["z1_period_start"] = f"{first_z1.name.year} Q{first_z1.name.quarter}"
    metrics["z1_period_end"] = f"{latest_z1.name.year} Q{latest_z1.name.quarter}"
    metrics["z1_quarters"] = int(len(z1_valid))
    metrics["z1_total_assets_start_b"] = float(first_z1["Total assets"])
    metrics["z1_total_assets_latest_b"] = float(latest_z1["Total assets"])
    metrics["z1_total_assets_cagr"] = (
        (metrics["z1_total_assets_latest_b"] / metrics["z1_total_assets_start_b"]) ** (1 / years) - 1
        if years > 0 and metrics["z1_total_assets_start_b"] > 0
        else 0.0
    )
    metrics["z1_total_assets_yoy_pct"] = (
        float(metrics["z1_total_assets_latest_b"] / prior_year_assets - 1) if pd.notna(prior_year_assets) else 0.0
    )
    metrics["z1_leverage_current"] = float(latest_z1["leverage_ratio"])
    metrics["z1_leverage_average"] = float(z1_valid["leverage_ratio"].mean())
    metrics["z1_leverage_peak"] = float(z1_valid["leverage_ratio"].max())
    metrics["z1_leverage_peak_date"] = z1_valid["leverage_ratio"].idxmax().date().isoformat()
    metrics["z1_leverage_trough"] = float(z1_valid["leverage_ratio"].min())
    metrics["z1_leverage_trough_date"] = z1_valid["leverage_ratio"].idxmin().date().isoformat()
    metrics["z1_equity_pct_latest"] = float(latest_z1["equity_pct"])
    metrics["z1_debt_pct_latest"] = float(latest_z1["debt_securities_pct"])
    metrics["z1_cash_pct_latest"] = float(latest_z1["cash_to_assets"])
    metrics["z1_derivative_pct_latest"] = float(latest_z1["derivative_to_assets"])
    metrics["z1_loans_pct_latest"] = float(latest_z1["loans_to_assets"])
    metrics["z1_prime_brokerage_share_latest_pct"] = float(latest_z1["prime_brokerage_pct"])
    metrics["z1_other_secured_share_latest_pct"] = float(latest_z1["other_secured_pct"])
    metrics["z1_unsecured_share_latest_pct"] = float(latest_z1["unsecured_pct"])
    metrics["z1_foreign_borrowing_share_latest_pct"] = float(latest_z1["foreign_borrowing_share"])

    pf_all = data["form_pf_gav_nav"].copy()
    latest_pf_quarter = str(max(pf_all["quarter"], key=_quarter_sort_value))
    pf_all_latest = pf_all[pf_all["quarter"] == latest_pf_quarter].copy()
    pf_hf_latest = data["pf_hf"][data["pf_hf"]["quarter"] == latest_pf_quarter].copy()
    hf_row = pf_hf_latest.iloc[0]

    metrics["form_pf_latest_quarter"] = latest_pf_quarter
    metrics["form_pf_hedge_fund_gav_latest_b"] = float(hf_row["gav"])
    metrics["form_pf_hedge_fund_nav_latest_b"] = float(hf_row["nav"])
    metrics["form_pf_hedge_fund_gav_nav_latest_x"] = float(hf_row["gav_nav_ratio"])
    metrics["form_pf_all_private_gav_latest_b"] = float(pf_all_latest["gav"].sum())
    metrics["form_pf_all_private_nav_latest_b"] = float(pf_all_latest["nav"].sum())
    metrics["form_pf_all_private_gav_nav_latest_x"] = (
        metrics["form_pf_all_private_gav_latest_b"] / metrics["form_pf_all_private_nav_latest_b"]
    )

    derivatives = data["form_pf_derivatives"].copy()
    hf_derivatives = derivatives[derivatives["fund_type"] == "Hedge Fund"].copy()
    latest_derivatives = hf_derivatives.iloc[-1]
    metrics["form_pf_derivatives_latest_b"] = float(latest_derivatives["derivative_value"])
    metrics["form_pf_derivatives_to_nav_latest_x"] = float(latest_derivatives["derivative_pct_nav"])

    concentration = data["form_pf_concentration"].copy()
    latest_concentration_quarter = str(max(concentration["quarter"], key=_quarter_sort_value))
    latest_concentration = concentration[concentration["quarter"] == latest_concentration_quarter].copy()
    top10 = latest_concentration[latest_concentration["top_n"] == "Top 10"]
    top500 = latest_concentration[latest_concentration["top_n"] == "Top 500"]
    metrics["form_pf_top10_nav_share_latest_pct"] = float(top10["nav_share"].iloc[0]) if not top10.empty else 0.0
    metrics["form_pf_top500_nav_share_latest_pct"] = float(top500["nav_share"].iloc[0]) if not top500.empty else 0.0

    borrowing_creditor = data["form_pf_borrowing_creditor"].copy()
    latest_creditor_quarter = str(max(borrowing_creditor["quarter"], key=_quarter_sort_value))
    latest_creditors = borrowing_creditor[borrowing_creditor["quarter"] == latest_creditor_quarter].copy()
    us_fin = latest_creditors[latest_creditors["creditor_type"] == "US Financial"]
    non_us_fin = latest_creditors[latest_creditors["creditor_type"] == "Non-US Financial"]
    metrics["form_pf_creditor_latest_quarter"] = latest_creditor_quarter
    metrics["form_pf_us_financial_share_latest_pct"] = float(us_fin["share"].iloc[0]) if not us_fin.empty else 0.0
    metrics["form_pf_non_us_financial_share_latest_pct"] = (
        float(non_us_fin["share"].iloc[0]) if not non_us_fin.empty else 0.0
    )

    swaps = data["swaps_weekly"].copy()
    swaps["date"] = pd.to_datetime(swaps["date"])
    latest_swaps = swaps.sort_values("date").iloc[-1]
    metrics["swaps_latest_date"] = latest_swaps["date"].date().isoformat()
    metrics["swaps_ir_total_latest_b"] = float(latest_swaps["ir_total"])

    fcm = data["fcm_monthly_industry"].copy()
    fcm["as_of_date"] = pd.to_datetime(fcm["as_of_date"])
    latest_fcm = fcm.sort_values("as_of_date").iloc[-1]
    metrics["fcm_latest_date"] = latest_fcm["as_of_date"].date().isoformat()
    metrics["fcm_capital_adequacy_ratio_latest"] = float(latest_fcm["capital_adequacy_ratio"])
    metrics["fcm_excess_net_capital_latest_b"] = float(latest_fcm["excess_net_capital"] / 1e9)

    dtcc_daily = data["dtcc_daily_summary"].copy()
    dtcc_daily["date"] = pd.to_datetime(dtcc_daily["date"])
    daily_totals = dtcc_daily.groupby("date")["trade_count"].sum()
    metrics["dtcc_max_daily_trades"] = int(daily_totals.max())

    holdings = data["thirteenf"].copy()
    holdings["put_call"] = holdings.get("put_call", "").fillna("")
    metrics["thirteenf_total_rows"] = int(len(holdings))
    long_holdings = holdings[holdings["put_call"].eq("")].copy()
    metrics["thirteenf_long_positions_total"] = int(len(long_holdings))
    latest_report_period = str(max(holdings["report_period"].astype(str), key=_quarter_sort_value))
    latest_long = long_holdings[long_holdings["report_period"].astype(str) == latest_report_period].copy()
    issuer_totals = latest_long.groupby("issuer")["value_usd"].sum().sort_values(ascending=False)
    metrics["thirteenf_report_period_start"] = str(min(holdings["report_period"].astype(str), key=_quarter_sort_value))
    metrics["thirteenf_report_period_end"] = latest_report_period
    metrics["thirteenf_latest_long_value_b"] = float(latest_long["value_usd"].sum() / 1e9)
    metrics["thirteenf_latest_long_positions"] = int(len(latest_long))
    metrics["thirteenf_funds_tracked"] = int(latest_long["fund"].nunique())
    metrics["thirteenf_top_issuer_name"] = issuer_totals.index[0]
    metrics["thirteenf_top_issuer_value_b"] = float(issuer_totals.iloc[0] / 1e9)
    metrics["thirteenf_nvidia_value_b"] = float(issuer_totals.get("NVIDIA CORPORATION", 0) / 1e9)

    if cross_results is not None:
        tests_df = cross_results["test_summary"].copy()
    else:
        tests_df = pd.read_csv(REPORTS_DIR / "cross_source_tests.csv")
    adf_row = tests_df[tests_df["description"].str.contains("Z.1 leverage ratio", na=False)].iloc[0]
    metrics["leverage_adf_pvalue"] = float(adf_row["p_value"])

    if advanced_results is not None:
        liquidity = advanced_results["liquidity"]["mismatch_At most 30 days"]
    else:
        liquidity = pd.DataFrame()
    if not liquidity.empty:
        metrics["liquidity_30d_mean_gap_pct"] = float(liquidity["mismatch"].mean())
        metrics["liquidity_30d_dangerous_quarters"] = int((liquidity["mismatch"] < -0.20).sum())
    else:
        metrics["liquidity_30d_mean_gap_pct"] = 0.0
        metrics["liquidity_30d_dangerous_quarters"] = 0

    return metrics


def write_claims_ledger(metrics: dict[str, float | int | str], report_dir: Path = REPORTS_DIR) -> Path:
    """Write a ledger tying public numeric claims to generated sources."""
    report_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for claim in PUBLIC_CLAIMS:
        rows.append(
            {
                "claim_id": claim["claim_id"],
                "claim_label": claim["claim_label"],
                "value": metrics[claim["claim_id"]],
                "display_value": claim["display"](metrics),
                "source_files": "; ".join(claim["source_files"]),
                "generation_step": claim["generation_step"],
            }
        )

    path = report_dir / "claims_ledger.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def write_executive_summary(metrics: dict[str, float | int | str], report_dir: Path = REPORTS_DIR) -> Path:
    """Write a concise executive summary aligned with the claims ledger."""
    report_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Hedge Fund Industry X-Ray — Executive Summary",
        "",
        f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d')}",
        f"**Data Period:** {metrics['z1_period_start']} to {metrics['z1_period_end']} ({metrics['z1_quarters']} quarters)",
        "**Sources:** 9 (FRED Z.1, Form PF, CFTC Swaps, 13F, EDGAR, CFTC COT, VIX, DTCC, FCM)",
        "",
        "---",
        "",
        "## Key Findings",
        "",
        "### 1. Industry Growth",
        (
            f"Total assets grew from **${metrics['z1_total_assets_start_b']:,.0f}B** "
            f"to **${metrics['z1_total_assets_latest_b']:,.0f}B** over the sample, "
            f"a CAGR of **{metrics['z1_total_assets_cagr']:.1%}**."
        ),
        "",
        "### 2. Leverage Trends",
        f"- Current leverage ratio: **{metrics['z1_leverage_current']:.2f}x**",
        f"- Long-term average: **{metrics['z1_leverage_average']:.2f}x**",
        f"- Peak: **{metrics['z1_leverage_peak']:.2f}x** ({metrics['z1_leverage_peak_date']})",
        f"- Trough: **{metrics['z1_leverage_trough']:.2f}x** ({metrics['z1_leverage_trough_date']})",
        "",
        "### 3. Portfolio Composition (Latest Quarter)",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Equity allocation | {metrics['z1_equity_pct_latest']:.1%} |",
        f"| Debt securities | {metrics['z1_debt_pct_latest']:.1%} |",
        f"| Cash-to-assets | {metrics['z1_cash_pct_latest']:.1%} |",
        f"| Derivatives / assets | {metrics['z1_derivative_pct_latest']:.1%} |",
        f"| Loans / assets | {metrics['z1_loans_pct_latest']:.1%} |",
        "",
        "### 4. Borrowing Structure (Latest Quarter)",
        "| Source | Share |",
        "|--------|-------|",
        f"| Prime brokerage | {metrics['z1_prime_brokerage_share_latest_pct']:.1%} |",
        f"| Other secured | {metrics['z1_other_secured_share_latest_pct']:.1%} |",
        f"| Unsecured | {metrics['z1_unsecured_share_latest_pct']:.1%} |",
        f"| Foreign borrowing share | {metrics['z1_foreign_borrowing_share_latest_pct']:.1%} |",
        "",
        "### 5. Cross-Source Highlights",
        (
            f"- Form PF hedge fund GAV/NAV ratio: **{metrics['form_pf_hedge_fund_gav_nav_latest_x']:.2f}x** "
            f"on **${metrics['form_pf_hedge_fund_gav_latest_b']:,.0f}B** of GAV"
        ),
        f"- CFTC interest-rate swap notional outstanding: **${metrics['swaps_ir_total_latest_b'] / 1000:.1f}T**",
        (
            f"- 13F latest long-equity snapshot: **${metrics['thirteenf_latest_long_value_b']:,.0f}B** "
            f"across **{metrics['thirteenf_funds_tracked']}** tracked funds"
        ),
        f"- FCM industry capital adequacy ratio: **{metrics['fcm_capital_adequacy_ratio_latest']:.2f}x**",
        "",
        "## Provenance",
        "",
        "Every public numeric claim in this summary and the README is traceable in "
        "[`outputs/reports/claims_ledger.csv`](./claims_ledger.csv).",
    ]

    path = report_dir / "executive_summary.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_run_manifest(
    metrics: dict[str, float | int | str],
    input_paths: list[Path],
    generated_figures: list[Path],
    generated_reports: list[Path],
    report_dir: Path = REPORTS_DIR,
) -> Path:
    """Write a provenance manifest for the current artifact run."""
    report_dir.mkdir(parents=True, exist_ok=True)
    coverage = {
        "z1": {
            "start": metrics["z1_period_start"],
            "end": metrics["z1_period_end"],
            "quarters": metrics["z1_quarters"],
        },
        "form_pf": {"quarter": metrics["form_pf_latest_quarter"]},
        "creditors": {"quarter": metrics["form_pf_creditor_latest_quarter"]},
        "swaps": {"latest_date": metrics["swaps_latest_date"]},
        "fcm": {"latest_date": metrics["fcm_latest_date"]},
        "13f": {
            "report_period_start": metrics["thirteenf_report_period_start"],
            "report_period_end": metrics["thirteenf_report_period_end"],
            "rows": metrics["thirteenf_total_rows"],
            "long_rows": metrics["thirteenf_long_positions_total"],
        },
    }
    manifest = {
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "git_commit_sha": _git_commit_sha(),
        "artifact_command": "python -m src.pipeline --artifacts",
        "input_files": [
            {
                "path": _relative_path(path),
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
            for path in sorted(input_paths)
            if path.exists()
        ],
        "source_coverage": coverage,
        "key_headline_metrics": {
            "z1_total_assets_latest_b": metrics["z1_total_assets_latest_b"],
            "form_pf_derivatives_latest_b": metrics["form_pf_derivatives_latest_b"],
            "swaps_ir_total_latest_b": metrics["swaps_ir_total_latest_b"],
            "thirteenf_latest_long_value_b": metrics["thirteenf_latest_long_value_b"],
            "liquidity_30d_mean_gap_pct": metrics["liquidity_30d_mean_gap_pct"],
            "leverage_adf_pvalue": metrics["leverage_adf_pvalue"],
        },
        "generated_outputs": {
            "figures": [_relative_path(path) for path in sorted(generated_figures)],
            "reports": [_relative_path(path) for path in sorted(generated_reports)],
            "notebook": _relative_path(NOTEBOOK_PATH),
        },
    }

    path = report_dir / "run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return path


def execute_notebook_in_place(notebook_path: Path = NOTEBOOK_PATH) -> Path:
    """Execute the public notebook from top to bottom and save outputs in place."""
    os.environ.setdefault("MPLBACKEND", "Agg")
    with notebook_path.open() as f:
        nb = nbformat.read(f, as_version=4)

    client = NotebookClient(
        nb,
        timeout=900,
        kernel_name="python3",
        resources={"metadata": {"path": str(notebook_path.parent)}},
    )
    client.execute()

    with notebook_path.open("w") as f:
        nbformat.write(nb, f)
    return notebook_path


def generate_public_figures(
    data: dict[str, pd.DataFrame],
    advanced_results: dict,
    figures_dir: Path = FIGURES_DIR,
) -> list[Path]:
    """Regenerate the tracked portfolio-facing figures."""
    import matplotlib.pyplot as plt

    figures_dir.mkdir(parents=True, exist_ok=True)
    created = []

    z1 = data["z1"]
    pf_hf = data["pf_hf"]

    figure_calls = [
        (plot_total_assets, (z1,), "total_assets.png"),
        (plot_asset_composition, (z1,), "asset_composition.png"),
        (plot_debt_securities, (z1,), "debt_securities.png"),
        (plot_liability_structure, (z1,), "liability_structure.png"),
        (plot_balance_sheet_overview, (z1,), "balance_sheet_overview.png"),
        (plot_derivative_exposure, (z1,), "derivative_exposure.png"),
        (plot_borrowing_patterns, (z1,), "borrowing_patterns.png"),
        (plot_correlation_heatmap, (z1,), "correlation_heatmap.png"),
        (plot_form_pf_leverage, (pf_hf, z1), "form_pf_leverage.png"),
        (plot_strategy_allocation, (data["form_pf_strategy"],), "strategy_allocation.png"),
        (plot_concentration_trend, (data["form_pf_concentration"],), "concentration_trend.png"),
        (plot_swaps_notional, (data["swaps_weekly"],), "swaps_notional.png"),
        (plot_clearing_rate, (data["swaps_weekly"], data["dtcc_daily_summary"]), "clearing_rate.png"),
        (plot_fcm_capital, (data["fcm_monthly_industry"],), "fcm_capital.png"),
        (plot_fcm_concentration, (data["fcm_concentration"],), "fcm_concentration.png"),
        (plot_dtcc_summary, (data["dtcc_quarterly"],), "dtcc_summary.png"),
        (plot_cross_source_leverage, (z1, pf_hf), "cross_source_leverage.png"),
        (plot_granger_heatmap, (advanced_results["granger"],), "granger_causality_heatmap.png"),
        (
            plot_impulse_response,
            (advanced_results["var"]["irf_df"], advanced_results["var"]["variables"]),
            "var_impulse_response.png",
        ),
        (
            plot_monte_carlo,
            (advanced_results["monte_carlo"], "z1_Total assets"),
            "monte_carlo_z1_total_assets.png",
        ),
        (
            plot_monte_carlo,
            (advanced_results["monte_carlo"], "z1_Total net assets"),
            "monte_carlo_z1_total_net_assets.png",
        ),
        (
            plot_structural_breaks,
            (
                advanced_results["aligned"]["pf_gav_nav_ratio"],
                advanced_results["structural_breaks"]["pf_gav_nav_ratio"],
            ),
            "structural_breaks_pf_gav_nav_ratio.png",
        ),
        (
            plot_structural_breaks,
            (
                advanced_results["aligned"]["swap_ir_cleared_pct"],
                advanced_results["structural_breaks"]["swap_ir_cleared_pct"],
            ),
            "structural_breaks_swap_ir_cleared_pct.png",
        ),
        (
            plot_structural_breaks,
            (advanced_results["aligned"]["vix_mean"], advanced_results["structural_breaks"]["vix_mean"]),
            "structural_breaks_vix_mean.png",
        ),
        (plot_strategy_hhi, (advanced_results["strategy_rotation"]["hhi_df"],), "strategy_hhi.png"),
        (plot_liquidity_mismatch_detail, (advanced_results["liquidity"],), "liquidity_mismatch_detail.png"),
    ]

    for func, args, filename in figure_calls:
        path = figures_dir / filename
        func(*args, save_path=str(path))
        created.append(path)
        plt.close("all")

    return created


def refresh_public_artifacts(
    root_dir: Path = ROOT_DIR,
    execute_notebook: bool = True,
    analysis_results: dict | None = None,
) -> dict[str, object]:
    """Regenerate public figures, reports, notebook outputs, and provenance."""
    del root_dir  # kept for a stable public interface

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    input_paths = snapshot_public_inputs(RAW_DIR, PROCESSED_DIR)
    data, processed_paths = load_public_data(PROCESSED_DIR)
    input_paths = sorted({path.resolve() for path in (input_paths + processed_paths)})

    if analysis_results is None:
        from src.analysis.advanced import run_all_advanced
        from src.analysis.cross_source import run_full_analysis

        cross_results = run_full_analysis(save=True)
        advanced_results = run_all_advanced(save=True)
    else:
        cross_results = analysis_results["cross_source"]
        advanced_results = analysis_results["advanced"]

    metrics = compute_public_metrics(data, cross_results=cross_results, advanced_results=advanced_results)
    generated_figures = generate_public_figures(data, advanced_results, FIGURES_DIR)
    claims_path = write_claims_ledger(metrics, REPORTS_DIR)
    executive_summary_path = write_executive_summary(metrics, REPORTS_DIR)
    notebook_path = execute_notebook_in_place(NOTEBOOK_PATH) if execute_notebook else NOTEBOOK_PATH

    generated_reports = [REPORTS_DIR / name for name in PUBLIC_REPORTS if (REPORTS_DIR / name).exists()]
    if claims_path not in generated_reports:
        generated_reports.append(claims_path)
    if executive_summary_path not in generated_reports:
        generated_reports.append(executive_summary_path)
    manifest_path = write_run_manifest(metrics, input_paths, generated_figures, generated_reports, REPORTS_DIR)
    if manifest_path not in generated_reports:
        generated_reports.append(manifest_path)

    return {
        "metrics": metrics,
        "figures": generated_figures,
        "reports": generated_reports,
        "notebook": notebook_path,
    }
