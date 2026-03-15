"""Matplotlib/seaborn chart functions for hedge fund analysis."""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns


# ---------------------------------------------------------------------------
# Style defaults
# ---------------------------------------------------------------------------

COLORS = {
    'dark': '#2c3e50',
    'blue': '#2980b9',
    'light_blue': '#3498db',
    'red': '#e74c3c',
    'dark_red': '#c0392b',
    'green': '#27ae60',
    'light_green': '#2ecc71',
    'orange': '#f39c12',
    'light_orange': '#e67e22',
    'purple': '#8e44ad',
    'light_purple': '#9b59b6',
    'teal': '#1abc9c',
}

MARKET_EVENTS = {
    '2018-02-01': 'Volmageddon',
    '2020-03-01': 'COVID Crash',
    '2021-01-01': 'GameStop\nSqueeze',
    '2022-03-01': 'Fed Rate\nHikes Begin',
}


def setup_style():
    """Apply default plotting style."""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['figure.figsize'] = (14, 6)
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def add_event_annotations(ax, ypos_frac=0.95):
    """Add vertical lines for key market events."""
    ylim = ax.get_ylim()
    ypos = ylim[0] + (ylim[1] - ylim[0]) * ypos_frac
    for date_str, label in MARKET_EVENTS.items():
        date = pd.Timestamp(date_str)
        try:
            ax.axvline(date, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
            ax.text(date, ypos, label, ha='center', va='top', fontsize=8,
                    color='gray', style='italic')
        except Exception:
            pass


def _save(fig, save_path):
    """Save figure if path is provided."""
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, bbox_inches='tight', dpi=150)


# ---------------------------------------------------------------------------
# Chart functions
# ---------------------------------------------------------------------------

def plot_total_assets(df, save_path=None):
    """Total assets with QoQ growth bars (dual axis)."""
    fig, ax1 = plt.subplots(figsize=(14, 6))

    ax1.plot(df.index, df['Total assets'], color=COLORS['dark'], linewidth=2.5, label='Total Assets')
    ax1.fill_between(df.index, df['Total assets'], alpha=0.1, color=COLORS['dark'])
    ax1.set_ylabel('Total Assets ($B)', color=COLORS['dark'])

    ax2 = ax1.twinx()
    colors = [COLORS['green'] if x >= 0 else COLORS['red'] for x in df['total_assets_qoq'].fillna(0)]
    ax2.bar(df.index, df['total_assets_qoq'] * 100, width=60, alpha=0.4, color=colors, label='QoQ Growth %')
    ax2.set_ylabel('QoQ Growth (%)', color='#7f8c8d')
    ax2.axhline(0, color='gray', linewidth=0.5)

    add_event_annotations(ax1)
    ax1.set_title('Hedge Fund Industry — Total Assets & Quarterly Growth')
    fig.legend(loc='upper left', bbox_to_anchor=(0.12, 0.88))
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_asset_composition(df, save_path=None):
    """Stacked area chart of asset composition."""
    asset_cols = {
        'Corporate equities; asset': 'Corporate Equities',
        'Total debt securities; asset': 'Debt Securities',
        'Total loans; asset': 'Loans',
        'Security repurchase agreements; asset': 'Repo Agreements',
        'Miscellaneous assets; asset': 'Misc Assets',
    }
    df_plot = df.copy()
    df_plot['Cash & equivalents'] = (
        df_plot['Deposits; asset']
        + df_plot['Other cash and cash equivalents; asset']
        + df_plot['Money market fund shares; asset']
    )
    cols_to_stack = list(asset_cols.values()) + ['Cash & equivalents']
    rename_map = asset_cols.copy()
    df_plot = df_plot.rename(columns=rename_map)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

    # Absolute
    ax1.stackplot(df_plot.index, *[df_plot[c] for c in cols_to_stack],
                  labels=cols_to_stack, alpha=0.8)
    ax1.set_title('Asset Composition (Absolute, $B)')
    ax1.legend(loc='upper left', fontsize=9)
    add_event_annotations(ax1)

    # Proportional
    totals = df_plot[cols_to_stack].sum(axis=1)
    pct_data = df_plot[cols_to_stack].div(totals, axis=0) * 100
    ax2.stackplot(df_plot.index, *[pct_data[c] for c in cols_to_stack],
                  labels=cols_to_stack, alpha=0.8)
    ax2.set_title('Asset Composition (% of Total)')
    ax2.set_ylabel('%')
    add_event_annotations(ax2)

    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_debt_securities(df, save_path=None):
    """Treasury vs corporate bond breakdown."""
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(df.index, df['Treasury securities; asset'], linewidth=2,
            label='Treasury Securities', color=COLORS['blue'])
    ax.plot(df.index, df['Corporate and foreign bonds; asset'], linewidth=2,
            label='Corporate & Foreign Bonds', color=COLORS['red'])
    ax.fill_between(df.index, df['Treasury securities; asset'], alpha=0.1, color=COLORS['blue'])
    ax.fill_between(df.index, df['Corporate and foreign bonds; asset'], alpha=0.1, color=COLORS['red'])

    ax.set_title('Debt Securities Breakdown')
    ax.set_ylabel('$B')
    ax.legend()
    add_event_annotations(ax)
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_liability_structure(df, save_path=None):
    """Stacked liability composition + leverage ratio."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[2, 1], sharex=True)

    liab_data = pd.DataFrame({
        'Repo Agreements': df['Total security repurchase agreements; liability'],
        'Prime Brokerage': df['Loans, total secured borrowing via prime brokerage; liability'],
        'Other Secured': df['Loans, total other secured borrowing; liability'],
        'Unsecured': df['Loans, total unsecured borrowing; liability'],
    })

    ax1.stackplot(df.index, *[liab_data[c] for c in liab_data.columns],
                  labels=liab_data.columns, alpha=0.8)
    ax1.set_title('Liability Structure')
    ax1.set_ylabel('$B')
    ax1.legend(loc='upper left')
    add_event_annotations(ax1)

    ax2.plot(df.index, df['leverage_ratio'], linewidth=2.5, color=COLORS['dark_red'])
    ax2.axhline(df['leverage_ratio'].mean(), color='gray', linestyle='--', alpha=0.5,
                label=f"Mean: {df['leverage_ratio'].mean():.2f}x")
    ax2.set_ylabel('Leverage Ratio (x)')
    ax2.legend()

    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_balance_sheet_overview(df, save_path=None):
    """Three-line overlay — assets, liabilities, net assets."""
    fig, ax = plt.subplots(figsize=(14, 7))

    ax.plot(df.index, df['Total assets'], linewidth=2.5, label='Total Assets', color=COLORS['dark'])
    ax.plot(df.index, df['Total liabilities'], linewidth=2.5, label='Total Liabilities', color=COLORS['red'])
    ax.plot(df.index, df['Total net assets'], linewidth=2.5, label='Net Assets', color=COLORS['green'])

    ax.fill_between(df.index, df['Total liabilities'], df['Total assets'], alpha=0.05, color=COLORS['dark'])
    ax.fill_between(df.index, 0, df['Total net assets'], alpha=0.05, color=COLORS['green'])

    ax.set_title('Balance Sheet Overview — Assets vs Liabilities vs Net Assets')
    ax.set_ylabel('$B')
    ax.legend()
    add_event_annotations(ax)
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_derivative_exposure(df, save_path=None):
    """Derivative exposure with ratio to total assets."""
    fig, ax1 = plt.subplots(figsize=(14, 6))

    ax1.plot(df.index, df['Derivatives (long value)'], linewidth=2.5,
             color=COLORS['purple'], label='Derivatives (Long Value)')
    ax1.fill_between(df.index, df['Derivatives (long value)'], alpha=0.15, color=COLORS['purple'])
    ax1.set_ylabel('Derivatives ($B)', color=COLORS['purple'])

    ax2 = ax1.twinx()
    ax2.plot(df.index, df['derivative_to_assets'] * 100, linewidth=1.5,
             color=COLORS['light_orange'], linestyle='--', label='Derivatives / Total Assets (%)')
    ax2.set_ylabel('% of Total Assets', color=COLORS['light_orange'])

    add_event_annotations(ax1)
    ax1.set_title('Derivative Exposure')
    fig.legend(loc='upper left', bbox_to_anchor=(0.12, 0.88))
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_borrowing_patterns(df, save_path=None):
    """Domestic vs foreign borrowing side-by-side."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    ax1.plot(df.index, df['domestic_borrowing'], linewidth=2, label='Domestic', color=COLORS['blue'])
    ax1.plot(df.index, df['foreign_borrowing'], linewidth=2, label='Foreign', color=COLORS['red'])
    ax1.fill_between(df.index, df['domestic_borrowing'], alpha=0.1, color=COLORS['blue'])
    ax1.fill_between(df.index, df['foreign_borrowing'], alpha=0.1, color=COLORS['red'])
    ax1.set_title('Borrowing by Source (Absolute)')
    ax1.set_ylabel('$B')
    ax1.legend()
    add_event_annotations(ax1)

    ax2.plot(df.index, df['foreign_borrowing_share'] * 100, linewidth=2, color=COLORS['red'])
    ax2.fill_between(df.index, df['foreign_borrowing_share'] * 100, alpha=0.1, color=COLORS['red'])
    ax2.set_title('Foreign Borrowing Share (%)')
    ax2.set_ylabel('%')
    add_event_annotations(ax2)

    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_correlation_heatmap(df, cols=None, save_path=None):
    """Correlation matrix heatmap of balance sheet components."""
    if cols is None:
        cols = ['Total assets', 'Total liabilities', 'Total net assets',
                'Corporate equities; asset', 'Total debt securities; asset',
                'Total loans; asset', 'Derivatives (long value)',
                'Security repurchase agreements; asset']

    available = [c for c in cols if c in df.columns]
    short_labels = [c.split(';')[0].replace('Total ', '') for c in available]

    fig, ax = plt.subplots(figsize=(10, 8))
    corr = df[available].corr()
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
                xticklabels=short_labels, yticklabels=short_labels, ax=ax)
    ax.set_title('Balance Sheet Component Correlations')
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


# ---------------------------------------------------------------------------
# Form PF, FCM, DTCC, and CFTC Swaps chart functions
# ---------------------------------------------------------------------------

def _parse_quarter(series):
    """Convert quarter strings like '2013Q1' to end-of-quarter timestamps."""
    return pd.PeriodIndex(series, freq='Q').to_timestamp('Q')


def plot_form_pf_leverage(df, z1_df=None, save_path=None):
    """Form PF hedge fund leverage — GAV, NAV, and GAV/NAV ratio.

    Parameters
    ----------
    df : DataFrame
        form_pf_gav_nav.csv filtered to fund_type == 'Hedge Fund'.
        Expected columns: quarter, gav, nav.
    z1_df : DataFrame, optional
        hedge_fund_analysis.csv with leverage_ratio and a datetime index.
    save_path : str, optional
        Path to save the figure.
    """
    required = {'quarter', 'gav', 'nav'}
    if not required.issubset(df.columns):
        print(f"plot_form_pf_leverage: missing columns {required - set(df.columns)}")
        return

    data = df.copy()
    data['date'] = _parse_quarter(data['quarter'])
    data = data.sort_values('date')
    data['gav_nav_ratio'] = data['gav'] / data['nav'].replace(0, np.nan)

    fig, ax1 = plt.subplots(figsize=(14, 6))

    ax1.plot(data['date'], data['gav'], linewidth=2.5, color=COLORS['blue'],
             label='GAV ($B)')
    ax1.plot(data['date'], data['nav'], linewidth=2.5, color=COLORS['green'],
             label='NAV ($B)')
    ax1.set_ylabel('$B')
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    ax2.plot(data['date'], data['gav_nav_ratio'], linewidth=2, color=COLORS['red'],
             label='GAV / NAV')
    ax2.set_ylabel('GAV / NAV Ratio', color=COLORS['red'])

    if z1_df is not None and 'leverage_ratio' in z1_df.columns:
        ax2.plot(z1_df.index, z1_df['leverage_ratio'], linewidth=1.5,
                 color=COLORS['dark_red'], linestyle='--', label='Z.1 Leverage Ratio')

    ax2.legend(loc='upper right')
    add_event_annotations(ax1)
    ax1.set_title('Form PF — Hedge Fund Leverage (GAV/NAV)')
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_strategy_allocation(df, save_path=None):
    """Stacked area chart of hedge fund NAV by strategy over time.

    Parameters
    ----------
    df : DataFrame
        form_pf_strategy.csv.
        Expected columns: quarter, strategy, nav.
    save_path : str, optional
        Path to save the figure.
    """
    required = {'quarter', 'strategy', 'nav'}
    if not required.issubset(df.columns):
        print(f"plot_strategy_allocation: missing columns {required - set(df.columns)}")
        return

    data = df.copy()
    data['date'] = _parse_quarter(data['quarter'])
    pivot = data.pivot_table(index='date', columns='strategy', values='nav',
                             aggfunc='sum').fillna(0).sort_index()

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.stackplot(pivot.index, *[pivot[c] for c in pivot.columns],
                 labels=pivot.columns, alpha=0.8)
    ax.set_title('Form PF — Hedge Fund Strategy Allocation (NAV)')
    ax.set_ylabel('NAV ($B)')
    ax.legend(loc='upper left', fontsize=9, ncol=2)
    add_event_annotations(ax)
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_notional_exposure(df, save_path=None):
    """Grouped bar chart of notional exposure by investment type.

    Parameters
    ----------
    df : DataFrame
        form_pf_notional.csv.
        Expected columns: quarter, investment_type, long_notional, short_notional.
    save_path : str, optional
        Path to save the figure.
    """
    required = {'quarter', 'investment_type', 'long_notional'}
    if not required.issubset(df.columns):
        print(f"plot_notional_exposure: missing columns {required - set(df.columns)}")
        return

    data = df.copy()
    latest_q = data['quarter'].max()
    latest = data[data['quarter'] == latest_q].copy()

    top = latest.nlargest(10, 'long_notional')

    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(len(top))
    width = 0.35

    ax.bar(x - width / 2, top['long_notional'], width, label='Long Notional',
           color=COLORS['blue'], alpha=0.85)
    if 'short_notional' in top.columns:
        ax.bar(x + width / 2, -top['short_notional'].abs(), width,
               label='Short Notional', color=COLORS['red'], alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(top['investment_type'], rotation=45, ha='right', fontsize=10)
    ax.axhline(0, color='gray', linewidth=0.5)
    ax.set_ylabel('Notional ($B)')
    ax.set_title(f'Form PF — Notional Exposure by Investment Type ({latest_q})')
    ax.legend()
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_concentration_trend(df, save_path=None):
    """Multi-line chart of hedge fund concentration (Top 10/25/50 NAV share).

    Parameters
    ----------
    df : DataFrame
        form_pf_concentration.csv.
        Expected columns: quarter, plus some of top_10_nav_share,
        top_25_nav_share, top_50_nav_share.
    save_path : str, optional
        Path to save the figure.
    """
    if 'quarter' not in df.columns:
        print("plot_concentration_trend: missing 'quarter' column")
        return

    # Handle pivoted format (top_10_nav_share columns) or long format (top_n + nav_share)
    if 'top_n' in df.columns and 'nav_share' in df.columns:
        # Long format: pivot to get one line per top_n
        data = df.copy()
        data['date'] = _parse_quarter(data['quarter'])
        data = data.sort_values('date')
        top_n_colors = {
            'Top 10': COLORS['red'],
            'Top 25': COLORS['orange'],
            'Top 50': COLORS['blue'],
        }
        fig, ax = plt.subplots(figsize=(14, 6))
        for tn, color in top_n_colors.items():
            subset = data[data['top_n'] == tn]
            if not subset.empty:
                ax.plot(subset['date'], subset['nav_share'] * 100, linewidth=2,
                        label=tn, color=color)
    else:
        share_cols = {
            'top_10_nav_share': ('Top 10', COLORS['red']),
            'top_25_nav_share': ('Top 25', COLORS['orange']),
            'top_50_nav_share': ('Top 50', COLORS['blue']),
        }
        available = {k: v for k, v in share_cols.items() if k in df.columns}
        if not available:
            print("plot_concentration_trend: no share columns found")
            return

        data = df.copy()
        data['date'] = _parse_quarter(data['quarter'])
        data = data.sort_values('date')

        fig, ax = plt.subplots(figsize=(14, 6))
        for col, (label, color) in available.items():
            ax.plot(data['date'], data[col] * 100, linewidth=2, label=label, color=color)

    ax.set_ylabel('NAV Share (%)')
    ax.set_title('Form PF — Fund Concentration Trends')
    ax.legend()
    add_event_annotations(ax)
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_liquidity_mismatch(df, save_path=None):
    """Liquidity at 30 days by type — investor, portfolio, financing.

    Parameters
    ----------
    df : DataFrame
        form_pf_liquidity.csv.
        Expected columns: quarter, liquidity_type, period, cumulative_pct.
    save_path : str, optional
        Path to save the figure.
    """
    required = {'quarter', 'liquidity_type', 'period', 'cumulative_pct'}
    if not required.issubset(df.columns):
        print(f"plot_liquidity_mismatch: missing columns {required - set(df.columns)}")
        return

    data = df.copy()
    data['date'] = _parse_quarter(data['quarter'])

    # Filter to the 30-day period
    mask = data['period'].str.contains('30', na=False)
    data_30 = data[mask].copy()
    if data_30.empty:
        print("plot_liquidity_mismatch: no '30 days' period found")
        return

    liq_types = data_30['liquidity_type'].unique()
    n_panels = len(liq_types)
    if n_panels == 0:
        return

    fig, axes = plt.subplots(1, min(n_panels, 3), figsize=(6 * min(n_panels, 3), 5),
                             squeeze=False)
    axes = axes.flatten()

    type_colors = {
        'investor_liquidity': COLORS['blue'],
        'portfolio_liquidity': COLORS['green'],
        'financing_liquidity': COLORS['orange'],
    }

    for i, ltype in enumerate(liq_types[:3]):
        ax = axes[i]
        subset = data_30[data_30['liquidity_type'] == ltype].sort_values('date')
        color = type_colors.get(ltype, COLORS['dark'])
        ax.plot(subset['date'], subset['cumulative_pct'] * 100, linewidth=2, color=color)
        ax.fill_between(subset['date'], subset['cumulative_pct'] * 100, alpha=0.15,
                        color=color)
        ax.set_title(ltype.replace('_', ' ').title(), fontsize=11)
        ax.set_ylabel('Cumulative % at 30 Days')
        add_event_annotations(ax)

    fig.suptitle('Form PF — Liquidity at 30 Days by Type', fontsize=14, y=1.02)
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_clearing_rate(swaps_df, dtcc_df=None, save_path=None):
    """OTC derivatives clearing rates over time.

    Parameters
    ----------
    swaps_df : DataFrame
        swaps_weekly.csv.
        Expected columns: date, plus some of ir_cleared_pct, credit_cleared_pct,
        fx_cleared_pct.
    dtcc_df : DataFrame, optional
        dtcc_daily_summary.csv with date and rates_cleared_pct columns.
    save_path : str, optional
        Path to save the figure.
    """
    if 'date' not in swaps_df.columns:
        print("plot_clearing_rate: missing 'date' column in swaps_df")
        return

    data = swaps_df.copy()
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values('date')

    clearing_cols = {
        'ir_cleared_pct': ('Interest Rate', COLORS['blue']),
        'credit_cleared_pct': ('Credit', COLORS['red']),
        'fx_cleared_pct': ('FX', COLORS['green']),
    }
    available = {k: v for k, v in clearing_cols.items() if k in data.columns}
    if not available:
        print("plot_clearing_rate: no clearing percentage columns found")
        return

    fig, ax = plt.subplots(figsize=(14, 6))
    for col, (label, color) in available.items():
        ax.plot(data['date'], data[col] * 100, linewidth=2, label=label, color=color)

    if dtcc_df is not None and 'rates_cleared_pct' in dtcc_df.columns:
        dtcc = dtcc_df.copy()
        dtcc['date'] = pd.to_datetime(dtcc['date'])
        ax.scatter(dtcc['date'], dtcc['rates_cleared_pct'] * 100, s=15,
                   color=COLORS['teal'], alpha=0.5, label='DTCC Rates Cleared %',
                   zorder=5)

    ax.set_ylabel('Cleared (%)')
    ax.set_title('OTC Derivatives — Clearing Rates')
    ax.legend()
    add_event_annotations(ax)
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_fcm_capital(df, save_path=None):
    """FCM industry capital and adequacy ratio.

    Parameters
    ----------
    df : DataFrame
        fcm_monthly_industry.csv.
        Expected columns: date, adj_net_capital, excess_net_capital,
        capital_adequacy_ratio.
    save_path : str, optional
        Path to save the figure.
    """
    # Accept either 'date' or 'as_of_date'
    data = df.copy()
    if 'as_of_date' in data.columns and 'date' not in data.columns:
        data['date'] = data['as_of_date']
    required = {'date', 'adj_net_capital', 'excess_net_capital', 'capital_adequacy_ratio'}
    if not required.issubset(data.columns):
        print(f"plot_fcm_capital: missing columns {required - set(data.columns)}")
        return

    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values('date')

    # Convert raw USD to billions
    data['adj_net_capital_b'] = data['adj_net_capital'] / 1e9
    data['excess_net_capital_b'] = data['excess_net_capital'] / 1e9

    fig, ax1 = plt.subplots(figsize=(14, 6))

    ax1.plot(data['date'], data['adj_net_capital_b'], linewidth=2.5,
             color=COLORS['blue'], label='Adj Net Capital ($B)')
    ax1.plot(data['date'], data['excess_net_capital_b'], linewidth=2.5,
             color=COLORS['green'], label='Excess Net Capital ($B)')
    ax1.set_ylabel('$B')
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    ax2.plot(data['date'], data['capital_adequacy_ratio'], linewidth=2,
             color=COLORS['orange'], linestyle='--', label='Capital Adequacy Ratio')
    ax2.set_ylabel('Capital Adequacy Ratio', color=COLORS['orange'])
    ax2.legend(loc='upper right')

    add_event_annotations(ax1)
    ax1.set_title('FCM Industry — Capital & Adequacy')
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_fcm_concentration(df, save_path=None):
    """FCM market concentration — HHI and top-5 share.

    Parameters
    ----------
    df : DataFrame
        fcm_concentration.csv.
        Expected columns: date, hhi, top5_share.
    save_path : str, optional
        Path to save the figure.
    """
    # Accept either 'date' or 'as_of_date'
    data = df.copy()
    if 'as_of_date' in data.columns and 'date' not in data.columns:
        data['date'] = data['as_of_date']
    required = {'date', 'hhi', 'top5_share'}
    if not required.issubset(data.columns):
        print(f"plot_fcm_concentration: missing columns {required - set(data.columns)}")
        return

    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values('date')

    fig, ax1 = plt.subplots(figsize=(14, 6))

    ax1.plot(data['date'], data['hhi'], linewidth=2.5, color=COLORS['purple'],
             label='HHI')
    ax1.set_ylabel('HHI', color=COLORS['purple'])
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    ax2.plot(data['date'], data['top5_share'] * 100, linewidth=2,
             color=COLORS['teal'], label='Top 5 Share (%)')
    ax2.set_ylabel('Top 5 Share (%)', color=COLORS['teal'])
    ax2.legend(loc='upper right')

    add_event_annotations(ax1)
    ax1.set_title('FCM Industry — Market Concentration')
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_cross_source_leverage(z1_df, pf_df, save_path=None):
    """Cross-source leverage comparison — Z.1 vs Form PF.

    Parameters
    ----------
    z1_df : DataFrame
        hedge_fund_analysis.csv with leverage_ratio and a datetime index.
    pf_df : DataFrame
        form_pf_gav_nav.csv filtered to fund_type == 'Hedge Fund'.
        Expected columns: quarter, gav, nav.
    save_path : str, optional
        Path to save the figure.
    """
    if 'leverage_ratio' not in z1_df.columns:
        print("plot_cross_source_leverage: missing 'leverage_ratio' in z1_df")
        return
    if not {'quarter', 'gav', 'nav'}.issubset(pf_df.columns):
        print("plot_cross_source_leverage: missing columns in pf_df")
        return

    pf = pf_df.copy()
    pf['date'] = _parse_quarter(pf['quarter'])
    pf = pf.sort_values('date')
    pf['gav_nav_ratio'] = pf['gav'] / pf['nav'].replace(0, np.nan)

    fig, ax1 = plt.subplots(figsize=(14, 6))

    ax1.plot(z1_df.index, z1_df['leverage_ratio'], linewidth=2.5,
             color=COLORS['blue'], label='Z.1 Leverage Ratio')
    ax1.set_ylabel('Z.1 Leverage Ratio', color=COLORS['blue'])
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    ax2.plot(pf['date'], pf['gav_nav_ratio'], linewidth=2.5,
             color=COLORS['red'], label='Form PF GAV/NAV')
    ax2.set_ylabel('Form PF GAV / NAV', color=COLORS['red'])
    ax2.legend(loc='upper right')

    add_event_annotations(ax1)
    ax1.set_title('Cross-Source Leverage Comparison — Z.1 vs Form PF')
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()


def plot_swaps_notional(df, save_path=None):
    """Stacked area chart of OTC swap notional outstanding by asset class.

    Parameters
    ----------
    df : DataFrame
        swaps_weekly.csv.
        Expected columns: date, plus some of ir_notional, credit_notional,
        fx_notional.
    save_path : str, optional
        Path to save the figure.
    """
    if 'date' not in df.columns:
        print("plot_swaps_notional: missing 'date' column")
        return

    data = df.copy()
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values('date')

    notional_cols = {
        'ir_total': ('Interest Rate', COLORS['blue']),
        'credit_total': ('Credit', COLORS['red']),
        'fx_total': ('FX', COLORS['green']),
    }
    available = {k: v for k, v in notional_cols.items() if k in data.columns}
    if not available:
        print("plot_swaps_notional: no notional columns found")
        return

    fig, ax = plt.subplots(figsize=(14, 6))
    cols = list(available.keys())
    labels = [available[c][0] for c in cols]
    colors = [available[c][1] for c in cols]

    ax.stackplot(data['date'], *[data[c].fillna(0) for c in cols],
                 labels=labels, colors=colors, alpha=0.8)
    ax.set_ylabel('Notional Outstanding ($B)')
    ax.set_title('OTC Swap Notional Outstanding by Asset Class')
    ax.legend(loc='upper left')
    add_event_annotations(ax)
    plt.tight_layout()
    _save(fig, save_path)
    plt.show()
