from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/market/", include("market.urls")),
    path("api/backtest/", include("backtest.urls")),
    path("api/agent/", include("agent.urls")),
]
