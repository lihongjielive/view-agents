# LangGraph PoC（P2）

## 原则

| langgraph-agent | multi-agent（本 PoC） |
|-----------------|------------------------|
| `messages` 为上下文 | **SQLite Store** 为真相 |
| `@tool` 直接执行 | **提议** → `submit_proposal` → Worker |
| 单图 ReAct | 固定 DAG：propose → execute → propose → execute |

图**不含 LLM**（可后续把 `propose_*` 换成 `bind_tools` 节点）；节点只产出 `Proposal`，由 `ToolGateway` 裁决。

## 拓扑

```text
START → ensure_workflow → propose_refund → execute_refund
              → propose_coupon → execute_coupon → END
```

## 运行

```bash
pip install -e ".[langgraph]"
pytest tests/test_langgraph_poc.py -q
ma-langgraph-poc
```

## 与 langgraph-agent 对照

在 `langgraph-agent` 中模型 `tool_calls` 应映射为 HTTP `POST /v1/proposals` 或本仓库 `submit_proposal`，**禁止**在 LLM 节点内直接 `post_refund`。