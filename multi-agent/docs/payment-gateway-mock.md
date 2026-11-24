# 支付网关 Mock（尽量做全）

Python 实现：`multi_agent.payment.server`（FastAPI）。生产联调可 `payment-mock` 独立进程，测试用 `PaymentClient("asgi://payment")` 进程内调用。

## 退款 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/refunds` | 创建退款，**business_key 幂等** |
| GET | `/v1/refunds/{business_key}` | 按业务键查询（超时追查） |
| GET | `/v1/refunds` | 列表过滤 `tenant` / `order_id` / `state` |
| POST | `/v1/reconciliation/by-keys` | 批量对账 |

请求头：`X-Tenant`（必填）。

创建 body：

```json
{
  "business_key": "T1:refund.create:ORD-991:AS-77",
  "order_id": "ORD-991",
  "after_sale_id": "AS-77",
  "amount": 100.0,
  "currency": "CNY",
  "callback_url": null
}
```

退款记录状态：`PENDING` | `ACCEPTED` | `SUCCEEDED` | `FAILED`。

## 故障注入（尽量覆盖文图）

| `mode` | 行为 |
|--------|------|
| `none` | 正常返回 200 |
| `drop_response_after_success` | **网关已入账**，HTTP 504（响应丢失） |
| `timeout` | 同 504（通信超时语义） |
| `slow` | 慢响应（`slow_ms`） |
| `fail_business` | 业务拒绝，state=FAILED |
| `late_callback` | 先 504，稍后记入 `/v1/admin/callbacks` |

| 方法 | 路径 |
|------|------|
| POST | `/v1/admin/fault-injection` |
| DELETE | `/v1/admin/fault-injection` |
| GET | `/v1/admin/metrics` | POST 次数、退款数 |
| GET | `/v1/admin/callbacks` | 迟到回调记录 |

`scope`: `global` 或指定 `business_key`。

## 启动

```bash
pip install -e .
payment-mock   # http://0.0.0.0:18080
```

## 与 Worker 协作（slide 08）

1. Worker 先写 `tool_operations=PENDING`（SQLite）
2. POST `/v1/refunds`
3. 504 → 本地 `UNKNOWN`，**禁止盲重试 POST**
4. GET `/v1/refunds/{business_key}` → `SUCCEEDED` 则 Task 收敛