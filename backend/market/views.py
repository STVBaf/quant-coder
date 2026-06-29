from datetime import date, timedelta

from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import overview
from .serializers import DailyBarSerializer, StockSerializer
from .services import fetch_daily_bars, get_or_create_stock


@api_view(["GET"])
def kline(request, code):
    """Daily K-line bars for a stock. Defaults to the last year."""
    end = request.GET.get("end", date.today().isoformat())
    start = request.GET.get("start", (date.today() - timedelta(days=365)).isoformat())
    bars = fetch_daily_bars(code, start, end)
    stock = get_or_create_stock(code)
    return Response(
        {
            "stock": StockSerializer(stock).data,
            "bars": DailyBarSerializer(bars, many=True).data,
        }
    )


@api_view(["GET"])
def overview_data(request):
    """Dashboard snapshot: indices, breadth, sectors."""
    return Response(
        {
            "indices": overview.index_quotes(),
            "breadth": overview.market_breadth(),
            "sectors": overview.industry_board(),
        }
    )
