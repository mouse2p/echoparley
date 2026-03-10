# ADR 0005：cascade 与 direct path 比较

状态：已采纳。

## 决策

cascade 由 mock VAD、STT、punctuation、text-LM 与 aligned TTS stage 组成，并逐 stage 记录 delay。direct adapter 与 cascade 接收相同 planted dialogue；fault plan 用 seed 决定失败 stage，并返回显式 fallback。

## 理由与后果

比较结果只代表本地 synthetic simulator 中的实际记账，不代表任何商业 STT、LLM 或 TTS。stage 可重配置但必须保持 pipeline order。失败不会被伪装成成功，report 会保留 failed stage 与 degraded output。
