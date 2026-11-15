"""Regressões de proteção contra SSRF no web_fetch."""
import socket
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pluto import tools


class WebFetchSsrfTests(unittest.TestCase):
    def setUp(self):
        self.cfg = SimpleNamespace(web_enabled=True)

    def test_private_and_local_destinations_denied(self):
        for url in ("http://127.0.0.1:8080/", "http://[::1]/",
                    "http://169.254.169.254/latest/meta-data/",
                    "http://10.0.0.1/", "http://localhost/",
                    "http://sub.localhost/", "file:///etc/passwd",
                    "http://user:pass@example.com/"):
            with self.subTest(url=url):
                self.assertFalse(tools._web_fetch_public_url(url))

    def test_public_dns_resolution_is_allowed(self):
        info = [(socket.AF_INET, socket.SOCK_STREAM, 6, "",
                 ("93.184.215.14", 443))]
        with patch("socket.getaddrinfo", return_value=info):
            self.assertTrue(tools._web_fetch_public_url("https://example.com"))

    def test_mixed_public_private_dns_is_denied(self):
        info = [(socket.AF_INET, socket.SOCK_STREAM, 6, "",
                 ("93.184.215.14", 443)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, "",
                 ("127.0.0.1", 443))]
        with patch("socket.getaddrinfo", return_value=info):
            self.assertFalse(tools._web_fetch_public_url("https://example.com"))

    def test_unresolvable_destination_is_denied(self):
        with patch("socket.getaddrinfo", side_effect=OSError("DNS unavailable")):
            self.assertFalse(tools._web_fetch_public_url("https://example.com"))

    def test_redirect_is_not_followed(self):
        response = SimpleNamespace(status_code=302, close=lambda: None)
        with patch.object(tools, "_web_enabled", return_value=True), \\
             patch.object(tools, "_web_fetch_public_url", return_value=True), \\
             patch.object(tools.requests, "get", return_value=response) as get:
            result = tools.web_fetch({"url": "https://example.com"}, self.cfg)
        self.assertIn("BLOQUEADO", result)
        self.assertFalse(get.call_args.kwargs["allow_redirects"])


if __name__ == "__main__":
    unittest.main()
