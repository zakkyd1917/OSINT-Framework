# Evidence and access assessment policy

The catalog is a research finding aid, not a certification program.

## Independent classifications

Availability: unverified; endpoint_responds; access_restricted; network_inconclusive;
missing_candidate; retired_documented; historical_only. Only a functional
test with a documented query may establish a service's actual utility.
These are separate from lifecycle stages and the upstream's status labels.

Access: fully_free_without_registration; free_registration_required;
metered_free_quota; freemium_with_meaningful_free_tier; trial_only;
paid_subscription; per_record_charge; institution_only; restricted_access;
unavailable; unknown. The meaningful-free-tier designation requires evidence:
can a user achieve the advertised research task without making a payment?

Human contribution: none/read-only; manual_query; account_setup; API_key_setup;
custom_coding; complex_research_workflow; specialist_methodology; third_party_approval.
A researcher may have several of these burdens simultaneously.

JavaScript: no_js_supported; js_optional; js_required_documented;
js_only_suspected; unknown. The HTTP verifier never executes JavaScript.
Do not call a tool broken merely because it returns a JavaScript shell.
A JS-only source should receive a replacement review; retaining it should
require documented unique capability, concrete value and compensating controls.

Confidence:
- none: inherited claim or observation absent
- low: transport response only
- medium: manual page/service review, dated evidence
- high: dated hands-on functional test plus independent corroboration
No single HTTP response receives high functional confidence.

## Costs and evidence sources

For each reviewed service, record provider pricing URL, review date, free quota,
registration, API access, rate limits, payment or data/compute fees, and
restrictions on redistribution. Avoid inferring costs from domain names,
marketing headlines, GitHub stars, or the mere existence of an account form.

Samples verified against primary provider pages on 2026-10-09:

- OpenAlex: free keyless and registered API budgets with metered usage;
  https://help.openalex.org/access/pricing/
- GDELT: free raw datasets; separate cloud-processing products may charge;
  https://gdeltproject.org/about.html
- ACLED: account required for downloads/API, API requires authentication;
  https://acleddata.com/api-documentation/getting-started
- Docket Alarm: commercial subscriptions and varying access fees;
  https://www.docketalarm.com/

Pricing and access may change. Revalidate before operational reliance.

## Source preservation and responsible handling

Keep the original target URL and historical assertions in the original snapshot.
Never automatically destroy a record based on 404, 403, timeout, redirect,
missing DNS, certificate error or a third-party claim. Record timestamps and
response digests, then recommend replacement or manual escalation.

Web capture hashes identify what the monitor received; they are not cryptographic
signatures from the source, and do not prove authenticity, completeness or
legal admissibility. Record raw source material separately only when rights,
privacy and storage policies permit.

Public-network checks cannot reach .onion, internal services or authenticated
pages. Those require specially authorized, manually scoped methods, not generic
probe escalation. Do not bypass TLS validation or execute third-party code to
make a service appear functional.
