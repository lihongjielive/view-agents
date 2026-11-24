"""Phase 0：HTTP Bearer 可选门控（MCP_HTTP_BEARER_TOKEN）。"""
from __future__ import annotations

import os
from typing import Any

from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp


def expected_bearer_token() -> str | None:
    raw = os.getenv("MCP_HTTP_BEARER_TOKEN", "").strip()
    return raw or None


class BearerGateMiddleware(BaseHTTPMiddleware):
    """未配置 token 时透传；配置后要求 Authorization: Bearer <token>。"""

    def __init__(self, app: ASGIApp, *, token: str) -> None:
        super().__init__(app)
        self._token = token

    async def dispatch(self, request: Request, call_next) -> Response:
        auth = request.headers.get("authorization", "")
        if auth != f"Bearer {self._token}":
            return JSONResponse(
                {"detail": "unauthorized", "hint": "Authorization: Bearer <MCP_HTTP_BEARER_TOKEN>"},
                status_code=401,
            )
        return await call_next(request)


def build_http_middlewares() -> list[Middleware]:
    token = expected_bearer_token()
    if not token:
        return []
    return [Middleware(BearerGateMiddleware, token=token)]