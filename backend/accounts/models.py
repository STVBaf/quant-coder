from django.contrib.auth.models import User
from django.db import models

from market.models import Stock


class WatchItem(models.Model):
    """A stock on a user's watchlist."""

    user = models.ForeignKey(User, related_name="watchlist", on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "stock")
        ordering = ["-created_at"]
