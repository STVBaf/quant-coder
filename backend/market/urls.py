from django.urls import path

from . import views

urlpatterns = [
    path("overview/", views.overview_data, name="overview"),
    path("kline/<str:code>/", views.kline, name="kline"),
]
