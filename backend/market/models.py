from django.db import models


class Stock(models.Model):
    """A tradable A-share security."""

    code = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=50)
    industry = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.code} {self.name}"


class DailyBar(models.Model):
    """One day of OHLCV for a stock."""

    stock = models.ForeignKey(Stock, related_name="bars", on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()

    class Meta:
        unique_together = ("stock", "date")
        ordering = ["date"]

    def __str__(self):
        return f"{self.stock.code} @ {self.date}"
