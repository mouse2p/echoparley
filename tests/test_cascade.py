from echoparley.cascade import ScriptedCascade


def test_scripted_cascade_exposes_each_stage() -> None:
    cascade = ScriptedCascade(lambda _: "hello", lambda value: value.upper(), lambda _: "ab")
    result = cascade.run("synthetic-audio")
    assert (result.transcript, result.response, result.units) == ("hello", "HELLO", (1, 2))
    assert result.total_delay_ms == 230


def test_cascade_rejects_negative_stage_latency() -> None:
    import pytest

    with pytest.raises(ValueError, match="non-negative"):
        ScriptedCascade(str, str, str, (1, -1, 1))


def test_path_comparison_uses_measured_delays() -> None:
    from echoparley.cascade import compare_paths

    result = ScriptedCascade(str, str, lambda _: "a").run("x")
    comparison = compare_paths(result, 100, (1, 2))
    assert comparison["latency_winner"] == "direct"
    assert comparison["cascade_ms"] == result.total_delay_ms
