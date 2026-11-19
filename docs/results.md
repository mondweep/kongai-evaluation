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
| D2 AI Sanitizer redaction quality (PII service `kong/ai-pii-service:v0.3.1-en` run on a laptop, reached through a Cloudflare tunnel; `anonymize: all_and_credentials`, placeholder mode) | **Structured PII fully removed in 14/25 prompts.** Cards 5/5, emails 4/5 (one left `...rson@fakecorp.example`), UK mobiles 4/5 (missed `+44 7700 900456`), postcodes 1/5, **NI numbers 0/5** (in one it redacted the words "My National Insurance" and left the number). **Unstructured PII: 7/15 fully removed** (names, passport, IP, most of a date of birth), 5/15 partly (street address, sort code, a Spanish name, half of a split card number), **3/15 not at all** (card, phone and NI number spelled out in words). |
| D2b False positives | **9/25 benign prompts were altered before reaching the LLM**, e.g. "What is the capital of PLACEHOLDER1?", "Who painted PLACEHOLDER1?", "Explain the difference between TCP and PLACEHOLDER1", "Write a PLACEHOLDER1 query". The LLM then answers a different question. |
| D2c Roles | Only the **user** message is sanitized. A **system** and an **assistant** message containing a name, email and card number reached the LLM unchanged, even with `allow_all_conversation_history: true`. |
| D2d Modes | `synthetic` swaps in realistic fake values ("Timothy Jennings", "ginasmith@example.net"). `recover_redacted: true` puts the original values back into the response, so the client sees real data while the LLM saw placeholders. `block_if_detected: true` returns HTTP 400 with the PII types found, but it also blocked "What is the capital of France?". |
| D2e Latency | Round trip about 0.8 to 1.0 s per request in this setup, versus about 0.3 s without the sanitizer. Most of the extra is the tunnel to the laptop, so this is not a fair production figure. |
| D4 Logs | Konnect's request logs hold tokens, cost, model and consumer, but **no prompt text** while `log_payloads` is off. Client IP and country are stored. |

**Verdict:** partly demonstrated. Prompt Guard is a regex filter. It does what you configure and nothing more. AI Sanitizer needs a self-hosted PII service. Once that runs, it catches names, cards and emails well, but it misses UK NI numbers and most postcodes, ignores system and assistant messages, and alters about a third of harmless prompts. Treat it as one layer, not a guarantee, and tune it with `custom_patterns` for UK identifiers.

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
| A1 Admin audit trail (webhook to a Supabase function, `receiver/`) | Events arrive in about 1 s, in JSON, and each one carries a **signature** (`sig`) as tamper evidence. They include who (principal), when, source IP, user agent and outcome. **Gaps:** (1) creating and deleting a gateway consumer through the control-plane API produced **only 'PAT authentication succeeded' events**, with no record of *what* changed. (2) A request with an invalid token (401) produced **no event**. (3) After my receiver returned errors, Konnect marked the webhook **inactive and stopped sending**, with no automatic retry. Events during that roughly 10-minute outage were **never delivered**, until I re-enabled it by hand. |
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

### S4b AI Semantic Prompt Guard (pgvector on Supabase, Gemini `gemini-embedding-001` embeddings)

| Configuration | Direct attacks | Paraphrased attacks | False positives |
|---|---|---|---|
| `search.threshold` 0.5, 0.2 or 0.8 (the setting the docs point to) | **0/15** | **0/15** | 0/25 |
| `vectordb.threshold` = 0.4 (cosine distance) | **15/15** | **15/15** | **0/25** |
| `vectordb.threshold` = 0.3 | 3/15 (some 500s from the database pool) | 10/15 | 0/25 |

- **The guard fails open with a plausible-looking config.** The SQL Kong runs is `embedding <=> $1 < $2`. Database logs showed `$2 = NULL` whenever only `search.threshold` was set. `vectordb.threshold` defaults to null, and in that state the guard silently blocks nothing, even the exact text of a deny prompt.
- **Config changes don't always take effect.** After a failed database connection, the plugin kept its broken instance until it was deleted and recreated. Updating it in place wasn't enough.
- When the vector DB is unreachable, it **fails closed** (HTTP 500).
- Caveat: the attack and benign corpora were written for this test (55 prompts), so treat 30/30 as indicative.

### C5 AI Semantic Cache (same stack)

| Test | Result |
|---|---|
| Exact repeat (threshold 0.1) | Cache hit, and no upstream call |
| Paraphrase ("Which city is the capital of France?") | Cache hit |
| Different question (Germany), threshold 0.1 | Miss (correct) |
| Same Germany question, threshold 0.2 | **Hit: the cached answer about France came back** |
| **Cross-consumer:** consumer A asks about account 55779911, then consumer B asks the same question | **Hit: B receives A's cached answer** |
| Consumer B asks about a *different* account (12345678) | **Hit: B receives A's answer about 55779911** |

**Verdict:** the cache does cut cost, but with the default (route-wide) scope it **leaks answers between users**. A loose threshold also returns wrong answers. It's only safe for public, non-personal prompts, or with the cache partitioned per consumer.

## 6. Virtual models (one model name, several providers)

See `docs/virtual-model-evaluation.md`. Headlines: two AI Proxy Advanced targets can share one `model_alias`; default failover served 0/6 requests when the primary failed (explicit criteria: 5/6); a per-model cost cap routes traffic to the next target instead of rejecting it; unknown model names return HTTP 500; the Konnect "Models" (AI Gateway 2.x) entities can be created on the trial but get no proxy URL without a self-hosted data plane.

## Real model (Gemini 2.5 Flash, free tier, via Kong)

| Test | Result |
|---|---|
| Smoke test | Pass. Kong translated OpenAI-format requests to Gemini and back. |
| C4 Token accuracy | Prompt tokens matched Google's own `countTokens` in **8/8** cases. Completion tokens include Gemini's hidden "thinking" tokens, which are billed as output, so Kong counts what you pay for. |
| C4b Cost accuracy | The cost in Konnect's logs matched `(prompt×0.30 + completion×2.50)/1M` within rounding (under 0.01%) for all 6 logged calls. |
| Observation | Hidden reasoning tokens dominated the cost. "Give a two-word synonym for happy" used **1,707 thinking tokens**. Token limits that count only visible output would badly under-count, but Kong doesn't. |

After the test, the Gemini key was removed from Konnect.

## Still to do

Nothing from the plan. Cleanup of the test setup is listed in the README.
