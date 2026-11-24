"""统一插口契约（contracts/unified_socket.json）。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTRACT_PATH = (
    Path(__file__).resolve().parents[2] / "contracts" / "unified_socket.json"
)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    catalog_summary: str
    description: str
    plug: str
    input_schema: dict[str, Any]
    read_only_hint: bool
    destructive_hint: bool
    idempotent_hint: bool
    maps_to: dict[str, str] | None

    def annotations(self) -> dict[str, bool]:
        return {
            "readOnlyHint": self.read_only_hint,
            "destructiveHint": self.destructive_hint,
            "idempotentHint": self.idempotent_hint,
        }

    def describe_payload(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "name": self.name,
            "plug": self.plug,
            "catalogSummary": self.catalog_summary,
            "description": self.description,
            "inputSchema": self.input_schema,
            "annotations": self.annotations(),
        }
        if self.maps_to:
            out["maps_to"] = self.maps_to
        return out


@lru_cache(maxsize=1)
def load_socket_manifest() -> dict[str, Any]:
    return json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def tool_index() -> dict[str, ToolSpec]:
    raw = load_socket_manifest()
    out: dict[str, ToolSpec] = {}
    for t in raw.get("tools", []):
        out[t["name"]] = ToolSpec(
            name=t["name"],
            catalog_summary=t.get("catalogSummary", t["name"]),
            description=t["description"],
            plug=t.get("plug", "core"),
            input_schema=t.get("inputSchema", {"type": "object"}),
            read_only_hint=bool(t.get("readOnlyHint", False)),
            destructive_hint=bool(t.get("destructiveHint", False)),
            idempotent_hint=bool(t.get("idempotentHint", True)),
            maps_to=t.get("maps_to"),
        )
    return out


def get_tool(name: str) -> ToolSpec | None:
    return tool_index().get(name)


def catalog_entries(*, plug_id: str | None = None) -> list[dict[str, str]]:
    entries = []
    for spec in tool_index().values():
        if plug_id and spec.plug != plug_id:
            continue
        entries.append(
            {
                "name": spec.name,
                "catalogSummary": spec.catalog_summary,
                "plug": spec.plug,
            }
        )
    return sorted(entries, key=lambda x: x["name"])


def assert_tool_allowed(name: str) -> None:
    """插口安全：禁止契约外的支付直写类工具名。"""
    manifest = load_socket_manifest()
    patterns = manifest.get("forbidden_tool_patterns", [])
    lowered = name.lower()
    for pat in patterns:
        if pat.lower() in lowered:
            raise ValueError(f"forbidden tool pattern in name: {name}")
    if name not in tool_index():
        raise KeyError(f"tool not in unified socket contract: {name}")


def contract_path_for_langgraph() -> Path:
    return _CONTRACT_PATH