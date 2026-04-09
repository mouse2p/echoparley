import numpy as np
import pytest

from echoparley.cascade import StageObservation


def test_stage_observation_validates_names_and_delay() -> None:
    assert StageObservation("stt", "audio", "words", 20).stage == "stt"
    with pytest.raises(ValueError, match="invalid"):
        StageObservation("remote", "x", "y", 0)


def test_empty_cascade_execution_is_successful() -> None:
    from echoparley.cascade import CascadeExecution, StageLatencyLedger

    execution = CascadeExecution((), StageLatencyLedger(), "", "", ())
    assert execution.succeeded and execution.ledger.total_ms == 0


def test_mock_cascade_executes_every_default_stage() -> None:
    from echoparley.cascade import execute_mock_cascade

    execution = execute_mock_cascade(
        np.array([0.0, 0.2, 0.2, 0.0]), "hello world", "scripted reply"
    )
    assert [item.stage for item in execution.observations] == [
        "vad",
        "stt",
        "punctuation",
        "lm",
        "tts",
    ]
    assert execution.transcript == "Hello world."
    assert [item.text for item in execution.aligned_units] == ["scripted", "reply"]


def test_mock_cascade_keeps_silence_observable() -> None:
    from echoparley.cascade import execute_mock_cascade

    execution = execute_mock_cascade(np.zeros(4), "", "should not emit")
    assert execution.observations[0].output_label == "0 speech spans"
    assert execution.response == ""
    assert execution.aligned_units == ()


def test_mock_cascade_stops_at_seeded_failure() -> None:
    from echoparley.cascade import SeededFaultPlan, execute_mock_cascade

    plan = SeededFaultPlan(0, 1, ("punctuation",))
    execution = execute_mock_cascade(np.ones(2), "raw words", "reply", fault_plan=plan)
    assert not execution.succeeded
    assert execution.degradation is not None and execution.degradation.failed_stage == "punctuation"
    assert [item.stage for item in execution.observations] == ["vad", "stt"]
    assert execution.ledger.total_ms == 105


def test_each_stage_can_fail_deterministically() -> None:
    from echoparley.cascade import CASCADE_STAGE_ORDER, SeededFaultPlan, execute_mock_cascade

    for stage in CASCADE_STAGE_ORDER:
        execution = execute_mock_cascade(
            np.ones(3), "words", "reply", fault_plan=SeededFaultPlan(0, 1, (stage,))
        )
        assert execution.degradation is not None
        assert execution.degradation.failed_stage == stage


def test_mock_cascade_executes_only_enabled_stage_subset() -> None:
    from echoparley.cascade import CascadeConfiguration, execute_mock_cascade

    config = CascadeConfiguration(("punctuation", "tts"), (7, 11))
    execution = execute_mock_cascade(np.ones(2), "hello", "two units", configuration=config)
    assert [item.stage for item in execution.observations] == ["punctuation", "tts"]
    assert execution.ledger.total_ms == 18


def test_stage_latency_mapping_preserves_pipeline_order() -> None:
    from echoparley.cascade import execute_mock_cascade, stage_latency_mapping

    mapping = stage_latency_mapping(execute_mock_cascade(np.ones(2), "hello", "reply"))
    assert list(mapping) == ["vad", "stt", "punctuation", "lm", "tts"]
    assert sum(mapping.values()) == 255


def test_stage_latency_mapping_rejects_duplicate_names() -> None:
    from echoparley.cascade import (
        CascadeExecution,
        StageLatencyLedger,
        StageTiming,
        stage_latency_mapping,
    )

    execution = CascadeExecution(
        (), StageLatencyLedger((StageTiming("stt", 1), StageTiming("stt", 2))), "", "", ()
    )
    with pytest.raises(ValueError, match="duplicate"):
        stage_latency_mapping(execution)
