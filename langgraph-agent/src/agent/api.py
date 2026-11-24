"""HTTP 接口：将 build_graph 暴露为 REST（与 CLI 共用同一 StateGraph）。"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from agent.agent_framework import default_agent
from agent.config import load_project_env
from agent.graph import build_graph

load_project_env()

app = FastAPI(
    title="langgraph-agent",
    description="LangGraph StateGraph：llm → exists_action → action 循环",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    """单轮/多轮对话请求：thread_id 相同则共用 MemorySaver 历史。"""

    message: str = Field(..., min_length=1, description="用户任务或一句话")
    thread_id: str = Field(default="default", description="会话 id，对应 checkpoint thread_id")


class ChatResponse(BaseModel):
    reply: str
    thread_id: str


@lru_cache
def _compiled_graph():
    """
    懒加载编译图（单例）：与 CLI `build_graph(default_agent())` 相同入口。

    注意：lru_cache 保证多请求复用同一图实例；checkpointer 按 thread_id 隔离状态。
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")
    return build_graph(default_agent(), checkpointer=True)

# 从一整段对话消息列表里，找出「最后一条有实质内容的助手回复」并转成字符串返回；找不到就返回空字符串 ""。
# reversed(messages) ： 从最新往旧消息找（用户要的是「当前这轮」助手说了什么），HumanMessage → AIMessage(tool_calls=…) → ToolMessage → AIMessage("好的，已为您…")
# isinstance(m, AIMessage)： 只要模型输出，跳过 HumanMessage、ToolMessage、SystemMessage（若混在列表里）
# m.content： 没有 content 的 AI 消息跳过（常见于只有 tool_calls、文字为空的那条）
# str / str(m.content)： LangChain 里 content 有时是 str，有时是多模态块列表，统一成字符串
# text.strip()： 过滤只有空格、换行的「空答」
# return ""： 没有任何合格 AIMessage 时，API 里会当作错误；CLI 里用 "(no assistant message)" 之类兜底
def _last_ai_text(messages: list) -> str:
    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content:
            text = m.content if isinstance(m.content, str) else str(m.content)
            if text.strip():
                return text
    return ""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    """
    调用 Agent 图直至 END，返回助手自然语言回复。

    等价于 CLI：`agent run "<message>" --thread <thread_id>`
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY 未配置，请设置环境变量或 .env",
        )
    try:
        graph = _compiled_graph()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    config: dict[str, Any] = {"configurable": {"thread_id": body.thread_id}}
    # chat 模式：仅传 input，历史由 checkpoint 维护
    result = graph.invoke({"input": body.message}, config)
    reply = _last_ai_text(result.get("messages") or [])
    if not reply:
        raise HTTPException(status_code=500, detail="模型未返回文本")
    return ChatResponse(reply=reply, thread_id=body.thread_id)


def main() -> None:
    """包入口：`agent-serve` 或 `python -m agent.api`。"""
    import uvicorn

    host = os.getenv("AGENT_HOST", "0.0.0.0")
    port = int(os.getenv("AGENT_PORT", "8000"))
    uvicorn.run("agent.api:app", host=host, port=port, reload=False)


# llm.py      产出 AIMessage（可能带 tool_calls）
# edges.py    看最后一条 AI 有没有 tool_calls，决定走哪条路
# action.py   有 tool_calls 时真正执行工具
# graph.py    把节点和边接在一起

if __name__ == "__main__":
    main()