# ADR 0002：统一 token interleaving

状态：已采纳。

## 决策

text、speech unit 与 turn-control token 共用带 `speaker/start_ms/end_ms` 的 versioned stream。`strict-turn` 保留完整 turn，`time-aligned` 按时间与 namespace tie-break 排序，`dense-interleave` 使用显式 cadence。

## 理由与后果

三种 policy 都能精确拆分回原 namespace，policy 名称与 cadence 写入 artifact，避免 replay 时依赖隐藏默认值。dense policy 适合机制压力测试，但不表示真实模型采用相同调度。任何新 policy 都必须提供正反向 golden test 与 schema migration。
