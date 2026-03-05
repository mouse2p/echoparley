"""Deterministic shell completion generation from an argparse parser."""

from __future__ import annotations

import argparse
import re

_SAFE_TOKEN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _validated_commands(parser: argparse.ArgumentParser) -> tuple[str, ...]:
    names = command_names(parser)
    if any(_SAFE_TOKEN.fullmatch(name) is None for name in names):
        raise ValueError("completion command contains unsupported shell characters")
    return names


def command_names(parser: argparse.ArgumentParser) -> tuple[str, ...]:
    """Return sorted subcommand names declared by a parser."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return tuple(sorted(action.choices))
    return ()


def bash_completion(parser: argparse.ArgumentParser) -> str:
    """Generate a dependency-free Bash completion function."""
    commands = " ".join(_validated_commands(parser))
    options = " ".join(
        sorted({option for values in command_options(parser).values() for option in values})
    )
    return "\n".join(
        (
            "_echoparley_complete() {",
            "  local current",
            '  current="${COMP_WORDS[COMP_CWORD]}"',
            f'  COMPREPLY=( $(compgen -W "{commands} {options}" -- "$current") )',
            "}",
            "complete -F _echoparley_complete echoparley",
            "",
        )
    )


def zsh_completion(parser: argparse.ArgumentParser) -> str:
    """Generate a compact Zsh command completion definition."""
    commands = " ".join(_validated_commands(parser))
    return "\n".join(
        (
            "#compdef echoparley",
            f"_arguments '1:command:({commands})' '*::arg:->args'",
            "",
        )
    )


def command_options(parser: argparse.ArgumentParser) -> dict[str, tuple[str, ...]]:
    """Return sorted long options for each subcommand."""
    options: dict[str, tuple[str, ...]] = {}
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, subparser in action.choices.items():
                values = {
                    option
                    for item in subparser._actions
                    for option in item.option_strings
                    if option.startswith("--")
                }
                options[name] = tuple(sorted(values))
    return dict(sorted(options.items()))


def completion_assets(parser: argparse.ArgumentParser) -> dict[str, str]:
    """Return stable relative filenames and generated contents."""
    return {"_echoparley": zsh_completion(parser), "echoparley.bash": bash_completion(parser)}
