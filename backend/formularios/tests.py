"""Testes automatizados das rotas do aplicativo."""
import json

from django.test import TestCase
from django.urls import reverse


class StatusApiTests(TestCase):
    def test_status_retorna_resposta_de_sucesso(self):
        resposta = self.client.get(reverse("status"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.json(),
            {
                "status": "ok",
                "mensagem": "API do IAEmpreendedora funcionando.",
            },
        )


class QuestionarioApiTests(TestCase):
    def setUp(self):
        self.url = reverse("enviar_questionario")
        self.respostas_validas = {
            "faixa_etaria": "18 a 24 anos",
            "conhecimento_financeiro": "Moderado",
            "ferramenta_financeira": "Planilhas",
            "uso_ia": "Algumas vezes",
            "uso_ia_financas": "Tirar dúvidas financeiras",
            "beneficios_ia": [
                "Organização de gastos",
                "Planejamento financeiro",
            ],
            "confianca_ia": "Confiança moderada",
            "interesse_ia": "Sim",
            "feedback": "Gostei da iniciativa.",
        }

    def enviar(self, dados):
        return self.client.post(
            self.url,
            data=json.dumps(dados),
            content_type="application/json",
        )

    def test_questionario_aceita_respostas_validas(self):
        resposta = self.enviar(self.respostas_validas)

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["status"], "ok")

    def test_questionario_rejeita_campo_obrigatorio_ausente(self):
        dados = self.respostas_validas.copy()
        del dados["faixa_etaria"]

        resposta = self.enviar(dados)

        self.assertEqual(resposta.status_code, 400)
        self.assertIn("faixa_etaria", resposta.json()["erros"])

    def test_questionario_rejeita_opcao_invalida(self):
        dados = self.respostas_validas.copy()
        dados["confianca_ia"] = "Confio em qualquer resposta"

        resposta = self.enviar(dados)

        self.assertEqual(resposta.status_code, 400)
        self.assertIn("confianca_ia", resposta.json()["erros"])

    def test_questionario_aceita_varios_beneficios(self):
        resposta = self.enviar(self.respostas_validas)

        self.assertEqual(resposta.status_code, 201)

    def test_questionario_rejeita_beneficios_sem_selecao(self):
        dados = self.respostas_validas.copy()
        dados["beneficios_ia"] = []

        resposta = self.enviar(dados)

        self.assertEqual(resposta.status_code, 400)
        self.assertIn("beneficios_ia", resposta.json()["erros"])

    def test_questionario_nao_combina_opcao_sem_beneficios(self):
        dados = self.respostas_validas.copy()
        dados["beneficios_ia"] = [
            "Não vejo benefícios",
            "Organização de gastos",
        ]

        resposta = self.enviar(dados)

        self.assertEqual(resposta.status_code, 400)
        self.assertIn("beneficios_ia", resposta.json()["erros"])

    def test_questionario_rejeita_json_malformado(self):
        resposta = self.client.post(
            self.url,
            data="{json inválido",
            content_type="application/json",
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.json()["status"], "erro")

    def test_questionario_rejeita_metodo_get(self):
        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 405)

    def test_feedback_e_opcional(self):
        dados = self.respostas_validas.copy()
        del dados["feedback"]

        resposta = self.enviar(dados)

        self.assertEqual(resposta.status_code, 201)

    def test_questionario_rejeita_feedback_acima_do_limite(self):
        dados = self.respostas_validas.copy()
        dados["feedback"] = "x" * 1001

        resposta = self.enviar(dados)

        self.assertEqual(resposta.status_code, 400)
        self.assertIn("feedback", resposta.json()["erros"])
