from echoparley.cli import build_parser
from echoparley.completion import command_names


def test_command_names_match_parser_choices() -> None:
    names = command_names(build_parser())
    assert names == tuple(sorted(names))
    assert {"demo", "prosody", "bench", "scenarios"} <= set(names)


def test_bash_completion_registers_the_executable() -> None:
    from echoparley.completion import bash_completion

    script = bash_completion(build_parser())
    assert "complete -F _echoparley_complete echoparley" in script
    assert "prosody" in script and script.endswith("\n")
    assert "--json" in script and "--frequency" in script


def test_zsh_completion_declares_compdef_and_commands() -> None:
    from echoparley.completion import zsh_completion

    script = zsh_completion(build_parser())
    assert script.startswith("#compdef echoparley\n")
    assert "bench" in script and "scenarios" in script


def test_bash_and_zsh_completion_contain_every_command() -> None:
    from echoparley.completion import bash_completion, zsh_completion

    parser = build_parser()
    for name in command_names(parser):
        assert name in bash_completion(parser)
        assert name in zsh_completion(parser)


def test_command_options_include_json_and_specific_flags() -> None:
    from echoparley.completion import command_options

    options = command_options(build_parser())
    assert all("--json" in values for values in options.values())
    assert {"--frequency", "--duration"} <= set(options["prosody"])


def test_completion_rejects_unsafe_command_names() -> None:
    import argparse

    import pytest

    from echoparley.completion import bash_completion

    parser = argparse.ArgumentParser()
    parser.add_subparsers().add_parser("bad name")
    with pytest.raises(ValueError, match="shell characters"):
        bash_completion(parser)


def test_completion_generator_script_is_importable() -> None:
    import runpy
    from pathlib import Path

    namespace = runpy.run_path(str(Path("scripts/generate_completions.py")))
    assert callable(namespace["main"])


def test_checked_in_completion_assets_match_parser() -> None:
    from pathlib import Path

    from echoparley.completion import bash_completion, zsh_completion

    parser = build_parser()
    assert Path("completions/echoparley.bash").read_text() == bash_completion(parser)
    assert Path("completions/_echoparley").read_text() == zsh_completion(parser)
