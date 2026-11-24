"""会议类 mock 工具：图示「预订会议 / 取消会议」。"""
from langchain_core.tools import tool


@tool
def book_meeting(title: str, start_time: str) -> str:
    """
    预订会议。

    Args:
        title: 会议标题
        start_time: 开始时间描述，如「明天 14:00」
    """
    # 固定 id 便于单元测试断言（tests/test_graph.py）
    return (
        f" 已预订会议 id=mtg-1001，标题「{title}」，开始时间 {start_time}。"
    )


@tool
def cancel_meeting(meeting_id: str) -> str:
    """取消会议。meeting_id: 会议编号，如 mtg-1001。"""
    return f" 已取消会议 {meeting_id}。"