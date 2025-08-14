from pathlib import Path

from echoparley.metrics import evaluation_table, match_boundaries
from echoparley.reports import svg_report
from echoparley.simulator import simulate_dialogue
from echoparley.synth import barge_in_scenario

scenario = barge_in_scenario(3)
result = simulate_dialogue(scenario)
scores = match_boundaries(
    tuple(event.time_ms for event in result.trace), result.planted_boundaries_ms, 250
)
metrics = evaluation_table(scores, 0.0, 0.0, 1.0)
Path("barge-in.svg").write_text(svg_report(result, metrics, title="Synthetic barge-in"))
print(metrics)
