# Proposal: LangGraph Agent 全流程工程

> **Status:** archived · 2026-11-23 · see `ARCHIVE.md`

## 背景

工作区已有 `langgraph-agent` 骨架，与教程图示中的 **节点（Node）→ 状态（State）→ 条件边（Conditional Edge）→ 工具库 → 循环 → 终答** 模型一致，但若干核心源文件缺失，工程无法完整安装与运行。

用户提供的图示要点：

1. **全流程**：用户任务 → LangGraph 状态 → 核心推理（思考 / 行动 / 行动输入）→ 观测 → 条件判断（继续迭代 / 结束）→ 最终答案。
2. **图论模型**：`START → llm → exists_action → (action → llm)* → END`；状态贯穿各节点。
3. **AgentState**：`input`、`chat_history`（以 `messages` 承载）、`intermediate_steps`、`flags`。
4. **Agent 框架类**：`system` 系统提示，封装「大脑」配置。
5. **工具库**：预订/取消会议、查文档、搜问题、发邮件（可先 mock）。

## 目标

交付可安装的 Python 包 `langgraph-agent`：

- 用 **LangGraph `StateGraph`** 实现图示循环 Agent。
- **OpenAI 官方 API**（`langchain-openai` + `OPENAI_API_KEY`）。
- **CLI**：单轮 `run`、多轮 `chat`、线程 `thread_id` + `MemorySaver` 历史。
- **测试**：不依赖真实 API 的单元测试（条件边、action mock 工具）。

## Non-goals

- 不实现真实邮件/日历/文档系统集成（工具保持 mock）。
- 不做 Web UI、结构化卡片、流式 SSE 服务（仅 CLI 自然语言输出）。
- 不使用 RAG、长期向量记忆、多 Agent 嵌套图（后续 change 可扩展）。
- 不绑定 GZC `code-spring-cloud` 网关或 Java 服务。

## 成功标准

1. `pip install -e ".[dev]"` 成功；`pytest` 全绿。
2. 配置 `.env` 后 `agent run "..."` 能完成至少一次 tool 调用环路并返回自然语言终答。
3. `agent chat` 同 `thread_id` 下多轮对话可复用 checkpoint 历史。
4. 代码结构与 `openspec/changes/.../design.md` 目录约定一致。

## 风险与假设

- 假设 Python ≥ 3.10，开发环境可访问 `api.openai.com`。
- 图示中的「历史存储」首版用进程内 `MemorySaver`；生产换 DB checkpointer 为后续变更。

## 关联 change id

`build-langgraph-agent-full-workflow`