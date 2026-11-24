"""LangGraph PoC（P2）：固定 DAG「提议 → 执行」，真相仍在 Store。

与 langgraph-agent 差异：
- 无 messages 真相；节点只调 submit_proposal / SupervisorEngine
- propose_* 节点禁止 payment.post_refund（由 Worker 唯一写入）
"""
from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from multi_agent.domain import TaskStatus
from multi_agent.engine import SupervisorEngine
from multi_agent.gateway import Proposal, ToolGateway
from multi_agent.langgraph_poc.state import PocState
from multi_agent.payment.client import PaymentClient
from multi_agent.proposals import submit_proposal
from multi_agent.store import Store


def build_proposal_graph(engine: SupervisorEngine):
    """编译图：START→ensure→propose_refund→execute→…→execute_coupon→END。"""
    gw = ToolGateway(engine.store)

    def ensure_workflow(state: PocState) -> dict:
        """在 Store 建 workflow（若无 workflow_id）。"""
        if state.get("workflow_id"):
            return {}
        wf = engine.start_case(
            tenant=state.get("tenant", "T1"),
            order_id=state["order_id"],
            after_sale_id=state["after_sale_id"],
            refund_amount=state.get("refund_amount", 100.0),
        )
        return {"workflow_id": wf}

    def propose_refund(state: PocState) -> dict:
        """图 03：仅 Gateway 裁决，无副作用。"""
        wf = state["workflow_id"]
        dec = submit_proposal(
            gw,
            wf,
            Proposal(
                tenant=state.get("tenant", "T1"),
                tool="refund.create",
                order_id=state["order_id"],
                after_sale_id=state["after_sale_id"],
                amount=state.get("refund_amount", 100.0),
                actor="langgraph-poc",
                approval_snapshot_id="appr-default",
            ),
        ).decision
        return {
            "refund_proposal_code": dec.code,
            "refund_allowed": dec.allow,
        }

    def execute_refund(state: PocState) -> dict:
        """委托 SupervisorEngine.run_refund_workflow（含 Outbox）。"""
        if not state.get("refund_allowed"):
            return {"error": "refund_denied", "refund_executed": False}
        wf = state["workflow_id"]
        ok = engine.run_refund_workflow(wf, refund_amount=state.get("refund_amount", 100.0))
        return {"refund_executed": ok}

    def propose_coupon(state: PocState) -> dict:
        wf = state["workflow_id"]
        dec = submit_proposal(
            gw,
            wf,
            Proposal(
                tenant=state.get("tenant", "T1"),
                tool="coupon.issue",
                order_id=state["order_id"],
                after_sale_id=state["after_sale_id"],
                amount=state.get("coupon_amount", 10.0),
                actor="langgraph-poc",
                approval_snapshot_id="appr-default",
            ),
        ).decision
        return {
            "coupon_proposal_code": dec.code,
            "coupon_allowed": dec.allow,
        }

    def execute_coupon(state: PocState) -> dict:
        if not state.get("coupon_allowed"):
            return {"error": "coupon_denied", "coupon_executed": False}
        wf = state["workflow_id"]
        ok = engine.run_coupon(wf, coupon_amount=state.get("coupon_amount", 10.0))
        return {"coupon_executed": ok}

    def after_refund_propose(state: PocState) -> Literal["execute_refund", "end"]:
        if state.get("refund_allowed"):
            return "execute_refund"
        return "end"

    def after_refund_exec(state: PocState) -> Literal["propose_coupon", "end"]:
        wf = state["workflow_id"]
        refund = next(
            t for t in engine.store.list_tasks(wf) if t.logical_step_key == "refund"
        )
        if refund.status == TaskStatus.SUCCEEDED:
            return "propose_coupon"
        return "end"

    def after_coupon_propose(state: PocState) -> Literal["execute_coupon", "end"]:
        if state.get("coupon_allowed"):
            return "execute_coupon"
        return "end"

    builder = StateGraph(PocState)
    builder.add_node("ensure_workflow", ensure_workflow)
    builder.add_node("propose_refund", propose_refund)
    builder.add_node("execute_refund", execute_refund)
    builder.add_node("propose_coupon", propose_coupon)
    builder.add_node("execute_coupon", execute_coupon)

    builder.add_edge(START, "ensure_workflow")
    builder.add_edge("ensure_workflow", "propose_refund")
    builder.add_conditional_edges(
        "propose_refund",
        after_refund_propose,
        {"execute_refund": "execute_refund", "end": END},
    )
    builder.add_conditional_edges(
        "execute_refund",
        after_refund_exec,
        {"propose_coupon": "propose_coupon", "end": END},
    )
    builder.add_conditional_edges(
        "propose_coupon",
        after_coupon_propose,
        {"execute_coupon": "execute_coupon", "end": END},
    )
    builder.add_edge("execute_coupon", END)

    return builder.compile()


def run_poc_case(
    *,
    store: Store | None = None,
    payment: PaymentClient | None = None,
    order_id: str = "ORD-LG-1",
    after_sale_id: str = "AS-LG-1",
    refund_amount: float = 88.0,
    coupon_amount: float = 8.0,
) -> PocState:
    from multi_agent.payment.server import reset_state

    reset_state()
    store = store or Store(":memory:")
    payment = payment or PaymentClient("asgi://payment")
    engine = SupervisorEngine(store, payment)
    graph = build_proposal_graph(engine)
    initial: PocState = {
        "tenant": "T1",
        "order_id": order_id,
        "after_sale_id": after_sale_id,
        "refund_amount": refund_amount,
        "coupon_amount": coupon_amount,
    }
    return graph.invoke(initial)