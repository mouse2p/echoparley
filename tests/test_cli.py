from pathlib import Path

import pytest

from echoparley.cli import build_parser, main


def test_cli_exposes_required_subcommands() -> None:
    help_text = build_parser().format_help()
    for command in (
        "units",
        "synth",
        "train",
        "simulate",
        "chat",
        "replay",
        "eval",
        "compare",
        "report",
        "demo",
        "prosody",
        "scenarios",
        "bench",
    ):
        assert command in help_text


@pytest.mark.parametrize("command", ["synth", "simulate", "eval", "compare"])
def test_offline_commands_complete(command: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([command, "--seed", "2"]) == 0
    assert capsys.readouterr().out


def test_demo_writes_svg_report(tmp_path: Path) -> None:
    output = tmp_path / "report.svg"
    assert main(["demo", "--scenario", "booking", "--output", str(output)]) == 0
    assert output.read_text().startswith("<svg")


def test_prosody_command_measures_a_synthetic_tone(capsys: pytest.CaptureFixture[str]) -> None:
    import json

    assert main(["prosody", "--frequency", "200"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["data_origin"] == "deterministic-synthetic"
    assert abs(payload["median_f0_hz"] - 200) < 5


def test_scenarios_command_lists_expanded_templates(capsys: pytest.CaptureFixture[str]) -> None:
    import json

    assert main(["scenarios", "--seed", "2"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert "three-speaker-contention" in payload["names"]
    assert payload["statistics"]["data_origin"] == "synthetic-planted"


def test_prosody_command_rejects_nonpositive_frequency() -> None:
    with pytest.raises(ValueError, match="positive"):
        main(["prosody", "--frequency", "0"])


def test_scenarios_command_is_reproducible(capsys: pytest.CaptureFixture[str]) -> None:
    main(["scenarios", "--seed", "5"])
    first = capsys.readouterr().out
    main(["scenarios", "--seed", "5"])
    assert capsys.readouterr().out == first
