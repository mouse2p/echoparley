"""Summarize the reproducible expanded synthetic scenario catalog."""

import json

from echoparley.artifacts import bytes_checksum
from echoparley.scenarios import corpus_report, encode_scenario_corpus, scenario_catalog


def run(seed: int = 5) -> dict[str, object]:
    """Return checksummed corpus statistics at one seed."""
    catalog = scenario_catalog(seed)
    encoded = encode_scenario_corpus(tuple((scenario, None) for scenario in catalog.values()))
    return {
        "seed": seed,
        "scenario_names": sorted(catalog),
        "corpus": corpus_report(tuple(catalog.values())),
        "manifest_bytes": len(encoded),
        "manifest_checksum": bytes_checksum(encoded),
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
