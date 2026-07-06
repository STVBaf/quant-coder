"""akshare data access with DB caching.

External calls are slow and flaky, so daily bars are persisted to the DB and
only fetched from akshare when the local cache misses. akshare calls are wrapped
in a short retry because eastmoney intermittently drops connections.
"""
import time
from datetime import date, timedelta

import akshare as ak

from .models import DailyBar, Stock


def _retry(fn, attempts: int = 3, delay: float = 0.8):
    """Call fn(), retrying on transient network errors with linear backoff."""
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # akshare raises requests.ConnectionError etc.
            last = e
            if i < attempts - 1:
                time.sleep(delay * (i + 1))
    raise last


def _normalize_code(code: str) -> str:
    """Strip exchange prefixes/suffixes, keep the 6-digit code."""
    return code.strip().lower().replace("sh", "").replace("sz", "").replace(".", "")[-6:]


_name_cache: dict[str, str] = {}


def _lookup_name(code: str) -> str:
    """Resolve a stock name via the full code→name table, cached in-process.

    Uses stock_info_a_code_name (not eastmoney) so it stays reachable when the
    eastmoney endpoints are blocked. Falls back to the code on failure.
    """
    if not _name_cache:
        try:
            df = _retry(ak.stock_info_a_code_name)
            _name_cache.update(dict(zip(df["code"], df["name"])))
        except Exception:
            pass  # leave cache empty; callers fall back to the code
    return _name_cache.get(code, code)


def get_or_create_stock(code: str) -> Stock:
    code = _normalize_code(code)
    stock, created = Stock.objects.get_or_create(code=code, defaults={"name": code})
    if created or stock.name == code:
        name = _lookup_name(code)
        if name != stock.name:
            stock.name = name
            stock.save(update_fields=["name"])
    return stock


def fetch_daily_bars(code: str, start: str, end: str) -> list[DailyBar]:
    """Return daily bars for [start, end], pulling from akshare on cache miss."""
    stock = get_or_create_stock(code)
    qs = stock.bars.filter(date__gte=start, date__lte=end)

    if not _cache_covers(qs, start, end):
        _refresh_from_akshare(stock, start, end)
        qs = stock.bars.filter(date__gte=start, date__lte=end)

    return list(qs)


def _cache_covers(qs, start: str, end: str) -> bool:
    """True if the cache plausibly spans the requested window."""
    if not qs.exists():
        return False
    first, last = qs.first().date, qs.last().date
    return first <= date.fromisoformat(start) + timedelta(days=7) and last >= date.fromisoformat(end) - timedelta(days=7)


def _sina_symbol(code: str) -> str:
    """Add the exchange prefix Sina's API expects: 6* → sh, else sz."""
    return ("sh" if code.startswith("6") else "sz") + code


def _refresh_from_akshare(stock: Stock, start: str, end: str) -> None:
    # Sina source (stock_zh_a_daily): eastmoney's stock_zh_a_hist often drops the
    # connection in this environment, while Sina stays reachable. Columns are
    # English here (date/open/high/low/close/volume).
    df = _retry(
        lambda: ak.stock_zh_a_daily(
            symbol=_sina_symbol(stock.code),
            start_date=start.replace("-", ""),
            end_date=end.replace("-", ""),
            adjust="qfq",
        )
    )
    bars = [
        DailyBar(
            stock=stock,
            date=row["date"],
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
            volume=row["volume"],
        )
        for _, row in df.iterrows()
    ]
    DailyBar.objects.bulk_create(bars, ignore_conflicts=True)
