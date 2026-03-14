Parse all CFTC weekly swap report Excel files and build time series datasets.

## Steps

1. Scan `data/raw/swaps/` for all `.xlsx` files
2. For each file, extract the date from the filename
3. From each file, extract:
   - **Sheet 1**: IR notional outstanding (total, cleared, uncleared)
   - **Sheet 1**: Credit notional outstanding (total, cleared, uncleared)
   - **Sheet 1**: FX notional outstanding (if available, post-2018)
   - **Sheet 2**: Counterparty split (SD/MSP vs Others)
   - **Sheet 7a**: IR product breakdown (Basis, Fixed-Float, OIS, Swaption)
   - **Sheet 13a**: Credit product breakdown (Index/Tranche, by region, cleared/uncleared)
   - **Sheet 19a**: FX product breakdown (if available)

4. Build weekly DataFrames:
   - `swaps_notional_weekly.csv` — headline notional by asset class
   - `swaps_credit_weekly.csv` — credit detail (HY vs IG, by region)
   - `swaps_ir_products_weekly.csv` — IR product breakdown

5. Aggregate to quarterly for alignment with FRED and Form PF data
6. Save all to `data/processed/`
7. Print summary: date range, total records, notable spikes

## Notes
- Handle missing sheets gracefully (FX data starts Oct 2018, equity/commodity removed Oct 2015)
- Government shutdown gap: Dec 22 2018 – Jan 26 2019
- All values in millions USD (convert to billions for cross-source alignment)
- Early files (2013) may have slightly different structures