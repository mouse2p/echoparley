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
- `echoparley.prosody`：autocorrelation F0、contour smoothing、tone event 与 prosodic vector。
- `echoparley.scenarios`：扩展 template、三 speaker contention、taxonomy 与 manifest v2。
- `echoparley.context`：recency、turn-boundary、salience eviction 与 retention score。
- `echoparley.vq`：collapse health、EMA update、dead-code revival 与 loss SVG。
- `echoparley.bench`：warmup/repeat harness、RTF sample、JSONL 与宽松 regression guard。
- `echoparley.proptest`：seeded case generator、counterexample shrinking 与跨模块 invariant。
- `echoparley.completion`：从 argparse parser 生成 Bash/Zsh completion。
- `echoparley.snippets` / `apidoc`：可执行 tutorial fence 与 docstring inventory。

public dataclass 会在构造时验证边界。schema mapping 拒绝未知字段；JSONL decoder 验证 checksum。
