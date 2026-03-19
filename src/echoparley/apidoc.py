"""Docstring-driven API reference inventory."""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class APIEntry:
    module: str
    name: str
    kind: str
    summary: str


def public_api_entries(module_name: str) -> tuple[APIEntry, ...]:
    """Inspect public functions and classes defined by one package module."""
    module = importlib.import_module(module_name)
    entries = []
    for name, value in inspect.getmembers(module):
        if name.startswith("_") or getattr(value, "__module__", None) != module_name:
            continue
        kind = (
            "class" if inspect.isclass(value) else "function" if inspect.isfunction(value) else None
        )
        if kind is None:
            continue
        documentation = inspect.getdoc(value) or ""
        summary = documentation.splitlines()[0] if documentation else ""
        entries.append(APIEntry(module_name, name, kind, summary))
    return tuple(entries)


def missing_docstrings(module_name: str) -> tuple[str, ...]:
    return tuple(entry.name for entry in public_api_entries(module_name) if not entry.summary)
