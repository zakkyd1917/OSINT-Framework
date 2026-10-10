"""Release-quality smoke tests for the server-side static Cloudflare gateway.

Tests execute no browser JavaScript, launch no servers, and make no HTTP requests.
"""
import pathlib
import subprocess
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class EdgeDeploymentTests(unittest.TestCase):
    def test_browser_page_is_script_free(self):
        content=(ROOT/"public"/"index.html").read_text(encoding="utf-8").lower()
        self.assertTrue(content.startswith("<!doctype html>"))
        self.assertNotIn("<script",content)
        self.assertNotIn("href=\"javascript:",content)
        self.assertNotIn("src=\"http:",content)

    def test_reproducible_edge_bundle(self):
        completed=subprocess.run([sys.executable,str(ROOT/"tools"/"build_edge_worker.py")],
                                 cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(completed.returncode,0,completed.stderr)
        worker=(ROOT/"dist"/"worker.mjs").read_text(encoding="utf-8")
        self.assertIn("raw.githubusercontent.com/zakkyd1917/OSINT-Framework/master/public/index.html",worker)
        self.assertIn("script-src 'none'",worker)
        self.assertIn("EMBEDDED_HTML",worker)
        self.assertIn("cf: {cacheEverything: true, cacheTtl: 10800}",worker)
        self.assertIn("fallback",worker)
        self.assertNotIn("osintframework.com",worker)

    def test_no_client_tracking(self):
        html=(ROOT/"public"/"index.html").read_text(encoding="utf-8").lower()
        for forbidden in ("google-analytics","gtag(","pixel.gif","<iframe","<script","navigator.sendbeacon"):
            self.assertNotIn(forbidden,html)

if __name__=="__main__":
    unittest.main()
