from pathlib import Path

from agent_kit.agents.data_analysis_agent import AnalysisTask, DataAnalysisAgent, TaskType

FIXTURE = Path(__file__).parent / "fixtures" / "sample.csv"


def test_data_analysis_pipeline():
    task = AnalysisTask("T1", TaskType.EXPLORATION, str(FIXTURE), "探索")
    out = DataAnalysisAgent().run(task)
    assert "report" in out
    assert "sales" in out["report"]
    assert out["summary"]["metrics"]["metrics"]["rows"] == 5