from agent_kit.skills.code_interpreter import run_code_snippet
from agent_kit.skills.data_analysis import run_data_analysis
from agent_kit.skills.report_generation import generate_report

SKILL_REGISTRY = {
    "data_analysis": run_data_analysis,
    "report_generation": generate_report,
    "code_interpreter": run_code_snippet,
}

__all__ = ["SKILL_REGISTRY"]