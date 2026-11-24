"""报告生成技能。"""


def generate_report(
    title: str = "Agent 执行报告",
    sections: list[dict] | None = None,
    analysis: dict | None = None,
    **_: object,
) -> dict:
    lines = [f"# {title}", ""]
    if sections:
        for sec in sections:
            lines.append(f"## {sec.get('heading', '步骤')}")
            lines.append(str(sec.get("body", "")))
            lines.append("")
    if analysis and "summary" in analysis:
        s = analysis["summary"]
        lines.append("## 数据摘要")
        lines.append(f"- 行数: {s.get('rows')}")
        lines.append(f"- 列: {', '.join(s.get('columns', []))}")
    markdown = "\n".join(lines).strip() + "\n"
    return {"format": "markdown", "content": markdown}