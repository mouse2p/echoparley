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


def test_release_version_matches_project_lock_and_changelog() -> None:
    import re
    import tomllib
    from pathlib import Path

    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    lock = tomllib.loads(Path("uv.lock").read_text(encoding="utf-8"))
    locked = next(item["version"] for item in lock["package"] if item["name"] == "echoparley")
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    released = re.search(r"^## ([0-9]+\.[0-9]+\.[0-9]+)$", changelog, re.MULTILINE)
    assert released is not None
    assert __version__ == project["project"]["version"] == locked == released.group(1)
