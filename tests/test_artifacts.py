"""Tests for public artifact generation and provenance helpers."""

import json

import pandas as pd

from src import artifacts


def _dummy_metrics():
    metrics = {claim["claim_id"]: 1 for claim in artifacts.PUBLIC_CLAIMS}
    metrics.update(
        {
            "z1_period_start": "2020 Q1",
            "z1_period_end": "2024 Q4",
            "z1_quarters": 20,
        }
    )
    return metrics


def test_write_claims_ledger_covers_public_claims(tmp_path):
    path = artifacts.write_claims_ledger(_dummy_metrics(), report_dir=tmp_path)

    ledger = pd.read_csv(path)

    assert path.name == "claims_ledger.csv"
    assert set(ledger["claim_id"]) == {claim["claim_id"] for claim in artifacts.PUBLIC_CLAIMS}


def test_write_run_manifest_has_required_fields(tmp_path, monkeypatch):
    root_dir = tmp_path / "repo"
    root_dir.mkdir()
    input_path = root_dir / "data" / "processed" / "sample.csv"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("a,b\n1,2\n")
    figure_path = root_dir / "outputs" / "figures" / "sample.png"
    figure_path.parent.mkdir(parents=True)
    figure_path.write_bytes(b"png")
    report_path = root_dir / "outputs" / "reports" / "sample.csv"
    report_path.parent.mkdir(parents=True)
    report_path.write_text("x\n1\n")

    monkeypatch.setattr(artifacts, "ROOT_DIR", root_dir)
    monkeypatch.setattr(artifacts, "NOTEBOOK_PATH", root_dir / "notebooks" / "hedge_fund_analysis.ipynb")

    metrics = _dummy_metrics()
    metrics.update(
        {
            "form_pf_latest_quarter": "2025Q1",
            "form_pf_creditor_latest_quarter": "2025Q1",
            "swaps_latest_date": "2026-03-31",
            "fcm_latest_date": "2026-01-31",
            "thirteenf_report_period_start": "2024Q1",
            "thirteenf_report_period_end": "2025Q4",
            "thirteenf_total_rows": 10,
            "thirteenf_long_positions_total": 8,
            "z1_total_assets_latest_b": 1.0,
            "form_pf_derivatives_latest_b": 2.0,
            "swaps_ir_total_latest_b": 3.0,
            "thirteenf_latest_long_value_b": 4.0,
            "liquidity_30d_mean_gap_pct": 0.5,
            "leverage_adf_pvalue": 0.1,
        }
    )

    manifest_path = artifacts.write_run_manifest(
        metrics,
        [input_path],
        [figure_path],
        [report_path],
        report_dir=report_path.parent,
    )

    manifest = json.loads(manifest_path.read_text())

    assert manifest["artifact_command"] == "python -m src.pipeline --artifacts"
    assert "generated_at" in manifest
    assert manifest["input_files"][0]["path"] == "data/processed/sample.csv"
    assert manifest["generated_outputs"]["figures"] == ["outputs/figures/sample.png"]


def test_refresh_public_artifacts_returns_expected_paths(tmp_path, monkeypatch):
    figures_dir = tmp_path / "outputs" / "figures"
    reports_dir = tmp_path / "outputs" / "reports"
    notebook_path = tmp_path / "notebooks" / "hedge_fund_analysis.ipynb"
    notebook_path.parent.mkdir(parents=True)
    notebook_path.write_text("{}")

    dummy_metrics = _dummy_metrics()
    dummy_metrics.update(
        {
            "form_pf_latest_quarter": "2025Q1",
            "form_pf_creditor_latest_quarter": "2025Q1",
            "swaps_latest_date": "2026-03-31",
            "fcm_latest_date": "2026-01-31",
            "thirteenf_report_period_start": "2024Q1",
            "thirteenf_report_period_end": "2025Q4",
            "thirteenf_total_rows": 10,
            "thirteenf_long_positions_total": 8,
            "z1_total_assets_latest_b": 1.0,
            "form_pf_derivatives_latest_b": 2.0,
            "swaps_ir_total_latest_b": 3.0,
            "thirteenf_latest_long_value_b": 4.0,
            "liquidity_30d_mean_gap_pct": 0.5,
            "leverage_adf_pvalue": 0.1,
        }
    )

    monkeypatch.setattr(artifacts, "FIGURES_DIR", figures_dir)
    monkeypatch.setattr(artifacts, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(artifacts, "NOTEBOOK_PATH", notebook_path)
    monkeypatch.setattr(artifacts, "RAW_DIR", tmp_path / "data" / "raw")
    monkeypatch.setattr(artifacts, "PROCESSED_DIR", tmp_path / "data" / "processed")
    monkeypatch.setattr(artifacts, "snapshot_public_inputs", lambda *args, **kwargs: [])
    monkeypatch.setattr(artifacts, "load_public_data", lambda *args, **kwargs: ({}, []))
    monkeypatch.setattr(
        artifacts,
        "generate_public_figures",
        lambda *args, **kwargs: [figures_dir / "total_assets.png"],
    )
    monkeypatch.setattr(
        artifacts,
        "compute_public_metrics",
        lambda *args, **kwargs: dummy_metrics,
    )
    monkeypatch.setattr(
        artifacts,
        "write_claims_ledger",
        lambda metrics, report_dir: (
            (report_dir / "claims_ledger.csv").write_text("x\n"),
            report_dir / "claims_ledger.csv",
        )[1],
    )
    monkeypatch.setattr(
        artifacts,
        "write_executive_summary",
        lambda metrics, report_dir: (
            (report_dir / "executive_summary.md").write_text("# summary\n"),
            report_dir / "executive_summary.md",
        )[1],
    )
    monkeypatch.setattr(
        artifacts,
        "write_run_manifest",
        lambda metrics, input_paths, generated_figures, generated_reports, report_dir: (
            (report_dir / "run_manifest.json").write_text("{}"),
            report_dir / "run_manifest.json",
        )[1],
    )
    monkeypatch.setattr(artifacts, "execute_notebook_in_place", lambda *args, **kwargs: notebook_path)

    result = artifacts.refresh_public_artifacts(
        execute_notebook=False,
        analysis_results={"cross_source": {}, "advanced": {}},
    )

    assert result["figures"] == [figures_dir / "total_assets.png"]
    assert reports_dir / "claims_ledger.csv" in result["reports"]
    assert result["notebook"] == notebook_path


def test_tracked_artifact_files_exist():
    for filename in artifacts.PUBLIC_FIGURES:
        assert (artifacts.FIGURES_DIR / filename).exists(), filename

    for filename in artifacts.PUBLIC_REPORTS:
        assert (artifacts.REPORTS_DIR / filename).exists(), filename


def test_tracked_claims_ledger_has_all_public_claims():
    ledger = pd.read_csv(artifacts.REPORTS_DIR / "claims_ledger.csv")
    assert set(ledger["claim_id"]) == {claim["claim_id"] for claim in artifacts.PUBLIC_CLAIMS}
