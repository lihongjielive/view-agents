# Specs: agent-memory P1

## MEM-SESSION-1

- **SHALL** `SessionStore` 保留 P0 消息/检查点 API。  
- **SHALL** P1 `session-resume` 输出当前 `in_progress` 检查点。

## MEM-COMP-1

- **SHALL** 压缩结果含 `compressed_from_message_ids`。  
- **SHALL** `get-message` 按 id 回查全文。  
- **MAY** P1 `build-context --llm-compress` 调 `compress_with_llm`。

## MEM-PERSONA-1

- **SHALL** `upsert` 按 `(user_id, fact_key)` 去重。  
- **SHALL** 用户撤销偏好时删除匹配 `content LIKE '%附来源%'` 或指定 key。  
- **SHALL** `facts_for_task` 支持任务 hint 过滤。

## MEM-VECTOR-1

- **SHALL** 检索返回 **原文** 而非仅向量。  
- **SHALL** 支持 `project` 筛选。  
- **SHALL** P1 OpenAI embedding 路径有单元测（mock API）。

## MEM-COORD-1

- **SHALL** `build_context` 拼接：摘要、近期、画像、检索、检查点。  
- **SHALL** `demo-report` 作为文档验收场景。

## MEM-DOC-1

- **SHALL** `docs/images/` 含 5 张教材图。  
- **SHALL** `docs/four-memories.md` 链接五图与模块。

## MEM-INTEG-1（P1）

- **SHALL** `agent-kit` 在 env 开启时使用 `MemoryCoordinator`。  
- **SHALL NOT** 默认破坏 agent-kit 既有 14 项离线测。