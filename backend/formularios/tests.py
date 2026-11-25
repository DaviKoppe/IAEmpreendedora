"""Testes automatizados das rotas do aplicativo."""
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
