# ADR 0001：离线 semantic unit

状态：已采纳。

## 决策

默认前端使用 seeded PCA 与 k-means，把 synthetic feature frame 映射为离散 unit；prosody-aware 变体把可解释的 F0、pause、speech-rate 特征作为附加列。可选 PyTorch 路径只训练小型 synthetic VQ，不下载权重。

## 理由与后果

这条路径能测试 codebook occupancy、alignment、roundtrip 与 collapse handling，同时保持 NumPy-only 默认安装。它不声称 unit 具备真实语义质量。概念背景见 [VQ-VAE](https://arxiv.org/abs/1711.00937) 与 [HuBERT](https://arxiv.org/abs/2106.07447)；实现、schema 与 fixture 均为本项目自有设计。
