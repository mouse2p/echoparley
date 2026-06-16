# 性能测量

`echoparley bench --repeats 5 --output samples.jsonl` 测量 unit extraction、stream roundtrip 与 accelerated simulator。harness 在计时前 warm up，并保存 Python、NumPy、package 与操作系统版本。

结果是当前机器的 wall-clock measurement，不是跨机器 benchmark。RTF 使用 synthetic audio duration 作分母；stream throughput 使用处理 item 数量。CI 只采用默认十倍 tolerance 的 loose guard，用于发现数量级退化，不比较微小波动。JSONL 中每个 sample 与 summary 都有 schema version 和 checksum。
