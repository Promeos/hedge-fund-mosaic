Run a full data quality validation sweep across all data sources.

## Steps

1. Check that all expected files exist in `data/raw/`:
   - `hedge_fund_balance_sheet_fred.csv` (30 columns)
   - `vix_quarterly.csv` (5 columns: VIX_mean, VIX_max, VIX_min, VIX_end, VIX_std)
   - `13f_all_holdings.csv` (columns: fund, filing_date, issuer, value_thousands, shares, put_call)
   - `cftc_cot.csv` (columns: date, market, lev_fund_long, lev_fund_short, lev_fund_net)

2. For each file, validate:
   - **Schema:** Expected columns are present with correct types
   - **Completeness:** Count NaN/null values per column. Apply domain-aware severity:
     - **13F `put_call`:** WARN (not FAIL) — most holdings are equities, not options, so null is expected
     - **Swaps NaN columns** (`equity_cleared`, `commodity_total`, etc.): WARN (not FAIL) — asset classes were not reported by the CFTC in early periods
   - **Temporal continuity:** No missing quarters (FRED/VIX), no duplicate dates. Apply composite-key awareness:
     - **DTCC:** Use `(date, asset_class)` as the composite key for duplicate detection, not `date` alone — each date has one row per asset class (COMMODITIES, CREDITS, EQUITIES, FOREX, RATES)
   - **Range checks:** No negative total assets/liabilities, leverage_ratio between 0.5-10x, percentages between 0-1

3. Load the FRED balance sheet using `src.data.prepare.load_fred_balance_sheet()` (filters to post-2012 when Z.1 hedge fund data begins), then compute derived metrics using `src.analysis.metrics.compute_derived_metrics()`. Check for:
   - `inf` or `NaN` in computed ratios (division by zero)
   - Borrowing breakdown sums to ~100% (`prime_brokerage_pct + other_secured_pct + unsecured_pct`)
   - QoQ growth rates bounded (flag changes > 30%)

4. Cross-source checks:
   - VIX date range covers the same period as FRED data
   - 13F fund names match the 8 expected funds in `HEDGE_FUND_CIKS`

5. Print a structured report:
   ```
   DATA QUALITY REPORT
   ===================
   [PASS/WARN/FAIL] Description
   ```

6. Save report to `outputs/reports/data_quality.txt`

## Notes
- WARN-level issues during known market events (COVID 2020-Q1, GameStop 2021-Q1) are expected — note but don't fail
- Run this before any analysis to catch upstream issues early
