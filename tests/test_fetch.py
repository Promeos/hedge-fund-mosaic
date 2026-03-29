"""Tests for src.data.fetch — constants and offline-testable logic (no API calls)."""

import pandas as pd

from src.data.fetch import (
    HEDGE_FUND_CIKS,
    HEDGE_FUND_SERIES,
    SEC_HEADERS,
    load_best_13f_holdings,
    normalize_13f_holdings,
)


class TestConstants:
    def test_all_fred_series_ids_start_with_bogz1(self):
        """All Z.1 series IDs should follow the BOGZ1FL62* pattern."""
        for name, sid in HEDGE_FUND_SERIES.items():
            assert sid.startswith("BOGZ1FL62"), f"{name}: {sid} does not match expected prefix"

    def test_all_fred_series_are_quarterly(self):
        """Z.1 series IDs should end with 'Q' for quarterly frequency."""
        for name, sid in HEDGE_FUND_SERIES.items():
            assert sid.endswith("Q"), f"{name}: {sid} is not quarterly"

    def test_series_count(self):
        """Balance sheet should have assets + liabilities + net/memo items."""
        assert len(HEDGE_FUND_SERIES) >= 25

    def test_cik_format(self):
        """CIKs should be 10-digit zero-padded strings."""
        for fund, cik in HEDGE_FUND_CIKS.items():
            assert len(cik) == 10, f"{fund} CIK {cik} is not 10 digits"
            assert cik.isdigit(), f"{fund} CIK {cik} contains non-digits"

    def test_sec_headers_has_user_agent(self):
        assert "User-Agent" in SEC_HEADERS

    def test_expected_funds_present(self):
        expected = {"Citadel Advisors", "Bridgewater Associates", "Renaissance Technologies"}
        assert expected.issubset(set(HEDGE_FUND_CIKS.keys()))


class TestFetchHedgeFundDataCache:
    def test_loads_from_cache(self, tmp_path):
        """When cache file exists, fetch_hedge_fund_data should read it without calling FRED."""
        from src.data.fetch import fetch_hedge_fund_data

        cache_file = tmp_path / "cached.csv"
        dates = pd.date_range("2020-03-31", periods=3, freq="QE")
        df = pd.DataFrame({"Total assets": [10, 11, 12]}, index=dates)
        df.index.name = "Date"
        df.to_csv(cache_file)

        # No fred_client needed — cache should short-circuit
        result = fetch_hedge_fund_data(fred_client=None, series_map={}, cache_path=str(cache_file))
        assert len(result) == 3
        assert "Total assets" in result.columns


class TestThirteenFHelpers:
    def test_normalize_13f_holdings_handles_mixed_value_eras(self):
        df = pd.DataFrame(
            {
                "filing_date": ["2021-11-15", "2026-02-17"],
                "value_thousands": [24_403_796, 20_322_281_328],
            }
        )

        result = normalize_13f_holdings(df)

        assert result.loc[0, "value_unit"] == "thousands"
        assert result.loc[0, "value_usd"] == 24_403_796_000
        assert result.loc[1, "value_unit"] == "usd"
        assert result.loc[1, "value_usd"] == 20_322_281_328

    def test_load_best_13f_holdings_prefers_latest_window_over_stale_aggregate(self, tmp_path):
        stale = pd.DataFrame(
            {
                "fund": ["Fund A"],
                "filing_date": ["2021-05-15"],
                "report_period": ["2021Q1"],
                "value_thousands": [1_000],
            }
        )
        stale.to_csv(tmp_path / "13f_all_holdings.csv", index=False)

        latest_a = pd.DataFrame(
            {
                "fund": ["Fund A"],
                "filing_date": ["2026-02-17"],
                "report_period": ["2025Q4"],
                "value_thousands": [2_000],
            }
        )
        latest_b = pd.DataFrame(
            {
                "fund": ["Fund B"],
                "filing_date": ["2026-02-17"],
                "report_period": ["2025Q4"],
                "value_thousands": [3_000],
            }
        )
        latest_a.to_csv(tmp_path / "13f_fund_a_20240322_20260322.csv", index=False)
        latest_b.to_csv(tmp_path / "13f_fund_b_20240322_20260322.csv", index=False)

        result = load_best_13f_holdings(
            cache_dir=str(tmp_path),
            expected_funds={"Fund A": "1", "Fund B": "2"},
        )

        assert sorted(result["fund"].unique()) == ["Fund A", "Fund B"]
        assert result["report_period"].max() == "2025Q4"

    def test_load_best_13f_holdings_falls_back_to_processed_snapshot(self, tmp_path):
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        snapshot = pd.DataFrame(
            {
                "fund": ["Fund A"],
                "filing_date": ["2026-02-17"],
                "report_period": ["2025Q4"],
                "value_thousands": [2_000],
                "value_unit": ["usd"],
            }
        )
        snapshot.to_csv(processed_dir / "13f_holdings.csv", index=False)

        result = load_best_13f_holdings(cache_dir=str(tmp_path / "raw"))

        assert len(result) == 1
        assert result.loc[0, "report_period"] == "2025Q4"
        assert result.loc[0, "value_usd"] == 2_000
