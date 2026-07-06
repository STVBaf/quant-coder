from django.urls import path

from . import views

urlpatterns = [
    path("chat/", views.chat, name="chat"),
    path("research/", views.research_create, name="research_create"),
    path("research/<int:task_id>/", views.research_detail, name="research_detail"),
]
