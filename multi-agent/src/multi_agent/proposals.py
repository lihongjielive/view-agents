"""Agent 候选动作 — 仅提议，由 Gateway 裁决（slide 03）。"""
from __future__ import annotations

from dataclasses import dataclass

from multi_agent.gateway import GatewayDecision, Proposal, ToolGateway


@dataclass
class ProposalResult:
    decision: GatewayDecision
    """Models propose; no side effects on payment or tasks here."""


def submit_proposal(gateway: ToolGateway, workflow_id: str, proposal: Proposal) -> ProposalResult:
    """POST /proposals 语义：只返回裁决，不写外部系统。"""
    return ProposalResult(decision=gateway.evaluate(workflow_id, proposal))