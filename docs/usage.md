# 使用指南

`echoparley synth` 查看 planted turns；`units` 拟合离线 PCA+k-means；`simulate` 运行 duplex engine；`eval` 输出 boundary F1、false interrupt、missed barge-in 与 floor hold 指标；`report` 生成 SVG；`replay` 检查 checksummed JSONL；`demo` 串联完整离线路径。

所有 seed 都显式传入。需要保存结果时，同时保存 CLI 参数、package version、config fingerprint 与 report 中的 synthetic data-origin 标记。

## Scenario manifest

`echoparley scenarios --seed 7 --output scenarios.jsonl` 将扩展场景写为
`dialogue-scenario` artifact。每行含 schema 2.0 manifest、speaker index、完整 turn
标注和覆盖语义内容的 checksum。读取时会校验 checksum、artifact kind、schema 与
场景名称唯一性；这些文件仍然只描述 synthetic planted ground truth。

## 输出与 exit status

每个 subcommand 都接受 `--json`，成功时输出 `schema_version`、`command`、
`status: "ok"` 和 `data`。普通模式保留适合终端阅读的紧凑输出。正常完成与 help
返回 0；参数解析、文件读取和输入验证错误返回 2。JSON 模式下的运行期错误写入
stderr，并使用相同 schema 和 `status: "error"`。命令不会连接远程 endpoint。
