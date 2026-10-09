# OSINT Evidence Catalog

An independent, static, evidence-led directory of open-source research resources.
The index is NOT a certification that resources work or that their data is accurate.

## Provenance and classification

- claimedStatus, claimedPricing and claimedOpsec preserve inherited assertions, not independent verification.
- status identifies the editorial lifecycle: unverified, monitoring, historical or retired.
- evidence/ records transport observations, never service functionality guarantees.
- access separates price, practical free-tier usefulness, registration, payment and human effort.
- jsAssessment identifies potential JavaScript requirements and exceptional-value reviews.
- catalogId links recurring resource destinations across different research categories.

Previously abandoned URLs are retained with historical labels or monitoring flags.
Nothing is removed just because a network checker encounters an error.

## TLS-verified, non-executing monitoring

Run these commands from the repository root:

    python3 -m unittest discover -s tests -v
    python3 tools/build_static_catalog.py
    python3 tools/verify_sources.py --dry-run --batch-size 20
    python3 tools/verify_sources.py --batch-size 20

The checker makes GET requests against public HTTPS endpoints only. It uses
certificate verification, the operating-system trust store, TLS 1.2 minimum,
and negotiates TLS 1.3 when supported. It never executes JavaScript, submits
forms, authenticates to target services, follows redirects to insecure or
internal addresses, or accepts self-signed/invalid certificates.

An HTTP 200 response is transport evidence, not a completed functional test.
HTTP 403/429, TLS errors, timeouts, and captive-login pages are inconclusive.
Repeated HTTP 404/410 observations six or more hours apart can create a review
issue, but cannot delete a resource. See evidence/README.md for details.

Once promoted to the default branch and GitHub Actions is enabled, the
verify-sources workflow cycles through 90 destinations every 12 hours.
It stores dated evidence, regenerates a static directory, and issues targeted
GitHub review alerts only for repeated 404/410 observations. Public forks may
start with scheduled workflows disabled. Actions require manual enablement.

## Cloudflare live deployment

The independent static catalog is published at https://osint-evidence-catalog.cca-records.workers.dev/ using a dedicated Worker. It contains no browser-side JavaScript, no site cookies, no advertising scripts and no remote fonts. An edge-only script retrieves the **owner-controlled** GitHub master static HTML on a three-hour cache and falls back to an embedded copy if GitHub is unavailable. No upstream maintainer or third-party catalog is consulted. The existing `wrangler.jsonc` supports static-asset-only deployments; for the resilient Worker use `wrangler-edge.jsonc`.

Reproducible deployment:

    python3 tools/build_static_catalog.py
    python3 tools/build_edge_worker.py
    npx wrangler deploy --config wrangler-edge.jsonc

The independent Worker currently deploys from the connected Cloudflare account. Automated catalog observations happen through GitHub Actions. Successful evidence changes propagate to Cloudflare after its cache refresh interval, without GitHub requiring a Cloudflare secret.

The repository Homepage setting may still display the original project URL; update it in GitHub Settings when convenient to the new Worker URL. This is metadata, not a network dependency.

## No browser JavaScript

The default public/index.html is a static HTML directory with no executable
JavaScript, remote stylesheets, tracking pixels, browser storage, or cookies.
The previous interactive app and Worker are not prerequisites. The source
inventory remains ordinary readable JSON.

## Independence and required attribution

This code and directory derive from software published under the MIT License.
The original LICENSE notice remains intact as legally required.
The new tooling does not write to, synchronize with, or call any other user's
GitHub repository, service domain, or application.

GitHub still records this repository as a fork until an administrator uses
Settings > General > Danger Zone > Leave fork network. That platform-level
operation is separate from application code and cannot be performed by this
connected tool set. Do not delete the fork as a substitute for detaching it.

Original master is preserved at:
archive/pre-independence-2026-10-09

Work in progress:
development/verified-catalog
