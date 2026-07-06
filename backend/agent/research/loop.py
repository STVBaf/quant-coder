"""Autonomous research loop driven by the Claude Agent SDK.

The agent is given a research task in natural language plus a set of stock
codes. It can inspect available data columns, then repeatedly WRITE strategy
code and RUN it in the Docker sandbox, reading back real backtest metrics, until
it meets the goal or hits the iteration cap. Every iteration (code + metrics +
the agent's reasoning) is recorded via `on_event` for the UI and for persistence.

Tools are exposed as an in-process MCP server; the sandbox tool is the only way
the agent can execute code, and it runs strictly inside the container.
"""
import asyncio
import json
from pathlib import Path
from typing import Callable

from django.conf import settings

from .dataset import describe_columns, materialize
from .sandbox.runner import run_code

SYSTEM_PROMPT = """你是一名 A 股量化研究员，在一个安全的研究平台里工作。

你的工作方式是一个迭代循环：
1. 先用 list_data_columns 查看有哪些量价数据和技术指标可用；
2. 写一段 Python 策略代码，通过 run_strategy 在沙箱里回测；
3. 读回真实的回测指标（累计收益 / 最大回撤 / 夏普 / 胜率）；
4. 诊断问题（回撤过大？过拟合？信号太少？），改进代码，再次 run_strategy；
5. 达到用户目标或你判断已收敛时，给出最终结论。

策略代码约定（run_strategy 的 code 参数）：
- 必须定义 CODE = "6位股票代码"（你要回测的标的，须在可用列表内）；
- 必须定义 build_signals(df) -> pd.Series，返回持仓序列（1.0=持有多头，0.0=空仓）；
- df 已含量价与指标列，索引为日期；可直接用列，也可自己从 close 计算；
- 引擎会自动 shift(1) 防未来函数，你不要自己 shift。

要求：所有结论必须基于 run_strategy 返回的真实数字，不得编造。关注样本内外稳健性，
避免只为了好看的曲线而过度调参。回答专业、简洁，用中文。"""

MAX_TURNS = 12


def _build_tools(data_dir: Path, on_event: Callable):
    """Create the SDK tool functions bound to this run's data dir + event sink."""
    from claude_agent_sdk import tool

    @tool("list_data_columns", "列出沙箱数据集里可用的量价字段和技术指标", {})
    async def list_data_columns(args):
        cols = describe_columns()
        return {"content": [{"type": "text",
                             "text": json.dumps(cols, ensure_ascii=False)}]}

    @tool("run_strategy",
          "在 Docker 沙箱里运行策略代码并回测，返回真实绩效指标。"
          "code 需定义 CODE 和 build_signals(df)。",
          {"code": str})
    async def run_strategy(args):
        code = args["code"]
        # Sandbox call is blocking (subprocess); run it off the event loop.
        out = await asyncio.to_thread(run_code, code, data_dir)
        on_event("run_strategy", {"code": code, "result": out})
        return {"content": [{"type": "text",
                             "text": json.dumps(out, ensure_ascii=False, default=str)}],
                "is_error": not out.get("ok", False)}

    return [list_data_columns, run_strategy]


def _sdk_env() -> dict:
    """Auth/proxy for the SDK's CLI subprocess (no dedicated api_key field)."""
    env = {}
    if settings.ANTHROPIC_API_KEY:
        env["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
    if settings.ANTHROPIC_BASE_URL:
        env["ANTHROPIC_BASE_URL"] = settings.ANTHROPIC_BASE_URL
    return env


async def _run(task_prompt: str, codes: list[str], on_event: Callable) -> str:
    from claude_agent_sdk import (
        query, create_sdk_mcp_server, ClaudeAgentOptions,
        AssistantMessage, TextBlock, ToolUseBlock, ResultMessage,
    )

    on_event("status", {"stage": "materializing", "codes": codes})
    data_dir = await asyncio.to_thread(materialize, codes)

    server = create_sdk_mcp_server(
        name="research", version="1.0.0", tools=_build_tools(data_dir, on_event)
    )
    options = ClaudeAgentOptions(
        model=settings.ANTHROPIC_MODEL,
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"research": server},
        allowed_tools=[
            "mcp__research__list_data_columns",
            "mcp__research__run_strategy",
        ],
        permission_mode="bypassPermissions",  # non-interactive backend
        max_turns=MAX_TURNS,
        env=_sdk_env(),
    )

    prompt = (f"研究任务：{task_prompt}\n"
              f"可用标的（股票代码）：{', '.join(codes)}\n"
              f"请开始你的迭代研究。")

    final_text = ""
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    on_event("thought", {"text": block.text})
                    final_text = block.text
                elif isinstance(block, ToolUseBlock):
                    on_event("tool_call", {"name": block.name, "input": block.input})
        elif isinstance(msg, ResultMessage):
            on_event("status", {"stage": "done"})
    return final_text


def run_research(task_prompt: str, codes: list[str], on_event: Callable) -> str:
    """Sync entry point for background threads. Returns the agent's final text."""
    return asyncio.run(_run(task_prompt, codes, on_event))
