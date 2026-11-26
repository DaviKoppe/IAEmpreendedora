"""Rotas do aplicativo de formulários."""
from django.urls import path
from . import views

urlpatterns = [
    path("status/", views.status, name="status"),
    path("questionario/", views.enviar_questionario, name="enviar_questionario"),
]
