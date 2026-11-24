from agent_kit.tools.calculator import calculate
from agent_kit.tools.search import web_search


def test_calculator():
    assert calculate("2+3*4")["value"] == 14.0


def test_search_stub():
    out = web_search("北京天气")
    assert out["results"]