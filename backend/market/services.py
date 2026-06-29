"""akshare data access with DB caching.

External calls are slow and flaky, so daily bars are persisted to the DB and
only fetched from akshare when the local cache misses.
"""
from datetime import date, timedelta

import akshare as ak

from .models import DailyBar, Stock


def _normalize_code(code: str) -> str:
    """Strip exchange prefixes/suffixes, keep the 6-digit code."""
    return code.strip().lower().replace("sh", "").replace("sz", "").replace(".", "")[-6:]


_name_cache: dict[str, str] = {}


def _lookup_name(code: str) -> str:
    """Resolve a stock name via the full-market snapshot, cached in-process.

    stock_individual_info_em is broken in this akshare version, so we use the
    spot snapshot (stable columns) and cache the whole table on first hit.
    """
    if not _name_cache:
        try:
            df = ak.stock_zh_a_spot_em()
            _name_cache.update(dict(zip(df["代码"], df["名称"])))
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


def _refresh_from_akshare(stock: Stock, start: str, end: str) -> None:
    df = ak.stock_zh_a_hist(
        symbol=stock.code,
        period="daily",
        start_date=start.replace("-", ""),
        end_date=end.replace("-", ""),
        adjust="qfq",
    )
    bars = [
        DailyBar(
            stock=stock,
            date=row["日期"],
            open=row["开盘"],
            high=row["最高"],
            low=row["最低"],
            close=row["收盘"],
            volume=row["成交量"],
        )
        for _, row in df.iterrows()
    ]
    DailyBar.objects.bulk_create(bars, ignore_conflicts=True)
