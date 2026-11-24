from agent_kit.tools.api_client import api_get
from agent_kit.tools.calculator import calculate
from agent_kit.tools.search import web_search

TOOL_REGISTRY = {
    "search": web_search,
    "calculator": calculate,
    "api_client": api_get,
}

__all__ = ["TOOL_REGISTRY", "web_search", "calculate", "api_get"]