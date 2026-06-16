"""Extraction and execution of explicitly marked documentation snippets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PythonSnippet:
    """Runnable source plus its one-based Markdown starting line."""

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


def execute_snippets(
    snippets: tuple[PythonSnippet, ...], *, filename: str = "<documentation>"
) -> tuple[dict[str, object], ...]:
    """Compile and execute each trusted project-documentation snippet independently."""
    namespaces = []
    for snippet in snippets:
        namespace: dict[str, object] = {"__name__": "__echoparley_snippet__"}
        padded = "\n" * (snippet.start_line - 1) + snippet.source
        exec(compile(padded, filename, "exec"), namespace)
        namespaces.append(namespace)
    return tuple(namespaces)
