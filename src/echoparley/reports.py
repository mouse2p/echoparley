"""Dependency-free deterministic SVG reports for synthetic evaluations."""

from __future__ import annotations

import html

from echoparley.artifacts import content_checksum
from echoparley.simulator import SimulationResult


def svg_report(result: SimulationResult, metrics: dict[str, object], *, title: str) -> str:
    """Render a timeline and metric table with stable ordering."""
    width, height = 800, 180 + 24 * len(metrics)
    maximum = max((event.time_ms for event in result.trace), default=1)
    rows = []
    for index, event in enumerate(result.trace):
        x = 40 + round(700 * event.time_ms / maximum)
        y = 55 + 22 * (index % 3)
        rows.append(
            f'<circle cx="{x}" cy="{y}" r="5" fill="#2563eb">'
            f"<title>{html.escape(event.agent)} {event.state.value}</title></circle>"
        )
    table = []
    for index, (key, value) in enumerate(sorted(metrics.items())):
        table.append(
            f'<text x="40" y="{130 + index * 24}" class="metric">'
            f"{html.escape(key)}: {html.escape(str(value))}</text>"
        )
    metadata = {"metrics": metrics, "title": title, "trace_events": len(result.trace)}
    digest = content_checksum(metadata)[:16]
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">',
            "<style>text{font-family:monospace;fill:#111827}.metric{font-size:14px}</style>",
            f'<metadata data-origin="synthetic-planted" data-digest="{digest}"/>',
            f'<text x="40" y="28" font-size="20">{html.escape(title)}</text>',
            '<line x1="40" y1="90" x2="740" y2="90" stroke="#94a3b8"/>',
            *rows,
            *table,
            "</svg>",
            "",
        ]
    )


def latency_histogram(values: tuple[int, ...], bin_ms: int = 50) -> tuple[tuple[int, int], ...]:
    """Count non-negative delays into deterministic fixed-width bins."""
    if bin_ms <= 0 or any(value < 0 for value in values):
        raise ValueError("histogram requires positive bins and non-negative values")
    counts: dict[int, int] = {}
    for value in values:
        start = value // bin_ms * bin_ms
        counts[start] = counts.get(start, 0) + 1
    return tuple(sorted(counts.items()))
