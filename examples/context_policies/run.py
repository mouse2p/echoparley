"""Compare context eviction on a planted long dialogue."""

import json

from echoparley.context import (
    ContextBenchmarkConfig,
    benchmark_context_policies,
    best_retention_policy,
    context_benchmark_report,
)
from echoparley.scenarios import long_topic_scenario
from echoparley.state import ConversationTurn


def run(seed: int = 3) -> dict[str, object]:
    """Measure relevant-turn retention under one shared token budget."""
    scenario = long_topic_scenario(seed, 30)
    turns = tuple(
        ConversationTurn(turn.speaker, turn.text, 3, turn.start_ms, turn.end_ms, turn.topic)
        for turn in scenario.turns
    )
    scores = benchmark_context_policies(turns, ContextBenchmarkConfig(18, frozenset({"target"})))
    return {
        **context_benchmark_report(scores),
        "seed": seed,
        "best_policy": best_retention_policy(scores).value,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
