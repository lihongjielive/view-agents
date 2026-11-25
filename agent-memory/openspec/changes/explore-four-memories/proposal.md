# Proposal: agent-memory（P0 完成 → P1 集成）

> **Status:** `apply` — P1 已完成  
> **Change id:** `explore-four-memories`  
> **前置:** [explore.md](./explore.md)、P0 已落地

## 背景

P0 交付 `agent-memory` 五项目并列：四类记忆 + `MemoryCoordinator` + CLI `demo-report` + 6 tests。教材 **5 张配图** 已归档至 `docs/images/`。

用户要求应用层承担 **保存、整理、取回**；P1 聚焦 **生产化嵌入**、**CLI 续跑**、与 **agent-kit** 对接。

## 目标

### P0（已完成）

| # | 能力 |
|---|------|
| 1 | SessionStore / 检查点 / get-message |
| 2 | 规则摘要 + maybe_compress |
| 3 | PersonaStore 提取/撤销 |
| 4 | VectorMemory + project 筛选 |
| 5 | Coordinator + demo-report + CI |

### P1 — 本提案

| # | 能力 | 说明 |
|---|------|------|
| 1 | **OpenAI Embedding** | 可选向量后端；失败回落词袋 |
| 2 | **CLI 续跑** | `session-resume`、`ingest-chunk`、`persona-list` |
| 3 | **LLM 摘要开关** | `build-context --llm-compress` |
| 4 | **agent-kit 适配** | `memory_adapter` + `AGENT_KIT_USE_COORDINATOR` |
| 5 | **文档** | 五图 + `four-memories.md` 导读（本 propose 已完成图归档） |

### P2（非阻塞）

- Chroma / pgvector 持久索引  
- LongMemEval 小样例  
- langgraph Checkpointer 与 SessionStore 关联设计稿  

## Non-goals

- 不替代 multi-agent Store / Worker 状态真相  
- P1 不做多租户画像权限产品化  
- 不把五图重制为矢量 PDF（保留原 JPG）

## 成功标准（P1 归档）

1. `pytest -q` 全绿（含 mock embedding）  
2. `agent-kit run` 在 `AGENT_KIT_USE_COORDINATOR=1` 时上下文含「检查点」块  
3. `docs/four-memories.md` 五图可渲染（相对路径 `images/0x-*.jpg`）  
4. OpenSpec tasks P1 全勾选  

## 交付物

| 产物 | 路径 |
|------|------|
| 设计 | [design.md](./design.md) |
| 规格 | [specs.md](./specs.md) |
| 任务 | [tasks.md](./tasks.md) |
| 配图 | `docs/images/01–05*.jpg` |

## 下一步

**`/opsx:apply`** 按 [tasks.md](./tasks.md) P1 清单实施。