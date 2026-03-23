Print a fast summary of the latest data point from each source. Console output only — no charts, no saved files.

## Steps

1. **Load the most recent data point** from each processed dataset in `data/processed/`:

   - **Z.1 Balance Sheet** (`hedge_fund_balance_sheet.csv`): Latest quarter leverage ratio, total assets, cash-to-assets, equity %
   - **Form PF** (`form_pf_summary.csv` or similar): Latest GAV, NAV, GAV/NAV ratio, strategy HHI
   - **Swaps** (`swaps_quarterly.csv`): Latest IR/Credit/FX notional, clearing rates
   - **DTCC** (`dtcc_quarterly.csv`): Latest trade count, cleared %, PB %, avg trade size
   - **FCM** (`fcm_industry_monthly.csv`): Latest total capital, customer seg, capital adequacy
   - **VIX** (`vix_quarterly.csv` in `data/raw/`): Latest quarterly VIX level
   - **COT** (`cftc_cot.csv` in `data/raw/`): Latest net positioning
   - **13F** (`13f_all_holdings.csv` in `data/raw/`): Top 5 holdings by value, total AUM

2. **Compute percentile ranks** for key metrics against their full historical series:
   - Flag metrics at historical extremes (>95th or <5th percentile) with ⚠️
   - Show the percentile rank next to each metric

3. **Print structured summary**:
   ```
   ══════════════════════════════════════════
     QUICK STATS — {latest quarter}
   ══════════════════════════════════════════
   Z.1 Balance Sheet
     Total Assets:      $X.X T  (QoQ: +X.X%)
     Leverage Ratio:    X.Xx     [XX pctile]
     Cash-to-Assets:    X.X%     [XX pctile]
     Equity Allocation: XX.X%    [XX pctile]

   Form PF
     GAV:               $X.X T
     NAV:               $X.X T
     GAV/NAV Ratio:     X.Xx     [XX pctile]

   Derivatives (Swaps)
     IR Notional:       $XXX T   (~XX% cleared)
     Credit Notional:   $X T     (~XX% cleared)
     FX Notional:       $XX T    (~XX% cleared)

   FCM Industry
     Total Capital:     $XXX B
     Customer Seg:      $XXX B
     Capital Adequacy:  X.Xx

   Market
     VIX (quarterly):   XX.X     [XX pctile]
   ══════════════════════════════════════════
   ```

4. **Do NOT** generate charts, save files, or run analysis — this is a quick read-only snapshot.
