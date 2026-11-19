# Cognitum MetaLLM tier test, 19 Nov 2026

12 POST /v1/chat/completions calls with dummy prompts (10 planned + 2 retries at max_tokens 1600), using the key in COGNITUM_ONE_KEY. Total billed: $0.0231.

| # | Requested | Prompt | Result | Tier that answered | Latency | Tokens in/out (reasoning) | Price |
|---|---|---|---|---|---|---|---|
| 1 | low | easy | 200 | low | 1.9 s | 19 / 20 (20) | $0.000115 |
| 2 | low | hard | 422 reasoning used all 400 tokens | low | 4.4 s | 102 / 400 | ~$0.0019, billed |
| 3 | mid | medium | 200 | **low** (cap_degraded, "sponsored_grant_cap(mid->low)") | 2.8 s | 28 / 339 (281) | $0.00153 |
| 4 | mid | hard | 422 | low | 5.0 s | 102 / 400 | $0.0019, billed |
| 5 | high | easy | 200 | **low**, exact cache hit of call 1 | 0.6 s | 19 / 20 | $0 |
| 6 | high | hard | 422 | low | 4.2 s | 102 / 400 | $0.0019, billed |
| 7 | auto | easy | 200 | low ("difficulty=low") | 1.0 s | 19 / 3 | $0.00004 |
| 8 | auto | medium | 200 | low ("difficulty=low") | 1.8 s | 28 / 64 | $0.00032 |
| 9 | auto | code | 422 at 400; 200 at 1600 | low ("difficulty=mid", capped mid->low) | 7.4 s | 31 / 1002 (773) | $0.00445 (+$0.0018 failed) |
| 10 | auto | hard | 422 at 400 and at 1600 | low | 9.3 s | 102 / 1600 | $0.0072 (+$0.0019 failed), billed |

## Findings
1. **Vendor model ID leaks.** Every 200 response names the vendor model, `z-ai/glm-5.3-flash`, in `x_cognitum.resolved_model` and in the `x-cognitum-resolved-model` header. The spec says raw vendor IDs are never leaked.
2. **This key never leaves the low tier.** It is on a sponsored grant capped at low, so mid and high requests are downgraded (`cap_degraded: true`). The Free plan page says low and mid are included. Escalation could not be tested: escalation rate 0.
3. **Failed calls are billed.** The six 422 "reasoning used the whole output budget" errors cost $0.0166, 72% of the $0.0231 spend. `/v1/usage` still reports `emptyBilledRate: 0`. Hard prompts never got an answer on the low tier, even with 1,600 tokens.
4. **Cache crosses tiers.** A `cognitum-high` request got the cached answer from an earlier `cognitum-low` call, free, and /v1/usage logs it as cognitum-low. Call 5's receipt says `cap_degraded: true` with reason "explicit:low", which is inconsistent.
5. **Pricing.** The receipts fit exactly $1.40 per million input tokens and $4.40 per million output tokens on the low tier, with reasoning tokens billed as output. `price_usd` equals `usage.cost`, and /v1/usage totals match the sum of the receipts to the cent. Cognitum publishes no per-token rates, only plans (Pro $19/mo for "~4–7M tokens"), so the receipts can't be checked against a published rate. One oddity: /v1/usage counts 24 requests for our 12 calls.
6. **Guardrails ran by default.** Every receipt carried a `safety` block (mode warn, input scanned, 0 findings). `fallback_used` never appeared.
7. GET /v1/models also lists `cognitum-ultra`, which the spec and the chat endpoint's enum don't include.

## Kong in front of MetaLLM (approved by Mondweep, 19 Nov 2026)
I added a temporary route `vm-metallm` on `vm-svc`, with key-auth (consumer vm-user) and ai-proxy-advanced. It had two targets, provider `openai` with `upstream_url` https://api.cognitum.one/v1/chat/completions, aliases `metallm-auto` and `metallm-low`, and costs set to $1.40/$4.40 per M. I sent 4 calls through the serverless gateway:

| Call | Result |
|---|---|
| metallm-auto, with apikey | 200, 2.0 s (Kong adds ~1 ms). Kong logged cost $0.0000662, the same as Cognitum's receipt |
| metallm-low, with apikey | 200, 1.8 s. Kong logged $0.000207, the same as the receipt |
| no apikey | 401 from Kong; Cognitum never called |
| unknown model "gpt-4o" | 500 "failed to get balancer instance" (no clean 4xx) |

- Stacking works with no code changes: Kong's OpenAI provider talks to MetaLLM through `upstream_url`.
- Kong's analytics see only the Cognitum tier (`cognitum-auto`), never the vendor. But Kong passes Cognitum's `x_cognitum` body block and `x-cognitum-resolved-model` header through unchanged, so the vendor ID still reaches the client. A response-transformer could strip the header (not tested).
- Kong can't see escalation or `cap_degraded`, because those live only in Cognitum's receipt. Budget limits in Kong would rest on Kong's own token-times-price estimate, which matched the receipt exactly here.
- Cleanup: the route, both plugins and the stored Cognitum key were deleted (HTTP 204). The other thread's vm-chat entities were left untouched.
