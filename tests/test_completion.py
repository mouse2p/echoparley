from echoparley.cli import build_parser
from echoparley.completion import command_names


def test_command_names_match_parser_choices() -> None:
    names = command_names(build_parser())
    assert names == tuple(sorted(names))
    assert {"demo", "prosody", "bench", "scenarios"} <= set(names)
