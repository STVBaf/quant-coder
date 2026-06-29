"""Market overview data: indices, breadth, sectors.

These are live snapshots, fetched fresh on each request (no DB caching).
"""
import akshare as ak

# (akshare index_daily symbol, display name)
INDICES = [
    ("sh000001", "上证指数"),
    ("sz399001", "深证成指"),
    ("sz399006", "创业板指"),
]


def index_quotes() -> list[dict]:
    """Latest level and daily change for the headline indices."""
    quotes = []
    for symbol, name in INDICES:
        df = ak.stock_zh_index_daily(symbol=symbol)
        last, prev = df.iloc[-1], df.iloc[-2]
        change = (last["close"] - prev["close"]) / prev["close"] * 100
        quotes.append(
            {
                "symbol": symbol,
                "name": name,
                "close": round(last["close"], 2),
                "change_pct": round(change, 2),
            }
        )
    return quotes


def market_breadth() -> dict:
    """Up/down/limit counts for the whole A-share market."""
    df = ak.stock_market_activity_legu()
    return {row["item"]: row["value"] for _, row in df.iterrows()}


def industry_board() -> list[dict]:
    """Per-industry sector performance, for the heatmap."""
    df = ak.stock_board_industry_name_em()
    return [
        {
            "name": row["板块名称"],
            "change_pct": row["涨跌幅"],
            "turnover": row["换手率"],
            "leader": row["领涨股票"],
        }
        for _, row in df.iterrows()
    ]
