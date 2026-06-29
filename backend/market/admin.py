from django.contrib import admin

from .models import DailyBar, Stock

admin.site.register(Stock)
admin.site.register(DailyBar)
