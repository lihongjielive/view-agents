# PostgreSQL Store 适配（P2）

SQLite `Store` 为 MVP 默认真相；`PostgresStore` 继承同名 API，DDL 见 [`deploy/postgres/schema.sql`](../deploy/postgres/schema.sql)。

## 安装与连接

```bash
pip install -e ".[postgres]"
export MULTI_AGENT_STORE_URL=postgresql://multi:multi@localhost:5432/multi_agent
```

或使用工厂：

```python
from multi_agent.store_factory import open_store

store = open_store()  # 读 MULTI_AGENT_STORE_URL
```

本地数据库（可选）：

```bash
docker compose --profile p2-postgres up -d
```

## 与 LangGraph / API

`ma-api` 仍默认 SQLite 文件；接入 Postgres 时设置 `MULTI_AGENT_STORE_URL` 并在启动前用 `open_store()` 构造 `SupervisorEngine`（后续 change 可改 `api_server` 默认工厂）。

## 测试

无 DSN 时跳过：

```bash
pytest tests/test_postgres_store.py -q
```