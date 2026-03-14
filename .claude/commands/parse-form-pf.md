Parse all Form PF supporting data Excel files and build a unified time series dataset.

## Steps

1. Scan `data/raw/form_pf/` for all `.xlsx` files (supporting data files)
2. For each file, extract the quarter from the filename
3. Extract key hedge fund metrics from each file:
   - Tab.2.1: Hedge Fund GAV
   - Tab.2.3: Hedge Fund NAV
   - Tab.2.9: Borrowings % of GAV (Hedge Fund row)
   - Tab.5.1: Derivative value (Hedge Fund row)
   - Tab.6.3: Top 10/25/50/100 concentration
   - Tab.8.16: Long notional by investment type
   - Tab.8.17: Short notional by investment type
   - Tab.8.27: Borrowing detail
   - Tab.8.34: Borrowing by creditor type

4. Build a quarterly DataFrame with all metrics
5. Compute derived metrics:
   - GAV/NAV ratio (leverage proxy)
   - Derivatives/NAV ratio
   - Net exposure by asset class (long - short)
   - Borrowing composition

6. Save to `data/processed/form_pf_hedge_fund_timeseries.csv`
7. Print summary statistics and notable trends

## Notes
- Earlier files may have fewer tabs or different sheet names — handle gracefully
- All values in billions USD
- Cross-reference with FRED Z.1 data for validation