from rest_framework import serializers

from .models import DailyBar, Stock


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ["code", "name", "industry"]


class DailyBarSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyBar
        fields = ["date", "open", "high", "low", "close", "volume"]
