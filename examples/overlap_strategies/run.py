"""Compare deterministic barge-in decisions on shared evidence."""

import json

from echoparley.simulator import strategy_comparison_table, sweep_barge_in_strategies


def run() -> dict[str, object]:
    """Return a table measured from explicitly planted posterior values."""
    posteriors = (0.5, 0.76, 0.85, 0.95)
    rows = strategy_comparison_table(sweep_barge_in_strategies(posteriors))
    return {
        "data_origin": "synthetic-planted",
        "posteriors": list(posteriors),
        "strategies": list(rows),
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
