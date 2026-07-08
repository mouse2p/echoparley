"""Summarize the reproducible expanded synthetic scenario catalog."""

import json

from echoparley.scenarios import corpus_report, scenario_catalog


def run(seed: int = 5) -> dict[str, object]:
    """Return checksummed corpus statistics at one seed."""
    catalog = scenario_catalog(seed)
    return {
        "seed": seed,
        "scenario_names": sorted(catalog),
        "corpus": corpus_report(tuple(catalog.values())),
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
