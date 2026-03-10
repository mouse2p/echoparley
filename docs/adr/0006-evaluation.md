# ADR 0006：turn-taking evaluation

状态：已采纳。

## 决策

所有 turn boundary、interrupt、floor hold 与 topic 指标只对照 scenario 中的 planted annotation。报告包含 F1、chance-corrected agreement、transition entropy、floor occupancy、latency percentile 与 seeded bootstrap interval。

## 理由与后果

hand-built case 提供可复核 known value，seeded bootstrap 提供重复性。指标衡量机制是否恢复了植入结构，而不是 conversational quality。SVG metadata 固定写明 `synthetic-planted`，防止图表脱离数据来源后被误读。
