"""Regenerate checked-in shell completion assets from the CLI parser."""

from pathlib import Path

from echoparley.cli import build_parser
from echoparley.completion import completion_assets


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    target = root / "completions"
    target.mkdir(exist_ok=True)
    for name, content in completion_assets(build_parser()).items():
        (target / name).write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
