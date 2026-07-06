from django.urls import path

from . import views

urlpatterns = [
    path("overview/", views.overview_data, name="overview"),
    path("quote/<str:code>/", views.quote, name="quote"),
    path("kline/<str:code>/", views.kline, name="kline"),
]
