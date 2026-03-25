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
