# echoparley

echoparley 是一个离线优先的端到端语音对话机制实验台。它把离散 speech unit、文本与语音统一 token stream、全双工 turn-taking、可重放 session 和带植入标注的评估组合成一个小型 Python 框架。

本项目验证的是机制：WAV/framing、log-mel 与滑动统计、PCA+k-means unit extraction、三种 interleave policy、barge-in state machine、latency accounting、replay determinism 和 synthetic evaluation methodology。它不实现或声称任何真实 speech LLM 的对话质量，不使用真实对话数据集、pretrained weight、外部 endpoint 或人工评测分数。

## 安装

需要 Python 3.11+：

```bash
python -m venv .venv
.venv/bin/pip install -e .
```

可选 CPU PyTorch 演示：

```bash
.venv/bin/pip install -e '.[torch]' --extra-index-url https://download.pytorch.org/whl/cpu
```

## 快速开始

```bash
echoparley demo --scenario barge-in --seed 7 --output report.svg
echoparley compare --scenario booking --seed 4
echoparley --help
```

Python API：

```python
from echoparley.simulator import simulate_dialogue
from echoparley.synth import barge_in_scenario

result = simulate_dialogue(barge_in_scenario(seed=7))
assert result.trace_bytes() == simulate_dialogue(barge_in_scenario(seed=7)).trace_bytes()
```

## 架构

数据从合成场景或 PCM WAV 进入 feature/unit 前端，随后映射为带时间戳的 unified stream。`DuplexEngine` 以 `LISTEN → TAKE_FLOOR → SPEAK → YIELD` 为正常路径，以 `BARGE_IN → RECOVER → LISTEN` 处理打断。adapter 提供 scripted、replay、local-loopback 与 cascade 路径；session 层将每个事件写成 checksummed JSONL。评估层只把输出与 synthetic planted annotations 比较，并生成无外部绘图库的确定性 SVG。

## 示例

- `examples/synthetic_units`：生成 synthetic embedding 并提取 unit。
- `examples/duplex_barge_in`：重放打断场景并输出 SVG timeline。
- `examples/session_replay`：验证 event trace byte-identical replay。
- `examples/path_comparison`：比较 scripted cascade 与直接路径的延迟记账。
- `examples/prosody_analysis`：测量植入纯音的 F0 与 tone event。
- `examples/scenario_corpus`：汇总扩展 synthetic scenario catalog。
- `examples/context_policies`：比较相同 token budget 下的 context retention。
- `examples/overlap_strategies`：扫描三种 barge-in policy。
- `examples/runtime_benchmark`：运行带 warmup 的本机性能测量。
- `examples/session_diff`：生成两个 session 的确定性 SVG diff。

## 限制与诚实说明

- 所有默认数字来自确定性 synthetic fixtures；它们不是公开 benchmark 结果。
- NumPy unit 是机制基线，不代表 HuBERT 等 pretrained semantic representation。
- local HTTP adapter 只允许 loopback mock；没有网络服务集成或密钥处理。
- PyTorch VQ/LM demo 只要求在 synthetic data 上真实降低 loss；它不生成可用语音模型。
- simulator 是 accelerated logical time，不替代真实设备、网络和人类交互测量。

详见 [架构](docs/architecture.md)、[使用指南](docs/usage.md) 与 [API](docs/api.md)。项目使用 [MIT](LICENSE) 许可证。
