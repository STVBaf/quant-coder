from django.db import models

from market.models import Stock


class Strategy(models.Model):
    """A named strategy with JSON-encoded parameters."""

    KINDS = [
        ("ma_cross", "双均线"),
        ("rsi", "RSI"),
        ("bollinger", "布林带"),
    ]
    name = models.CharField(max_length=50)
    kind = models.CharField(max_length=20, choices=KINDS)
    params = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.kind})"


class Backtest(models.Model):
    """A single backtest run and its results."""

    strategy = models.ForeignKey(Strategy, related_name="runs", on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    start = models.DateField()
    end = models.DateField()
    metrics = models.JSONField(default=dict)  # return, max_drawdown, sharpe, win_rate
    equity_curve = models.JSONField(default=list)  # [[date, value], ...]
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.strategy.name} on {self.stock.code}"
