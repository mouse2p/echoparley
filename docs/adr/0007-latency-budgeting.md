# ADR 0007：latency budgeting

状态：已采纳。

## 决策

每个 synthetic turn 分开记录 perception、decision 与 first-unit 时间；budget 同时约束 decision delay 和 total response delay。cascade ledger 另外保存各 stage delay，benchmark 使用 warmup 与 repeat，并只设数量级级别的宽松上界。

## 理由与后果

hard assertion 能在 simulator 中阻止预算悄然回归。accelerated logical time 的数字不能推断设备或网络性能；RTF 与 wall-clock benchmark 明确标记 machine-dependent，CI guard 只捕获数量级退化。
