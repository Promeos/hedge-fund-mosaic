"""Tests for src.analysis.advanced."""

import pandas as pd

from src.analysis.advanced import thirteenf_concentration


def test_thirteenf_concentration_normalizes_post_2022_raw_values(monkeypatch):
    """Post-2022 raw 13F values should stay in dollars, not be scaled by 1000."""
    holdings = pd.DataFrame(
        {
            "fund": ["Fund A", "Fund A", "Fund A", "Fund B"],
            "report_period": ["2025Q4", "2025Q4", "2025Q4", "2025Q4"],
            "filing_date": ["2026-02-14", "2026-02-14", "2026-02-14", "2026-02-14"],
            "issuer": ["Issuer X", "Issuer Y", "Issuer Option", "Issuer X"],
            "value_thousands": [100, 50, 999, 30],
            "value_unit": ["usd", "usd", "usd", "usd"],
            "put_call": ["", "", "CALL", ""],
        }
    )

    monkeypatch.setattr("src.analysis.advanced.load_best_13f_holdings", lambda *args, **kwargs: holdings)

    result = thirteenf_concentration({})

    assert result["overlap"].loc["Issuer X", "total_value"] == 130

    fund_a = result["fund_hhi"][result["fund_hhi"]["fund"] == "Fund A"].iloc[0]
    assert fund_a["top_holding"] == "Issuer X"
    assert fund_a["total_value"] == 150
