"""agent-memory: 四种 Agent 记忆（会话 / 压缩 / 画像 / 向量）。"""

__version__ = "0.1.0"

from agent_memory.coordinator import MemoryCoordinator

__all__ = ["MemoryCoordinator", "__version__"]