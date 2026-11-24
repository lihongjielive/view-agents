"""加载 settings.json 与环境变量。"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    root: Path
    openai_api_key: str | None
    openai_model: str
    mcp_http_url: str
    mcp_bearer: str | None
    multi_agent_api_url: str
    memory_dir: Path
    socket_contract_path: Path
    raw: dict

    @classmethod
    def load(cls) -> Settings:
        load_dotenv(_ROOT / ".env")
        settings_path = _ROOT / "settings.json"
        raw = json.loads(settings_path.read_text(encoding="utf-8"))
        mem = _ROOT / os.getenv("AGENT_KIT_MEMORY_DIR", "memory/data")
        mem.mkdir(parents=True, exist_ok=True)
        rel_contract = raw.get("mcp", {}).get(
            "contract_path", "../mcp-server/contracts/unified_socket.json"
        )
        contract = (_ROOT / rel_contract).resolve()
        if not contract.is_file():
            contract = (
                _ROOT.parent / "mcp-server" / "contracts" / "unified_socket.json"
            ).resolve()
        return cls(
            root=_ROOT,
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            mcp_http_url=os.getenv("MCP_HTTP_URL", "http://127.0.0.1:8010/mcp"),
            mcp_bearer=os.getenv("MCP_HTTP_BEARER_TOKEN") or None,
            multi_agent_api_url=os.getenv(
                "MULTI_AGENT_API_URL", "http://127.0.0.1:18082"
            ),
            memory_dir=mem,
            socket_contract_path=contract,
            raw=raw,
        )


def load_agent_yaml() -> dict:
    import yaml

    path = _ROOT / "agents" / "agent.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))