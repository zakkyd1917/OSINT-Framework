#!/usr/bin/env python3
"""Conservative, JavaScript-free catalog observation.

Observes safe public HTTPS endpoints only. A responding page is NOT proof that a
source's advertised functionality, pricing, security, or datasets are accurate.
Never authenticates, submits forms, executes scripts, or deletes resources.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import html.parser
import ipaddress
import json
import pathlib
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG = ROOT / "public" / "arf.json"
EVIDENCE = ROOT / "evidence"
MAX_READ = 65536
TIMEOUT_SECONDS = 12
MAX_REDIRECTS = 4
USER_AGENT = "OSINT-EvidenceCatalog/1.0 (+public non-executing verification)"

def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

def iter_entries(node):
    if isinstance(node.get("children"), list):
        for child in node["children"]:
            yield from iter_entries(child)
    elif node.get("url"):
        yield node

def checked_url(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() != "https":
        raise ValueError("https_required")
    if parsed.username or parsed.password:
        raise ValueError("embedded_credentials_disallowed")
    host = (parsed.hostname or "").rstrip(".").lower()
    if not host or host.endswith(".onion") or host in {"localhost", "localhost.localdomain"}:
        raise ValueError("unsupported_hostname")
    if parsed.port not in (None, 443):
        raise ValueError("nonstandard_port_disallowed")
    if len(url) > 4096:
        raise ValueError("url_too_long")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise OSError("dns_resolution_error") from exc
    if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
        raise ValueError("nonpublic_address_disallowed")
    return parsed

class SafeRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.chain = []
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if len(self.chain) >= MAX_REDIRECTS:
            raise ValueError("redirect_limit_exceeded")
        # urllib resolves relative redirect targets; every hop is separately checked.
        checked_url(newurl)
        self.chain.append({"status": code, "url": newurl})
        return super().redirect_request(req, fp, code, msg, headers, newurl)

class ExtractText(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocked = 0
        self.body = []
        self.title = []
        self.in_title = False
        self.scripts = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "svg"):
            self.blocked += 1
            if tag == "script":
                self.scripts += 1
        if tag == "title":
            self.in_title = True
    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg"):
            self.blocked = max(0, self.blocked - 1)
        if tag == "title":
            self.in_title = False
    def handle_data(self, data):
        if self.blocked:
            return
        if self.in_title:
            self.title.append(data)
        elif data.strip():
            self.body.append(data.strip())

def observe(entry):
    original = entry["url"]
    result = {
        "catalogId": entry.get("catalogId"), "name": entry["name"],
        "requestedUrl": original, "observedAt": utc_now(),
        "method": "HTTPS GET, 64 KiB cap, JavaScript disabled, no cookies, TLS verified",
        "httpStatus": None, "finalUrl": None, "redirects": [],
        "functionTest": "not_tested", "confidence": "none",
        "observation": "inconclusive", "exception": None,
        "contentSha256": None, "tlsPolicy": "system-trust, TLS >= 1.2; TLS 1.3 preferred",
    }
    try:
        checked_url(original)
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        redirects = SafeRedirects()
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context), redirects)
        req = urllib.request.Request(original, method="GET", headers={
            "User-Agent": USER_AGENT, "Accept": "text/html,application/json,text/plain;q=0.9,*/*;q=0.1",
            "Accept-Encoding": "identity"
        })
        try:
            response = opener.open(req, timeout=TIMEOUT_SECONDS)
        except urllib.error.HTTPError as exc:
            response = exc
        with response as resp:
            status = resp.status
            final = resp.geturl()
            # Verify final destination too; a redirect bypass must not be accepted.
            checked_url(final)
            result["httpStatus"] = status
            result["finalUrl"] = final
            result["redirects"] = redirects.chain
            content_type = resp.headers.get("Content-Type", "").lower()
            raw = resp.read(MAX_READ)
            result["contentSha256"] = hashlib.sha256(raw).hexdigest()
            result["contentType"] = content_type[:180]
            if status in (404, 410):
                result["observation"] = "missing_candidate"
                result["exception"] = "http_missing"
                result["confidence"] = "medium"  # confidence in observed HTTP code only
            elif status in (401, 403, 407, 429):
                result["observation"] = "access_restricted_or_bot_blocked"
                result["exception"] = "access_gated"
            elif status >= 500:
                result["observation"] = "transient_server_failure"
                result["exception"] = "server_error"
            elif status >= 400:
                result["observation"] = "http_error_unclassified"
                result["exception"] = "http_error"
            elif 200 <= status < 300:
                result["observation"] = "endpoint_responds"
                result["confidence"] = "low"  # no claims about source functionality
                if "html" in content_type:
                    parser = ExtractText()
                    parser.feed(raw.decode("utf-8", errors="replace"))
                    text = " ".join(parser.body)
                    title = " ".join(parser.title)
                    result["pageTitle"] = title[:220]
                    result["htmlTextLength"] = len(text)
                    if "enable javascript" in text.lower() or "javascript is required" in text.lower():
                        result["observation"] = "javascript_required_suspected"
                        result["exception"] = "requires_js_review"
                    elif parser.scripts and len(text) < 80:
                        result["observation"] = "javascript_shell_suspected"
                        result["exception"] = "requires_js_review"
                    elif len(text) >= 80:
                        result["functionTest"] = "static_content_detected_only"
                elif "json" in content_type:
                    try:
                        json.loads(raw.decode("utf-8", errors="replace"))
                        result["functionTest"] = "parseable_json_prefix"
                    except ValueError:
                        result["functionTest"] = "json_inconclusive"
                else:
                    result["functionTest"] = "not_applicable"
            else:
                result["observation"] = "unexpected_http_status"
                result["exception"] = "http_unexpected"
    except ssl.SSLError:
        result["observation"] = "tls_validation_failed"
        result["exception"] = "tls_error"
    except ValueError as exc:
        result["observation"] = "not_probed_by_policy"
        result["exception"] = str(exc)
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLError):
            result["observation"] = "tls_validation_failed"
            result["exception"] = "tls_error"
        else:
            result["observation"] = "network_inconclusive"
            result["exception"] = "network_error"
    except (TimeoutError, OSError, ConnectionError):
        result["observation"] = "network_inconclusive"
        result["exception"] = "network_error"
    except Exception as exc:
        result["observation"] = "check_error"
        result["exception"] = type(exc).__name__
    return result

def select_batch(entries, batch_size, slot):
    # Deduplicate same URL across categories, but never drop catalog entries.
    by_url = {}
    for x in entries:
        by_url.setdefault(x["url"].strip(), x)
    unique = sorted(by_url.values(), key=lambda x: x["url"])
    if not unique:
        return []
    start = (slot * batch_size) % len(unique)
    return (unique + unique)[start:start + min(batch_size, len(unique))]

def update_state(prior, observations):
    states = dict(prior)
    now = dt.datetime.now(dt.timezone.utc)
    for item in observations:
        key = item["requestedUrl"]
        old = states.get(key, {})
        miss = item["observation"] == "missing_candidate"
        old_streak = int(old.get("missingStreak", 0))
        prior_at = old.get("lastCheckedAt")
        separated = False
        if prior_at:
            try:
                separated = now - dt.datetime.fromisoformat(prior_at) >= dt.timedelta(hours=6)
            except ValueError:
                pass
        streak = old_streak + 1 if miss and (not prior_at or separated) else (old_streak if miss else 0)
        alert_eligible = streak >= 2
        states[key] = {
            "catalogId": item["catalogId"],
            "lastCheckedAt": item["observedAt"], "lastObservation": item["observation"],
            "lastHttpStatus": item["httpStatus"], "missingStreak": streak,
            "alertEligible": alert_eligible, "alerted": old.get("alerted", False) if alert_eligible else False,
        }
    return states

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch-size", type=int, default=90)
    ap.add_argument("--slot", type=int, default=None, help="deterministic rotation index")
    ap.add_argument("--all", action="store_true", help="opt in to probing every URL")
    ap.add_argument("--dry-run", action="store_true", help="print selected URLs only, no network")
    args = ap.parse_args(argv)
    if not 1 <= args.batch_size <= 250:
        ap.error("--batch-size must be between 1 and 250")
    entries = list(iter_entries(load_json(CATALOG, {})))
    if args.slot is None:
        now = dt.datetime.now(dt.timezone.utc)
        args.slot = int(now.timestamp() // (12 * 3600))
    chosen = select_batch(entries, len(entries) if args.all else args.batch_size, args.slot)
    if args.dry_run:
        print(json.dumps({"selected": [x["url"] for x in chosen], "count": len(chosen)}, indent=2))
        return 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(observe, chosen))
    EVIDENCE.mkdir(exist_ok=True)
    states = update_state(load_json(EVIDENCE / "state.json", {}), results)
    save_json(EVIDENCE / "state.json", states)
    save_json(EVIDENCE / "latest.json", {
        "generatedAt": utc_now(), "slot": args.slot, "scope": "rotating_non_executing_http",
        "catalogEntries": len(entries), "checked": len(results),
        "observations": results
    })
    save_json(EVIDENCE / "exceptions.json", {
        "generatedAt": utc_now(),
        "items": [x for x in results if x["exception"] is not None],
        "confirmedMissingCandidates": [x for x in results if states[x["requestedUrl"]]["alertEligible"]]
    })
    summary = defaultdict(int)
    for x in results:
        summary[x["observation"]] += 1
    print(json.dumps({"checked": len(results), "observations": dict(summary)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
