from django.urls import path

from . import views

urlpatterns = [
    path("strategies/", views.strategies, name="strategies"),
    path("run/", views.run, name="run"),
]
