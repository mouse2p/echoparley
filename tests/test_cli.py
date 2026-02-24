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


def test_bench_command_exports_checksummed_samples(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import json

    from echoparley.bench import decode_benchmark_jsonl

    output = tmp_path / "bench.jsonl"
    assert main(["bench", "--repeats", "1", "--output", str(output)]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 3
    assert len(decode_benchmark_jsonl(output.read_bytes())) == 3


def test_bench_command_rejects_nonpositive_repeats() -> None:
    with pytest.raises(ValueError, match="configuration"):
        main(["bench", "--repeats", "0"])


def test_cli_json_envelope_schema_is_exhaustive() -> None:
    from echoparley.cli import _json_envelope

    envelope = _json_envelope("units", {"occupied": 2})
    assert set(envelope) == {"schema_version", "command", "status", "data"}
    assert envelope["schema_version"] == "1.0"


def test_every_subcommand_accepts_json_mode() -> None:
    parser = build_parser()
    choices = parser._subparsers._group_actions[0].choices
    for name, subparser in choices.items():
        assert "--json" in subparser.format_help(), name


def test_units_json_mode_wraps_result(capsys: pytest.CaptureFixture[str]) -> None:
    import json

    main(["units", "--json"])
    envelope = json.loads(capsys.readouterr().out)
    assert envelope["command"] == "units" and envelope["data"]["occupied"] == 2


@pytest.mark.parametrize("command", ["train", "chat", "prosody", "scenarios", "bench"])
def test_new_commands_share_json_schema(command: str, capsys: pytest.CaptureFixture[str]) -> None:
    import json

    arguments = [command, "--json"] + (["--repeats", "1"] if command == "bench" else [])
    assert main(arguments) == 0
    envelope = json.loads(capsys.readouterr().out)
    assert envelope["command"] == command and envelope["status"] == "ok"


@pytest.mark.parametrize("command", ["synth", "simulate", "eval", "compare", "report", "demo"])
def test_legacy_workflows_share_json_schema(
    command: str, capsys: pytest.CaptureFixture[str]
) -> None:
    import json

    assert main([command, "--json"]) == 0
    envelope = json.loads(capsys.readouterr().out)
    assert envelope["schema_version"] == "1.0" and envelope["command"] == command
