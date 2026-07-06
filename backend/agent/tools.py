"""Tools the quant agent can call.

Each tool wraps an existing backend capability. TOOL_SCHEMAS is sent to Claude;
dispatch() runs the matching Python function and returns a JSON-serializable result.
"""
from datetime import date, timedelta

from backtest import engine
from backtest.strategies import REGISTRY
from market.services import fetch_daily_bars, get_or_create_stock

TOOL_SCHEMAS = [
    {
        "name": "list_strategies",
        "description": "列出所有可用的回测策略及其默认参数。在用户问有哪些策略、或回测前确认参数时调用。",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_quote",
        "description": "查询某只 A 股最近的收盘价和区间涨跌幅。输入 6 位股票代码，如 600519。",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "6 位股票代码，如 600519"},
            },
            "required": ["code"],
        },
    },
    {
        "name": "run_backtest",
        "description": (
            "对某只股票运行一个策略回测，返回累计收益、最大回撤、夏普比率、胜率等指标。"
            "策略类型必须是 list_strategies 返回的之一。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "6 位股票代码"},
                "kind": {
                    "type": "string",
                    "enum": list(REGISTRY.keys()),
                    "description": "策略类型：ma_cross 双均线 / rsi / bollinger 布林带",
                },
                "params": {
                    "type": "object",
                    "description": "策略参数，如 {\"fast\": 5, \"slow\": 20}。省略则用默认值。",
                },
                "years": {
                    "type": "integer",
                    "description": "回测年数，默认 2 年",
                },
            },
            "required": ["code", "kind"],
        },
    },
]

_DEFAULT_PARAMS = {
    "ma_cross": {"fast": 5, "slow": 20},
    "rsi": {"period": 14, "low": 30, "high": 70},
    "bollinger": {"period": 20, "k": 2.0},
}


def dispatch(name: str, args: dict) -> dict:
    """Run a tool by name. Returns a JSON-serializable dict."""
    if name == "list_strategies":
        return {
            "strategies": [
                {"kind": k, "params": p} for k, p in _DEFAULT_PARAMS.items()
            ]
        }

    if name == "get_quote":
        return _get_quote(args["code"])

    if name == "run_backtest":
        return _run_backtest(
            args["code"],
            args["kind"],
            args.get("params") or _DEFAULT_PARAMS.get(args["kind"], {}),
            args.get("years", 2),
        )

    return {"error": f"unknown tool: {name}"}


def _get_quote(code: str) -> dict:
    end = date.today()
    start = end - timedelta(days=30)
    bars = fetch_daily_bars(code, start.isoformat(), end.isoformat())
    stock = get_or_create_stock(code)
    if not bars:
        return {"error": "无行情数据"}
    first, last = bars[0], bars[-1]
    change = (last.close - first.close) / first.close * 100
    return {
        "code": stock.code,
        "name": stock.name,
        "close": round(last.close, 2),
        "change_pct_30d": round(change, 2),
        "as_of": last.date.isoformat(),
    }


def _run_backtest(code: str, kind: str, params: dict, years: int) -> dict:
    end = date.today()
    start = end - timedelta(days=365 * years)
    bars = fetch_daily_bars(code, start.isoformat(), end.isoformat())
    stock = get_or_create_stock(code)
    try:
        result = engine.run(bars, kind, params)
    except ValueError as e:
        return {"error": str(e)}
    return {
        "code": stock.code,
        "name": stock.name,
        "kind": kind,
        "params": params,
        "period": f"{start.isoformat()} ~ {end.isoformat()}",
        "metrics": result["metrics"],
        "trade_count": len(result["trades"]),
    }
