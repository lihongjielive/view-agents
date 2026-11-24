from agent_kit.agents.agent import KitAgent


def test_demo_run_weather():
    result = KitAgent().run("查询北京天气")
    assert result.plan
    assert any(o["target"] == "search" for o in result.observations)


def test_demo_run_data_goal():
    result = KitAgent().run("分析 sales.csv 趋势")
    targets = {o["target"] for o in result.observations}
    assert "data_analysis" in targets or "search" in targets