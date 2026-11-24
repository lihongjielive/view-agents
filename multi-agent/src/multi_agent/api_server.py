"""对外 HTTP（图 03）：建单与**纯提议**接口，供 LangGraph tool 或人工联调。

- POST /v1/workflows：等价 Supervisor.start_case
- POST /v1/proposals：等价 submit_proposal（不写支付）
"""
from __future__ import annotations

import os
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from multi_agent.engine import SupervisorEngine
from multi_agent.gateway import Proposal, ToolGateway
from multi_agent.payment.client import PaymentClient
from multi_agent.proposals import submit_proposal
from multi_agent.store import Store

app = FastAPI(title="multi-agent-api", version="0.1.0")


class CreateWorkflowRequest(BaseModel):
    tenant: str = "T1"
    order_id: str = Field(..., min_length=1)
    after_sale_id: str = Field(..., min_length=1)
    refund_amount: float = Field(gt=0)


class ProposalRequest(BaseModel):
    workflow_id: str
    tenant: str = "T1"
    tool: str
    order_id: str
    after_sale_id: str
    amount: float = Field(gt=0)
    actor: str = "http-client"
    approval_snapshot_id: str = "appr-default"
    access_token: str = "token-valid"


@lru_cache  # 进程单例；生产应换连接池 + 真实 Store 工厂
def _engine() -> SupervisorEngine:
    path = os.getenv("MULTI_AGENT_STORE_PATH", ":memory:")
    pay_base = os.getenv("PAYMENT_MOCK_URL", "asgi://payment")
    return SupervisorEngine(Store(path), PaymentClient(pay_base))


@app.post("/v1/workflows")
def create_workflow(body: CreateWorkflowRequest) -> dict:
    wf = _engine().start_case(
        tenant=body.tenant,
        order_id=body.order_id,
        after_sale_id=body.after_sale_id,
        refund_amount=body.refund_amount,
    )
    return {"workflow_id": wf}


@app.post("/v1/proposals")
def create_proposal(body: ProposalRequest) -> dict:
    eng = _engine()
    gw = ToolGateway(eng.store)
    try:
        result = submit_proposal(
            gw,
            body.workflow_id,
            Proposal(
                tenant=body.tenant,
                tool=body.tool,
                order_id=body.order_id,
                after_sale_id=body.after_sale_id,
                amount=body.amount,
                actor=body.actor,
                approval_snapshot_id=body.approval_snapshot_id,
                access_token=body.access_token,
            ),
        )
    except KeyError as exc:
        raise HTTPException(404, "workflow_not_found") from exc
    return {
        "allow": result.decision.allow,
        "code": result.decision.code,
        "reason": result.decision.reason,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    import uvicorn

    host = os.getenv("MULTI_AGENT_API_HOST", "0.0.0.0")
    port = int(os.getenv("MULTI_AGENT_API_PORT", "18082"))
    uvicorn.run("multi_agent.api_server:app", host=host, port=port, reload=False)