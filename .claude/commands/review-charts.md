Review all charts in the notebook and plots.py for formatting quality, then fix issues.

## Scope

Review and fix chart formatting in:
1. `src/visualization/plots.py` — All 26 chart functions
2. `notebooks/hedge_fund_analysis.ipynb` — All inline chart cells

## Formatting Standards

### Tick Labels
- Date axes: `mdates.YearLocator()` + `DateFormatter('%Y')` + `rotation=45, ha='right'`
- Currency axes: `FuncFormatter(lambda x, _: f'${x:,.0f}B')`
- Percentage axes: `FuncFormatter(lambda x, _: f'{x:.0f}%')`
- Ratio axes: `FuncFormatter(lambda x, _: f'{x:.2f}x')`
- Reduce clutter: `MaxNLocator(nbins=8)` if too many ticks

### Legends
- Position: `loc='upper left'` or `loc='best'`, never obscuring data
- Style: `framealpha=0.9, edgecolor='gray', fontsize=10`
- Dual-axis: combine into single legend on primary axis
- Remove legends on single-series charts

### Labels & Titles
- Every axis labeled with units: "($B)", "(x)", "(%)"
- Descriptive titles with date range: "Hedge Fund Leverage (Q4 2012 – Q3 2025)"
- Font: title 14pt, labels 12pt semibold, ticks 10pt

### Spines & Grid
- Remove top and right spines
- Grid alpha 0.3
- Line widths: primary 2.0, secondary 1.5, reference 1.0 dashed

## Steps

1. Read `src/visualization/plots.py` completely
2. For each chart function, check formatting against the standards above
3. Fix issues directly in plots.py — prioritize:
   - Overlapping tick labels (most common)
   - Missing axis formatters (currency, percentage, ratio)
   - Legend placement and style
   - Spine cleanup
4. Read the notebook and fix any inline chart cells with the same issues
5. Run `ruff check src/visualization/plots.py` after changes
6. Run `pytest tests/` to verify nothing broke

## Do NOT
- Change chart content, data, or analytical logic
- Add new charts
- Change the color palette
- Modify non-chart cells in the notebook
