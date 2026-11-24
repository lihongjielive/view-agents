#!/usr/bin/env python3
"""将 fault_drill scenarios 流程图导出 PDF 到 docx/（PyMuPDF，无浏览器依赖）。"""
from __future__ import annotations

from pathlib import Path

import pymupdf as fitz

OUT_DIR = Path(__file__).resolve().parents[1] / "docx"
OUT_PDF = OUT_DIR / "fault-drill-scenarios-flowcharts.pdf"

# A4 横向
W, H = 842, 595
MARGIN = 36
FONT = "china-ss"
FS_TITLE = 14
FS_H2 = 12
FS = 9


def _text(page: fitz.Page, x: float, y: float, text: str, *, size: float = FS, bold: bool = False) -> None:
    page.insert_text(
        fitz.Point(x, y),
        text,
        fontsize=size,
        fontname=FONT,
        color=(0.1, 0.1, 0.1),
    )


def _box(
    page: fitz.Page,
    rect: fitz.Rect,
    text: str,
    *,
    fill: tuple[float, float, float] = (0.94, 0.96, 0.98),
) -> None:
    page.draw_rect(rect, color=(0.2, 0.25, 0.35), width=0.6, fill=fill)
    page.insert_textbox(
        rect,
        text,
        fontsize=FS,
        fontname=FONT,
        color=(0.1, 0.1, 0.1),
        align=fitz.TEXT_ALIGN_CENTER,
    )


def _arrow(page: fitz.Page, x0: float, y0: float, x1: float, y1: float) -> None:
    page.draw_line(fitz.Point(x0, y0), fitz.Point(x1, y1), color=(0.35, 0.35, 0.4), width=0.8)
    # 箭头三角
    if abs(y1 - y0) > abs(x1 - x0):
        tip, base = (x1, y1), (x0, y0)
        if y1 < y0:
            page.draw_polyline(
                [fitz.Point(x1, y1), fitz.Point(x1 - 4, y1 + 8), fitz.Point(x1 + 4, y1 + 8)],
                color=(0.35, 0.35, 0.4),
                fill=(0.35, 0.35, 0.4),
                closePath=True,
            )
        else:
            page.draw_polyline(
                [fitz.Point(x1, y1), fitz.Point(x1 - 4, y1 - 8), fitz.Point(x1 + 4, y1 - 8)],
                color=(0.35, 0.35, 0.4),
                fill=(0.35, 0.35, 0.4),
                closePath=True,
            )
    else:
        if x1 > x0:
            page.draw_polyline(
                [fitz.Point(x1, y1), fitz.Point(x1 - 8, y1 - 4), fitz.Point(x1 - 8, y1 + 4)],
                color=(0.35, 0.35, 0.4),
                fill=(0.35, 0.35, 0.4),
                closePath=True,
            )
        else:
            page.draw_polyline(
                [fitz.Point(x1, y1), fitz.Point(x1 + 8, y1 - 4), fitz.Point(x1 + 8, y1 + 4)],
                color=(0.35, 0.35, 0.4),
                fill=(0.35, 0.35, 0.4),
                closePath=True,
            )


def _chain_vertical(page: fitz.Page, cx: float, y0: float, labels: list[str], bw: float = 118, bh: float = 28, gap: float = 14) -> float:
    y = y0
    prev_cy = None
    for lab in labels:
        rect = fitz.Rect(cx - bw / 2, y, cx + bw / 2, y + bh)
        _box(page, rect, lab)
        cy = y + bh / 2
        if prev_cy is not None:
            _arrow(page, cx, prev_cy + bh / 2, cx, y)
        prev_cy = y
        y += bh + gap
    return y


def page_header(page: fitz.Page, title: str, subtitle: str) -> float:
    _text(page, MARGIN, MARGIN + 4, title, size=FS_TITLE)
    _text(page, MARGIN, MARGIN + 22, subtitle, size=FS)
    return MARGIN + 42


def draw_page1(page: fitz.Page) -> None:
    y = page_header(page, "1. 演练调用总览", "fault_drill/scenarios.py · pytest 与 run_all.py 入口")
    col_w = 200
    x_entry = MARGIN + col_w * 0.5
    x_pkg = MARGIN + col_w * 1.5
    x_deps = MARGIN + col_w * 2.5 + 80
    x_out = W - MARGIN - 90

    _box(page, fitz.Rect(x_entry - 85, y, x_entry + 85, y + 22), "入口")
    _chain_vertical(page, x_entry, y + 36, ["pytest", "test_fault_drill.py"], bw=150)
    _chain_vertical(page, x_entry + 120, y + 36, ["run_all.py"], bw=120)

    _arrow(page, x_entry + 75, y + 90, x_pkg - 75, y + 90)
    _box(page, fitz.Rect(x_pkg - 95, y, x_pkg + 95, y + 22), "fault_drill 包")
    steps_pkg = ["__init__.py 导出 5×run_*", "scenarios.py"]
    _chain_vertical(page, x_pkg, y + 36, steps_pkg, bw=170)

    deps_y = y + 36
    _box(page, fitz.Rect(x_deps - 100, y, x_deps + 100, y + 22), "依赖组件")
    for i, lab in enumerate(["Store", "OutboxPipeline", "SupervisorEngine", "PaymentClient"]):
        _box(page, fitz.Rect(x_deps - 95, deps_y + i * 38, x_deps + 95, deps_y + i * 38 + 30), lab)

    _arrow(page, x_pkg + 85, y + 120, x_deps - 95, y + 80)

    out_y = y + 80
    _box(page, fitz.Rect(x_out - 70, out_y, x_out + 70, out_y + 32), "assert 通过\n→ dict")
    _box(page, fitz.Rect(x_out - 70, out_y + 48, x_out + 70, out_y + 80), "assert 失败\n→ CI 报错")
    _arrow(page, x_deps + 95, y + 100, x_out - 70, out_y + 16)


def draw_page2(page: fitz.Page) -> None:
    y = page_header(page, "2. 五个场景逻辑链", "各 run_* 函数断言的期望行为")
    cols = [
        ("lost_publish_ack", ["create_workflow", "publish ack丢失", "仍有未发布", "重试 publish", "unpublished=0"]),
        ("crash_before_offset", ["publish", "ingest #1", "ingest 重放", "replay=0"]),
        ("worker_disconnect", ["A claim", "租约过期", "B claim", "A fenced 失败", "B 成功"]),
        ("success_response_lost", ["drop_response", "UNKNOWN", "POST=1", "reconcile", "SUCCEEDED"]),
        ("late_callback", ["late_callback", "POST 504", "等回调", "GET 200", "callbacks"]),
    ]
    n = len(cols)
    usable = W - 2 * MARGIN
    step = usable / n
    for i, (title, labs) in enumerate(cols):
        cx = MARGIN + step * i + step / 2
        _box(page, fitz.Rect(cx - 72, y, cx + 72, y + 20), title, fill=(0.9, 0.92, 0.95))
        _chain_vertical(page, cx, y + 30, labs, bw=120, bh=26, gap=10)


def draw_page3(page: fitz.Page) -> None:
    y = page_header(page, "3. 与图 01 主路径的关系", "同一协议栈：主路径测快路径，图 11 测异常收敛")
    cx = W / 2
    bw, bh = 220, 40
    r1 = fitz.Rect(cx - bw / 2, y + 20, cx + bw / 2, y + 20 + bh)
    r2 = fitz.Rect(cx - bw / 2, y + 90, cx + bw / 2, y + 90 + bh)
    r3 = fitz.Rect(cx - bw / 2, y + 200, cx + bw / 2, y + 200 + bh)
    r4 = fitz.Rect(cx + 140, y + 200, cx + 140 + 160, y + 200 + 50)

    _box(page, r1, "图01 E2E\nma-demo / e2e_skeleton", fill=(0.92, 0.96, 0.9))
    _box(page, r2, "图11 故障演练\nscenarios.py 五函数", fill=(0.96, 0.92, 0.9))
    _box(page, r3, "Store + 状态机 + Gateway + Worker", fill=(0.93, 0.94, 0.98))
    _box(page, r4, "幂等/栅栏\nUNKNOWN/Outbox", fill=(0.98, 0.93, 0.93))

    _arrow(page, cx, y + 60, cx, y + 90)
    _arrow(page, cx, y + 130, cx, y + 200)
    _arrow(page, cx + bw / 2, y + 220, cx + 140, y + 225)
    page.draw_line(
        fitz.Point(cx - 60, y + 60),
        fitz.Point(cx - 60, y + 220),
        color=(0.5, 0.5, 0.55),
        width=0.6,
        dashes="[3 2]",
    )
    _arrow(page, cx - 60, y + 130, cx - bw / 2, y + 220)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for drawer in (draw_page1, draw_page2, draw_page3):
        page = doc.new_page(width=W, height=H)
        drawer(page)
    doc.save(OUT_PDF)
    doc.close()
    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    main()