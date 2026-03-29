"""Notebook integrity tests for the tracked public notebook artifact."""

import re
from pathlib import Path

import nbformat

NOTEBOOK_PATH = Path(__file__).resolve().parents[1] / "notebooks" / "hedge_fund_analysis.ipynb"
ROOT_DIR = NOTEBOOK_PATH.parents[1]
REQUIRED_CELL_IDS = {"c995acf7", "1c7766ec", "4bdf51e0"}


def _load_notebook():
    with NOTEBOOK_PATH.open() as f:
        return nbformat.read(f, as_version=4)


def test_notebook_parses():
    nb = _load_notebook()
    assert nb.cells


def test_all_code_cells_have_execution_counts():
    nb = _load_notebook()
    code_cells = [cell for cell in nb.cells if cell.cell_type == "code"]

    assert code_cells
    assert all(cell.execution_count is not None for cell in code_cells)


def test_required_analysis_cells_are_nonempty_and_executed():
    nb = _load_notebook()
    found = {}
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        cell_id = cell.get("id")
        if cell_id in REQUIRED_CELL_IDS:
            found[cell_id] = cell

    assert set(found) == REQUIRED_CELL_IDS
    assert "load_best_13f_holdings" in "".join(found["c995acf7"]["source"])
    assert "value_usd" in "".join(found["1c7766ec"]["source"])
    assert "report_period" in "".join(found["4bdf51e0"]["source"])
    assert all(found[cell_id]["outputs"] for cell_id in REQUIRED_CELL_IDS)


def test_figure_emitting_cells_have_outputs():
    nb = _load_notebook()
    figure_cells = [
        cell for cell in nb.cells if cell.cell_type == "code" and "outputs/figures/" in "".join(cell.get("source", []))
    ]

    assert figure_cells
    pattern = re.compile(r"outputs/figures/([A-Za-z0-9_.-]+\.png)")
    for cell in figure_cells:
        assert cell.execution_count is not None
        matches = pattern.findall("".join(cell.get("source", [])))
        assert matches
        for filename in matches:
            assert (ROOT_DIR / "outputs" / "figures" / filename).exists()
