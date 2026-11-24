"""读取 mcp-server unified_socket.json 契约。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_kit.config import Settings


def contract_path(settings: Settings | None = None) -> Path:
    settings = settings or Settings.load()
    rel = settings.raw.get("mcp", {}).get(
        "contract_path", "../mcp-server/contracts/unified_socket.json"
    )
    path = (settings.root / rel).resolve()
    if not path.is_file():
        monorepo = settings.root.parent / "mcp-server" / "contracts" / "unified_socket.json"
        if monorepo.is_file():
            return monorepo
    return path


def load_unified_socket(settings: Settings | None = None) -> dict[str, Any]:
    path = contract_path(settings)
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_from_manifest(
    manifest: dict[str, Any], plug_id: str | None = None
) -> dict[str, Any]:
    tools = manifest.get("tools", [])
    entries = []
    for t in tools:
        if plug_id and t.get("plug") != plug_id:
            continue
        entries.append(
            {
                "name": t["name"],
                "catalogSummary": t.get("catalogSummary", ""),
                "plug": t.get("plug"),
            }
        )
    return {
        "socket_version": manifest.get("socket_version"),
        "plug_id_filter": plug_id,
        "tools": entries,
        "source": "unified_socket.json",
    }


def describe_from_manifest(manifest: dict[str, Any], name: str) -> dict[str, Any]:
    for t in manifest.get("tools", []):
        if t.get("name") == name:
            return {
                "name": name,
                "description": t.get("description", ""),
                "inputSchema": t.get("inputSchema"),
                "plug": t.get("plug"),
                "source": "unified_socket.json",
            }
    return {"error": "unknown_tool", "name": name}