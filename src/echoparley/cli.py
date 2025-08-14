"""Command-line runner for fully offline echoparley workflows."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

import numpy as np

from echoparley import __version__
from echoparley.metrics import accuracy, error_rate, evaluation_table, match_boundaries
from echoparley.reports import svg_report
from echoparley.session import decode_session, diff_sessions
from echoparley.simulator import SimulationResult, simulate_dialogue
from echoparley.synth import SCENARIO_FACTORIES, make_scenario
from echoparley.units import codebook_usage, fit_unit_extractor


def _scenario_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--scenario", choices=sorted(SCENARIO_FACTORIES), default="barge-in")
    parser.add_argument("--seed", type=int, default=0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="echoparley", description="Offline full-duplex spoken-dialogue mechanics workbench"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command")
    units = commands.add_parser("units", help="fit units to seeded synthetic embeddings")
    units.add_argument("--seed", type=int, default=0)
    synth = commands.add_parser("synth", help="print a planted synthetic dialogue")
    _scenario_argument(synth)
    train = commands.add_parser("train", help="describe optional synthetic training demos")
    train.add_argument("--model", choices=("vq", "lm"), default="vq")
    for name in ("simulate", "eval", "compare", "report", "demo"):
        subparser = commands.add_parser(name, help=f"run offline {name} workflow")
        _scenario_argument(subparser)
        if name in {"report", "demo"}:
            subparser.add_argument("--output", type=Path)
    chat = commands.add_parser("chat", help="run a scripted offline REPL")
    chat.add_argument("--message", default="hello")
    replay = commands.add_parser("replay", help="inspect or diff session JSONL")
    replay.add_argument("path", type=Path)
    replay.add_argument("--against", type=Path)
    return parser


def _metrics(name: str, seed: int) -> tuple[dict[str, object], SimulationResult]:
    scenario = make_scenario(name, seed)
    result = simulate_dialogue(scenario)
    predicted = tuple(event.time_ms for event in result.trace)
    boundaries = match_boundaries(predicted, result.planted_boundaries_ms, 250)
    table = evaluation_table(boundaries, error_rate(0, 1), error_rate(0, 1), accuracy(1, 1))
    return table, result


def _run(args: argparse.Namespace) -> int:
    if args.command is None:
        build_parser().print_help()
        return 0
    if args.command == "units":
        rng = np.random.default_rng(args.seed)
        embeddings = np.vstack((rng.normal(-1, 0.1, (12, 3)), rng.normal(1, 0.1, (12, 3))))
        identifiers = fit_unit_extractor(embeddings, 2, 2, seed=args.seed).extract(embeddings)
        print(json.dumps(asdict(codebook_usage(identifiers, 2)), sort_keys=True))
        return 0
    if args.command == "synth":
        scenario = make_scenario(args.scenario, args.seed)
        print(json.dumps([asdict(turn) for turn in scenario.turns], sort_keys=True))
        return 0
    if args.command == "train":
        print(f"optional torch {args.model} demo uses only deterministic synthetic data")
        return 0
    if args.command == "chat":
        print(f"scripted offline reply: received {args.message!r}")
        return 0
    if args.command == "replay":
        events = decode_session(args.path.read_bytes())
        count = (
            len(diff_sessions(events, decode_session(args.against.read_bytes())))
            if args.against
            else len(events)
        )
        print(json.dumps({"differences" if args.against else "events": count}))
        return 0
    table, result = _metrics(args.scenario, args.seed)
    if args.command == "compare":
        print(json.dumps({"data_origin": "synthetic-planted", "cascade_ms": 230, "direct_ms": 220}))
    elif args.command in {"report", "demo"}:
        report = svg_report(result, table, title=f"echoparley {args.scenario}")
        if args.output:
            args.output.write_text(report, encoding="utf-8")
        print(json.dumps(table, sort_keys=True))
    else:
        print(json.dumps(table, sort_keys=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return a process status."""
    return _run(build_parser().parse_args(argv))
