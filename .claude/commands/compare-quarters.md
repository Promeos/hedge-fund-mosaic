Compare two quarters side-by-side and highlight the biggest changes across all data sources.

## Arguments

- `quarter1` (optional): Earlier quarter, e.g., "2024Q3". Defaults to second-latest available quarter.
- `quarter2` (optional): Later quarter, e.g., "2024Q4". Defaults to latest available quarter.

Parse quarter arguments from the user's message. If none provided, auto-detect the two most recent quarters in the processed data.

## Steps

1. **Load processed data** for both quarters from `data/processed/`:
   - Z.1 balance sheet metrics
   - Form PF summary metrics
   - Swaps quarterly aggregates
   - DTCC quarterly summaries
   - FCM industry monthly (use quarter-end month)
   - VIX quarterly
   - COT positioning (use quarter-end week)

2. **Compute deltas** for all derived metrics:
   - Absolute change (Q2 value - Q1 value)
   - Percentage change ((Q2 - Q1) / |Q1| * 100)
   - Direction (↑ / ↓ / →)

3. **Rank changes** by absolute percentage magnitude across all metrics

4. **Print top 10 biggest moves**:
   ```
   ══════════════════════════════════════════════════════════
     QUARTER COMPARISON — {Q1} vs {Q2}
   ══════════════════════════════════════════════════════════
   Rank  Metric                    Q1 Value   Q2 Value   Change
   ────  ────────────────────────  ─────────  ─────────  ──────
    1    foreign_borrowing_share   32.1%      38.5%      ↑ +6.4pp
    2    derivative_to_assets      8.2%       6.1%       ↓ -25.6%
    3    fcm_hhi                   1,850      2,100      ↑ +13.5%
   ...
   ══════════════════════════════════════════════════════════
   ```

5. **Cross-source consistency check**: For each big move, note whether the direction is confirmed by other sources:
   - e.g., "leverage_ratio ↑ in Z.1 — confirmed by Form PF GAV/NAV ↑"
   - e.g., "equity_pct ↓ in Z.1 — but 13F total value ↑ — investigate divergence"

6. **Print summary** with 2-3 sentence narrative of the quarter's key themes.
