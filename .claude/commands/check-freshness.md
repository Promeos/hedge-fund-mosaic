Audit data freshness across all 9 sources and report what needs updating. This is a **read-only** operation — do NOT fetch or modify any data.

## Steps

1. **Scan each data source** in `data/raw/` and determine the latest data point:

   - **FRED Z.1**: Read `hedge_fund_balance_sheet_fred.csv` — find the max date in the date column
   - **VIX**: Read `vix_quarterly.csv` — find the max date
   - **13F**: List `13f_*.csv` files — parse date ranges from filenames (format: `13f_{fund}_{start}_{end}.csv`)
   - **CFTC COT**: Read `cftc_cot.csv` — find the max date in the date column
   - **Swaps**: List `swaps/CFTC_Swaps_Report_*.xlsx` — find the latest date from filenames (format: `MM_DD_YYYY`)
   - **DTCC**: List `dtcc/CFTC_CUMULATIVE_*.zip` — find the latest date from filenames
   - **FCM**: List `fcm/fcm_YYYY_MM.xlsx` — find the latest year/month
   - **Form PF**: List `form_pf/*.xlsx` — find the latest quarter from filenames
   - **Form ADV**: List `form_adv/*.json` — check file modification times

2. **Classify staleness** for each source:
   - **FRESH** (green): Data is within expected update frequency
   - **STALE** (yellow): Older than expected but not critically so
   - **CRITICAL** (red): Significantly behind — analysis quality affected

3. **Check parsed outputs**: Verify `data/processed/` has corresponding CSVs and they're newer than the raw files

4. **Print structured report** showing:
   - Source name, latest data point, staleness classification
   - Recommended action for any STALE or CRITICAL sources
   - Whether parsed CSVs need regeneration

## Expected Freshness Windows

| Source | Update Frequency | Acceptable Lag |
|--------|-----------------|----------------|
| FRED Z.1 | Quarterly | 3 months after quarter-end |
| VIX | Quarterly (resampled) | 7 days |
| 13F | Quarterly | 90 days |
| CFTC COT | Weekly | 7 days |
| Swaps | Weekly | 7 days |
| DTCC | Daily (business days) | 2 business days |
| FCM | Monthly (~2-month lag) | 3 months |
| Form PF | Quarterly | 6 months |
| Form ADV | On-demand | 30 days |
