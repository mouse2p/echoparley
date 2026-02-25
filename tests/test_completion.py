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
