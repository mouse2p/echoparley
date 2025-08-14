# API

- `echoparley.audio`：`AudioBuffer`、PCM16 WAV、framing 和 frame spans。
- `echoparley.features`：spectrum、mel filterbank、log-mel、sliding statistics。
- `echoparley.units`：PCA、k-means、unit alignment 与 usage perplexity。
- `echoparley.synth`：四类 seeded scenario 与 paired synthetic channels。
- `echoparley.stream`：三种 versioned interleave policy 和 exact mapping roundtrip。
- `echoparley.duplex`：显式六状态 engine、policy 和 transition trace。
- `echoparley.adapters`：protocol、scripted、replay 与 local-loopback mock。
- `echoparley.session`：recorder、replayer、digest 和 event-by-event diff。
- `echoparley.metrics` / `reports`：planted ground truth 指标与 deterministic SVG。

public dataclass 会在构造时验证边界。schema mapping 拒绝未知字段；JSONL decoder 验证 checksum。
