"""Unit tests require no network, API keys, or third-party dependencies."""
import datetime as dt
import importlib.util
import pathlib
import unittest
from unittest import mock

FILE = pathlib.Path(__file__).resolve().parents[1] / "tools" / "verify_sources.py"
spec = importlib.util.spec_from_file_location("verify_sources", FILE)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class CatalogTests(unittest.TestCase):
    def test_selection_wraps_and_deduplicates(self):
        data = [
            {"name":"A","url":"https://example.com/a"},
            {"name":"A2","url":"https://example.com/a"},
            {"name":"B","url":"https://example.com/b"},
            {"name":"C","url":"https://example.com/c"},
        ]
        self.assertEqual(len(v.select_batch(data, 2, 0)), 2)
        self.assertEqual(len(v.select_batch(data, 2, 1)), 2)
        self.assertEqual(v.select_batch(data, 2, 1)[1]["name"], "A")
    def test_recursive_folder_without_type(self):
        root = {"children":[{"name":"Folder","children":[{"name":"Tool","url":"https://example.org"}]}]}
        self.assertEqual(len(list(v.iter_entries(root))), 1)
    def test_reject_insecure_scheme(self):
        with self.assertRaisesRegex(ValueError,"https_required"):
            v.checked_url("http://example.com/")
        with self.assertRaisesRegex(ValueError,"https_required"):
            v.checked_url("javascript:alert(1)")
    def test_reject_internal_host(self):
        with self.assertRaises(ValueError):
            v.checked_url("https://localhost/test")
        with self.assertRaises(ValueError):
            v.checked_url("https://127.0.0.1/")
        with self.assertRaises(ValueError):
            v.checked_url("https://example.com:8080/")
    def test_reject_private_dns(self):
        with mock.patch.object(v.socket, "getaddrinfo", return_value=[(2,1,6,"",("192.168.1.1",443))]):
            with self.assertRaisesRegex(ValueError,"nonpublic_address_disallowed"):
                v.checked_url("https://internal.example/")
    def test_https_dns_positive(self):
        with mock.patch.object(v.socket, "getaddrinfo", return_value=[(2,1,6,"",("1.1.1.1",443))]):
            self.assertEqual(v.checked_url("https://example.com/").hostname, "example.com")
    def test_html_parser_ignores_js_payload(self):
        p = v.ExtractText()
        p.feed("<title>Real</title><script>alert(1)</script><p>Visible text</p>")
        self.assertNotIn("alert", " ".join(p.body))
        self.assertIn("Visible text", " ".join(p.body))
    def test_alert_requires_two_spaced_failures(self):
        one = {"requestedUrl":"https://example.com/","catalogId":"x","observedAt":"2026-10-08T10:00:00+00:00","httpStatus":404,"observation":"missing_candidate"}
        prior = v.update_state({},[one])
        self.assertEqual(prior[one["requestedUrl"]]["missingStreak"],1)
        two = dict(one, observedAt="2026-10-09T10:00:00+00:00")
        with mock.patch.object(v, "utc_now", return_value="2026-10-09T10:00:00+00:00"):
            current=v.update_state(prior,[two])
        self.assertGreaterEqual(current[one["requestedUrl"]]["missingStreak"],1)
        ok=dict(two, observation="endpoint_responds", httpStatus=200)
        self.assertEqual(v.update_state(current,[ok])[one["requestedUrl"]]["missingStreak"],0)

if __name__ == "__main__":
    unittest.main()
