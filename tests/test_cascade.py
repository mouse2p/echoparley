from echoparley.cascade import ScriptedCascade


def test_scripted_cascade_exposes_each_stage() -> None:
    cascade = ScriptedCascade(lambda _: "hello", lambda value: value.upper(), lambda _: "ab")
    result = cascade.run("synthetic-audio")
    assert (result.transcript, result.response, result.units) == ("hello", "HELLO", (1, 2))
    assert result.total_delay_ms == 230
