"""Deterministic shell completion generation from an argparse parser."""

from __future__ import annotations

import argparse


def command_names(parser: argparse.ArgumentParser) -> tuple[str, ...]:
    """Return sorted subcommand names declared by a parser."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return tuple(sorted(action.choices))
    return ()


def bash_completion(parser: argparse.ArgumentParser) -> str:
    """Generate a dependency-free Bash completion function."""
    commands = " ".join(command_names(parser))
    return "\n".join(
        (
            "_echoparley_complete() {",
            "  local current",
            '  current="${COMP_WORDS[COMP_CWORD]}"',
            f'  COMPREPLY=( $(compgen -W "{commands}" -- "$current") )',
            "}",
            "complete -F _echoparley_complete echoparley",
            "",
        )
    )


def zsh_completion(parser: argparse.ArgumentParser) -> str:
    """Generate a compact Zsh command completion definition."""
    commands = " ".join(command_names(parser))
    return "\n".join(
        (
            "#compdef echoparley",
            f"_arguments '1:command:({commands})' '*::arg:->args'",
            "",
        )
    )
