import pytest

from echoparley.runtime import TickConfig


def test_tick_config_defaults_to_accelerated_time() -> None:
    assert TickConfig() == TickConfig(20, True)
    with pytest.raises(ValueError, match="positive"):
        TickConfig(0)
