"""Claude-powered quant agent: a manual tool-use loop.

Loops until stop_reason == "end_turn", appending the full response content each
turn and feeding tool_result blocks back. Native Anthropic protocol with a
configurable base_url (proxy/relay supported via ANTHROPIC_BASE_URL).
"""
from anthropic import Anthropic
from django.conf import settings

from . import tools

SYSTEM_PROMPT = """你是一个 A 股量化研究助手，嵌入在一个量化回测平台里。

你可以调用工具查询行情、列出策略、运行策略回测。当用户用自然语言描述回测需求时\
（例如"用双均线回测茅台近三年，5日20日均线"），你应当：
1. 解析出股票代码、策略类型和参数；
2. 调用 run_backtest 工具实际运行回测；
3. 用简洁的中文解读结果——收益、回撤、夏普、胜率分别说明什么，策略在这只股票上\
表现如何，有什么风险。

不要编造数据，所有数字都必须来自工具返回。如果用户给的是股票名称而非代码，请根据\
常识推断代码（如"茅台"→600519），不确定时询问用户。回答专业、简洁，不啰嗦。"""

MAX_TURNS = 8


def _client() -> Anthropic:
    return Anthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        base_url=settings.ANTHROPIC_BASE_URL or None,
    )


def _tool_params():
    """Tool schemas with a cache_control breakpoint on the last definition."""
    schemas = [dict(s) for s in tools.TOOL_SCHEMAS]
    schemas[-1]["cache_control"] = {"type": "ephemeral"}
    return schemas


def _system_blocks():
    return [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ]


def run_agent(history: list[dict]) -> dict:
    """Run the tool-use loop over a conversation history.

    `history` is a list of {role, content} messages (content may be a string or
    a list of blocks). Returns the final assistant text plus a trace of tool
    calls for the UI to show.
    """
    client = _client()
    messages = [dict(m) for m in history]
    trace = []

    for _ in range(MAX_TURNS):
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=2048,
            system=_system_blocks(),
            tools=_tool_params(),
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            text = "".join(b.text for b in response.content if b.type == "text")
            return {"reply": text, "trace": trace, "messages": messages}

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = tools.dispatch(block.name, block.input or {})
            trace.append({"tool": block.name, "input": block.input, "result": result})
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": _to_text(result),
                }
            )

        messages.append({"role": "user", "content": tool_results})

    return {"reply": "（已达到最大工具调用轮数）", "trace": trace, "messages": messages}


def _to_text(result: dict) -> str:
    import json

    return json.dumps(result, ensure_ascii=False)
