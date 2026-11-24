# view-agents

LangGraph 演示与生产级 Multi-Agent 执行协议对照 monorepo。

| 目录 | 说明 |
|------|------|
| [`langgraph-agent/`](langgraph-agent/) | 单图 ReAct + 内存状态 + LLM 工具循环（演示） |
| [`multi-agent/`](multi-agent/) | 可恢复执行协议：SQLite Store、Gateway、Worker、支付 Mock（生产仿真） |

## 快速开始

```bash
# LangGraph 演示
cd langgraph-agent
pip install -e ".[dev]"
# 复制 env.example → .env 后
agent run "查一下会议室"

# Multi-Agent 协议仿真
cd multi-agent
pip install -e ".[dev,langgraph]"
pytest -q
ma-demo figure-01
```

文档与 OpenSpec 见各子项目 `README.md`、`openspec/`。