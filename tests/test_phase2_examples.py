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
