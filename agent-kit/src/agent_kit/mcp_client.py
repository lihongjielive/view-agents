"""MCP Host Client（HTTP tools/call + 契约 fallback）。"""
from __future__ import annotations

import json
import uuid
from typing import Any

import httpx

from agent_kit.config import Settings
from agent_kit.contract_loader import (
    catalog_from_manifest,
    describe_from_manifest,
    load_unified_socket,
)


class McpClient:
    def __init__(self, *, offline: bool = False) -> None:
        self.offline = offline
        self.settings = Settings.load()
        self._manifest = load_unified_socket(self.settings)

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.settings.mcp_bearer:
            h["Authorization"] = f"Bearer {self.settings.mcp_bearer}"
        return h

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = arguments or {}
        if self.offline:
            return self._offline_call(name, arguments)
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
        try:
            r = httpx.post(
                self.settings.mcp_http_url,
                json=payload,
                headers=self._headers(),
                timeout=self.settings.raw.get("mcp", {}).get("timeout_seconds", 30),
            )
            body = r.json()
            if "error" in body:
                return {"error": body["error"], "status_code": r.status_code}
            return self._normalize_result(body.get("result", body))
        except httpx.HTTPError as exc:
            return {
                "error": "mcp_unreachable",
                "detail": str(exc),
                "url": self.settings.mcp_http_url,
            }

    @staticmethod
    def _normalize_result(result: Any) -> dict[str, Any]:
        if isinstance(result, dict):
            if "structuredContent" in result and isinstance(result["structuredContent"], dict):
                return result["structuredContent"]
            if "content" in result:
                texts = [
                    c.get("text")
                    for c in result.get("content", [])
                    if isinstance(c, dict) and c.get("type") == "text"
                ]
                if texts:
                    merged = "".join(t for t in texts if t)
                    try:
                        return json.loads(merged)
                    except json.JSONDecodeError:
                        return {"text": merged}
            return result
        return {"result": result}

    def _offline_call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "mcp_ping":
            return {
                "ok": True,
                "service": "view-agents-mcp",
                "mode": "offline-mock",
                "socket_version": self._manifest.get("socket_version"),
            }
        if name == "mcp_tools_catalog":
            plug_id = arguments.get("plug_id")
            out = catalog_from_manifest(self._manifest, plug_id=plug_id)
            out["mode"] = "offline-mock"
            return out
        if name == "mcp_tools_describe":
            return describe_from_manifest(self._manifest, arguments.get("name", ""))
        if name == "multi_agent_health":
            return {
                "ok": False,
                "configured": False,
                "mode": "offline-mock",
                "hint": "start ma-api",
            }
        if name == "multi_agent_create_workflow":
            return {
                "workflow_id": "WF-OFFLINE-DEMO",
                "mode": "offline-mock",
                **{k: v for k, v in arguments.items() if k in ("order_id", "after_sale_id")},
            }
        if name == "multi_agent_submit_proposal":
            return {
                "code": "T03_OK",
                "mode": "offline-mock",
                "workflow_id": arguments.get("workflow_id"),
            }
        return {"error": "unknown_tool", "name": name, "mode": "offline-mock"}

    def catalog(self, plug_id: str | None = None) -> dict[str, Any]:
        args = {"plug_id": plug_id} if plug_id else {}
        out = self.call("mcp_tools_catalog", args)
        if out.get("error") and self.offline:
            return catalog_from_manifest(self._manifest, plug_id=plug_id)
        if out.get("error"):
            return catalog_from_manifest(self._manifest, plug_id=plug_id)
        return out

    def describe(self, name: str) -> dict[str, Any]:
        out = self.call("mcp_tools_describe", {"name": name})
        if out.get("error"):
            return describe_from_manifest(self._manifest, name)
        return out

    def ping(self) -> dict[str, Any]:
        return self.call("mcp_ping")