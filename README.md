# Hedge Fund Mosaic

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19187969.svg)](https://doi.org/10.5281/zenodo.19187969)

Piecing together the U.S. hedge fund industry from 9 public regulatory data sources.

An open-source intelligence project assembling the financial picture of U.S. hedge funds — balance sheets, derivatives, borrowing, positioning, and fund-level holdings — from fragments no one else combines.

**Reproducibility:** Every claim is backed by [`claims_ledger.csv`](outputs/reports/claims_ledger.csv) with source file, cell reference, and refresh timestamp. Pipeline manifest: [`run_manifest.json`](outputs/reports/run_manifest.json).

![Form PF — Hedge Fund Leverage](docs/hero_form_pf_leverage.png)

## The Thesis

The hedge fund industry reports to a dozen different regulators in a dozen different formats. No single source tells the full story. But combined, they do.

This project pulls from **9 public data sources** across the Federal Reserve, SEC, CFTC, DTCC, and CBOE to build a unified picture of:

- **$3.3 trillion** in total assets (Fed Z.1 Q3 2025) — with **$12.6T** in gross assets via Form PF
- **$20.2 trillion** in derivative exposure — 3.7x their net asset value
- **$415 trillion** in interest rate swap notional flowing through the system weekly
- **283,362 long equity/ETF positions** across 8 of the largest funds — report periods **2024Q1–2025Q4**, amendment-deduped
- **Over 1 million OTC derivative trades per day** flowing through DTCC
- The complete **borrowing, leverage, and counterparty structure** of an industry that answers to no single regulator

## Data Sources

| # | Source | What It Reveals | Coverage |
|---|--------|----------------|----------|
| 1 | **Federal Reserve Z.1** | Aggregate balance sheet (Table B.101.f) — assets, liabilities, net worth | Raw FRED series span 1945–2025; usable hedge fund observations begin 2012 Q4 |
| 2 | **SEC Form PF** | Private fund statistics — GAV, NAV, leverage, derivatives, borrowing by creditor, strategy allocation, concentration | 2013–2025, quarterly + monthly |
| 3 | **CFTC Weekly Swaps** | OTC derivatives market — interest rate, credit, and FX swap notional, volumes, counterparty splits | 2013–2026, weekly |
| 4 | **SEC EDGAR 13F** | Fund-level equity holdings for Citadel, Bridgewater, Renaissance, Point72, Two Sigma, D.E. Shaw, Millennium, AQR — amendment-deduped | Bundled local cache currently spans report periods **2024Q1–2025Q4** |
| 5 | **SEC EDGAR Submissions** | Complete filing history, SC 13G (5%+ ownership stakes), Form ADV registration | 1996–2026 |
| 6 | **CFTC COT** | Leveraged fund positioning in equity index futures | Weekly |
| 7 | **CBOE VIX** | Market volatility index | Daily, aggregated quarterly |
| 8 | **DTCC Swap Repository** | Trade-level OTC derivative transactions — notional, counterparty type, clearing status, block-trade and prime-broker flags | Local snapshot: 2025-03-13 to 2026-03-13, daily |
| 9 | **CFTC FCM Financials** | Broker-level adjusted net capital, excess capital, customer segregated funds, cleared swap segregation | Local snapshot: 2022-01 to 2026-01, monthly |

## What We've Found So Far

### The Industry Is 4x Larger Than Reported
The Fed's Z.1 shows **$3.26T** in hedge fund assets (Q3 2025, all-time high, +16% YoY). SEC Form PF shows **$12.6T in gross assets** and **$20.2T in derivatives**. The difference is leverage and off-balance-sheet exposure that the Fed's flow-of-funds framework doesn't capture.

Hedge funds are only part of the picture. Form PF covers all private funds — and the total is staggering:

| Fund Type | Gross Assets (GAV) | Net Assets (NAV) | Leverage (GAV/NAV) |
|-----------|-------------------|-------------------|-------------------|
| **Hedge Funds** | **$12.6T** | **$5.4T** | **2.32x** |
| Private Equity | $7.9T | $7.3T | 1.09x |
| Other Private Funds | $1.9T | $1.6T | 1.14x |
| Securitized Asset Funds | $1.1T | $0.4T | 2.74x |
| Real Estate Funds | $1.1T | $0.9T | 1.28x |
| Venture Capital | $0.5T | $0.4T | 1.09x |
| Liquidity Funds | $0.4T | $0.4T | 1.03x |
| **All Private Funds** | **$25.5T** | **$16.4T** | **1.55x** |

That's **$25.5 trillion** in gross assets across the U.S. private fund industry (Q1 2025) — and hedge funds carry by far the highest leverage at 2.32x. Securitized asset funds are even more leveraged at 2.74x, but at a fraction of the size.

### Extreme Concentration
- Top 10 funds control **8.2%** of industry NAV
- Top 500 funds control **54.8%**
- Combined 13F long equity value across 8 mega funds: **$831B** (2025Q4 snapshot, options excluded)
- NVIDIA held by all 8 funds (**$19.1B** combined); iShares ETFs are the #1 line item (**$20.3B**)
- Citadel filed **854 SC 13G forms** (5%+ ownership in 854 companies)

### The Borrowing Machine
- **79%** of hedge fund borrowing flows through prime brokerage (Fed Z.1, Q3 2025)
- Only **0.7%** is unsecured — **99.3%** is collateralized (Form PF, 2025-03)
- In **2025Q1**, **63.9%** of creditors are U.S. financial institutions and **35.3%** are non-U.S. financial institutions
- In **2025-03**, qualifying hedge funds held **$2.8T** in reverse repo and **$2.6T** in prime-broker financing

### Leverage Looks Safe — Until You Measure It Properly
The Fed's Z.1 leverage ratio (liabilities / net assets) averages **0.43x** and appears to oscillate around that mean — suggesting the industry self-corrects. But Z.1 only captures on-balance-sheet leverage.

SEC Form PF tells a different story. The **GAV/NAV ratio** — gross asset value divided by net asset value — captures the full picture including off-balance-sheet and derivative exposure. It has climbed from **1.76x** (2013 Q4) to **2.32x** (2025 Q1, all-time high) with a statistically significant upward trend (+0.008x per quarter, p≈0.00). An Augmented Dickey-Fuller test confirms GAV/NAV is **non-stationary** (p=0.99) — it is not mean-reverting. It has never pulled back to its historical average.

Both measures hit all-time highs simultaneously: Z.1 at **0.485x** (Q3 2025), GAV/NAV at **2.32x** (Q1 2025). The Z.1 data gives a false sense of safety — the leverage that matters most has been building uninterrupted for 12 years.

### The Derivatives Iceberg
- **$4.8T long / $4.9T short** in interest rate derivatives — nearly perfectly hedged
- **$1.8T long / $945B short** in equities — net long $883B
- **$517B long / $639B short** in credit — **net short $122B** (betting on defaults)
- The weekly CFTC swaps data shows **$415T** in IR notional outstanding — the plumbing beneath everything

### The Contagion Chain

The individual findings above aren't independent — they're links in a statistically verified cascade. Granger causality tests (5/28 significant pairs) show that volatility shocks *cause* leverage adjustments (VIX → GAV/NAV, p=0.002) and broker capital stress (VIX → FCM excess capital, p=0.002), while leverage shifts feed back into volatility (Z.1 leverage → VIX, p=0.025). This isn't correlation — the causal direction is testable and confirmed.

The accelerants are already in place:

- **Liquidity cushion:** Portfolio liquidity exceeds investor redemption terms by **46.5 percentage points** at the 30-day horizon on average; the cushion narrows in high-VIX quarters but stays positive in the bundled sample
- **Rising broker concentration:** FCM market HHI is trending upward (p<0.001) — fewer brokers are absorbing more risk each cycle, widening the blast radius when one breaks
- **Leverage is at the all-time peak:** 0.485x (Q3 2025) — the highest in 52 quarters of Z.1 data, with the fastest 5-quarter buildup on record. Monte Carlo simulation (10K paths, 8Q horizon) gives VaR 95% = -1.7% and P(negative) = 7.1%

The dominoes are: **volatility spike → fund deleveraging → broker capital strain → further forced selling** — and the system is more concentrated while its liquidity cushion compresses when volatility rises.

### Cross-Source Statistical Tests

The current suite emits **18 result rows**: 8 named cross-source tests plus 10 ADF/Mann-Kendall checks on key series. Key findings:

| Test | Result | p-value | What It Means |
|------|--------|---------|---------------|
| **Liquidity gap vs VIX** | **PASS** | 0.005 | The 30-day portfolio-minus-investor liquidity cushion narrows in high-VIX quarters, but remains positive in the bundled sample |
| **VIX → GAV/NAV (Granger)** | **PASS** | 0.002 | Volatility *causes* leverage changes — fear drives deleveraging |
| **Z.1 leverage stationarity** | FAIL | 0.139 | Non-stationary under AIC lag selection in the current run (ADF=-2.410); default-lag variants are more favorable |
| **Form PF GAV trend** | **PASS** | 0.000 | Industry gross assets trending strongly upward |
| **Form PF GAV/NAV trend** | **PASS** | 0.000 | Leverage ratio trending upward — funds are levering up |
| **Z.1 ~ Form PF cointegration** | FAIL | 0.173 | The two measures of industry size move independently |
| **Z.1/Form PF ratio stability** | FAIL | 0.944 | The gap between Fed and SEC views of the industry is *widening* |
| **CFTC IR vs DTCC rates clearing** | FAIL | 0.993 | Rates clearing measures are not equivalent within a 10pp band in the local 2025Q1–2026Q1 overlap |
| **Form PF → Z.1 leverage** | FAIL | 0.086 | Borderline — SEC data nearly predicts Fed data at 10% level |

Additionally, the advanced analysis found **3 structural breaks** in Form PF GAV/NAV (2017Q3, 2020Q2, 2023Q1) and **2 cointegrating relationships** between Form PF GAV and IR/Credit swap notional — the derivatives market and fund leverage are locked in long-run equilibrium. Full test results are saved to `outputs/reports/cross_source_tests.csv`.

<details>
<summary><strong>Statistical methods used and why</strong></summary>

<br>

| Method | Where Used | What It Tests | Why This Test |
|--------|-----------|---------------|---------------|
| **Augmented Dickey-Fuller (ADF)** | Z.1 leverage ratio, Form PF GAV, GAV/NAV, VIX, COT net positioning | Tests whether a time series has a unit root (non-stationary). Null hypothesis: the series is non-stationary. | Determines whether metrics like leverage mean-revert to a long-run average or trend indefinitely. A stationary leverage ratio implies self-correcting behavior; a non-stationary one implies structural drift. |
| **Mann-Kendall trend test** | Same series as ADF | Non-parametric test for monotonic trend. Does not assume normality. | Complements ADF — a series can be stationary (ADF) but still have a significant trend (Mann-Kendall). Used because financial time series often violate normality assumptions. |
| **Granger causality** | All pairwise combinations of VIX, Z.1 leverage, GAV/NAV, COT positioning, swap notional, FCM excess capital | Tests whether past values of series X improve predictions of series Y beyond Y's own history. | Establishes directional causation between data sources — e.g., does a VIX spike *cause* subsequent deleveraging, or do they just co-move? Identifying causal chains is critical for understanding systemic transmission. |
| **Engle-Granger cointegration** | Z.1 total assets vs Form PF GAV; Form PF GAV vs swap notional | Tests whether two non-stationary series share a long-run equilibrium — they can diverge short-term but are bound together over time. | If the Fed and SEC measures of industry size are cointegrated, they're measuring the same thing with different lags. If not, they're capturing fundamentally different phenomena. |
| **Two-sample t-test (Welch's)** | Liquidity gap in high-VIX vs low-VIX quarters | Tests whether the mean of a metric differs between two groups. Welch's variant does not assume equal variance. | Determines whether the liquidity mismatch (investor-redeemable minus portfolio-liquid) is significantly worse during stress periods. A significant result means liquidity risk is procyclical. |
| **TOST equivalence test** | CFTC swap clearing % vs DTCC clearing % | Tests whether two measures are equivalent within a specified margin (10 percentage points). | Standard hypothesis tests can only reject equality — they can't confirm it. TOST flips this: it tests whether two data sources agree closely enough to be interchangeable. |
| **Spearman rank correlation** | FCM customer segregation vs COT net positioning | Non-parametric correlation that measures monotonic (not just linear) relationships. | Used for cross-source validation where the relationship may be non-linear — e.g., does broker capital move in the same direction as futures positioning? |
| **Bai-Perron structural break detection** | Form PF GAV/NAV ratio | Identifies dates where the statistical properties of a time series change abruptly. | Locates regime shifts — points where the leverage relationship fundamentally changed (e.g., post-COVID, post-rate-hikes). These are not gradual trends but discrete structural changes. |
| **Monte Carlo simulation** | Z.1 total assets, liabilities, net assets | Generates 10,000 forward paths using historical return distributions to estimate Value-at-Risk and probability of drawdown. | Provides probabilistic risk estimates rather than point forecasts. VaR 95% tells you the worst-case quarterly loss you'd expect 19 out of 20 times. |
| **Vector Autoregression (VAR)** | Cross-source aligned quarterly data | Models multiple time series simultaneously, capturing how each variable responds to shocks in the others. | Enables impulse response analysis — if VIX spikes by 1 standard deviation, how do leverage, capital, and positioning respond over the next 8 quarters? |

</details>

## Visualizations

20+ publication-quality charts generated to `outputs/figures/`:

| Category | Charts |
|----------|--------|
| **Z.1 Balance Sheet** | Total assets, asset composition, debt securities, liability structure, balance sheet overview, derivative exposure, borrowing patterns, correlation heatmap |
| **Form PF** | GAV/NAV leverage, strategy allocation, concentration trends |
| **CFTC Swaps** | Clearing rates, notional outstanding |
| **FCM** | Capital & adequacy, market concentration |
| **DTCC** | Notional by asset class, clearing rates |
| **EDGAR** | Filing volume by fund |
| **Cross-Source** | Z.1 vs Form PF leverage comparison |

## Data Dictionary

All processed CSVs are written to `data/processed/`. Monetary values are in **billions USD** unless noted. Dates use quarterly (`2025Q1`) or monthly (`2025-03`) format.

<details>
<summary><strong>Federal Reserve Z.1 (3 files)</strong></summary>

<br>

**`hedge_fund_analysis.csv`** — 52 rows, quarterly (Q4 2012 – Q3 2025)

The primary analysis dataset. Fed Z.1 Table B.101.f balance sheet items joined with VIX and derived metrics.

| Column | Description |
|--------|-------------|
| `Total assets` | Aggregate hedge fund assets ($B) |
| `Total liabilities` | Aggregate liabilities ($B) |
| `Total net assets` | Assets minus liabilities ($B) |
| `Corporate equities; asset` | Equity holdings ($B) |
| `Derivatives (long value)` | Derivative exposure, long side ($B) |
| `Loans, total secured borrowing via prime brokerage; liability` | Prime brokerage borrowing ($B) |
| `VIX_mean`, `VIX_max`, `VIX_end` | Quarterly VIX statistics |
| `leverage_ratio` | Total liabilities / total net assets |
| `cash_to_assets` | (Deposits + cash + MMF) / total assets |
| `equity_pct` | Corporate equities / total assets |
| `derivative_to_assets` | Derivatives (long) / total assets |
| `prime_brokerage_pct` | Prime brokerage / total loans (liability) |
| `foreign_borrowing_share` | Foreign / (domestic + foreign) borrowing |
| `total_assets_qoq`, `total_assets_yoy` | Quarter-over-quarter and year-over-year growth |
| `leverage_change` | Quarter-over-quarter change in leverage ratio |

**`hedge_fund_metrics.csv`** — 319 rows. Same schema, includes pre-2012 quarters (many zeros).

**`statistical_analysis.csv`** — 319 rows. Same as metrics plus `regime` column from regime detection.

</details>

<details>
<summary><strong>SEC Form PF (19 files)</strong></summary>

<br>

**`form_pf_gav_nav.csv`** — 392 rows

| Column | Description |
|--------|-------------|
| `fund_type` | Hedge Fund, Private Equity, Liquidity Fund, etc. |
| `quarter` | e.g., `2025Q1` |
| `gav` | Gross asset value ($B) |
| `nav` | Net asset value ($B) |
| `gav_nav_ratio` | GAV / NAV — true leverage proxy |

**`form_pf_borrowing_detail.csv`** — 882 rows, monthly

| Column | Description |
|--------|-------------|
| `type` | Secured, Unsecured, or Total |
| `subtype` | Reverse Repo, Prime Broker, Other Secured, or Subtotal |
| `month` | e.g., `2025-03` |
| `amount_bn` | Borrowing amount ($B) |

**`form_pf_borrowing_creditor.csv`** — 196 rows, quarterly

| Column | Description |
|--------|-------------|
| `creditor_type` | US Financial, Non-US Financial, US Non-Financial, Non-US Non-Financial |
| `share` | Fraction of total borrowing (0–1) |

**`form_pf_notional.csv`** — 5,145 rows, monthly

| Column | Description |
|--------|-------------|
| `investment_type` | e.g., Interest Rate Derivatives, Credit Derivatives, Listed Equities |
| `long_notional` | Long exposure ($B) |
| `short_notional` | Short exposure ($B) |
| `net_exposure` | Long minus short ($B) |

**`form_pf_concentration.csv`** — 294 rows, quarterly

| Column | Description |
|--------|-------------|
| `top_n` | Top 10, 25, 50, 100, 250, or 500 |
| `nav_share` | Share of industry NAV (0–1) |
| `gav_share`, `borrowing_share`, `derivative_share` | Corresponding shares |

**`form_pf_strategy.csv`** — 441 rows, quarterly

| Column | Description |
|--------|-------------|
| `strategy` | Equity, Credit, Macro, Multi-Strategy, Relative Value, etc. |
| `gav`, `nav`, `borrowing` | Strategy-level aggregates ($B) |

**`form_pf_liquidity.csv`** — 882 rows, quarterly

| Column | Description |
|--------|-------------|
| `period` | At most 1 day, 7 days, 30 days, 90 days, 180 days, 365 days |
| `cumulative_pct` | Cumulative fraction liquidatable/redeemable (0–1) |
| `liquidity_type` | `investor_liquidity`, `portfolio_liquidity`, or `financing_liquidity` |

**`form_pf_metric_liquidity_mismatch.csv`** — 49 rows, quarterly

| Column | Description |
|--------|-------------|
| `portfolio_30d` | Fraction of portfolio liquidatable in 30 days |
| `investor_30d` | Fraction of investor capital redeemable in 30 days |
| `liquidity_mismatch_30d` | portfolio_30d minus investor_30d |

**Other Form PF files:** `form_pf_derivatives.csv` (derivative value by fund type), `form_pf_fund_counts.csv` (fund counts by type), `form_pf_fair_value.csv` (Level 1/2/3 fair value), `form_pf_geography.csv` (geographic allocation), `form_pf_leverage_dist.csv` (leverage ratio distribution), `form_pf_sector.csv` (sector allocation), `form_pf_borrowing_pct.csv` (borrowing as % of GAV), `form_pf_metric_concentration_top10.csv`, `form_pf_metric_hf_gav_nav.csv`, `form_pf_metric_strategy_hhi.csv`, `form_pf_metric_latest_notional.csv`.

</details>

<details>
<summary><strong>CFTC Weekly Swaps (3 files)</strong></summary>

<br>

**`swaps_weekly.csv`** — 605 rows, weekly (2013–2026)

| Column | Description |
|--------|-------------|
| `date` | Report date |
| `ir_total` | Interest rate swap notional outstanding ($B) |
| `ir_cleared`, `ir_uncleared` | Cleared vs uncleared IR notional ($B) |
| `ir_cleared_pct` | Fraction cleared (0–1) |
| `credit_total`, `fx_total`, `equity_total`, `commodity_total` | Notional by asset class ($B) |
| `credit_cleared_pct`, `fx_cleared_pct` | Clearing rates by asset class |

**`swaps_quarterly.csv`** — 51 rows. Quarterly aggregation with `weeks` count.

**`swaps_weekly_long.csv`** — 5,733 rows. Long-format with `metric`, `value_millions`, `value_billions`.

</details>

<details>
<summary><strong>DTCC Swap Repository (2 files)</strong></summary>

<br>

**`dtcc_daily_summary.csv`** — 1,309 rows, daily (2025–2026)

| Column | Description |
|--------|-------------|
| `date` | Trading date |
| `asset_class` | Commodity, Credit, Equity, ForeignExchange, InterestRate |
| `trade_count` | Number of trades |
| `total_notional_bn` | Total notional ($B) |
| `cleared_pct` | Fraction of trades cleared (0–1) |
| `pb_pct` | Fraction involving prime brokerage (0–1) |
| `block_pct` | Fraction that are block trades (0–1) |

**`dtcc_quarterly.csv`** — 25 rows. Quarter-end snapshots by asset class.

</details>

<details>
<summary><strong>CFTC FCM Financials (5 files)</strong></summary>

<br>

**`fcm_monthly_industry.csv`** — 49 rows, monthly (2022–2026)

| Column | Description |
|--------|-------------|
| `adj_net_capital` | Industry adjusted net capital (raw USD) |
| `net_capital_requirement` | Regulatory minimum (raw USD) |
| `excess_net_capital` | Capital above requirement (raw USD) |
| `customer_assets_seg` | Customer segregated assets (raw USD) |
| `cleared_swap_seg` | Cleared swap customer segregation (raw USD) |
| `capital_adequacy_ratio` | adj_net_capital / requirement |
| `swap_seg_share` | Cleared swap seg / (customer + swap seg) |
| `fcm_count` | Number of registered FCMs |

**`fcm_concentration.csv`** — 49 rows, monthly

| Column | Description |
|--------|-------------|
| `hhi` | Herfindahl-Hirschman Index of customer seg market share |
| `top5_share` | Top 5 FCM share of customer segregated assets |

**`fcm_monthly_all.csv`** — 3,083 rows. Individual FCM-level monthly data.

**`fcm_top_brokers.csv`** — 490 rows. Top 10 FCMs per month with market share.

**`fcm_quarterly.csv`** — 17 rows. Quarter-end industry snapshots.

</details>

## Setup

Requires **Python 3.10+**.

```bash
pip install -r requirements.txt
```

If you want to refresh raw source data, add a FRED API key:

```bash
echo "FRED_API_KEY=your_key_here" > .env
```

Get a free FRED API key at https://fred.stlouisfed.org/docs/api/api_key.html

> **Note:** Form PF data requires a manual download from the [SEC Form PF Statistics page](https://www.sec.gov/data-research/form-pf-statistics). Place the `.xlsx` file in `data/raw/form_pf/`. The portfolio-facing artifact workflow does not require live fetches and runs from the tracked `data/processed/` snapshot plus safe local caches.

## Usage

```bash
# Full local refresh: fetch -> parse -> analyze -> artifacts
python -m src.pipeline

# Refresh public figures, reports, provenance files, and the notebook from the tracked snapshot
python -m src.pipeline --artifacts

# Update the local raw cache only
python -m src.pipeline --fetch

# Reparse raw inputs into processed CSVs
python -m src.pipeline --parse

# Recompute analysis outputs only
python -m src.pipeline --analyze

# Optional source-specific fetchers
python -m src.data.fetch --13f
python -m src.data.fetch_swaps
python -m src.data.fetch_dtcc
python -m src.data.fetch_fcm
```

## Reproducibility

This repo now distinguishes between:

- `data/raw/`: an untracked local cache that can exceed 11 GB and is used for live fetch/parse work
- `data/processed/*.csv`: the tracked compact snapshot used for portfolio-facing analysis and artifact refreshes

The canonical public artifact command is:

```bash
python -m src.pipeline --artifacts
```

It regenerates the tracked figures in `outputs/figures/`, selected reports in `outputs/reports/`, the rendered notebook in `notebooks/hedge_fund_analysis.ipynb`, and the provenance files:

- `outputs/reports/claims_ledger.csv`
- `outputs/reports/run_manifest.json`

Every headline number in the README and executive summary is intended to be traceable through `outputs/reports/claims_ledger.csv`, while `outputs/reports/run_manifest.json` records input file hashes, source coverage windows, the artifact command, and the git commit SHA when available.

## Project Structure

```
├── data/
│   ├── raw/
│   │   ├── swaps/              # ~600 weekly CFTC swap reports (xlsx)
│   │   ├── dtcc/               # Daily DTCC cumulative swap reports (zip/csv)
│   │   ├── fcm/                # Monthly FCM financial reports (xlsx)
│   │   ├── form_pf/            # SEC Form PF statistics (xlsx + pdf)
│   │   ├── form_adv/           # Fund profiles from EDGAR Submissions API
│   │   ├── 13f_*.csv           # Fund-level holdings
│   │   ├── cftc_cot.csv        # Futures positioning
│   │   └── vix_quarterly.csv   # Volatility index
│   └── processed/              # Tracked compact snapshot used by public artifacts
├── src/
│   ├── data/
│   │   ├── fetch.py            # FRED, SEC EDGAR, CFTC, VIX fetchers
│   │   ├── fetch_swaps.py      # CFTC weekly swap report downloader
│   │   ├── fetch_dtcc.py       # DTCC trade-level swap data downloader
│   │   ├── fetch_fcm.py        # CFTC FCM financial report downloader
│   │   ├── parse_form_pf.py    # Form PF Excel parser (141 sheets → 19 CSVs)
│   │   ├── parse_fcm.py        # FCM financial report parser (49 files → 5 CSVs)
│   │   ├── parse_dtcc.py       # DTCC daily swap report parser (available ZIPs → 2 CSVs + log)
│   │   ├── parse_swaps.py      # CFTC weekly swap report parser (available files → 3 CSVs)
│   │   └── prepare.py          # Data cleaning and transformation
│   ├── analysis/
│   │   ├── metrics.py          # Derived metrics and statistics
│   │   ├── advanced.py         # Granger causality, VAR, Monte Carlo, structural breaks
│   │   └── cross_source.py     # Cross-source alignment, reconciliation, 18 hypothesis tests
│   └── visualization/
│       └── plots.py            # 18 matplotlib/seaborn chart functions
├── notebooks/
│   └── hedge_fund_analysis.ipynb  # Rendered, executed notebook artifact
└── outputs/
    ├── figures/                # Tracked portfolio-facing charts
    └── reports/                # Tracked reports, claims ledger, run manifest
```

## Tech Stack

Python 3.10+ — pandas, numpy, matplotlib, seaborn, fredapi, openpyxl, requests, python-dotenv

## Processed Data

Core tracked snapshot outputs in `data/processed/`:

| Source | Files | Key Outputs |
|--------|-------|-------------|
| Form PF | 19 | GAV/NAV, strategy allocation, concentration, leverage distribution, notional exposure, liquidity, fair value, geography, sector, borrowing, fund counts |
| FCM | 5 | Monthly industry totals, quarterly aggregates, top brokers, concentration (HHI) |
| DTCC | 2 CSVs + log | Daily summary and quarterly quarter-end snapshots by asset class |
| CFTC Swaps | 3 | Weekly time series, long format, quarterly aggregates |
| Z.1 | 2 | Canonical analysis dataset plus compatibility copy |

## Status

**Active development.** All 9 data sources are acquired and parsed, the cross-source analysis runs end-to-end, and the public artifact path is now `python -m src.pipeline --artifacts`. The current bundled local 13F window spans **2024Q1–2025Q4** with **384,723** amendment-deduped rows (**283,362** long equity/ETF positions). Tracked figures, reports, and the notebook are regenerated from the compact processed snapshot, and headline numbers are traced through `outputs/reports/claims_ledger.csv`.

> **Note:** `data/raw/13f_all_holdings.csv` is not treated as canonical if fresher per-fund caches exist. The loader prefers the newest coherent local 13F window and the artifact pipeline snapshots that into `data/processed/13f_holdings.csv`.

## License & Citation

This project is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

**You must give appropriate credit if you use, remix, or build upon this work.** Derivatives must be shared under the same license.

### How to cite

This project includes a [`CITATION.cff`](CITATION.cff) file for automated citation. You can also cite manually:

```
Ortiz, C. (2026). Hedge Fund Mosaic: Piecing together the U.S. hedge fund industry
from public regulatory data (v1.1.0). Zenodo. https://doi.org/10.5281/zenodo.19187969
```

```bibtex
@dataset{ortiz2026hedgefundmosaic,
  author = {Ortiz, Christopher},
  title = {Hedge Fund Mosaic: Piecing Together the U.S. Hedge Fund Industry from Public Regulatory Data},
  year = {2026},
  publisher = {Zenodo},
  version = {1.1.0},
  doi = {10.5281/zenodo.19187969},
  url = {https://doi.org/10.5281/zenodo.19187969}
}
```
