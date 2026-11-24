"""简易检索工具（教学 stub，可换真实 Search API）。"""


def web_search(query: str) -> dict:
    return {
        "query": query,
        "results": [
            {
                "title": "北京三日天气概要（示例）",
                "snippet": "晴转阴，建议户外上午、下午室内博物馆。",
            }
        ],
        "source": "agent-kit-stub",
    }