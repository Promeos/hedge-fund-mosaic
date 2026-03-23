"""Tests for src.analysis.cross_source."""

import pandas as pd

from src.analysis.cross_source import (
    align_quarterly,
)
from src.analysis.cross_source import (
    test_h7_concentration_correlation as run_h7_concentration_correlation,
)


def test_align_quarterly_uses_deduped_rates_notional_clearing():
    """DTCC alignment should dedupe rows and preserve rates-specific clearing."""
    dtcc = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2025-03-28",
                    "2025-03-31",
                    "2025-03-31",
                    "2025-03-31",
                ]
            ),
            "asset_class": ["RATES", "RATES", "RATES", "FOREX"],
            "total_notional_bn": [100.0, 200.0, 220.0, 300.0],
            "cleared_notional_bn": [60.0, 140.0, 176.0, 30.0],
            "cleared_pct": [0.70, 0.72, 0.73, 0.10],
        }
    )

    aligned = align_quarterly({"dtcc": dtcc})

    assert "dtcc_rates_cleared_notional_pct" in aligned.columns
    assert "dtcc_forex_cleared_notional_pct" in aligned.columns
    assert aligned.loc[pd.Timestamp("2025-03-31"), "dtcc_rates_cleared_notional_pct"] == 0.8
    assert aligned.loc[pd.Timestamp("2025-03-31"), "dtcc_forex_cleared_notional_pct"] == 0.1


def test_h7_accepts_value_thousands_and_report_period(monkeypatch, tmp_path):
    """H7 should work with the repo's 13F schema, not require legacy columns."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    holdings = pd.DataFrame(
        {
            "fund": [
                "Fund A",
                "Fund A",
                "Fund B",
                "Fund B",
                "Fund A",
                "Fund A",
                "Fund B",
                "Fund B",
                "Fund A",
                "Fund A",
                "Fund B",
                "Fund B",
                "Fund A",
                "Fund A",
                "Fund B",
                "Fund B",
            ],
            "report_period": [
                "2024Q1",
                "2024Q1",
                "2024Q1",
                "2024Q1",
                "2024Q2",
                "2024Q2",
                "2024Q2",
                "2024Q2",
                "2024Q3",
                "2024Q3",
                "2024Q3",
                "2024Q3",
                "2024Q4",
                "2024Q4",
                "2024Q4",
                "2024Q4",
            ],
            "value_thousands": [
                90,
                10,
                80,
                20,
                85,
                15,
                70,
                30,
                75,
                25,
                60,
                40,
                65,
                35,
                55,
                45,
            ],
        }
    )
    holdings.to_csv(raw_dir / "13f_all_holdings.csv", index=False)

    monkeypatch.setattr("src.analysis.cross_source.RAW", str(raw_dir))

    form_pf_concentration = pd.DataFrame(
        {
            "top_n": ["Top 10"] * 4,
            "quarter": ["2024Q1", "2024Q2", "2024Q3", "2024Q4"],
            "nav_share": [0.10, 0.20, 0.30, 0.40],
        }
    )

    result = run_h7_concentration_correlation(
        {
            "form_pf_concentration": form_pf_concentration,
        }
    )

    assert result["result"] in {"PASS", "FAIL"}
    assert "lacks required columns" not in result["interpretation"]
