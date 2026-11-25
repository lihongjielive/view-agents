# Tasks: explore-four-memories

## P0（已完成）

- [x] 四类记忆 + Coordinator + CLI
- [x] tests + CI + monorepo README
- [x] docs/four-memories.md + 五图

## Propose（已完成）

- [x] proposal P1 / design / specs
- [x] 五张教材图 → `docs/images/01–05*.jpg`

## P1 — `/opsx:apply`（已完成）

### 1. Embedding

- [x] `embeddings.py` + `vector_memory.py` 支持 openai/bag
- [x] `tests/test_vector_openai.py`

### 2. CLI

- [x] `session-resume`、`ingest-chunk`、`persona-list`
- [x] `build-context --llm-compress`

### 3. agent-kit

- [x] `memory_adapter.py`
- [x] `KitAgent` + `AGENT_KIT_USE_COORDINATOR`
- [x] agent-kit README + CI 安装 agent-memory

### 4. 收尾

- [x] proposal Status → apply 完成
- [x] 根 README OpenSpec 链接

## P2 backlog

- [ ] Chroma 可选依赖
- [ ] LangGraph 集成设计