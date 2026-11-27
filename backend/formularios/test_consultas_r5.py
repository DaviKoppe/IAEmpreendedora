"""Testes das consultas documentadas para o R5 em BANCO_DE_DADOS.md.

Os blocos de código da seção "Orientações para o R5" são extraídos do
próprio documento e executados sobre dados fictícios, no banco temporário
de testes. Os resultados são comparados com um cálculo independente feito
em Python puro. Se a documentação mudar e deixar de funcionar, estes testes
falham.
"""
import json
import re
import sqlite3
import textwrap
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib import admin
from django.db import connection
from django.test import TestCase

from .admin import RespostaQuestionarioAdmin
from .models import CAMPOS_ESCOLHA_UNICA, RespostaQuestionario
from .persistencia import salvar_respostas
from .validators import OPCOES, validar_respostas

CAMINHO_DOCUMENTO = settings.BASE_DIR / "BANCO_DE_DADOS.md"
FUSO_LOCAL = ZoneInfo("America/Sao_Paulo")

# Número de cada consulta SQL do documento -> coluna de escolha única.
CONSULTAS_ESCOLHA_UNICA = {
    "2": "faixa_etaria",
    "3": "conhecimento_financeiro",
    "4": "ferramenta_financeira",
    "5": "uso_ia",
    "6": "uso_ia_financas",
    "8": "confianca_ia",
    "9": "interesse_ia",
}

# "Educação financeira" nunca é escolhida, para testar alternativas com 0.
PADROES_BENEFICIOS = [
    ["Organização de gastos"],
    ["Organização de gastos", "Planejamento financeiro"],
    ["Identificação de desperdícios", "Auxílio na tomada de decisões"],
    ["Não vejo benefícios"],
    [
        "Planejamento financeiro",
        "Identificação de desperdícios",
        "Auxílio na tomada de decisões",
    ],
    ["Auxílio na tomada de decisões"],
    ["Organização de gastos", "Auxílio na tomada de decisões"],
]
FEEDBACKS = [
    "",
    "   ",
    "\n\t ",
    " ",
    "　 ",
    "Conteúdo útil.",
    "  Gostei bastante  ",
    "Ótima iniciativa!\n",
    "\r\n",
]
# Horários em UTC. 01:30 UTC ainda é o dia anterior em Brasília (22:30).
HORARIOS_UTC = [
    datetime(2026, 10, 30, 15, 0, tzinfo=timezone.utc),
    datetime(2026, 10, 31, 23, 59, tzinfo=timezone.utc),
    datetime(2026, 11, 1, 1, 30, tzinfo=timezone.utc),
    datetime(2026, 11, 1, 2, 59, 59, 500000, tzinfo=timezone.utc),
    datetime(2026, 11, 1, 3, 0, tzinfo=timezone.utc),
    datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc),
    datetime(2026, 11, 3, 2, 0, tzinfo=timezone.utc),
]
TOTAL_QUESTIONARIOS = 30


def extrair_secao_r5() -> str:
    """Retorna o texto da seção de orientações para o R5."""
    texto = CAMINHO_DOCUMENTO.read_text(encoding="utf-8")
    return texto.split("## Orientações para o R5")[1].split("\n## ")[0]


def extrair_blocos(linguagem: str) -> list[str]:
    """Extrai os blocos de código de uma linguagem, sem a indentação."""
    return [
        textwrap.dedent(bloco)
        for bloco in re.findall(
            rf"```{linguagem}\n(.*?)```",
            extrair_secao_r5(),
            re.S,
        )
    ]


SECAO_R5 = extrair_secao_r5()
BLOCOS_PYTHON = extrair_blocos("python")
BLOCOS_SQL = {
    re.match(r"-- (\w+)\.", bloco).group(1): bloco
    for bloco in extrair_blocos("sql")
}


def gerar_questionarios() -> list[dict[str, Any]]:
    """Gera questionários fictícios determinísticos, já validados."""
    questionarios = []
    for i in range(TOTAL_QUESTIONARIOS):
        dados: dict[str, Any] = {
            # A última alternativa de cada campo nunca é escolhida.
            campo: OPCOES[campo][(i * 7 + posicao) % (len(OPCOES[campo]) - 1)]
            for posicao, campo in enumerate(CAMPOS_ESCOLHA_UNICA)
        }
        dados["beneficios_ia"] = PADROES_BENEFICIOS[
            i % len(PADROES_BENEFICIOS)
        ]
        dados["feedback"] = FEEDBACKS[i % len(FEEDBACKS)]
        dados["criado_em"] = HORARIOS_UTC[i % len(HORARIOS_UTC)] + timedelta(
            seconds=i
        )
        questionarios.append(dados)
    return questionarios


def gravar(questionarios: list[dict[str, Any]]) -> None:
    """Grava os questionários pela mesma função usada pela API."""
    for dados in questionarios:
        respostas_api = {k: v for k, v in dados.items() if k != "criado_em"}
        assert validar_respostas(respostas_api) == {}, respostas_api
        resposta = salvar_respostas(respostas_api)
        RespostaQuestionario.objects.filter(pk=resposta.pk).update(
            criado_em=dados["criado_em"]
        )


def calcular_esperado(
    questionarios: list[dict[str, Any]],
    inicio: date | None,
    fim: date | None,
) -> dict[str, Any]:
    """Calcula os indicadores em Python puro, sem usar o banco."""

    def data_local(dados: dict[str, Any]) -> date:
        return dados["criado_em"].astimezone(FUSO_LOCAL).date()

    selecionados = [
        dados
        for dados in questionarios
        if (inicio is None or data_local(dados) >= inicio)
        and (fim is None or data_local(dados) <= fim)
    ]
    total = len(selecionados)
    esperado: dict[str, Any] = {"1": total}
    for chave, campo in CONSULTAS_ESCOLHA_UNICA.items():
        contagem = Counter(dados[campo] for dados in selecionados)
        esperado[chave] = [(a, contagem[a]) for a in OPCOES[campo]]
    contagem = Counter(
        beneficio
        for dados in selecionados
        for beneficio in set(dados["beneficios_ia"])
    )
    esperado["7"] = [(a, contagem[a]) for a in OPCOES["beneficios_ia"]]
    esperado["10"] = sum(
        1 for dados in selecionados if dados["feedback"].strip()
    )
    esperado["11a"] = sorted(Counter(map(data_local, selecionados)).items())
    esperado["11b"] = sorted(
        Counter(
            data_local(dados).strftime("%Y-%m") for dados in selecionados
        ).items()
    )
    return esperado


def executar_sql(
    chave: str,
    inicio: date | None = None,
    fim: date | None = None,
) -> list[dict[str, Any]]:
    """Executa uma consulta SQL do documento com o módulo sqlite3."""
    connection.ensure_connection()
    cursor = connection.connection.execute(
        BLOCOS_SQL[chave],
        {
            "inicio": inicio.isoformat() if inicio else None,
            "fim": fim.isoformat() if fim else None,
        },
    )
    colunas = [descricao[0] for descricao in cursor.description]
    return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]


class ConsultasR5Tests(TestCase):
    def setUp(self) -> None:
        # Cada teste recebe um namespace novo com as funções do documento.
        self.ns: dict[str, Any] = {}
        exec(self.bloco_python("def filtrar_periodo"), self.ns)

    def bloco_python(self, trecho: str) -> str:
        """Retorna o único bloco Python do documento que contém o trecho."""
        encontrados = [b for b in BLOCOS_PYTHON if trecho in b]
        self.assertEqual(len(encontrados), 1, trecho)
        return encontrados[0]

    def assert_percentual(
        self,
        obtido: float,
        quantidade: int,
        total: int,
    ) -> None:
        """Aceita qualquer arredondamento correto para uma casa decimal."""
        exato = 100 * quantidade / total if total else 0.0
        self.assertLessEqual(abs(obtido - exato), 0.05 + 1e-9)

    def assert_indicadores(
        self,
        questionarios: list[dict[str, Any]],
        inicio: date | None = None,
        fim: date | None = None,
    ) -> None:
        """Compara ORM e SQL do documento com o cálculo independente."""
        esperado = calcular_esperado(questionarios, inicio, fim)
        total = esperado["1"]
        respostas = self.ns["filtrar_periodo"](inicio, fim)

        self.assertEqual(respostas.count(), total)
        self.assertEqual(
            executar_sql("1", inicio, fim),
            [{"total_questionarios": total}],
        )

        for chave, campo in CONSULTAS_ESCOLHA_UNICA.items():
            with self.subTest(indicador=chave, campo=campo):
                orm = self.ns["distribuir_escolha_unica"](respostas, campo)
                sql = executar_sql(chave, inicio, fim)
                for linhas in (orm, sql):
                    self.assertEqual(
                        [(d["alternativa"], d["quantidade"]) for d in linhas],
                        esperado[chave],
                    )
                    for d in linhas:
                        self.assert_percentual(
                            d["percentual"],
                            d["quantidade"],
                            total,
                        )

        with self.subTest(indicador="7"):
            orm = self.ns["distribuir_beneficios"](respostas)
            sql = executar_sql("7", inicio, fim)
            for linhas in (orm, sql):
                self.assertEqual(
                    [(d["alternativa"], d["questionarios"]) for d in linhas],
                    esperado["7"],
                )
                for d in linhas:
                    self.assert_percentual(
                        d["percentual"],
                        d["questionarios"],
                        total,
                    )

        with self.subTest(indicador="10"):
            self.assertEqual(
                self.ns["contar_feedbacks"](respostas),
                esperado["10"],
            )
            self.assertEqual(
                executar_sql("10", inicio, fim),
                [{"feedbacks": esperado["10"]}],
            )

        with self.subTest(indicador="11"):
            diario = self.ns["evoluir_respostas"](respostas)
            mensal = self.ns["evoluir_respostas"](
                respostas,
                self.ns["TruncMonth"],
            )
            self.assertEqual(
                [(d["periodo"], d["quantidade"]) for d in diario],
                esperado["11a"],
            )
            self.assertEqual(
                [
                    (d["periodo"].strftime("%Y-%m"), d["quantidade"])
                    for d in mensal
                ],
                esperado["11b"],
            )
            self.assertEqual(
                [
                    (date.fromisoformat(d["dia"]), d["quantidade"])
                    for d in executar_sql("11a", inicio, fim)
                ],
                esperado["11a"],
            )
            self.assertEqual(
                [
                    (d["mes"], d["quantidade"])
                    for d in executar_sql("11b", inicio, fim)
                ],
                esperado["11b"],
            )

    def test_documento_contem_todas_as_consultas(self) -> None:
        consultas = ["1", *map(str, range(2, 11)), "11a", "11b"]

        self.assertEqual(sorted(BLOCOS_SQL), sorted(consultas))
        self.assertEqual(len(BLOCOS_PYTHON), 4)

    def test_alternativas_do_sql_coincidem_com_opcoes(self) -> None:
        consultas = {**CONSULTAS_ESCOLHA_UNICA, "7": "beneficios_ia"}
        for chave, campo in consultas.items():
            with self.subTest(indicador=chave):
                self.assertEqual(
                    [d["alternativa"] for d in executar_sql(chave)],
                    OPCOES[campo],
                )

    def test_banco_vazio_nao_divide_por_zero(self) -> None:
        self.assert_indicadores([])

        exec(self.bloco_python("indicadores = {"), self.ns)
        indicadores = self.ns["indicadores"]
        self.assertEqual(indicadores["total_questionarios"], 0)
        self.assertEqual(indicadores["feedbacks"], 0)
        self.assertEqual(indicadores["evolucao_diaria"], [])
        for d in indicadores["faixa_etaria"]:
            self.assertEqual((d["quantidade"], d["percentual"]), (0, 0.0))

    def test_consultas_sem_filtro(self) -> None:
        questionarios = gerar_questionarios()
        gravar(questionarios)

        self.assert_indicadores(questionarios)

    def test_consultas_com_filtro_de_periodo(self) -> None:
        questionarios = gerar_questionarios()
        gravar(questionarios)
        periodos = [
            (date(2026, 10, 31), date(2026, 10, 31)),
            (date(2026, 11, 1), None),
            (None, date(2026, 10, 31)),
            (date(2026, 11, 1), date(2026, 11, 2)),
            (date(2027, 1, 1), date(2027, 1, 31)),
        ]
        for inicio, fim in periodos:
            with self.subTest(inicio=inicio, fim=fim):
                self.assert_indicadores(questionarios, inicio, fim)

    def test_conversao_de_fuso_do_sql_equivale_a_de_brasilia(self) -> None:
        for dados in gerar_questionarios():
            criado_em = dados["criado_em"]
            self.assertEqual(
                (criado_em - timedelta(hours=3)).date(),
                criado_em.astimezone(FUSO_LOCAL).date(),
            )

    def test_exemplo_de_resultado_do_documento(self) -> None:
        gravar(gerar_questionarios())
        exec(self.bloco_python("indicadores = {"), self.ns)
        exemplos = re.findall(r"```text\n(.*?)```", SECAO_R5, re.S)

        self.assertEqual(
            json.loads(exemplos[0]),
            self.ns["indicadores"]["faixa_etaria"],
        )
        self.assertEqual(
            json.loads(exemplos[1]),
            self.ns["indicadores"]["beneficios_ia"],
        )
        soma = sum(
            d["percentual"] for d in self.ns["indicadores"]["beneficios_ia"]
        )
        self.assertGreater(soma, 100)

    def test_contagem_sem_distinct_duplica_questionarios(self) -> None:
        questionarios = gerar_questionarios()
        gravar(questionarios)
        exec(self.bloco_python("indicadores = {"), self.ns)
        exec(self.bloco_python(".distinct()"), self.ns)
        alvo = set(self.ns["beneficios"])

        self.assertEqual(
            self.ns["certo"],
            sum(1 for d in questionarios if alvo & set(d["beneficios_ia"])),
        )
        self.assertGreater(self.ns["errado"], self.ns["certo"])

    def test_criterio_de_espacos_igual_no_orm_sql_e_admin(self) -> None:
        espacos = [
            chr(codigo)
            for codigo in range(0x110000)
            if chr(codigo).isspace()
        ]
        feedbacks = [
            *espacos,
            "".join(espacos),
            f"{''.join(espacos)}a{''.join(espacos)}",
            "​",  # espaço de largura zero não é espaço em branco
            "texto",
        ]
        base = {campo: OPCOES[campo][0] for campo in CAMPOS_ESCOLHA_UNICA}
        for feedback in feedbacks:
            RespostaQuestionario.objects.create(**base, feedback=feedback)
        respostas = RespostaQuestionario.objects.all()
        modelo_admin = RespostaQuestionarioAdmin(
            RespostaQuestionario,
            admin.site,
        )

        esperado = sum(1 for feedback in feedbacks if feedback.strip())
        pelo_admin = sum(
            1 for resposta in respostas
            if modelo_admin.possui_feedback(resposta)
        )
        self.assertEqual(len(espacos), 29)
        self.assertEqual(esperado, 3)
        self.assertEqual(self.ns["contar_feedbacks"](respostas), esperado)
        self.assertEqual(executar_sql("10"), [{"feedbacks": esperado}])
        self.assertEqual(pelo_admin, esperado)

    def test_sqlite3_exige_os_dois_parametros(self) -> None:
        connection.ensure_connection()

        with self.assertRaises(sqlite3.ProgrammingError):
            connection.connection.execute(BLOCOS_SQL["1"], {"inicio": None})
