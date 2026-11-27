"""Testes da persistência das respostas do questionário (R4).

Todos os dados são fictícios e ficam apenas no banco temporário de testes,
que o Django cria e apaga a cada execução.
"""
import json
from io import StringIO
from typing import Any
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.http import HttpResponse
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from .models import (
    CAMPOS_ESCOLHA_UNICA,
    TAMANHO_MAXIMO_FEEDBACK,
    BeneficioResposta,
    RespostaQuestionario,
)
from .persistencia import salvar_respostas
from .validators import OPCOES

TABELA_RESPOSTAS = RespostaQuestionario._meta.db_table
TABELA_BENEFICIOS = BeneficioResposta._meta.db_table


def gerar_respostas_validas() -> dict[str, Any]:
    """Retorna um questionário fictício válido, no formato da API."""
    return {
        "faixa_etaria": "25 a 34 anos",
        "conhecimento_financeiro": "Alto",
        "ferramenta_financeira": "Anotações ou caderno",
        "uso_ia": "Já testei, mas quase não utilizo",
        "uso_ia_financas": "Organizar gastos",
        "beneficios_ia": [
            "Identificação de desperdícios",
            "Educação financeira",
        ],
        "confianca_ia": "Pouca confiança",
        "interesse_ia": "Talvez",
        "feedback": "Texto fictício de teste.",
    }


def gerar_campos_resposta() -> dict[str, str]:
    """Retorna só os campos da tabela de respostas, para uso direto no ORM."""
    dados = gerar_respostas_validas()
    return {campo: dados[campo] for campo in CAMPOS_ESCOLHA_UNICA}


class PersistenciaApiTests(TestCase):
    """Gravação pelo endpoint POST /api/questionario/."""

    def setUp(self) -> None:
        self.url = reverse("enviar_questionario")

    def enviar(self, dados: Any) -> HttpResponse:
        return self.client.post(
            self.url,
            data=json.dumps(dados),
            content_type="application/json",
        )

    def assert_nada_gravado(self) -> None:
        self.assertEqual(RespostaQuestionario.objects.count(), 0)
        self.assertEqual(BeneficioResposta.objects.count(), 0)

    def test_resposta_valida_e_gravada_com_todos_os_campos(self) -> None:
        dados = gerar_respostas_validas()

        resposta_http = self.enviar(dados)

        self.assertEqual(resposta_http.status_code, 201)
        resposta = RespostaQuestionario.objects.get()
        for campo in CAMPOS_ESCOLHA_UNICA:
            self.assertEqual(getattr(resposta, campo), dados[campo])
        self.assertEqual(resposta.feedback, dados["feedback"])
        self.assertIsNotNone(resposta.criado_em)
        self.assertCountEqual(
            resposta.beneficios.values_list("beneficio", flat=True),
            dados["beneficios_ia"],
        )

    def test_contrato_da_resposta_http_e_preservado(self) -> None:
        resposta_http = self.enviar(gerar_respostas_validas())

        self.assertEqual(resposta_http.status_code, 201)
        self.assertEqual(
            resposta_http.json(),
            {"status": "ok", "mensagem": "Respostas validadas com sucesso."},
        )

    def test_resposta_sem_feedback_grava_texto_vazio(self) -> None:
        dados = gerar_respostas_validas()
        del dados["feedback"]

        resposta_http = self.enviar(dados)

        self.assertEqual(resposta_http.status_code, 201)
        self.assertEqual(RespostaQuestionario.objects.get().feedback, "")

    def test_feedback_vazio_e_gravado(self) -> None:
        dados = gerar_respostas_validas()
        dados["feedback"] = ""

        self.assertEqual(self.enviar(dados).status_code, 201)
        self.assertEqual(RespostaQuestionario.objects.get().feedback, "")

    def test_feedback_no_limite_e_gravado(self) -> None:
        dados = gerar_respostas_validas()
        dados["feedback"] = "á" * TAMANHO_MAXIMO_FEEDBACK

        self.assertEqual(self.enviar(dados).status_code, 201)
        self.assertEqual(
            len(RespostaQuestionario.objects.get().feedback),
            TAMANHO_MAXIMO_FEEDBACK,
        )

    def test_todos_os_beneficios_validos_sao_gravados(self) -> None:
        dados = gerar_respostas_validas()
        beneficios = [
            beneficio
            for beneficio in OPCOES["beneficios_ia"]
            if beneficio != "Não vejo benefícios"
        ]
        dados["beneficios_ia"] = beneficios

        self.assertEqual(self.enviar(dados).status_code, 201)
        self.assertCountEqual(
            BeneficioResposta.objects.values_list("beneficio", flat=True),
            beneficios,
        )

    def test_opcao_nao_vejo_beneficios_e_gravada(self) -> None:
        dados = gerar_respostas_validas()
        dados["beneficios_ia"] = ["Não vejo benefícios"]

        self.assertEqual(self.enviar(dados).status_code, 201)
        self.assertEqual(
            BeneficioResposta.objects.get().beneficio,
            "Não vejo benefícios",
        )

    def test_cada_envio_gera_um_registro(self) -> None:
        self.enviar(gerar_respostas_validas())
        self.enviar(gerar_respostas_validas())

        self.assertEqual(RespostaQuestionario.objects.count(), 2)
        self.assertEqual(BeneficioResposta.objects.count(), 4)

    def test_nenhuma_resposta_fica_sem_os_beneficios_enviados(self) -> None:
        listas_de_beneficios = [
            ["Não vejo benefícios"],
            ["Educação financeira"],
            OPCOES["beneficios_ia"][:5],
        ]
        for beneficios in listas_de_beneficios:
            dados = gerar_respostas_validas()
            dados["beneficios_ia"] = beneficios
            self.enviar(dados)
        invalido = gerar_respostas_validas()
        invalido["beneficios_ia"] = []
        self.enviar(invalido)

        self.assertFalse(
            RespostaQuestionario.objects.filter(
                beneficios__isnull=True
            ).exists()
        )
        gravados = [
            sorted(resposta.beneficios.values_list("beneficio", flat=True))
            for resposta in RespostaQuestionario.objects.order_by("id")
        ]
        self.assertEqual(
            gravados,
            [sorted(beneficios) for beneficios in listas_de_beneficios],
        )

    def test_respostas_invalidas_nao_sao_gravadas(self) -> None:
        sem_campo = gerar_respostas_validas()
        del sem_campo["interesse_ia"]
        opcao_invalida = gerar_respostas_validas()
        opcao_invalida["uso_ia"] = "Todo dia"
        beneficio_repetido = gerar_respostas_validas()
        beneficio_repetido["beneficios_ia"] = [
            "Educação financeira",
            "Educação financeira",
        ]
        combinacao_proibida = gerar_respostas_validas()
        combinacao_proibida["beneficios_ia"] = [
            "Não vejo benefícios",
            "Educação financeira",
        ]
        sem_beneficios = gerar_respostas_validas()
        sem_beneficios["beneficios_ia"] = []
        feedback_longo = gerar_respostas_validas()
        feedback_longo["feedback"] = "a" * (TAMANHO_MAXIMO_FEEDBACK + 1)

        casos = {
            "campo ausente": sem_campo,
            "opção inválida": opcao_invalida,
            "benefício repetido": beneficio_repetido,
            "combinação proibida": combinacao_proibida,
            "sem benefícios": sem_beneficios,
            "feedback acima do limite": feedback_longo,
            "corpo que não é objeto": ["lista", "em", "vez", "de", "objeto"],
        }
        for descricao, dados in casos.items():
            with self.subTest(descricao):
                self.assertEqual(self.enviar(dados).status_code, 400)
                self.assert_nada_gravado()

    def test_json_malformado_nao_grava(self) -> None:
        resposta_http = self.client.post(
            self.url,
            data="{json quebrado",
            content_type="application/json",
        )

        self.assertEqual(resposta_http.status_code, 400)
        self.assert_nada_gravado()


class GravacaoAtomicaTests(TestCase):
    """Rollback de salvar_respostas quando a gravação dos benefícios falha."""

    def test_beneficio_duplicado_desfaz_a_resposta(self) -> None:
        dados = gerar_respostas_validas()
        dados["beneficios_ia"] = ["Educação financeira", "Educação financeira"]

        with self.assertRaises(IntegrityError):
            salvar_respostas(dados)

        self.assertEqual(RespostaQuestionario.objects.count(), 0)
        self.assertEqual(BeneficioResposta.objects.count(), 0)

    def test_beneficio_invalido_desfaz_a_resposta(self) -> None:
        dados = gerar_respostas_validas()
        dados["beneficios_ia"] = ["Educação financeira", "Benefício inventado"]

        with self.assertRaises(IntegrityError):
            salvar_respostas(dados)

        self.assertEqual(RespostaQuestionario.objects.count(), 0)
        self.assertEqual(BeneficioResposta.objects.count(), 0)

    def test_falha_inesperada_nos_beneficios_desfaz_a_resposta(self) -> None:
        with mock.patch.object(
            BeneficioResposta.objects,
            "bulk_create",
            side_effect=RuntimeError("falha simulada"),
        ):
            with self.assertRaises(RuntimeError):
                salvar_respostas(gerar_respostas_validas())

        self.assertEqual(RespostaQuestionario.objects.count(), 0)


class RestricoesBancoTests(TestCase):
    """Restrições do banco testadas diretamente pelo ORM, sem a API."""

    def criar_resposta(self, **alteracoes: str) -> RespostaQuestionario:
        return RespostaQuestionario.objects.create(
            **{**gerar_campos_resposta(), **alteracoes}
        )

    def test_todas_as_alternativas_do_validador_sao_aceitas(self) -> None:
        for campo in CAMPOS_ESCOLHA_UNICA:
            for opcao in OPCOES[campo]:
                with self.subTest(campo=campo, opcao=opcao):
                    self.criar_resposta(**{campo: opcao})

        resposta = self.criar_resposta()
        for beneficio in OPCOES["beneficios_ia"]:
            with self.subTest(beneficio=beneficio):
                BeneficioResposta.objects.create(
                    resposta=resposta,
                    beneficio=beneficio,
                )

    def test_alternativa_invalida_e_recusada_pelo_banco(self) -> None:
        for campo in CAMPOS_ESCOLHA_UNICA:
            for valor in ("Valor inventado", "", OPCOES[campo][0].upper()):
                with self.subTest(campo=campo, valor=valor):
                    with self.assertRaises(IntegrityError):
                        with transaction.atomic():
                            self.criar_resposta(**{campo: valor})

        self.assertEqual(RespostaQuestionario.objects.count(), 0)

    def test_valor_nulo_e_recusado_pelo_banco(self) -> None:
        for campo in (*CAMPOS_ESCOLHA_UNICA, "feedback"):
            with self.subTest(campo=campo):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        self.criar_resposta(**{campo: None})

        resposta = self.criar_resposta()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BeneficioResposta.objects.create(
                    resposta=resposta,
                    beneficio=None,
                )
        self.assertEqual(RespostaQuestionario.objects.count(), 1)
        self.assertEqual(BeneficioResposta.objects.count(), 0)

    def test_feedback_acima_do_limite_e_recusado_pelo_banco(self) -> None:
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.criar_resposta(
                    feedback="a" * (TAMANHO_MAXIMO_FEEDBACK + 1)
                )

        self.criar_resposta(feedback="a" * TAMANHO_MAXIMO_FEEDBACK)
        self.assertEqual(RespostaQuestionario.objects.count(), 1)

    def test_beneficio_invalido_e_recusado_pelo_banco(self) -> None:
        resposta = self.criar_resposta()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BeneficioResposta.objects.create(
                    resposta=resposta,
                    beneficio="Benefício inventado",
                )

    def test_beneficio_duplicado_e_recusado_pelo_banco(self) -> None:
        resposta = self.criar_resposta()
        BeneficioResposta.objects.create(
            resposta=resposta,
            beneficio="Educação financeira",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BeneficioResposta.objects.create(
                    resposta=resposta,
                    beneficio="Educação financeira",
                )

        self.assertEqual(resposta.beneficios.count(), 1)

    def test_mesmo_beneficio_em_respostas_diferentes_e_permitido(self) -> None:
        for resposta in (self.criar_resposta(), self.criar_resposta()):
            BeneficioResposta.objects.create(
                resposta=resposta,
                beneficio="Educação financeira",
            )

        self.assertEqual(BeneficioResposta.objects.count(), 2)

    def test_exclusao_pelo_orm_remove_os_beneficios(self) -> None:
        resposta = salvar_respostas(gerar_respostas_validas())
        outra = salvar_respostas(gerar_respostas_validas())

        resposta.delete()

        self.assertFalse(
            BeneficioResposta.objects.filter(resposta_id=resposta.pk).exists()
        )
        self.assertEqual(outra.beneficios.count(), 2)


class IntegridadeReferencialTests(TransactionTestCase):
    """Chave estrangeira verificada pelo SQLite, com commit real."""

    def test_beneficio_sem_resposta_existente_e_recusado(self) -> None:
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BeneficioResposta.objects.create(
                    resposta_id=999_999,
                    beneficio="Educação financeira",
                )

        self.assertEqual(BeneficioResposta.objects.count(), 0)

    def test_exclusao_por_sql_direto_e_bloqueada(self) -> None:
        # A FK no banco não tem ON DELETE CASCADE: a cascata é feita pelo
        # Django ORM. Um DELETE em SQL puro é recusado pelo SQLite.
        resposta = salvar_respostas(gerar_respostas_validas())

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        f'DELETE FROM "{TABELA_RESPOSTAS}" WHERE id = %s',
                        [resposta.pk],
                    )

        self.assertTrue(
            RespostaQuestionario.objects.filter(pk=resposta.pk).exists()
        )
        self.assertEqual(resposta.beneficios.count(), 2)


class EstruturaBancoTests(TestCase):
    """Tabelas, restrições e migrations do banco."""

    def test_tabelas_foram_criadas(self) -> None:
        tabelas = connection.introspection.table_names()

        self.assertIn(TABELA_RESPOSTAS, tabelas)
        self.assertIn(TABELA_BENEFICIOS, tabelas)

    def test_restricoes_existem_no_banco(self) -> None:
        with connection.cursor() as cursor:
            restricoes_respostas = connection.introspection.get_constraints(
                cursor,
                TABELA_RESPOSTAS,
            )
            restricoes_beneficios = connection.introspection.get_constraints(
                cursor,
                TABELA_BENEFICIOS,
            )

        for campo in CAMPOS_ESCOLHA_UNICA:
            self.assertIn(f"formularios_{campo}_valido", restricoes_respostas)
        self.assertIn(
            "formularios_feedback_tamanho_maximo",
            restricoes_respostas,
        )
        self.assertIn("formularios_beneficio_valido", restricoes_beneficios)
        unica = restricoes_beneficios[
            "formularios_beneficio_unico_por_resposta"
        ]
        self.assertTrue(unica["unique"])
        self.assertEqual(unica["columns"], ["resposta_id", "beneficio"])
        chaves_estrangeiras = [
            restricao
            for restricao in restricoes_beneficios.values()
            if restricao["foreign_key"]
        ]
        self.assertEqual(
            chaves_estrangeiras[0]["foreign_key"],
            (TABELA_RESPOSTAS, "id"),
        )

    def test_nao_ha_migrations_pendentes(self) -> None:
        saida = StringIO()

        call_command(
            "makemigrations",
            "--check",
            "--dry-run",
            stdout=saida,
        )

        self.assertIn("No changes detected", saida.getvalue())


class AdminSomenteLeituraTests(TestCase):
    """Django Admin permite consultar, mas não incluir, alterar ou excluir."""

    def setUp(self) -> None:
        self.resposta = salvar_respostas(gerar_respostas_validas())
        administrador = get_user_model().objects.create_superuser(
            username="admin_ficticio",
            password="senha-ficticia-de-teste",
        )
        self.client.force_login(administrador)

    def test_listagem_e_detalhe_estao_disponiveis(self) -> None:
        listagem = self.client.get(
            reverse("admin:formularios_respostaquestionario_changelist")
        )
        detalhe = self.client.get(
            reverse(
                "admin:formularios_respostaquestionario_change",
                args=[self.resposta.pk],
            )
        )

        self.assertEqual(listagem.status_code, 200)
        self.assertEqual(detalhe.status_code, 200)
        self.assertContains(detalhe, "Educação financeira")
        self.assertContains(detalhe, "Texto fictício de teste.")

    def test_inclusao_alteracao_e_exclusao_sao_bloqueadas(self) -> None:
        url_detalhe = reverse(
            "admin:formularios_respostaquestionario_change",
            args=[self.resposta.pk],
        )
        inclusao = self.client.get(
            reverse("admin:formularios_respostaquestionario_add")
        )
        alteracao = self.client.post(url_detalhe, {"interesse_ia": "Não"})
        exclusao = self.client.post(
            reverse(
                "admin:formularios_respostaquestionario_delete",
                args=[self.resposta.pk],
            ),
            {"post": "yes"},
        )

        self.assertEqual(inclusao.status_code, 403)
        self.assertEqual(alteracao.status_code, 403)
        self.assertEqual(exclusao.status_code, 403)
        self.resposta.refresh_from_db()
        self.assertEqual(self.resposta.interesse_ia, "Talvez")

    def test_usuario_sem_permissao_nao_consulta_respostas(self) -> None:
        url = reverse("admin:formularios_respostaquestionario_changelist")
        modelo_usuario = get_user_model()
        visitante = modelo_usuario.objects.create_user(
            username="visitante_ficticio",
            password="senha-ficticia-de-teste",
        )
        equipe_sem_permissao = modelo_usuario.objects.create_user(
            username="equipe_ficticia",
            password="senha-ficticia-de-teste",
            is_staff=True,
        )

        self.client.force_login(visitante)
        resposta_visitante = self.client.get(url)
        self.client.force_login(equipe_sem_permissao)
        resposta_equipe = self.client.get(url)

        self.assertEqual(resposta_visitante.status_code, 302)
        self.assertIn(reverse("admin:login"), resposta_visitante["Location"])
        self.assertEqual(resposta_equipe.status_code, 403)

    def test_admin_exige_login(self) -> None:
        self.client.logout()

        resposta_http = self.client.get(
            reverse("admin:formularios_respostaquestionario_changelist")
        )

        self.assertEqual(resposta_http.status_code, 302)
        self.assertIn(reverse("admin:login"), resposta_http["Location"])
