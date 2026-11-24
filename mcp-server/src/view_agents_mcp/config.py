"""环境配置（不回显密钥到 tool 返回值）。"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    multi_agent_api_url: str | None
    multi_agent_access_token: str
    langgraph_api_url: str | None

    @classmethod
    def from_environ(cls) -> Settings:
        url = os.getenv("MULTI_AGENT_API_URL", "").strip() or None
        lg = os.getenv("LANGGRAPH_API_URL", "").strip() or None
        return cls(
            multi_agent_api_url=url,
            multi_agent_access_token=os.getenv("MULTI_AGENT_ACCESS_TOKEN", "token-valid"),
            langgraph_api_url=lg,
        )

    def masked(self) -> dict[str, str | bool]:
        return {
            "multi_agent_api_configured": bool(self.multi_agent_api_url),
            "multi_agent_api_url": self.multi_agent_api_url or "",
            "langgraph_api_configured": bool(self.langgraph_api_url),
        }


settings = Settings.from_environ()