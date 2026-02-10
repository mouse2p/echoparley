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
