"""基于 Agent 的数据分析实战（教材核心模块）。"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import pandas as pd


class TaskType(str, Enum):
    EXPLORATION = "exploration"
    MODELING = "modeling"
    PREDICTION = "prediction"
    MONITORING = "monitoring"


@dataclass
class AnalysisTask:
    task_id: str
    task_type: TaskType
    data_source: str
    requirements: str
    priority: int = 1


class DataProcessor:
    def load(self, path: str) -> pd.DataFrame:
        return pd.read_csv(path)

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.dropna(how="all")


class ModelManager:
    def select(self, task_type: TaskType) -> str:
        return {
            TaskType.EXPLORATION: "descriptive",
            TaskType.MODELING: "linear_stub",
            TaskType.PREDICTION: "forecast_stub",
            TaskType.MONITORING: "threshold_stub",
        }[task_type]

    def fit_stub(self, model: str, df: pd.DataFrame) -> dict[str, Any]:
        numeric = df.select_dtypes(include="number")
        return {
            "model": model,
            "metrics": {"rows": len(df), "numeric_cols": list(numeric.columns)},
        }


class VisualizationEngine:
    def chart_spec(self, df: pd.DataFrame) -> dict[str, Any]:
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            return {"type": "table", "columns": list(df.columns)}
        col = numeric.columns[0]
        return {"type": "line", "x": list(range(len(df))), "y": numeric[col].tolist(), "series": col}


class ReportGenerator:
    def markdown(self, task: AnalysisTask, summary: dict[str, Any]) -> str:
        lines = [
            f"# 数据分析报告 — {task.task_id}",
            "",
            f"- 类型: {task.task_type.value}",
            f"- 数据源: {task.data_source}",
            f"- 需求: {task.requirements}",
            "",
            "## 结果",
            str(summary),
        ]
        return "\n".join(lines) + "\n"


class DataAnalysisAgent:
    def __init__(self) -> None:
        self.data_processor = DataProcessor()
        self.model_manager = ModelManager()
        self.visualization_engine = VisualizationEngine()
        self.report_generator = ReportGenerator()

    def run(self, task: AnalysisTask) -> dict[str, Any]:
        df = self.data_processor.load(task.data_source)
        df = self.data_processor.preprocess(df)
        model = self.model_manager.select(task.task_type)
        metrics = self.model_manager.fit_stub(model, df)
        chart = self.visualization_engine.chart_spec(df)
        summary = {
            "model": model,
            "metrics": metrics,
            "chart": chart,
            "describe": df.describe(include="all").to_dict(),
        }
        report = self.report_generator.markdown(task, summary)
        return {"summary": summary, "report": report}