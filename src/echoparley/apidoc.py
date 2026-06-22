"""Docstring-driven API reference inventory."""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class APIEntry:
    """One public module-local function or class and its docstring summary."""

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
    """Return public names that lack a usable docstring summary."""
    return tuple(entry.name for entry in public_api_entries(module_name) if not entry.summary)


def render_api_entry(entry: APIEntry) -> str:
    """Render one API entry as a compact Markdown definition item."""
    summary = entry.summary or "未提供 docstring。"
    return f"- `{entry.name}` ({entry.kind}): {summary}"


def render_module_reference(module_name: str) -> str:
    """Render all public module-local APIs from live docstrings."""
    entries = public_api_entries(module_name)
    lines = [f"## `{module_name}`", ""]
    lines.extend(render_api_entry(entry) for entry in entries)
    lines.append("")
    return "\n".join(lines)


def render_api_reference(modules: tuple[str, ...]) -> str:
    """Render a complete Markdown reference for distinct module names."""
    if not modules or len(modules) != len(set(modules)):
        raise ValueError("API reference modules must be nonempty and distinct")
    sections = "\n".join(render_module_reference(module) for module in modules)
    return "# Generated API reference\n\n" + sections
