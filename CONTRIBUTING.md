# Contributing

Thank you for your interest in contributing to Hedge Fund Mosaic.

## Reporting Issues

Open a [GitHub Issue](https://github.com/Promeos/hedge-fund-mosaic/issues) for:

- Bugs or data parsing errors
- Broken links or unclear documentation
- Suggestions for additional data sources or analyses
- Questions about methodology or findings

## Pull Requests

1. Fork the repo and create a branch from `master`
2. Make your changes
3. Run `ruff check .` and `ruff format --check .` to verify code style
4. Run `pytest` and confirm all tests pass
5. If you changed public claims, figures, reports, or the notebook, run `python -m src.pipeline --artifacts`
6. Commit the updated tracked snapshot and artifacts together
7. Open a PR with a clear description of what changed and why

The canonical offline artifact refresh command is:

```bash
python -m src.pipeline --artifacts
```

This refreshes the tracked public figures in `outputs/figures/`, portfolio-facing reports in
`outputs/reports/`, the rendered notebook in `notebooks/`, and provenance files including
`outputs/reports/claims_ledger.csv` and `outputs/reports/run_manifest.json`.

## Code Style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting. Configuration is in `pyproject.toml`:

- **Line length:** 120
- **Rules:** E, F, W, I (pycodestyle, pyflakes, warnings, isort)
- **Target:** Python 3.10+

## Data Access

There are two supported workflows:

- Public artifact refresh: works from the tracked `data/processed/` snapshot plus safe local caches and does not require live fetches.
- Raw data refresh: updates the untracked `data/raw/` cache, then reparses/analyzes/regenerates artifacts.

For raw data refreshes, most sources are publicly available and fetched automatically. You will need:

- A free [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html) set as `FRED_API_KEY` in a `.env` file
- The SEC Form PF Excel file (manually downloaded from [SEC.gov](https://www.sec.gov/divisions/investment/private-fund-statistics))

All other sources (CFTC weekly swaps, DTCC swap repository, FCM financials, SEC EDGAR, CBOE VIX) are fetched automatically by the pipeline scripts.

Repository policy:

- `data/raw/` is an untracked local cache and is intentionally excluded from version control.
- `data/processed/*.csv` is the tracked compact snapshot used for portfolio-safe artifact refreshes.
- `outputs/figures/*.png`, the rendered notebook, and the selected reports in `outputs/reports/` are tracked public artifacts.
- Every public numeric claim in the README and executive summary must be traceable through `outputs/reports/claims_ledger.csv`.

## Monetary Conventions

- All monetary values are in **billions USD**
- Cross-source alignment uses **quarterly frequency** (quarter-end dates)
- See `CLAUDE.md` for the full derived metrics reference

## License

By contributing, you agree that your contributions will be licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
