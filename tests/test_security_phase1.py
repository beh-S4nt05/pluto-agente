"""Regressões de segurança da API — Fase 1.

Testes isolados: não iniciam daemon, não usam credenciais reais.
"""
import tempfile
import unittest

from pluto.config import Config
from pluto.server.app import create_app


class ApiOriginSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Config(data_dir=self.tmp.name, mock=True)
        self.cfg.update({"auth_token": "phase1-test-token"})
        self.client = create_app(self.cfg).test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_authenticated_same_origin_request(self):
        r = self.client.get(
            "/api/perguntas",
            headers={"Origin": "http://localhost", "Host": "localhost",
                     "X-Pluto-Token": "phase1-test-token"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get("Access-Control-Allow-Origin"),
                         "http://localhost")

    def test_cross_origin_read_does_not_expose_cors(self):
        r = self.client.get(
            "/api/perguntas",
            headers={"Origin": "https://evil.example",
                     "X-Pluto-Token": "phase1-test-token"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("Access-Control-Allow-Origin", r.headers)

    def test_scheme_mismatch_is_not_same_origin(self):
        r = self.client.get(
            "/api/perguntas",
            headers={"Origin": "https://localhost", "Host": "localhost",
                     "X-Pluto-Token": "phase1-test-token"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("Access-Control-Allow-Origin", r.headers)

    def test_scheme_mismatch_post_requires_valid_token(self):
        r = self.client.post(
            "/api/tasks",
            json={"text": "test"},
            headers={"Origin": "https://localhost", "Host": "localhost"},
        )
        self.assertEqual(r.status_code, 403)

    def test_cross_origin_post_is_rejected(self):
        r = self.client.post(
            "/api/tasks",
            json={"text": "test"},
            headers={"Origin": "https://evil.example"},
        )
        self.assertEqual(r.status_code, 403)
        self.assertNotIn("Access-Control-Allow-Origin", r.headers)

    def test_missing_or_invalid_token_is_rejected(self):
        self.assertEqual(self.client.get("/api/perguntas").status_code, 401)
        self.assertEqual(
            self.client.get("/api/perguntas",
                            headers={"X-Pluto-Token": "incorrect"}).status_code,
            401,
        )

    def test_preflight_does_not_allow_cross_origin(self):
        r = self.client.options(
            "/api/perguntas",
            headers={"Origin": "https://evil.example",
                     "Access-Control-Request-Method": "GET"},
        )
        self.assertNotIn("Access-Control-Allow-Origin", r.headers)


if __name__ == "__main__":
    unittest.main()
