from datetime import date, timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from market.services import fetch_daily_bars, get_or_create_stock

from . import engine
from .models import Backtest, Strategy
from .strategies import REGISTRY


@api_view(["GET"])
def strategies(request):
    """List available strategy kinds and their default params."""
    return Response(
        [
            {"kind": "ma_cross", "name": "双均线", "params": {"fast": 5, "slow": 20}},
            {"kind": "rsi", "name": "RSI", "params": {"period": 14, "low": 30, "high": 70}},
            {"kind": "bollinger", "name": "布林带", "params": {"period": 20, "k": 2.0}},
        ]
    )


@api_view(["POST"])
def run(request):
    """Run a backtest: {code, kind, params, start?, end?} and persist the result."""
    body = request.data
    code = body.get("code")
    kind = body.get("kind")
    params = body.get("params", {})

    if not code or kind not in REGISTRY:
        return Response({"error": "缺少 code 或策略类型无效"}, status=400)

    end = body.get("end", date.today().isoformat())
    start = body.get("start", (date.today() - timedelta(days=365 * 2)).isoformat())

    bars = fetch_daily_bars(code, start, end)
    try:
        result = engine.run(bars, kind, params)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    stock = get_or_create_stock(code)
    strategy, _ = Strategy.objects.get_or_create(
        kind=kind, name=dict(Strategy.KINDS)[kind], defaults={"params": params}
    )
    Backtest.objects.create(
        user=request.user if request.user.is_authenticated else None,
        strategy=strategy,
        stock=stock,
        start=start,
        end=end,
        metrics=result["metrics"],
        equity_curve=result["equity_curve"],
    )

    return Response({"stock": {"code": stock.code, "name": stock.name}, **result})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def history(request):
    """The logged-in user's saved backtests, newest first."""
    runs = request.user.backtests.select_related("strategy", "stock")
    return Response(
        [
            {
                "id": r.id,
                "code": r.stock.code,
                "name": r.stock.name,
                "strategy": r.strategy.name,
                "kind": r.strategy.kind,
                "start": r.start,
                "end": r.end,
                "metrics": r.metrics,
                "created_at": r.created_at,
            }
            for r in runs
        ]
    )
