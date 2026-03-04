"""Regenerate checked-in shell completion assets from the CLI parser."""

from pathlib import Path

from echoparley.cli import build_parser
from echoparley.completion import bash_completion, zsh_completion


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    target = root / "completions"
    target.mkdir(exist_ok=True)
    parser = build_parser()
    (target / "echoparley.bash").write_text(bash_completion(parser), encoding="utf-8")
    (target / "_echoparley").write_text(zsh_completion(parser), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
