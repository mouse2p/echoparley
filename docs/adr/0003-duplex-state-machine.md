# ADR 0003：显式 duplex 状态机

状态：已采纳。

## 决策

turn engine 使用 `LISTEN / TAKE_FLOOR / SPEAK / YIELD / BARGE_IN / RECOVER` 六个显式状态。`GENERATION_READY` 只有在 `TAKE_FLOOR` 后才能进入 `SPEAK`；barge-in 必须清空 partial units，再经 `RECOVER` 返回 `LISTEN`。

## 理由与后果

显式 transition trace 便于 property generator 穷举随机 endpoint sequence，并让 immediate-yield、grace-window、competitive-floor 共用核心 invariant。状态机模拟的是调度机制，不衡量回复内容。full-duplex 术语背景可参考 [Moshi](https://arxiv.org/abs/2410.00037)。
