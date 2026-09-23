# Context eviction policy

三种 policy 共用精确 token budget。`recency` 保留最新连续 turn，适合局部衔接；
`turn-boundary` 只接纳完整 topic segment，可能因最后一个 segment 过大而留空；
`salience` 按 score 选择完整 turn，再恢复时间顺序，因此能保留较早的 planted relevant
turn，但不保证上下文连续。

`examples/context_policies` 在同一个 seeded long dialogue 上报告 relevant-turn recall 与
实际 token usage。示例 salience 来自已知 synthetic topic label，是评估 policy 的透明
fixture，不是 learned retrieval score。不同任务应同时记录 retention、连续性和预算利用率。
