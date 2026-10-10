#!/usr/bin/env python3
"""Build a reproducible Cloudflare edge gateway for the static HTML catalog.

JavaScript here executes only at Cloudflare's server edge, never in visitors'
browsers. Embedded HTML is an offline fallback if our OWN repository is down.
"""
import hashlib
import json
import pathlib

BASE = pathlib.Path(__file__).resolve().parents[1]
HTML = (BASE / "public" / "index.html").read_text(encoding="utf-8")
assert "<script" not in HTML.lower(), "Client-side scripts are forbidden"
assert HTML.lstrip().lower().startswith("<!doctype html>"), "Not a HTML document"
SHA = hashlib.sha256(HTML.encode("utf-8")).hexdigest()
JS = r"""
const EMBEDDED_HTML = __HTML__;
const SNAPSHOT_SHA256 = __HASH__;
const OWN_SOURCE = 'https://raw.githubusercontent.com/zakkyd1917/OSINT-Framework/master/public/index.html';
const SAFE_HEADERS = {
  'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; script-src 'none'; img-src 'none'; connect-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
  'Referrer-Policy': 'no-referrer',
  'X-Content-Type-Options': 'nosniff',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'Cache-Control': 'public, max-age=600'
};
async function catalogHtml() {
  try {
    const upstream = await fetch(OWN_SOURCE, {
      headers: {'Accept': 'text/html'},
      cf: {cacheEverything: true, cacheTtl: 129600}
    });
    if (upstream.ok && Number(upstream.headers.get('content-length') || 0) < 1500000) {
      const value = await upstream.text();
      if (value.length > 25000 && value.length < 1500000 &&
          value.trimStart().toLowerCase().startsWith('<!doctype html>') &&
          !/<script\b/i.test(value) && !/href\s*=\s*['"]?javascript:/i.test(value)) {
        return {html: value, origin:'own-github-repo'};
      }
    }
  } catch (_) {}
  return {html: EMBEDDED_HTML, origin:'embedded-fallback'};
}
export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      return new Response('Method not allowed', {status: 405, headers: SAFE_HEADERS});
    }
    if (url.pathname === '/healthz') {
      return new Response(JSON.stringify({service: 'osint-evidence-catalog', healthy: true,
        snapshot_sha256: SNAPSHOT_SHA256, js_on_client: false}), {
          headers: {...SAFE_HEADERS, 'Content-Type': 'application/json; charset=utf-8'}
      });
    }
    if (url.pathname === '/robots.txt') {
      return new Response('User-agent: *\nAllow: /\n', {
        headers: {...SAFE_HEADERS, 'Content-Type': 'text/plain; charset=utf-8'}
      });
    }
    if (url.pathname !== '/' && url.pathname !== '/index.html') {
      return new Response('Not found', {status: 404, headers: SAFE_HEADERS});
    }
    const page = await catalogHtml();
    return new Response(request.method === 'HEAD' ? null : page.html, {
      headers: {...SAFE_HEADERS, 'Content-Type': 'text/html; charset=utf-8',
        'X-Catalog-Source': page.origin, 'X-Embedded-Snapshot': SNAPSHOT_SHA256}
    });
  }
};
"""
out = JS.replace("__HTML__", json.dumps(HTML, ensure_ascii=False)).replace("__HASH__", json.dumps(SHA))
dest = BASE / "dist" / "worker.mjs"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(out, encoding="utf-8")
print(f"Built server-side edge Worker: {dest}, {len(out)} bytes; SHA-256 fallback {SHA}")
