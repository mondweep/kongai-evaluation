# Results so far (19 Nov 2026)

Environment: Konnect trial (EU), serverless gateway running Kong 3.16.0.2 Enterprise. Every test request went to a mock LLM upstream (see `mock/mock-llm.lua`) unless the test says otherwise. All data is synthetic.

Evidence levels: **claimed** (marketing), **documented** (docs explain how it works), **demonstrated** (our test passed), **attested** (an independent party vouches for it).

## Step 0: plugin availability

All 23 `ai-*` plugins are listed for the serverless control plane and pass Konnect's schema validation. "Available" is not the same as "works", because several of them depend on infrastructure that serverless can't host (see below).

## 1. Data exposure

| Test | Result |
|---|---|
| D0 AI Sanitizer on serverless | **Cannot run.** The plugin calls a separate PII service (default `localhost:8080`) that serverless does not provide. With the default `stop_on_error: true`, every request fails with HTTP 500 and nothing leaks, so it **fails closed**. With `stop_on_error: false`, the PII goes to the LLM **unredacted and without any warning**. |
| D1 Regex PII blocking (AI Prompt Guard) | Structured PII (cards, NI numbers, emails, UK mobiles, postcodes): **24/25 blocked**. The one miss was the `QQ` NI prefix, which our own regex excluded. Unstructured PII (names, addresses, health details, date of birth, obfuscated or split numbers, Spanish, sort code and account number, passport, IP address): **0/15 blocked**. False positives: **0/25** benign prompts. |
| D1b Roles | By default (`match_all_roles: false`), PII in a **system** or **assistant** message is **not checked** and passes through. Earlier user turns and content arrays are checked. |
| D1c Large bodies | Prompts over 8 KB were still checked and blocked. |
| D4 Logs | Konnect's request logs hold tokens, cost, model and consumer, but **no prompt text** while `log_payloads` is off. Client IP and country are stored. |

**Verdict:** partly demonstrated. Prompt Guard is a regex filter. It does what you configure and nothing more. Real PII redaction (AI Sanitizer) needs a self-hosted PII service, so it can't be demonstrated on serverless.

## 2. Uncontrolled costs

| Test | Result |
|---|---|
| C1 Token limit, sequential requests (300 tokens/min) | Blocked on the 4th request, after 354 tokens: **18% overshoot**, which is one request. Rate-limit headers are accurate. |
| C2 Concurrent burst of 10 (same limit) | **All 10 passed: 1,180 tokens, 3.9x the limit.** |
| C2b Concurrent burst of 30 | 6 passed and 24 were blocked: 708 tokens, 2.4x the limit. |
| C3 Cost limit (1.0 units per 5 min) | Cost per request matched the formula `(prompt×input + completion×output)/1M` exactly (0.218). Blocked after 1.09: **9% overshoot**, which is one request. |

**Verdict:** demonstrated for sequential traffic, with an overshoot of one request. Under concurrency, the limit can be exceeded several times over, as Kong's docs warn. Treat it as a soft cap, not a hard budget.

## 3. Compliance and audit

| Test | Result |
|---|---|
| A1 Admin audit trail | **Not yet tested.** Konnect has no pull API or in-product viewer for audit logs. They are delivered only by webhook (CEF format) to a receiver such as a SIEM, which needs an endpoint. The webhook is currently unconfigured. |
| A2 Per-request AI record | **Pass.** Every request is logged with consumer, route, model, provider, prompt tokens, completion tokens, cost and LLM latency. |
| A3 Data residency | Not verifiable from outside. Kong's serverless docs say "deployment on the same region is not guaranteed". |
| A4 Retention | The org's `retention_period_days` is 30. Individual request records carried an expiry about 14 days ahead. |

## 4. Operational risk (AI Proxy Advanced, two targets, one broken)

| Scenario | Result |
|---|---|
| Target A returns 500, **default** `failover_criteria` (`error`, `timeout`) | **50% of client requests failed.** No failover happened. |
| Add `http_500` | Still 50% failed. |
| Add `http_500` **and** `non_idempotent` | **100% success.** |
| Target A returns 429, add `http_429` and `non_idempotent` | 100% success |
| Target A hangs (2 s connect timeout) | 100% success, adding about 2.4 s per failed-over request |
| Target A has an unresolvable hostname | **50% failed** with "name resolution failed", whatever the settings, including passive health checks |

| O3 Gateway overhead (100 requests) | Kong's own processing time: **1 ms at p50 and p95**. Pass. |

**Verdict:** failover works, but **not with the default settings**. POST requests to LLMs need `non_idempotent` plus the HTTP codes you care about. DNS failures never fail over.

## 5. Security

| Test | Result |
|---|---|
| S4 Prompt injection (AI Prompt Guard, 7 regexes) | Direct attacks: **14/15 blocked**. Paraphrased, obfuscated, foreign-language, base64 and indirect (in a document) attacks: **0/15 blocked**. False positives: 0/25. |
| S1 Authentication | No key, wrong key and revoked key: **401** every time. Valid key: 200. |
| S2 Authorisation (ACL) | Consumer outside the allowed group: **403**. |
| S3 Provider key secrecy | A canary provider key never appeared in responses, headers or error bodies (malformed request, auth failures). |
| S3b What reaches the LLM provider | **By default the client's gateway API key is forwarded to the LLM provider**, along with the client IP (`x-real-ip`, `x-forwarded-for`), consumer username and every custom client header. Setting `hide_credentials: true` on key-auth stops the key. The IP headers still go. |
| S3c Provider key storage | The Gemini key sits in plain text in the plugin config, readable through the Konnect API by any admin. Production should use a vault reference. |

AI Semantic Prompt Guard, Semantic Response Guard and Semantic Cache all need Redis or pgvector plus an embeddings model. Serverless can't provide these, so they aren't tested yet.

## Real model (Gemini 2.5 Flash, free tier, via Kong)

| Test | Result |
|---|---|
| Smoke test | Pass. Kong translated OpenAI-format requests to Gemini and back. |
| C4 Token accuracy | Prompt tokens matched Google's own `countTokens` in **8/8** cases. Completion tokens include Gemini's hidden "thinking" tokens, which are billed as output, so Kong counts what you pay for. |
| C4b Cost accuracy | The cost in Konnect's logs matched `(prompt×0.30 + completion×2.50)/1M` within rounding (under 0.01%) for all 6 logged calls. |
| Observation | Hidden reasoning tokens dominated the cost. "Give a two-word synonym for happy" used **1,707 thinking tokens**. Token limits that count only visible output would badly under-count, but Kong doesn't. |

After the test, the Gemini key was removed from Konnect.

## Still to do

A1 with a webhook receiver, and semantic plugins if a vector DB is approved.
