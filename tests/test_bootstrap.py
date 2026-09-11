"""Smoke tests for package metadata and the initial command line."""

from __future__ import annotations

import pytest

import echoparley
from echoparley import ExperimentConfig, SchemaVersion, __version__
from echoparley.cli import main


def test_version_uses_patch_release_shape() -> None:
    parts = __version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_cli_reports_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match="0"):
        main(["--version"])
    assert capsys.readouterr().out == f"echoparley {__version__}\n"


def test_public_api_exports_foundations() -> None:
    assert echoparley.__all__ == ["ExperimentConfig", "SchemaVersion", "__version__"]
    assert ExperimentConfig().seed == 0
    assert str(SchemaVersion(1)) == "1.0"


def test_package_checker_verifies_metadata_and_cli() -> None:
    import runpy

    namespace = runpy.run_path("scripts/check_package.py")
    assert namespace["main"]() == 0
