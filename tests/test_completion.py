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
