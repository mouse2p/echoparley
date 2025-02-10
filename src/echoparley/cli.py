"""Command-line entry point for echoparley."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from echoparley import __version__


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level command parser."""
    parser = argparse.ArgumentParser(
        prog="echoparley",
        description="Offline full-duplex spoken-dialogue mechanics workbench",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""
    build_parser().parse_args(argv)
    return 0
