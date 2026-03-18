"""Extraction and execution of explicitly marked documentation snippets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PythonSnippet:
    source: str
    start_line: int


def extract_python_snippets(markdown: str) -> tuple[PythonSnippet, ...]:
    """Extract fenced blocks labeled `python echoparley-run`."""
    snippets = []
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        if lines[index].strip() != "```python echoparley-run":
            index += 1
            continue
        start = index + 2
        index += 1
        body = []
        while index < len(lines) and lines[index].strip() != "```":
            body.append(lines[index])
            index += 1
        if index == len(lines):
            raise ValueError(f"unterminated runnable Python fence at line {start}")
        snippets.append(PythonSnippet("\n".join(body) + "\n", start))
        index += 1
    return tuple(snippets)
