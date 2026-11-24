"""加载项目根目录 .env（无论从哪个工作目录启动 CLI/API）。"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# src/agent/config.py -> langgraph-agent/
# 从 src/agent/config.py 往上两级 → 仓库根 langgraph-agent/
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
# 固定指向 langgraph-agent/.env（不是当前 shell 所在目录）
_ENV_FILE = _PROJECT_ROOT / ".env"

# 统一的 .env 加载入口：锚定项目根 .env，override=False 不盖掉系统里已 export 的变量。
# 没有 Agent 业务逻辑、没有图或模型配置类；其它模块在需要读环境变量前先（或通过 import api）调用 load_project_env() 即可。

# 从项目根目录加载 .env 到环境变量，这样无论从哪个当前工作目录启动 CLI 或 API，都能读到 OPENAI_API_KEY、OPENAI_BASE_URL、OPENAI_MODEL 等配置。
def load_project_env() -> None:
    """优先加载 langgraph-agent/.env，再叠加已有环境变量。"""
    # 把 .env 里的键写进 os.environ；已有环境变量优先，不被 .env 覆盖
    load_dotenv(_ENV_FILE, override=False)