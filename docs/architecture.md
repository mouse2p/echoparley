# 架构

`audio → features → units → stream` 构成前端；`events → duplex → simulator` 构成 turn-taking 核心；`adapters/cascade → session/runtime → metrics/reports` 构成实验与评估层。每个 serialized artifact 都有 schema version、canonical JSON 约定与 checksum。

状态机禁止从 `LISTEN` 直接进入 `SPEAK`。remote endpoint 必须先触发 `TAKE_FLOOR`，generation ready 才能进入 `SPEAK`。高置信度 overlap 进入 `BARGE_IN`，清空 partial units 后经过 `RECOVER` 回到 `LISTEN`。

机制背景可参考 [VQ-VAE](https://arxiv.org/abs/1711.00937)、[HuBERT](https://arxiv.org/abs/2106.07447)、[SoundStream](https://arxiv.org/abs/2107.03312)、[EnCodec](https://arxiv.org/abs/2210.13438) 与 [Moshi](https://arxiv.org/abs/2410.00037)。echoparley 不使用这些工作的代码、权重或数据。
