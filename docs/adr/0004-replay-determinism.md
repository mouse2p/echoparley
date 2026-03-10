# ADR 0004：session replay determinism

状态：已采纳。

## 决策

session event 采用连续 sequence、单调 logical time、canonical JSON 与逐行 checksum。replayer 重建完整 event，diff 以 insert/delete/change 分类；相同输入与 seed 必须产生 byte-identical trace。

## 理由与后果

logical time 使默认测试不依赖 wall clock。checksummed JSONL 能定位 corruption，但不是加密签名。取消操作保留已经提交的 partial events，后续 replay 因而能准确区分 clean completion 与 graceful cancellation。
