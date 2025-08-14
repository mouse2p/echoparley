# 使用指南

`echoparley synth` 查看 planted turns；`units` 拟合离线 PCA+k-means；`simulate` 运行 duplex engine；`eval` 输出 boundary F1、false interrupt、missed barge-in 与 floor hold 指标；`report` 生成 SVG；`replay` 检查 checksummed JSONL；`demo` 串联完整离线路径。

所有 seed 都显式传入。需要保存结果时，同时保存 CLI 参数、package version、config fingerprint 与 report 中的 synthetic data-origin 标记。
