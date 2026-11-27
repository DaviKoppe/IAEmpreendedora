"""Django Admin somente para consulta das respostas do questionário.

O admin exige login de um usuário da equipe. Nenhum registro pode ser
incluído, alterado ou excluído por aqui: as respostas entram apenas pela
API, já validadas.
"""
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import (
    CAMPOS_ESCOLHA_UNICA,
    BeneficioResposta,
    RespostaQuestionario,
)


class SomenteLeituraMixin:
    """Remove as permissões de inclusão, alteração e exclusão."""

    def has_add_permission(
        self,
        request: HttpRequest,
        obj: RespostaQuestionario | None = None,
    ) -> bool:
        return False

    def has_change_permission(
        self,
        request: HttpRequest,
        obj: RespostaQuestionario | None = None,
    ) -> bool:
        return False

    def has_delete_permission(
        self,
        request: HttpRequest,
        obj: RespostaQuestionario | None = None,
    ) -> bool:
        return False


class BeneficioRespostaInline(SomenteLeituraMixin, admin.TabularInline):
    """Benefícios selecionados, exibidos dentro da resposta."""

    model = BeneficioResposta
    fields = ("beneficio",)
    extra = 0


@admin.register(RespostaQuestionario)
class RespostaQuestionarioAdmin(SomenteLeituraMixin, admin.ModelAdmin):
    """Lista e detalhe das respostas, com filtros por alternativa e data."""

    list_display = (
        "id",
        "criado_em",
        "faixa_etaria",
        "interesse_ia",
        "listar_beneficios",
        "possui_feedback",
    )
    list_filter = (
        "criado_em",
        *CAMPOS_ESCOLHA_UNICA,
        "beneficios__beneficio",
    )
    date_hierarchy = "criado_em"
    ordering = ("-criado_em",)
    fields = (
        "criado_em",
        *CAMPOS_ESCOLHA_UNICA,
        "feedback",
    )
    inlines = [BeneficioRespostaInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Carrega os benefícios junto para evitar uma consulta por linha."""
        return super().get_queryset(request).prefetch_related("beneficios")

    @admin.display(description="benefícios")
    def listar_beneficios(self, obj: RespostaQuestionario) -> str:
        """Lista os benefícios da resposta separados por vírgula."""
        return ", ".join(
            beneficio.beneficio for beneficio in obj.beneficios.all()
        )

    @admin.display(description="tem feedback", boolean=True)
    def possui_feedback(self, obj: RespostaQuestionario) -> bool:
        """Indica se a resposta tem feedback, sem exibi-lo na listagem."""
        return bool(obj.feedback.strip())
