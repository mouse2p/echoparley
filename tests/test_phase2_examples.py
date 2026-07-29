"""Execution tests for the expanded offline walkthroughs."""

import runpy


def _run(path: str) -> dict[str, object]:
    namespace = runpy.run_path(path)
    return namespace["run"]()


def test_prosody_walkthrough_measures_planted_tones() -> None:
    result = _run("examples/prosody_analysis/run.py")
    assert result["data_origin"] == "synthetic-planted"
    assert result["pitch"]["voiced_frames"] > 0
    assert result["planted_hz"] == [180.0, 240.0]


def test_scenario_walkthrough_checksums_all_expanded_templates() -> None:
    result = _run("examples/scenario_corpus/run.py")
    assert len(result["scenario_names"]) == 6
    assert result["corpus"]["dialogues"] == 6
    assert len(result["corpus"]["checksum"]) == 64
    assert result["manifest_bytes"] > 0
    assert len(result["manifest_checksum"]) == 64


def test_context_walkthrough_compares_every_policy() -> None:
    result = _run("examples/context_policies/run.py")
    assert result["data_origin"] == "synthetic-planted"
    assert {row["policy"] for row in result["policies"]} == {
        "recency",
        "turn-boundary",
        "salience",
    }
    assert result["best_policy"] in {row["policy"] for row in result["policies"]}


def test_overlap_walkthrough_uses_shared_evidence() -> None:
    result = _run("examples/overlap_strategies/run.py")
    assert result["posteriors"] == [0.5, 0.76, 0.85, 0.95]
    assert [row["strategy"] for row in result["strategies"]] == [
        "immediate-yield",
        "grace-window",
        "competitive-floor",
    ]


def test_runtime_benchmark_walkthrough_labels_machine_dependence() -> None:
    result = _run("examples/runtime_benchmark/run.py")
    assert result["metadata"]["machine_dependent"] is True
    assert result["samples"] == 3
    assert [row["case"] for row in result["summaries"]] == [
        "unit-extraction",
        "stream-roundtrip",
        "simulator",
    ]


def test_session_diff_walkthrough_renders_changed_event() -> None:
    namespace = runpy.run_path("examples/session_diff/run.py")
    svg, metadata = namespace["build"]()
    assert 'class="diff change"' in svg
    assert metadata["differences"] == 1
    assert len(metadata["checksum"]) == 64
