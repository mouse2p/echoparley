import pytest

from echoparley.cascade import StageObservation


def test_stage_observation_validates_names_and_delay() -> None:
    assert StageObservation("stt", "audio", "words", 20).stage == "stt"
    with pytest.raises(ValueError, match="invalid"):
        StageObservation("remote", "x", "y", 0)
