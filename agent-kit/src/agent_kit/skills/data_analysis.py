"""数据分析技能：加载 CSV / DataFrame 描述统计。"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def run_data_analysis(goal: str = "", csv_path: str | None = None, **_: object) -> dict:
    path = csv_path
    if not path and "csv" in goal.lower():
        for word in goal.split():
            if word.endswith(".csv") and Path(word).exists():
                path = word
                break
    if not path:
        return {"error": "no_csv", "hint": "传入 csv_path 或在目标中指明 .csv 文件"}

    df = pd.read_csv(path)
    numeric = df.select_dtypes(include="number")
    summary = {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "describe": numeric.describe().to_dict() if not numeric.empty else {},
        "head": df.head(5).to_dict(orient="records"),
    }
    return {"path": path, "summary": summary}