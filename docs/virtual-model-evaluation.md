# Kong "virtual models" (19 Nov 2026)

A virtual model is one name, such as `my-model`, that apps send in the `model` field. Kong decides which provider and real model answers. A Kong speaker (Shubham Nigam, Global Partner Solution Lead) described it as "my model". This page records how Kong implements it, what we tested on the Konnect trial (EU, serverless gateway, Kong 3.16), and how it compares with Cognitum's MetaLLM.

Full write-up with setup steps: Claude Doc "Kong virtual models: how they work and an evaluation".

## Two implementations

| | AI Model entity (AI Gateway 2.x) | AI Proxy Advanced plugin |
|---|---|---|
| Where | Konnect Models menu: Models and Providers | Plugin on a route |
| Name apps call | The model's `name`, or `config.route.model` alias | `targets[].model.model_alias` (3.14+) |
| Credentials | Once per AI Model Provider; write-only in API responses | Inline per target, plain text unless vaulted |
| Choosing a target | round-robin, priority, lowest-latency, lowest-usage (tokens or cost), least-connections, consistent-hashing, semantic | Same |
| Runs on our trial | **No**: config can be created, but there is no proxy URL. Docs: hybrid only, self-managed data planes | **Yes** |

## Demo results (serverless gateway, all entities tagged `virtual-model-demo`, deleted afterwards)

| Test | Result |
|---|---|
| AI Gateway 2.x on the trial | `POST /v1/ai-gateways` (needs `display_name`; `deployment_type` hybrid, managed or serverless), providers and the `my-model` AI Model all created. Target `config` needs a `type` discriminator. Even as `serverless`, `proxy_urls` stayed empty and no nodes appeared. Defaults on the new model: `failover_criteria: [error, timeout]`, no auth strategy. |
| Two targets sharing one alias | Works (not documented by Kong). `X-Kong-LLM-Model` shows the real model, e.g. `gemini/gemini-2.5-flash`. |
| Unknown model, real upstream name, or no `model` field | **HTTP 500** `failed to get balancer instance`. Should be a 4xx. |
| Switch backends | Changing target priority moved all traffic; client unchanged. |
| Fallback, default `failover_criteria` | Primary returns 500: **0/6 succeeded**. |
| Fallback, explicit (`http_429`, `http_5xx`, `non_idempotent`) | 5/6 succeeded; the 6th was a 503 from Gemini itself. |
| Real-world fallback | Gemini's free-tier quota returned 429 mid-test; with explicit criteria every user request was served by the second target. Only the header showed it. |
| Per-model cost cap (`ai-rate-limiting-advanced` `policies` with `match: [{type: model}]`, `cost` strategy) | After 7 requests used the expensive target's 0.005 budget, requests 8 to 12 went to the cheap target, all 200. A cap per target is possible, and Kong routes around it instead of rejecting. |

Notes: on Konnect, updating a plugin needs `PUT` (`PATCH` returned 405). Raw results: `results/vm-switch-fallback.json`, `results/vm-per-model-cost-cap.json`. Scripts: `scripts/virtual-model/`.

## Compared with Cognitum MetaLLM

MetaLLM is a hosted router: you call fixed tiers (`cognitum-auto`, `-low`, `-mid`, `-high`) and Cognitum picks the vendor model. Kong is a gateway: you choose the providers and the rules. Test of 12 MetaLLM calls (see `docs/metallm-findings.md`):

- The vendor model ID leaked (`z-ai/glm-5.3-flash`) in the receipt and a header, contrary to the spec.
- The key's sponsored grant capped all calls at the low tier, so escalation couldn't be tested.
- Failed calls (reasoning used the whole output budget) were billed: 72% of the $0.023 spent.
- The response cache crossed tiers.
- Kong in front of MetaLLM works with no code changes (OpenAI provider with `upstream_url`), and Kong's cost estimate matched Cognitum's receipts exactly.

## Recommendations

1. Use AI Proxy Advanced with a shared `model_alias` on the existing serverless gateway; the 2.x Models menu needs a self-hosted data plane.
2. Always set `failover_criteria` explicitly, including `non_idempotent`.
3. Cap expensive targets with per-model `policies` in AI Rate Limiting Advanced.
4. Expect 500s for wrong model names; have clients treat `failed to get balancer instance` as a client error.
