import pytest

from echoparley.adapters import AdapterAction


def test_adapter_action_validates_delay() -> None:
    assert AdapterAction(("hello",)).finished
    with pytest.raises(ValueError, match="non-negative"):
        AdapterAction((), -1)
