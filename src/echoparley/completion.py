"""Deterministic shell completion generation from an argparse parser."""

from __future__ import annotations

import argparse


def command_names(parser: argparse.ArgumentParser) -> tuple[str, ...]:
    """Return sorted subcommand names declared by a parser."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return tuple(sorted(action.choices))
    return ()
