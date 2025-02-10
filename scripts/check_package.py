"""Smoke-check an installed wheel in an isolated environment."""

from __future__ import annotations

from echoparley import __version__
from echoparley.cli import main

assert __version__.count(".") == 2
assert main([]) == 0
