# 离线机制 walkthrough

本教程只运行 seeded synthetic dialogue，不会下载模型或数据。先生成 planted barge-in 场景并验证可重现性：

```python echoparley-run
from echoparley.synth import barge_in_scenario

scenario = barge_in_scenario(seed=7)
assert scenario == barge_in_scenario(seed=7)
assert any(turn.kind == "interrupt" for turn in scenario.turns)
```

然后运行 accelerated duplex simulator。这里的时间是 logical milliseconds，不是设备 latency：

```python echoparley-run
from echoparley.simulator import simulate_dialogue
from echoparley.synth import barge_in_scenario

result = simulate_dialogue(barge_in_scenario(seed=7))
assert result.trace_bytes() == simulate_dialogue(barge_in_scenario(seed=7)).trace_bytes()
assert all(item.total_ms <= 500 for item in result.latencies)
```

最后检查 planted boundary score；该数字不代表真实 conversational quality：

```python echoparley-run
from echoparley.metrics import match_boundaries

score = match_boundaries((100, 300), (90, 310), tolerance_ms=20)
assert score.f1 == 1.0
```
