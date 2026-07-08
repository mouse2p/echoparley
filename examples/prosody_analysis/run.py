"""Measure pitch only on a deterministic synthetic tone fixture."""

import json
from dataclasses import asdict

from echoparley.prosody import (
    annotate_tone_events,
    autocorrelation_f0,
    smooth_pitch_track,
    summarize_pitch,
    synthesize_tone_scenario,
)


def run(seed: int = 7) -> dict[str, object]:
    """Return transparent measurements for a planted two-tone signal."""
    base_hz = 160.0 + 20.0 * (seed % 3)
    fixture = synthesize_tone_scenario((base_hz, base_hz + 60.0), segment_seconds=0.25)
    track = smooth_pitch_track(autocorrelation_f0(fixture.samples, fixture.sample_rate))
    return {
        "data_origin": "synthetic-planted",
        "seed": seed,
        "planted_hz": list(fixture.frequencies_hz),
        "pitch": asdict(summarize_pitch(track)),
        "tone_events": [asdict(event) for event in annotate_tone_events(track)],
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
