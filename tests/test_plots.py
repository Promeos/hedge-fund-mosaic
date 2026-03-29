"""Smoke tests for public plotting functions."""

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest
from matplotlib import pyplot as plt

from src.analysis.metrics import compute_derived_metrics
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
    plot_liquidity_mismatch,
    plot_liquidity_mismatch_detail,
    plot_monte_carlo,
    plot_notional_exposure,
    plot_strategy_allocation,
    plot_strategy_hhi,
    plot_structural_breaks,
    plot_swaps_notional,
    plot_total_assets,
)


@pytest.fixture(autouse=True)
def no_show(monkeypatch):
    monkeypatch.setattr("matplotlib.pyplot.show", lambda: None)
    yield
    plt.close("all")


@pytest.fixture
def plot_inputs(sample_balance_sheet):
    z1 = compute_derived_metrics(sample_balance_sheet.copy())
    z1.index = pd.to_datetime(z1.index)

    pf_hf = pd.DataFrame(
        {
            "quarter": ["2024Q1", "2024Q2", "2024Q3", "2024Q4"],
            "fund_type": ["Hedge Fund"] * 4,
            "gav": [1000, 1100, 1200, 1250],
            "nav": [500, 520, 540, 560],
            "gav_nav_ratio": [2.0, 2.115, 2.222, 2.232],
        }
    )
    pf_strategy = pd.DataFrame(
        {
            "quarter": ["2024Q1", "2024Q1", "2024Q2", "2024Q2", "2024Q3", "2024Q3"],
            "strategy": ["Equity", "Macro", "Equity", "Macro", "Equity", "Macro"],
            "nav": [200, 100, 220, 110, 230, 120],
        }
    )
    pf_notional = pd.DataFrame(
        {
            "quarter": ["2024Q4", "2024Q4", "2024Q4"],
            "investment_type": ["Equity", "FX", "Rates"],
            "long_notional": [300, 250, 200],
            "short_notional": [100, 80, 50],
        }
    )
    pf_concentration = pd.DataFrame(
        {
            "quarter": ["2024Q1", "2024Q2", "2024Q3", "2024Q4"] * 2,
            "top_n": ["Top 10"] * 4 + ["Top 500"] * 4,
            "nav_share": [0.08, 0.081, 0.082, 0.083, 0.54, 0.541, 0.542, 0.543],
        }
    )
    pf_liquidity = pd.DataFrame(
        {
            "quarter": ["2024Q1", "2024Q1", "2024Q2", "2024Q2"],
            "period": ["At most 30 days"] * 4,
            "liquidity_type": [
                "investor_liquidity",
                "portfolio_liquidity",
                "investor_liquidity",
                "portfolio_liquidity",
            ],
            "cumulative_pct": [0.20, 0.55, 0.22, 0.56],
        }
    )
    swaps = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-05", periods=4, freq="W-FRI"),
            "ir_total": [1000, 1010, 1020, 1030],
            "credit_total": [120, 125, 130, 135],
            "fx_total": [220, 225, 230, 235],
            "ir_cleared_pct": [0.8, 0.81, 0.82, 0.83],
            "credit_cleared_pct": [0.5, 0.52, 0.54, 0.56],
            "fx_cleared_pct": [0.35, 0.36, 0.37, 0.38],
        }
    )
    dtcc_daily = pd.DataFrame(
        {
            "date": ["2024-01-05", "2024-01-12", "2024-01-19", "2024-01-26"],
            "asset_class": ["RATES"] * 4,
            "cleared_notional_pct": [0.7, 0.72, 0.74, 0.76],
        }
    )
    fcm_monthly = pd.DataFrame(
        {
            "as_of_date": pd.date_range("2024-01-31", periods=4, freq="ME"),
            "adj_net_capital": [100e9, 102e9, 104e9, 106e9],
            "excess_net_capital": [60e9, 61e9, 62e9, 63e9],
            "capital_adequacy_ratio": [2.1, 2.15, 2.2, 2.25],
        }
    )
    fcm_concentration = pd.DataFrame(
        {
            "as_of_date": pd.date_range("2024-01-31", periods=4, freq="ME"),
            "hhi": [0.07, 0.071, 0.072, 0.073],
            "top5_share": [0.54, 0.541, 0.542, 0.543],
        }
    )
    p_matrix = pd.DataFrame(
        [[np.nan, 0.01], [0.20, np.nan]],
        index=["z1_leverage_ratio", "vix_mean"],
        columns=["z1_leverage_ratio", "vix_mean"],
    )
    irf_df = pd.DataFrame(
        {
            "z1_leverage_ratio -> z1_leverage_ratio": [0.5, 0.3, 0.1],
            "z1_leverage_ratio -> vix_mean": [0.1, 0.05, 0.02],
            "vix_mean -> z1_leverage_ratio": [0.2, 0.1, 0.05],
            "vix_mean -> vix_mean": [0.4, 0.2, 0.1],
        },
        index=[0, 1, 2],
    )
    mc_paths = np.array(
        [
            [100.0, 102.0, 104.0, 106.0],
            [100.0, 99.0, 101.0, 103.0],
            [100.0, 101.0, 98.0, 97.0],
        ]
    )
    mc_results = {}
    for key, current in [("z1_Total assets", 100.0), ("z1_Total net assets", 80.0)]:
        final_returns = mc_paths[:, -1] / mc_paths[:, 0] - 1
        mc_results[key] = {
            "paths": mc_paths if key == "z1_Total assets" else mc_paths * 0.8,
            "current_value": current,
            "var_95": np.percentile(final_returns, 5),
            "cvar_95": final_returns[final_returns <= np.percentile(final_returns, 5)].mean(),
            "prob_negative": float((final_returns < 0).mean()),
            "final_returns": final_returns,
        }
    breaks_result = {
        "name": "Series",
        "segments": [{"mean": 1.0, "std": 0.1}],
        "breaks": [{"date": "2024-06-30", "f_stat": 10.0}],
    }
    strategy_hhi = pd.DataFrame(
        {
            "date": pd.date_range("2024-03-31", periods=4, freq="QE"),
            "hhi": [0.20, 0.21, 0.22, 0.23],
            "top_share": [0.35, 0.36, 0.37, 0.38],
        }
    )
    liquidity_results = {
        "mismatch_At most 30 days": pd.DataFrame(
            {"mismatch": [0.35, 0.33]},
            index=pd.to_datetime(["2024-03-31", "2024-06-30"]),
        ),
        "mismatch_At most 90 days": pd.DataFrame(
            {"mismatch": [0.25, 0.24]},
            index=pd.to_datetime(["2024-03-31", "2024-06-30"]),
        ),
        "mismatch_At most 180 days": pd.DataFrame(
            {"mismatch": [0.15, 0.14]},
            index=pd.to_datetime(["2024-03-31", "2024-06-30"]),
        ),
    }
    dtcc_quarterly = pd.DataFrame(
        {
            "quarter": ["2024Q1", "2024Q1", "2024Q2", "2024Q2"],
            "asset_class": ["RATES", "FOREX", "RATES", "FOREX"],
            "quarter_end_total_notional_bn": [500, 150, 520, 160],
            "quarter_end_cleared_pct": [0.75, 0.15, 0.78, 0.18],
        }
    )

    return {
        "z1": z1,
        "pf_hf": pf_hf,
        "pf_strategy": pf_strategy,
        "pf_notional": pf_notional,
        "pf_concentration": pf_concentration,
        "pf_liquidity": pf_liquidity,
        "swaps": swaps,
        "dtcc_daily": dtcc_daily,
        "fcm_monthly": fcm_monthly,
        "fcm_concentration": fcm_concentration,
        "p_matrix": p_matrix,
        "irf_df": irf_df,
        "variables": ["z1_leverage_ratio", "vix_mean"],
        "mc_results": mc_results,
        "breaks_result": breaks_result,
        "strategy_hhi": strategy_hhi,
        "liquidity_results": liquidity_results,
        "dtcc_quarterly": dtcc_quarterly,
    }


@pytest.mark.parametrize(
    ("filename", "func", "arg_builder"),
    [
        ("total_assets.png", plot_total_assets, lambda d: (d["z1"],)),
        ("asset_composition.png", plot_asset_composition, lambda d: (d["z1"],)),
        ("debt_securities.png", plot_debt_securities, lambda d: (d["z1"],)),
        ("liability_structure.png", plot_liability_structure, lambda d: (d["z1"],)),
        ("balance_sheet_overview.png", plot_balance_sheet_overview, lambda d: (d["z1"],)),
        ("derivative_exposure.png", plot_derivative_exposure, lambda d: (d["z1"],)),
        ("borrowing_patterns.png", plot_borrowing_patterns, lambda d: (d["z1"],)),
        ("correlation_heatmap.png", plot_correlation_heatmap, lambda d: (d["z1"],)),
        ("form_pf_leverage.png", plot_form_pf_leverage, lambda d: (d["pf_hf"], d["z1"])),
        ("strategy_allocation.png", plot_strategy_allocation, lambda d: (d["pf_strategy"],)),
        ("notional_exposure.png", plot_notional_exposure, lambda d: (d["pf_notional"],)),
        ("concentration_trend.png", plot_concentration_trend, lambda d: (d["pf_concentration"],)),
        ("liquidity_mismatch.png", plot_liquidity_mismatch, lambda d: (d["pf_liquidity"],)),
        ("swaps_notional.png", plot_swaps_notional, lambda d: (d["swaps"],)),
        ("clearing_rate.png", plot_clearing_rate, lambda d: (d["swaps"], d["dtcc_daily"])),
        ("fcm_capital.png", plot_fcm_capital, lambda d: (d["fcm_monthly"],)),
        ("fcm_concentration.png", plot_fcm_concentration, lambda d: (d["fcm_concentration"],)),
        ("dtcc_summary.png", plot_dtcc_summary, lambda d: (d["dtcc_quarterly"],)),
        ("cross_source_leverage.png", plot_cross_source_leverage, lambda d: (d["z1"], d["pf_hf"])),
        ("granger_heatmap.png", plot_granger_heatmap, lambda d: (d["p_matrix"],)),
        ("var_impulse_response.png", plot_impulse_response, lambda d: (d["irf_df"], d["variables"])),
        ("monte_carlo.png", plot_monte_carlo, lambda d: (d["mc_results"], "z1_Total assets")),
        ("structural_breaks.png", plot_structural_breaks, lambda d: (d["z1"]["leverage_ratio"], d["breaks_result"])),
        ("strategy_hhi.png", plot_strategy_hhi, lambda d: (d["strategy_hhi"],)),
        ("liquidity_mismatch_detail.png", plot_liquidity_mismatch_detail, lambda d: (d["liquidity_results"],)),
    ],
)
def test_plot_smoke_generates_png(tmp_path, plot_inputs, filename, func, arg_builder):
    save_path = tmp_path / filename
    func(*arg_builder(plot_inputs), save_path=str(save_path))
    assert save_path.exists()
    assert save_path.stat().st_size > 0
