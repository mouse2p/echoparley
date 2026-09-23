# VQ toolkit

`echoparley.vq` 提供 codebook occupancy、entropy perplexity、effective size、collapse
判定、EMA update、dead-code revival 与 deterministic SVG loss curve。它们用于检查
synthetic embedding 上的量化机制；perplexity 只表示 code 使用分布，不衡量语音内容
或对话质量。

EMA 路径按 batch assignment 更新 centroid，revival 从当前 seeded synthetic batch
选择替代向量。小 batch 仍可能产生不稳定 usage，threshold 也不能跨数据集直接比较。
可选 Torch demo 只验证 reconstruction 与 quantization loss 在固定 seed 下真实下降，
不包含 pretrained encoder、真实 speech corpus 或可部署 codec。
