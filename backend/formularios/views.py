"""Visões HTTP do aplicativo de formulários."""
from django.http import JsonResponse


def status(request):
    """Informa que a API está disponível."""
    return JsonResponse({"status": "ok", "mensagem": "API do IAEmpreendedora funcionando."})
