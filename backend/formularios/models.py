"""Modelos de dados das respostas do questionário.

As alternativas aceitas vêm do dicionário OPCOES de validators.py, que é a
fonte única de verdade. Elas são usadas tanto nos choices dos campos quanto
nas restrições CHECK do banco, que valem para qualquer forma de gravação
(API, shell do Django ou scripts). O Django Admin é somente leitura.
"""
from django.db import models
from django.db.models import Q
from django.db.models.functions import Length
from django.db.models.lookups import LessThanOrEqual

from .validators import OPCOES

TAMANHO_ALTERNATIVA = 50
# Mesmo limite aplicado por validar_respostas em validators.py.
TAMANHO_MAXIMO_FEEDBACK = 1000

CAMPO_BENEFICIOS = "beneficios_ia"
# Campos de escolha única, na mesma ordem de OPCOES. O campo de múltipla
# escolha (beneficios_ia) é gravado na tabela BeneficioResposta.
CAMPOS_ESCOLHA_UNICA = tuple(
    campo for campo in OPCOES if campo != CAMPO_BENEFICIOS
)


def gerar_choices(campo: str) -> list[tuple[str, str]]:
    """Gera os choices de um campo a partir das alternativas de OPCOES."""
    return [(opcao, opcao) for opcao in OPCOES[campo]]


def criar_campo_alternativa(campo: str, rotulo: str) -> models.CharField:
    """Cria um campo de texto que aceita apenas as alternativas de OPCOES."""
    return models.CharField(
        rotulo,
        max_length=TAMANHO_ALTERNATIVA,
        choices=gerar_choices(campo),
    )


def criar_restricao_alternativa(
    campo: str,
    nome_campo: str | None = None,
) -> models.CheckConstraint:
    """Cria a restrição CHECK que limita a coluna às alternativas válidas.

    Args:
        campo: Chave de OPCOES com as alternativas aceitas.
        nome_campo: Nome da coluna no modelo, quando for diferente da
            chave de OPCOES.

    Returns:
        A restrição, com nome único no banco de dados.
    """
    nome_campo = nome_campo or campo
    return models.CheckConstraint(
        condition=Q(**{f"{nome_campo}__in": OPCOES[campo]}),
        name=f"formularios_{nome_campo}_valido",
    )


class RespostaQuestionario(models.Model):
    """Um questionário enviado, com as respostas de escolha única."""

    faixa_etaria = criar_campo_alternativa("faixa_etaria", "faixa etária")
    conhecimento_financeiro = criar_campo_alternativa(
        "conhecimento_financeiro",
        "conhecimento financeiro",
    )
    ferramenta_financeira = criar_campo_alternativa(
        "ferramenta_financeira",
        "ferramenta financeira",
    )
    uso_ia = criar_campo_alternativa("uso_ia", "uso de IA")
    uso_ia_financas = criar_campo_alternativa(
        "uso_ia_financas",
        "uso de IA nas finanças",
    )
    confianca_ia = criar_campo_alternativa("confianca_ia", "confiança na IA")
    interesse_ia = criar_campo_alternativa("interesse_ia", "interesse na IA")
    feedback = models.TextField("feedback", blank=True, default="")
    criado_em = models.DateTimeField(
        "enviado em",
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        verbose_name = "resposta do questionário"
        verbose_name_plural = "respostas do questionário"
        constraints = [
            *(
                criar_restricao_alternativa(campo)
                for campo in CAMPOS_ESCOLHA_UNICA
            ),
            # O SQLite não aplica limite de tamanho em colunas de texto.
            models.CheckConstraint(
                condition=LessThanOrEqual(
                    Length("feedback"),
                    TAMANHO_MAXIMO_FEEDBACK,
                ),
                name="formularios_feedback_tamanho_maximo",
            ),
        ]

    def __str__(self) -> str:
        return f"Resposta nº {self.pk}"


class BeneficioResposta(models.Model):
    """Um benefício selecionado em uma resposta (campo beneficios_ia)."""

    resposta = models.ForeignKey(
        RespostaQuestionario,
        on_delete=models.CASCADE,
        related_name="beneficios",
        verbose_name="resposta",
    )
    beneficio = criar_campo_alternativa(CAMPO_BENEFICIOS, "benefício")

    class Meta:
        verbose_name = "benefício da resposta"
        verbose_name_plural = "benefícios da resposta"
        constraints = [
            models.UniqueConstraint(
                fields=["resposta", "beneficio"],
                name="formularios_beneficio_unico_por_resposta",
            ),
            criar_restricao_alternativa(CAMPO_BENEFICIOS, "beneficio"),
        ]

    def __str__(self) -> str:
        return self.beneficio
