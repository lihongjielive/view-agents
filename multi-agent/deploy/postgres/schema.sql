-- PostgreSQL DDL：与 SQLite Store 同表结构（P2 适配层）
CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    tenant TEXT NOT NULL,
    order_id TEXT NOT NULL,
    after_sale_id TEXT NOT NULL,
    approval_snapshot_id TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    logical_step_key TEXT NOT NULL,
    status TEXT NOT NULL,
    owner TEXT,
    attempt_no INTEGER NOT NULL DEFAULT 0,
    row_version INTEGER NOT NULL DEFAULT 1,
    lease_until TEXT,
    depends_on_task_id TEXT,
    result_version INTEGER NOT NULL DEFAULT 0,
    business_key TEXT UNIQUE,
    created_at TEXT NOT NULL,
    UNIQUE (workflow_id, logical_step_key)
);

CREATE TABLE IF NOT EXISTS tool_operations (
    business_key TEXT PRIMARY KEY,
    tool_name TEXT NOT NULL,
    status TEXT NOT NULL,
    task_id TEXT NOT NULL,
    remote_ref TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outbox_events (
    id TEXT PRIMARY KEY,
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    published_at TEXT,
    idempotency_key TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    detail_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consumed_events (
    idempotency_key TEXT PRIMARY KEY,
    consumed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reconciliation_queue (
    id SERIAL PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    business_key TEXT NOT NULL,
    status TEXT NOT NULL,
    detail_json TEXT,
    created_at TEXT NOT NULL
);