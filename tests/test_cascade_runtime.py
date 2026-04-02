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
