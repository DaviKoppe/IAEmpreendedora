"""Visões HTTP do aplicativo de formulários."""
import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .persistencia import salvar_respostas
from .validators import validar_respostas


def status(request):
    """Informa que a API está disponível."""
    return JsonResponse({"status": "ok", "mensagem": "API do IAEmpreendedora funcionando."})


@require_POST
def enviar_questionario(request):
    """Valida as respostas enviadas pelo formulário e as armazena no banco."""
    try:
        dados = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"status": "erro", "mensagem": "O corpo da requisição deve conter um JSON válido."},
            status=400,
        )

    erros = validar_respostas(dados)
    if erros:
        return JsonResponse(
            {"status": "erro", "mensagem": "Existem respostas inválidas.", "erros": erros},
            status=400,
        )

    salvar_respostas(dados)

    return JsonResponse(
        {
            "status": "ok",
            "mensagem": "Respostas validadas com sucesso.",
        },
        status=201,
    )
