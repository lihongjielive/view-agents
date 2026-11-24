# K8s 样板（图 01 — 对照部署，非 Python 仿真运行时必需）

Python MVP 在单机 `pytest` / `ma-demo` 即可验证协议。本目录为 **生产对照拓扑**（图 01 + 10），`kubectl apply --dry-run=client` 可用。

| 文件 | 说明 |
|------|------|
| `namespace.yaml` | `multi-agent` 命名空间 |
| `payment-mock.yaml` | 支付 Mock Deployment + Service（:8080） |

Worker / Supervisor 进程拆分见 [design.md](../../openspec/changes/explore-production-refund-multi-agent/design.md) P2。