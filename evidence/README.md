# Verification evidence

This directory holds *observations*, not claims that the tool works.

- \`latest.json\`: timestamped, bounded, HTTPS-only observations for the last scheduled batch.
- \`state.json\`: rolling status, previous observations, alert eligibility, and issue-deduplication state.
- \`exceptions.json\`: anomalies for human review.

## Interpretation

HTTP 200 means only that an endpoint responded. It does not certify a source's
correctness, cost, coverage, ability to accept input, right to redistribute
data, safety, anonymity, or utility for research. HTTP 403/429, login pages,
and captchas are *inconclusive*, not evidence of retirement. TLS errors
indicate a failed authenticated connection, not proof that the source is gone.
Only repeated 404/410 observations six or more hours apart may produce a
review issue. No automatic source deletion or replacement is permitted.

The observer performs HTTPS GET only, with system certificate validation and
TLS >= 1.2 (prefers TLS 1.3 when available); never disables certificate
verification, submits generic search terms, authenticates, solves challenges,
or executes JavaScript. Data is bounded to 64 KiB per response. No screenshots,
page contents, personal data, cookies, search terms or sensitive inputs are
stored. SHA-256 hashes record bytes inspected and are not authenticity proofs.

GitHub Actions schedules run only after workflows are present on the default
branch and Actions are enabled. Issues require \`issues: write\` permissions.
