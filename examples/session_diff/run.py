"""Render a deterministic comparison of two small synthetic sessions."""

import json
from pathlib import Path

from echoparley.reports import session_comparison_metadata, session_diff_report_svg
from echoparley.session import SessionEvent


def build() -> tuple[str, dict[str, object]]:
    """Return an SVG and checksummed metadata for a planted event change."""
    left = (SessionEvent(0, 0, "listen", {}), SessionEvent(1, 20, "speak", {}))
    right = (SessionEvent(0, 0, "listen", {}), SessionEvent(1, 25, "speak", {}))
    return session_diff_report_svg(left, right), session_comparison_metadata(left, right)


def run(output: str = "session-diff.svg") -> dict[str, object]:
    """Write the visualization and return its comparison metadata."""
    svg, metadata = build()
    Path(output).write_text(svg, encoding="utf-8")
    return {**metadata, "output": output, "data_origin": "synthetic-planted"}


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
