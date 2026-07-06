"""Tongdaxin (通达信) realtime quotes via mootdx.

mootdx talks the native TDX binary protocol straight to broker quote servers —
no HTTP scraping, no API key, and it stays up when eastmoney/sina endpoints
flake out. We use it as the primary source for *realtime* data (index levels,
stock snapshots) that akshare's daily-bar endpoints can't provide.

The client picks a server on first use (slow), so it's built once and reused.
"""
import threading

from mootdx.quotes import Quotes

# TDX index codes differ from the akshare/sina symbols.
TDX_INDEX = {
    "sh000001": ("999999", "上证指数"),
    "sz399001": ("399001", "深证成指"),
    "sz399006": ("399006", "创业板指"),
}

_client = None
_lock = threading.Lock()


def _get_client():
    """Lazily build the mootdx client once; factory() is expensive."""
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                _client = Quotes.factory(market="std")
    return _client


def _pct(price, last_close):
    if not last_close:
        return 0.0
    return round((price - last_close) / last_close * 100, 2)


def index_quotes() -> list[dict]:
    """Realtime index levels + intraday change for the headline indices.

    Unlike the akshare daily-bar source, `price`/`last_close` here are live, so
    the dashboard can poll this for a ticking change_pct during market hours.
    """
    client = _get_client()
    codes = [tdx for tdx, _ in TDX_INDEX.values()]
    df = client.quotes(symbol=codes)
    by_code = {str(row["code"]): row for _, row in df.iterrows()}

    quotes = []
    for symbol, (tdx, name) in TDX_INDEX.items():
        row = by_code.get(tdx)
        if row is None:
            continue
        price = float(row["price"])
        quotes.append(
            {
                "symbol": symbol,
                "name": name,
                "close": round(price, 2),
                "change_pct": _pct(price, float(row["last_close"])),
                "as_of": "realtime",
            }
        )
    return quotes


def stock_quote(code: str) -> dict:
    """Realtime snapshot for a single stock (price + intraday change)."""
    client = _get_client()
    df = client.quotes(symbol=[code])
    if df is None or df.empty:
        raise ValueError(f"no quote for {code}")
    row = df.iloc[0]
    price = float(row["price"])
    return {
        "code": code,
        "price": round(price, 2),
        "change_pct": _pct(price, float(row["last_close"])),
        "high": round(float(row["high"]), 2),
        "low": round(float(row["low"]), 2),
    }
