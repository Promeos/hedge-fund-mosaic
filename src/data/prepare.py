"""Data cleaning and transformation for FRED Z.1 balance sheet and VIX data.

Merges quarterly balance sheet observations with VIX volatility data,
handling date alignment and numeric coercion. Output is the canonical
analysis-ready DataFrame used by metrics and visualization modules.
"""

from __future__ import annotations

import pandas as pd


def prep_financial_report(df: pd.DataFrame) -> pd.DataFrame:
    """Parse dates and coerce numeric columns. NaN is preserved to distinguish
    missing data from true zeros — critical for ratio and leverage calculations."""
    date_col = df.columns[1]
    numeric_cols = df.columns[2:]

    df[date_col] = pd.to_datetime(df.loc[:, date_col])
    df[numeric_cols] = df.loc[:, numeric_cols].apply(pd.to_numeric, downcast="float", errors="coerce")

    return df


def load_fred_balance_sheet(filepath: str) -> pd.DataFrame:
    """Load FRED Z.1 hedge fund balance sheet data, filtering pre-2012 empty rows.

    The Z.1 table B.101.f (Domestic Hedge Funds) only started in Q4 2012.
    Earlier rows are all zeros/NaN from FRED and should be excluded.
    """
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    # Filter to rows with actual data (Q4 2012 onward)
    df = df.loc["2012-10-01":]
    # Replace remaining zeros with NaN where entire row was zero (pre-reporting)
    return df


def align_vix_to_fred(df_fred: pd.DataFrame, df_vix: pd.DataFrame) -> pd.DataFrame:
    """Merge VIX quarterly data into FRED balance sheet by aligning date conventions.

    FRED uses quarter-start dates (2024-01-01 = Q1), VIX uses quarter-end
    (2024-03-31 = Q1). This aligns them by mapping both to period quarters.
    """
    # Convert both to quarterly period for matching
    fred_quarters = df_fred.index.to_period("Q")
    vix_quarters = df_vix.index.to_period("Q")

    df_vix_aligned = df_vix.copy()
    df_vix_aligned.index = vix_quarters
    df_vix_aligned = df_vix_aligned[~df_vix_aligned.index.duplicated(keep="last")]

    df_out = df_fred.copy()
    df_out.index = fred_quarters
    df_out = df_out.join(df_vix_aligned, how="left")
    df_out.index = df_fred.index  # Restore original datetime index
    return df_out
