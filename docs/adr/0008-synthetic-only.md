# ADR 0008：synthetic-only 默认路径

状态：已采纳。

## 决策

默认测试、CLI 与 example 只使用 seeded waveform、feature、scripted adapter、loopback mock 和 planted dialogue。项目不下载 pretrained model、真实 conversation dataset，也不连接远程 endpoint。

## 理由与后果

该边界让机械 invariant 可离线重现，并避免把 synthetic score 描述为真实 benchmark。PyTorch extra 展示真实 loss decrease 与 codebook behavior，但不产生可部署 speech model。任何未来真实数据 adapter 必须单独标识来源、许可、隐私与评测限制。
