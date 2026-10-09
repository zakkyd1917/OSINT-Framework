#!/usr/bin/env python3
"""Allowlisted, bounded, non-executing API functional shape probes.

Only public predefined test endpoints. No user data, accounts, POST, JS,
authentication, hidden endpoints, or arbitrary parameter insertion.
"""
import argparse
import datetime as dt
import json
import pathlib
import ssl
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_sources import SafeRedirects, checked_url  # noqa: E402

def run_profile(profile):
    url = profile["testUrl"]
    out = {"name": profile["name"], "testUrl": url, "genericInput": profile["genericInput"],
           "method": "allowlisted HTTPS GET, JS not executed, 64 KiB response cap",
           "observedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "httpStatus": None, "functionTest": "inconclusive", "confidence": "none",
           "expectedKeys": profile["expectedJsonKeys"], "redirects": []}
    try:
        checked_url(url)
        ssl_context=ssl.create_default_context()
        ssl_context.minimum_version=ssl.TLSVersion.TLSv1_2
        handler=SafeRedirects()
        opener=urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ssl_context), handler)
        req=urllib.request.Request(url, method="GET", headers={
            "User-Agent": "OSINT-EvidenceCatalog/1.0",
            "Accept": "application/json",
            "Accept-Encoding": "identity"
        })
        with opener.open(req,timeout=12) as response:
            out["httpStatus"]=response.status
            checked_url(response.geturl())
            out["redirects"]=handler.chain
            raw=response.read(65536)
            if response.status == 200:
                doc=json.loads(raw.decode("utf-8",errors="strict"))
                if isinstance(doc,dict) and all(k in doc for k in profile["expectedJsonKeys"]):
                    out["functionTest"]="expected_public_api_json_shape_observed"
                    out["confidence"]="medium"
                else:
                    out["functionTest"]="unexpected_api_shape"
    except (ValueError, urllib.error.URLError, TimeoutError, OSError, UnicodeError):
        out["functionTest"]="inconclusive"
    except Exception:
        out["functionTest"]="probe_error"
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--slot",type=int,default=None)
    parser.add_argument("--dry-run",action="store_true")
    args=parser.parse_args()
    profiles=json.loads((ROOT/"verification"/"functional_profiles.json").read_text(encoding="utf-8"))["profiles"]
    slot=args.slot if args.slot is not None else int(dt.datetime.now(dt.timezone.utc).timestamp()//43200)
    chosen=profiles[slot % len(profiles)]
    if args.dry_run:
        print(json.dumps(chosen,indent=2))
        return
    results=[run_profile(chosen)]
    path=ROOT/"evidence"/"functional_latest.json"
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({"results":results},indent=2)+"\n",encoding="utf-8")
    print(json.dumps(results,indent=2))

if __name__=="__main__":
    main()
