# agent-memory

**第五并列项目**：Agent 四种记忆（会话/检查点、摘要压缩、事实画像、向量检索）及组合取回。

OpenSpec：`openspec/changes/explore-four-memories/explore.md`

## 快速开始

```powershell
cd agent-memory
pip install -e ".[dev]"
agent-memory demo-report
pytest -q
```

## CLI

| 命令 | 说明 |
|------|------|
| `demo-report` | 报告任务演示，输出完整组装上下文 |
| `build-context <session_id> --user --task --query [--llm-compress]` | 按会话组装 |
| `session-resume <session_id>` | 中断恢复：检查点 + 上下文 |
| `ingest-chunk <text> --project` | 向量库入库 |
| `persona-list <user_id> --task` | 用户画像 |
| `get-message <id>` | 摘要外的原话回查 |

Embedding：`AGENT_MEMORY_EMBED_MODE=openai` + `OPENAI_API_KEY`（失败回落词袋）。

文档：[`docs/four-memories.md`](docs/four-memories.md)（含 `docs/images/` 教材五图）  
OpenSpec P1：[`openspec/changes/explore-four-memories/proposal.md`](openspec/changes/explore-four-memories/proposal.md)