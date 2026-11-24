"""Export architecture-flow.png at 1920x1080 using Pillow (no Cairo/Node)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
OUT = Path(__file__).resolve().parents[1] / "docs" / "assets" / "architecture-flow.png"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _gradient_bg(draw: ImageDraw.ImageDraw, img: Image.Image) -> None:
    for y in range(H):
        t = y / max(H - 1, 1)
        r = int(0xF8 + (0xEE - 0xF8) * t)
        g = int(0xFA + (0xF2 - 0xFA) * t)
        b = int(0xFC + (0xFF - 0xFC) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def _rounded_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int,
    fill: str,
    outline: str | None = None,
    width: int = 2,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _text_center(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str,
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = xy
    draw.text((x - tw // 2, y - th // 2), text, font=font, fill=fill)


def main() -> None:
    img = Image.new("RGB", (W, H), "#f8fafc")
    draw = ImageDraw.Draw(img)
    _gradient_bg(draw, img)

    title_f = _font(36, bold=True)
    sub_f = _font(22)
    label_f = _font(26, bold=True)
    small_f = _font(20)
    edge_f = _font(22)

    _text_center(draw, (W // 2, 72), "架构（与你的流程图一致）", title_f, "#1e293b")
    _text_center(draw, (W // 2, 118), "LangGraph · StateGraph · llm ↔ action", sub_f, "#64748b")

    # Scale from 1280x520 layout
    sx, sy = W / 1280, H / 520

    def px(x: float) -> int:
        return int(x * sx)

    def py(y: float) -> int:
        return int(y * sy)

    # User pill
    _rounded_rect(draw, (px(40), py(200), px(160), py(252)), py(26), "#e2e8f0", "#94a3b8", 2)
    _text_center(draw, (px(100), py(226)), "用户任务", label_f, "#0f172a")

    # AgentState
    _rounded_rect(draw, (px(200), py(188), px(348), py(264)), px(12), "#dbeafe", "#3b82f6", 3)
    _text_center(draw, (px(274), py(218)), "AgentState", label_f, "#1d4ed8")
    _text_center(draw, (px(274), py(248)), "messages · steps", small_f, "#64748b")

    # LLM
    _rounded_rect(draw, (px(400), py(188), px(568), py(264)), px(12), "#2563eb", "#1d4ed8", 3)
    _text_center(draw, (px(484), py(218)), "llm", label_f, "#ffffff")
    _text_center(draw, (px(484), py(248)), "思考 + 规划", small_f, "#bfdbfe")

    # Diamond exists_action
    cx, cy = px(640), py(226)
    r = py(76)
    diamond = [(cx, cy - r), (cx + px(90), cy), (cx, cy + r), (cx - px(90), cy)]
    draw.polygon(diamond, fill="#fef3c7", outline="#f59e0b", width=3)
    _text_center(draw, (cx, cy - py(8)), "exists_action", label_f, "#0f172a")
    _text_center(draw, (cx, cy + py(18)), "条件边", small_f, "#64748b")

    # Action
    _rounded_rect(draw, (px(520), py(368), px(700), py(444)), px(12), "#fb923c", "#ea580c", 3)
    _text_center(draw, (px(610), py(398)), "action", label_f, "#431407")
    _text_center(draw, (px(610), py(428)), "工具执行", small_f, "#7c2d12")

    # CLI
    _rounded_rect(draw, (px(820), py(200), px(960), py(252)), py(26), "#dcfce7", "#22c55e", 3)
    _text_center(draw, (px(890), py(226)), "CLI 输出", label_f, "#166534")

    # Memory ellipse
    mx, my = px(274), py(318)
    rx, ry = px(118), py(36)
    draw.ellipse((mx - rx, my - ry, mx + rx, my + ry), fill="#ede9fe", outline="#7c3aed", width=3)
    _text_center(draw, (mx, my - py(8)), "MemorySaver", label_f, "#5b21b6")
    _text_center(draw, (mx, my + py(16)), "+ thread_id", small_f, "#64748b")

    def arrow_line(p1: tuple[int, int], p2: tuple[int, int], color: str, width: int = 4) -> None:
        draw.line([p1, p2], fill=color, width=width)
        import math

        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        length = math.hypot(dx, dy) or 1
        ux, uy = dx / length, dy / length
        tip = p2
        left = (int(tip[0] - ux * 14 - uy * 8), int(tip[1] - uy * 14 + ux * 8))
        right = (int(tip[0] - ux * 14 + uy * 8), int(tip[1] - uy * 14 - ux * 8))
        draw.polygon([tip, left, right], fill=color)

    arrow_line((px(160), py(226)), (px(198), py(226)), "#475569")
    arrow_line((px(348), py(226)), (px(398), py(226)), "#2563eb")
    arrow_line((px(568), py(226)), (px(550), py(226)), "#2563eb")
    arrow_line((px(730), py(226)), (px(818), py(226)), "#22c55e")
    draw.text((px(760), py(190)), "终答", font=edge_f, fill="#15803d")

    arrow_line((px(640), py(302)), (px(610), py(368)), "#ea580c")
    draw.text((px(668), py(320)), "tool_calls", font=edge_f, fill="#c2410c")

    # action -> llm loop (bezier approximated as polyline)
    loop = [
        (px(520), py(406)),
        (px(420), py(406)),
        (px(420), py(226)),
        (px(400), py(226)),
    ]
    for i in range(len(loop) - 1):
        arrow_line(loop[i], loop[i + 1], "#ea580c", width=5)

    # dashed state -> memory
    for x in range(px(274), px(274), 1):
        pass
    y0, y1 = py(264), py(282)
    x = px(274)
    step = py(10)
    y = y0
    dash = True
    while y < y1:
        y_end = min(y + step, y1)
        if dash:
            draw.line([(x, y), (x, y_end)], fill="#7c3aed", width=3)
        y += step
        dash = not dash
    arrow_line((x, y1 - 4), (x, y1), "#7c3aed", 3)

    # Legend card
    lx, ly = px(980), py(160)
    lw, lh = px(260), py(200)
    _rounded_rect(draw, (lx, ly, lx + lw, ly + lh), px(12), "#ffffff", "#e2e8f0", 2)
    draw.text((lx + px(20), ly + py(12)), "图例", font=label_f, fill="#0f172a")
    items = [
        ("#2563eb", "大脑 · OpenAI + bind_tools", py(42)),
        ("#fb923c", "双手 · mock 工具 + take_action", py(68)),
        ("#7c3aed", "记忆 · checkpointer", py(104)),
        ("#f59e0b", "条件边 · 继续 / 结束", py(135)),
    ]
    for color, txt, yy in items:
        yy_abs = ly + yy
        if "记忆" in txt:
            draw.ellipse(
                (lx + px(20), yy_abs, lx + px(40), yy_abs + py(14)),
                fill="#ede9fe",
                outline=color,
                width=2,
            )
        elif "条件" in txt:
            cx2 = lx + px(27)
            cy2 = yy_abs + py(10)
            rr = py(10)
            draw.polygon(
                [
                    (cx2, cy2 - rr),
                    (cx2 + rr, cy2),
                    (cx2, cy2 + rr),
                    (cx2 - rr, cy2),
                ],
                fill="#fef3c7",
                outline=color,
            )
        else:
            _rounded_rect(
                draw,
                (lx + px(20), yy_abs, lx + px(34), yy_abs + py(14)),
                3,
                color,
            )
        draw.text((lx + px(42), yy_abs - py(2)), txt, font=small_f, fill="#64748b")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()