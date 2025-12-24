"""Dependency-free deterministic SVG reports for synthetic evaluations."""

from __future__ import annotations

import html

from echoparley.artifacts import content_checksum
from echoparley.session import SessionDifference, SessionEvent, difference_kind
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


def strategy_comparison_svg(rows: tuple[dict[str, object], ...]) -> str:
    """Render measured synthetic strategy yield rates as deterministic bars."""
    bars = []
    for index, row in enumerate(rows):
        rate = float(row["yield_rate"])
        if not 0 <= rate <= 1:
            raise ValueError("strategy yield rates must be bounded")
        width = round(rate * 400)
        label = html.escape(str(row["strategy"]))
        bars.append(
            f'<text x="20" y="{35 + index * 35}">{label}</text>'
            f'<rect x="180" y="{20 + index * 35}" width="{width}" '
            'height="18" fill="#0f766e"/>'
        )
    height = 40 + 35 * len(rows)
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="620" height="{height}">',
            '<metadata data-origin="synthetic-planted"/>',
            *bars,
            "</svg>",
            "",
        ]
    )


def session_timeline_group(
    events: tuple[SessionEvent, ...], *, label: str, x_offset: int = 0
) -> str:
    """Render one session as a labeled SVG group for composition."""
    if any(events[index + 1].time_ms < events[index].time_ms for index in range(len(events) - 1)):
        raise ValueError("session timeline events must be chronological")
    maximum = max((event.time_ms for event in events), default=1)
    elements = [f'<text x="{x_offset + 20}" y="22">{html.escape(label)}</text>']
    for index, event in enumerate(events):
        x = x_offset + 20 + round(320 * event.time_ms / max(1, maximum))
        y = 45 + index * 20
        elements.append(
            f'<circle cx="{x}" cy="{y}" r="4" class="event">'
            f"<title>{html.escape(event.kind)}</title></circle>"
        )
    return "\n".join(elements)


def side_by_side_session_svg(
    left: tuple[SessionEvent, ...],
    right: tuple[SessionEvent, ...],
    *,
    left_label: str = "left",
    right_label: str = "right",
) -> str:
    """Compose two replay timelines using independent time scales."""
    height = 70 + 20 * max(len(left), len(right))
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="{height}">',
            "<style>.event{fill:#2563eb}.divider{stroke:#94a3b8}</style>",
            '<line class="divider" x1="380" y1="0" x2="380" y2="100%"/>',
            session_timeline_group(left, label=left_label),
            session_timeline_group(right, label=right_label, x_offset=400),
            "</svg>",
            "",
        ]
    )


def event_diff_rows(values: tuple[SessionDifference, ...], *, start_y: int = 20) -> tuple[str, ...]:
    """Render insert/delete/change rows with semantic CSS classes."""
    rows = []
    for index, value in enumerate(values):
        kind = difference_kind(value).value
        left = value.left.kind if value.left else "∅"
        right = value.right.kind if value.right else "∅"
        label = html.escape(f"{value.sequence}: {left} → {right}")
        rows.append(f'<text x="20" y="{start_y + index * 22}" class="diff {kind}">{label}</text>')
    return tuple(rows)
