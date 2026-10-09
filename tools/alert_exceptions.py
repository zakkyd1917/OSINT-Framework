#!/usr/bin/env python3
"""Create a deduplicated GitHub issue ONLY for two spaced confirmed 404/410 probes.

This tool never probes source websites; verification and alerting are separate.
Requires GITHUB_TOKEN and GITHUB_REPOSITORY in GitHub Actions.
"""
import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "evidence" / "state.json"

def main():
    token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repository or "/" not in repository:
        print("No GitHub credentials or repository context; alerts skipped.")
        return 0
    if not STATE.exists():
        print("No evidence state yet.")
        return 0
    states = json.loads(STATE.read_text(encoding="utf-8"))
    created = 0
    for url, item in states.items():
        if not item.get("alertEligible") or item.get("alerted"):
            continue
        # Only reproducible 404/410 classifications qualify for autonomous issues.
        if item.get("lastObservation") != "missing_candidate":
            continue
        title = "[OSINT source review] Repeated HTTP missing: " + (item.get("catalogId") or url[:60])
        description = (
            "Two or more separate HTTPS GET observations, at least six hours apart, "
            "returned HTTP 404/410. This indicates a missing URL candidate only, "
            "NOT definitive closure of the underlying service.\n\n"
            "URL: " + url + "\n"
            "Last observed: " + str(item.get("lastCheckedAt")) + "\n"
            "Last HTTP status: " + str(item.get("lastHttpStatus")) + "\n\n"
            "Action: verify manually, locate legitimate successor, or mark historical. "
            "Do not delete based on the check alone."
        )
        data = json.dumps({"title": title, "body": description}).encode("utf-8")
        req = urllib.request.Request(
            "https://api.github.com/repos/" + repository + "/issues",
            data=data, method="POST",
            headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json", "User-Agent": "OSINT-EvidenceCatalog/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 201:
                    item["alerted"] = True
                    created += 1
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print("Alert creation failed (state left pending): " + type(e).__name__)
            # Avoid fail-open retry floods in this run; next scheduled run retries.
    STATE.write_text(json.dumps(states, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("New review issues: " + str(created))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
