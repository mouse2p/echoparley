# echoparley

echoparley 是一个离线优先的端到端语音对话机制实验台。项目聚焦离散语音单元、文本与语音统一 token 流、全双工轮次控制、可重放会话，以及基于合成对话的轮次评估。

当前基础包只依赖 NumPy，并支持 Python 3.11 及以上版本。所有默认流程使用带明确植入标注的合成输入，不下载模型或数据集，也不连接外部服务。

```bash
python -m venv .venv
.venv/bin/pip install -e .
.venv/bin/echoparley --version
```

echoparley 验证语音对话系统的工程机制，而不是任何真实语音大模型的对话质量。后续模块提供可复现的离线生成、模拟与评估接口。

## 许可证

[MIT](LICENSE)

