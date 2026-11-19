# Kong AI Gateway: test report on the five AI risk claims

**Date:** 19 November 2026
**Environment:** Kong Konnect trial (EU region), serverless gateway, Kong 3.16.0.2 Enterprise
**Data:** synthetic only
**Detailed results:** [results.md](results.md) · **Test plan:** [validation-plan.md](validation-plan.md) · **Scripts:** [../scripts/](../scripts/) · **Raw outputs:** [../results/](../results/)

## Summary

Kong says its AI Gateway addresses five risks. We tested each claim hands-on rather than relying on the marketing.

The controls are real. **Most of them only work as claimed once they are configured carefully, and several fail open or leak with their default settings.** Cost accounting, authentication and gateway overhead were the strongest results. PII protection, failover defaults and the semantic cache were the weakest.

| Risk | Verdict | In one line |
|---|---|---|
| 1. Data exposure | **Partly demonstrated** | PII filters catch common formats but miss UK identifiers, reworded data and non-user messages. By default the client's API key is forwarded to the LLM provider. |
| 2. Uncontrolled costs | **Demonstrated, with a caveat** | Token and cost counting is exact. Limits are soft, and a concurrent burst reached 3.9× the limit. |
| 3. Compliance and audit | **Partly demonstrated** | The per-request AI log is good and stores no prompts. The admin audit trail is signed but incomplete, and it lost events. |
| 4. Operational risk | **Demonstrated, not with the defaults** | Failover works only with non-default settings. It never happens for DNS failures. Overhead is about 1 ms. |
| 5. Security | **Partly demonstrated** | Authentication and ACLs are solid. Regex injection filters are easy to bypass. The semantic guard works but blocks nothing with a plausible-looking config. |

Evidence levels used throughout: **claimed** (marketing), **documented** (docs explain how it works), **demonstrated** (our test passed), **attested** (an independent party vouches for it). Nothing in this report is attested. We could not read Kong's certification list on its trust portal.

## 1. Data exposure

**Claim:** Kong stops sensitive data from reaching LLM providers.

| Control | Result |
|---|---|
| AI Prompt Guard (regex) | Blocked 24/25 structured PII items (cards, NI numbers, emails, UK mobiles, postcodes) and 0/15 unstructured ones (names, addresses, health details, numbers spelled out in words). 0/25 false positives. **System and assistant messages are not checked by default.** |
| AI Sanitizer (needs a separate PII service) | Serverless can't host the service. Without it, requests fail with HTTP 500 by default. With `stop_on_error: false`, **PII passes through silently**. |
| AI Sanitizer, with the PII service run on a laptop | PII fully removed from **14/25 structured prompts**: cards 5/5, emails 4/5, mobiles 4/5, postcodes 1/5, **UK NI numbers 0/5**. Unstructured: 7/15 fully removed, 5/15 partly, 3/15 not at all. **Only the user message is sanitized**: a name, email and card number in system and assistant messages reached the LLM unchanged. **9/25 harmless prompts were altered** (e.g. "What is the capital of PLACEHOLDER1?"). With blocking on, it blocked that question. |
| What leaves the gateway | **By default the client's gateway API key goes to the LLM provider**, along with the client IP, consumer name and every custom header. `hide_credentials: true` stops the key. The IP headers still go. |
| Logs | Konnect stores tokens, cost, model and consumer, but no prompt text while `log_payloads` is off. |

**Bottom line:** a useful layer, not a guarantee. For UK data, add custom patterns for NI numbers and postcodes, cover every message role, and expect false positives that change what the model is asked.

## 2. Uncontrolled costs

**Claim:** token and cost limits keep AI spend under control.

| Test | Result |
|---|---|
| Token counting (Gemini 2.5 Flash) | Prompt tokens matched Google's own count **8/8**. Hidden "thinking" tokens are counted as output, which is what you are billed for. |
| Cost calculation | Matched the price formula within 0.01% on all 6 logged calls. |
| Token limit, one request at a time | Blocked on the 4th request: **18% over**, i.e. one request. |
| Cost limit, one request at a time | **9% over**, one request. |
| 10 concurrent requests | **All 10 passed: 3.9× the limit.** |
| 30 concurrent requests | 6 passed: 2.4× the limit. |
| Semantic cache | Cuts cost, but see the security finding below. |

**Bottom line:** the accounting is trustworthy. The limits are soft caps, not hard budgets, as Kong's docs warn. Set them below the real budget and add provider-side caps.

## 3. Compliance and audit

**Claim:** full audit trail and governance of AI usage.

| Test | Result |
|---|---|
| Per-request AI record | **Pass.** Consumer, route, model, provider, tokens, cost and latency are logged for every request. |
| Admin audit log (webhook) | Events arrive in about 1 s and are **signed**. But creating or deleting a consumer logged only "PAT authentication succeeded", with nothing about what changed. A rejected (401) request logged nothing. When our receiver returned errors, Konnect **disabled the webhook and dropped about 10 minutes of events**, until it was re-enabled by hand. |
| Data residency | Not verifiable from outside. Kong's serverless docs say same-region deployment "is not guaranteed". |
| Retention | Org setting 30 days. Individual request records expired after about 14 days. |

**Bottom line:** good for AI usage reporting. Not sufficient on its own as an admin audit trail. Monitor the webhook's status and keep your own copy of events.

## 4. Operational risk

**Claim:** load balancing and failover keep AI services available.

| Scenario (two targets, one broken) | Result |
|---|---|
| Target returns 500, default settings | **50% of requests failed.** No failover. |
| Add `http_500` | Still 50% failed. |
| Add `http_500` and `non_idempotent` | **100% success.** |
| Target returns 429, with the right settings | 100% success |
| Target hangs | 100% success, about 2.4 s slower per failed-over request |
| Target's hostname doesn't resolve | **50% failed, whatever the settings** |
| Gateway overhead | **About 1 ms** (p50 and p95) |

**Bottom line:** works, but only if you know to set `non_idempotent` and the HTTP codes, because LLM calls are POSTs. DNS failures are never retried.

## 5. Security

**Claim:** protection against prompt injection and unauthorised access.

| Test | Result |
|---|---|
| Authentication | No key, wrong key and revoked key all got 401. **Pass.** |
| Authorisation (ACL) | Consumer outside the allowed group got 403. **Pass.** |
| Provider key secrecy | The provider key never appeared in responses, headers or error messages. **Pass.** It is stored in plain text in the plugin config, visible to any Konnect admin, so production should use a vault reference. |
| Regex injection guard (7 patterns) | Blocked 14/15 direct attacks and **0/15** reworded, foreign-language, base64 or indirect attacks. |
| Semantic injection guard (pgvector + Gemini embeddings) | With `vectordb.threshold` 0.4: **30/30 attacks blocked, 0/25 false positives**. With only `search.threshold` set (the setting the docs point to): **0/30 blocked**. It silently fails open. Config changes sometimes didn't apply until the plugin was deleted and recreated. |
| Semantic cache | With the default route-wide scope, **one consumer received another consumer's cached answer**, even about a different account number. A loose threshold returned the answer to a different question. |

**Bottom line:** access control is solid. Content controls need the semantic guard, with the threshold verified by testing. Never use the semantic cache across users without partitioning it.

## Recommended production settings

1. Set `hide_credentials: true` on key-auth, and strip client IP and custom headers before the LLM.
2. Store provider keys as vault references, not in plugin config.
3. AI Proxy Advanced: add `non_idempotent` plus `http_500`, `http_502`, `http_503` and `http_429` to `failover_criteria`.
4. Treat rate and cost limits as soft. Set them below the real budget and keep provider-side spending caps.
5. Semantic Prompt Guard: set `vectordb.threshold` explicitly, and add a test that a known attack is blocked after every config change.
6. Semantic Cache: scope it per consumer, or use it only for public, non-personal prompts.
7. AI Sanitizer: host the PII service with high availability, keep `stop_on_error: true`, add custom patterns for UK identifiers, and check how it handles system and assistant messages.
8. Audit: alert when the audit webhook goes inactive, and keep your own copy of events.

## Limits of this evaluation

- Trial account and a **serverless** gateway. Hybrid or dedicated gateways may behave differently, and serverless is capped at 100 requests per second.
- Most tests used a mock LLM that echoes what it receives. Only the token and cost checks used a real model (Gemini 2.5 Flash, free tier).
- The PII, injection and benign test sets were written for this test (95 prompts in total: 40 PII, 30 attacks, 25 benign). Treat the counts as indicative, not as benchmarks.
- The AI Sanitizer ran on a laptop behind a tunnel, so its latency (about 0.8 to 1.0 s per request) is not a production figure.
- Nothing here is independently attested.

## Related work in this repo

- [virtual-model-evaluation.md](virtual-model-evaluation.md): one model name routed to several providers
- [mcp-management.md](mcp-management.md): managing Konnect through Kong's MCP server
- [ruv-stack-evaluation.md](ruv-stack-evaluation.md): Kong in front of rUv's agent stack
