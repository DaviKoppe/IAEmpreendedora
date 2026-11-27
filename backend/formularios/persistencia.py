"""Gravação das respostas do questionário no banco de dados."""
from typing import Any

from django.db import transaction

from .models import (
    CAMPO_BENEFICIOS,
    CAMPOS_ESCOLHA_UNICA,
    BeneficioResposta,
    RespostaQuestionario,
)


@transaction.atomic
def salvar_respostas(dados: dict[str, Any]) -> RespostaQuestionario:
    """Grava uma resposta do questionário e os benefícios selecionados.

    A gravação é atômica: se qualquer benefício falhar, a resposta também
    é desfeita e nada fica salvo. Deve receber apenas dados já aprovados
    por validar_respostas; as restrições do banco são a última barreira.

    Args:
        dados: Respostas do questionário no formato do contrato da API.

    Returns:
        A resposta gravada.

    Raises:
        django.db.IntegrityError: Se algum valor violar as restrições do
            banco (alternativa inválida, benefício repetido etc.).
    """
    resposta = RespostaQuestionario.objects.create(
        **{campo: dados[campo] for campo in CAMPOS_ESCOLHA_UNICA},
        feedback=dados.get("feedback", ""),
    )
    BeneficioResposta.objects.bulk_create(
        [
            BeneficioResposta(resposta=resposta, beneficio=beneficio)
            for beneficio in dados[CAMPO_BENEFICIOS]
        ]
    )
    return resposta
