"""Market overview data: indices, breadth, sectors.

These are live snapshots, fetched fresh on each request (no DB caching), except
sectors which carry a short TTL cache (the eastmoney board endpoint is flaky and
doesn't need per-request freshness).
Indices prefer the realtime TDX source (mootdx) and fall back to akshare's
daily bars when it's unreachable; breadth/sectors stay on akshare (richer data).
"""
import time

import akshare as ak

from . import tdx

# (akshare index_daily symbol, display name)
INDICES = [
    ("sh000001", "上证指数"),
    ("sz399001", "深证成指"),
    ("sz399006", "创业板指"),
]


def _index_quotes_akshare() -> list[dict]:
    """Fallback: latest close + daily change from akshare daily bars."""
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
                "as_of": str(last["date"]),
            }
        )
    return quotes


def index_quotes() -> list[dict]:
    """Realtime index levels, TDX-first with an akshare fallback.

    TDX gives a live intraday price (so a polling dashboard ticks), while the
    akshare fallback only returns the most recent close.
    """
    try:
        quotes = tdx.index_quotes()
        if quotes:
            return quotes
    except Exception:
        pass
    return _index_quotes_akshare()


def market_breadth() -> dict:
    """Up/down/limit counts for the whole A-share market."""
    df = ak.stock_market_activity_legu()
    return {row["item"]: row["value"] for _, row in df.iterrows()}


def _industry_board_akshare() -> list[dict]:
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


# Sector cache: eastmoney's board endpoint is slow/flaky, so refresh at most once
# every 2 minutes and serve the last good result if a refresh fails.
_SECTOR_TTL = 120  # seconds
_sector_cache: dict = {"data": None, "ts": 0.0}


def industry_board() -> list[dict]:
    """Cached industry-board data (2-min TTL, last-good on failure).

    Within the TTL the cached list is returned untouched. After it expires we
    try one refresh; a failed refresh keeps serving the previous data instead of
    propagating the error, so the heatmap never goes blank once it has loaded.
    """
    now = time.time()
    fresh = _sector_cache["data"] is not None and now - _sector_cache["ts"] < _SECTOR_TTL
    if fresh:
        return _sector_cache["data"]

    try:
        data = _industry_board_akshare()
        _sector_cache.update(data=data, ts=now)
        return data
    except Exception:
        if _sector_cache["data"] is not None:
            return _sector_cache["data"]  # stale but better than nothing
        raise
