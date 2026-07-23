"""Run the small machine-dependent offline benchmark suite."""

import json

from echoparley.bench import benchmark_result_record, benchmark_suite


def run(seed: int = 2, repeats: int = 1) -> dict[str, object]:
    """Measure all benchmark cases after their built-in warmups."""
    samples = benchmark_suite(seed, repeats)
    return benchmark_result_record(samples, seed=seed, repeats=repeats)


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
