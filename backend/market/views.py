from datetime import date, timedelta

from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import overview, tdx
from .serializers import DailyBarSerializer, StockSerializer
from .services import fetch_daily_bars, get_or_create_stock


@api_view(["GET"])
def kline(request, code):
    """Daily K-line bars for a stock. Defaults to the last year."""
    end = request.GET.get("end", date.today().isoformat())
    start = request.GET.get("start", (date.today() - timedelta(days=365)).isoformat())
    try:
        bars = fetch_daily_bars(code, start, end)
    except Exception:
        return Response(
            {"error": "行情接口暂时不可用（外部数据源波动），请稍后重试"},
            status=503,
        )
    if not bars:
        return Response(
            {"error": f"未找到 {code} 的行情数据，请确认代码是否正确"}, status=404
        )
    stock = get_or_create_stock(code)
    return Response(
        {
            "stock": StockSerializer(stock).data,
            "bars": DailyBarSerializer(bars, many=True).data,
        }
    )


@api_view(["GET"])
def overview_data(request):
    """Dashboard snapshot: indices, breadth, sectors.

    Each source is fetched independently so one flaky akshare endpoint can't
    500 the whole dashboard — failures land in `errors` and the rest renders.
    """
    data = {"indices": [], "breadth": {}, "sectors": [], "errors": []}
    for key, fn in (
        ("indices", overview.index_quotes),
        ("breadth", overview.market_breadth),
        ("sectors", overview.industry_board),
    ):
        try:
            data[key] = fn()
        except Exception:
            data["errors"].append(key)
    return Response(data)


@api_view(["GET"])
def quote(request, code):
    """Realtime snapshot for a single stock (TDX source), for the ticker tape."""
    try:
        return Response(tdx.stock_quote(code))
    except Exception:
        return Response({"error": "实时报价暂时不可用"}, status=503)
