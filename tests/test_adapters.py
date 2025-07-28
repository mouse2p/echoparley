import pytest

from echoparley.adapters import AdapterAction


def test_adapter_action_validates_delay() -> None:
    assert AdapterAction(("hello",)).finished
    with pytest.raises(ValueError, match="non-negative"):
        AdapterAction((), -1)


def test_scripted_adapter_preserves_action_order() -> None:
    from echoparley.adapters import ScriptedAdapter

    adapter = ScriptedAdapter((AdapterAction(("one",)), AdapterAction(("two",))))
    assert adapter.act(()).tokens == ("one",)
    assert adapter.act(()).tokens == ("two",)
    with pytest.raises(StopIteration, match="exhausted"):
        adapter.act(())


def test_scripted_adapter_reset_replays_from_start() -> None:
    from echoparley.adapters import ScriptedAdapter

    adapter = ScriptedAdapter((AdapterAction(("again",)),))
    adapter.act(())
    adapter.reset()
    assert adapter.act(()).tokens == ("again",)
