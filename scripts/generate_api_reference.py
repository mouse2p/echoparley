"""Regenerate the checked-in docstring-derived API reference."""

from pathlib import Path

from echoparley.apidoc import PHASE_TWO_API_MODULES, render_api_reference


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    target = root / "docs" / "api-generated.md"
    target.write_text(render_api_reference(PHASE_TWO_API_MODULES), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
