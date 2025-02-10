"""Smoke tests for package metadata and the initial command line."""

from __future__ import annotations

import pytest

from echoparley import __version__
from echoparley.cli import main


def test_version_uses_patch_release_shape() -> None:
    parts = __version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_cli_reports_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match="0"):
        main(["--version"])
    assert capsys.readouterr().out == f"echoparley {__version__}\n"
