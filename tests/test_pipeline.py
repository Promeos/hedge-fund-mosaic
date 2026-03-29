"""Tests for pipeline CLI orchestration."""

from src import pipeline


def test_main_runs_full_pipeline_in_order(monkeypatch):
    calls = []

    def fake_fetch():
        calls.append(("fetch", None))

    def fake_parse():
        calls.append(("parse", None))

    def fake_analyze():
        calls.append(("analyze", None))
        return {"cross_source": "cross", "advanced": "advanced"}

    def fake_artifacts(analysis_results=None):
        calls.append(("artifacts", analysis_results))

    monkeypatch.setattr(pipeline, "step_fetch", fake_fetch)
    monkeypatch.setattr(pipeline, "step_parse", fake_parse)
    monkeypatch.setattr(pipeline, "step_analyze", fake_analyze)
    monkeypatch.setattr(pipeline, "step_artifacts", fake_artifacts)

    pipeline.main([])

    assert calls == [
        ("fetch", None),
        ("parse", None),
        ("analyze", None),
        ("artifacts", {"cross_source": "cross", "advanced": "advanced"}),
    ]


def test_main_artifacts_only(monkeypatch):
    calls = []

    monkeypatch.setattr(pipeline, "step_fetch", lambda: calls.append("fetch"))
    monkeypatch.setattr(pipeline, "step_parse", lambda: calls.append("parse"))
    monkeypatch.setattr(pipeline, "step_analyze", lambda: calls.append("analyze"))
    monkeypatch.setattr(
        pipeline,
        "step_artifacts",
        lambda analysis_results=None: calls.append(("artifacts", analysis_results)),
    )

    pipeline.main(["--artifacts"])

    assert calls == [("artifacts", None)]
