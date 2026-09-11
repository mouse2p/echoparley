"""Smoke-check an installed wheel in an isolated environment."""

from __future__ import annotations

import json
from contextlib import redirect_stdout
from importlib.metadata import version
from io import StringIO

from echoparley import __version__
from echoparley.cli import main as cli_main


def main() -> int:
    """Verify distribution metadata and a JSON CLI path from the installed wheel."""
    if version("echoparley") != __version__:
        raise AssertionError("distribution and import versions differ")
    output = StringIO()
    with redirect_stdout(output):
        status = cli_main(["units", "--seed", "1", "--json"])
    payload = json.loads(output.getvalue())
    if status != 0 or payload.get("schema_version") != "1.0":
        raise AssertionError("installed CLI smoke check failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
