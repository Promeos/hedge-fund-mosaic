"""Regression tests for DTCC summary-schema handling."""

from src.data.parse_dtcc import _clean_existing_summary


def test_clean_existing_summary_recovers_legacy_and_current_rows(tmp_path):
    summary_path = tmp_path / "dtcc_daily_summary.csv"
    summary_path.write_text(
        "\n".join(
            [
                (
                    "date,asset_class,trade_count,total_notional_bn,usd_notional_bn,cleared_count,"
                    "cleared_notional_bn,uncleared_notional_bn,cleared_pct,pb_count,pb_pct,"
                    "block_count,block_pct,cleared_notional_pct"
                ),
                "2026-03-13,RATES,10,100.0,90.0,8,70.0,30.0,0.8,1,0.1,2,0.2,0.7",
                "2026-03-14,RATES,20,200.0,180.0,16,150.0,50.0,0.8,0.75,2,0.1,3,0.15,10.0",
            ]
        )
        + "\n"
    )

    cleaned = _clean_existing_summary(str(summary_path))

    assert list(cleaned.columns) == [
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
    assert len(cleaned) == 2
    assert cleaned.loc[cleaned["date"] == "2026-03-13", "avg_trade_size_bn"].iloc[0] == 10.0
    assert cleaned.loc[cleaned["date"] == "2026-03-14", "avg_trade_size_bn"].iloc[0] == 10.0

    rewritten_header = summary_path.read_text().splitlines()[0]
    assert rewritten_header.count(",") + 1 == 15
