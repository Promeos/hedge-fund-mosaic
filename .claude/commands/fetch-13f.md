Fetch current 13F holdings for all 8 tracked hedge funds using the rolling 2-year window.

## Tracked Funds

The funds are defined in `HEDGE_FUND_CIKS` in `src/data/fetch.py`:
- Citadel Advisors, Bridgewater Associates, Renaissance Technologies
- Point72 Asset Management, Two Sigma Investments
- D.E. Shaw & Co, Millennium Management, AQR Capital Management

## Steps

1. **Check current 13F cache** in `data/raw/`:
   - List all `13f_*.csv` files
   - Parse date ranges from filenames
   - Identify which files cover old date windows (pre-2024)

2. **Run the fetcher** with rolling 2-year defaults:
   ```bash
   python3 -c "
   from src.data.fetch import fetch_13f_holdings, HEDGE_FUND_CIKS
   import pandas as pd, os, time
   holdings = []
   for name, cik in HEDGE_FUND_CIKS.items():
       print(f'Fetching {name}...')
       df = fetch_13f_holdings(cik, name, cache_dir='data/raw')
       if not df.empty and 'value_thousands' in df.columns:
           holdings.append(df)
       time.sleep(0.2)
   if holdings:
       combined = pd.concat(holdings, ignore_index=True)
       combined.to_csv('data/raw/13f_all_holdings.csv', index=False)
       print(f'Total: {len(combined)} holdings across {combined[\"fund\"].nunique()} funds')
   "
   ```

3. **Report results**:
   - Number of filings found per fund
   - Date range of holdings
   - Total portfolio value across all funds
   - Top 10 holdings by value

4. **Note**: Old cache files (2020-2021 window) are preserved — the new date window creates separate cache files. Delete old files manually if desired.
