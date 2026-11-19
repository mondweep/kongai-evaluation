# Metering & Billing evaluation (19 Nov 2026)

Konnect trial, EU region, serverless gateway (Kong 3.16). Everything was created with the owner's approval and tagged or labelled `metering-eval`. Traffic went to the mock LLM, so no real model or data was used. Scripts are in [`scripts/metering/`](../scripts/metering/), and raw results are in `results/metering-*.json`.

## Bottom line

Metering is accurate and needs no code. One gateway plugin turns every request and every LLM call into usage events. Our per-customer token totals matched Konnect's own request log exactly. Entitlements work in the backend: the customer who went over the limit was flagged within seconds. **The gateway doesn't stop them, though.** Blocking needs the `entitlement-enforcement` plugin, and that plugin needs Redis, which the serverless gateway doesn't have. Without Redis it either lets everyone through or blocks everyone. Billing creates a usage charge per subscription, but the first invoice only comes at the end of the billing period, so no invoice was produced in this test.

## Setup

| Item | Detail |
|---|---|
| System account `metering-eval-ingest` | Roles: Metering Ingest and Entitlement Access only. Token expires 22 Nov 2026 |
| Route `POST /meter-ai/chat` | `key-auth`, `ai-proxy` (OpenAI format, to the mock LLM, priced at $0.15 and $0.60 per 1M tokens) and `metering-and-billing`, which posts to `/v3/openmeter/events` |
| Consumers | `meter-alice` and `meter-bob` |
| Meters | `ai_tokens`: sum of `$.tokens` on `kong.llm_request`, split by token type, model, provider and route. `api_requests`: count of `kong.api_request`, split by route and status |
| Feature and plan | Feature `ai_tokens` on that meter. Plan `ai_starter` (USD, monthly) with a unit price of $0.00001 per token and a **metered entitlement of 1,000 tokens a month, hard limit** |
| Customers | `meter-alice` (subscribed to the plan) and `meter-bob` (no subscription) |
| Billing | The org already had Konnect's built-in **Sandbox** payment, tax and invoicing app as its default billing profile, so no Stripe account was needed |

## Results

| Test | Result |
|---|---|
| M1 Events from the gateway | Each AI call produced **three events**: `kong.api_request` (method, URI, status, sizes, route, service, client IP and user agent) and two `kong.llm_request` events, one for prompt tokens (`type: request`) and one for completion tokens (`type: response`). They arrived within about a second. |
| M2 Events before any meter or customer exists | Stored anyway, flagged "no meter found" and "no customer found". Meters created later counted them, because `events_from` was left empty. |
| M3 Accuracy | Per consumer, metered tokens matched Konnect's request log exactly. Alice: 1,114 prompt and 480 completion tokens. Bob: 206 and 100. Request counts matched too (Alice 24 + 6, Bob 5 + 5). |
| M4 Customer identity | The plugin's `subject.field: username` was **ignored**. Subjects always came as `consumer:<consumer id>`. A customer's subject keys must use that form. They can't be changed while the customer has an active subscription. |
| M5 Model names | Prompt-token events carry the requested model (`gpt-4o-mini`), and completion-token events carry the model the upstream returned (`mock`). A meter split by model therefore shows two models for one call. |
| M6 Rejected requests | Requests the gateway rejected (403) were still counted in `api_requests`, and produced zero-token LLM events with model `UNSPECIFIED`. A request-count price would bill rejected calls unless `allow_status_codes` is set. |
| M7 Entitlement | The usage window started at subscription time, so earlier traffic didn't count. When Alice passed 1,000 tokens, entitlement access changed to `has_access: false` with `usage_limit_reached`. Bob, who has no plan, got `feature_unavailable`. |
| M8 Over the limit without enforcement | **The gateway kept serving Alice (HTTP 200).** Entitlements are only recorded until a gateway plugin enforces them. |
| M9 `entitlement-enforcement` without Redis, `fail_policy: allow` (the default) | Everyone was let through, including Alice, who was over her limit. |
| M10 Same, `fail_policy: block` | **Everyone was blocked** with 403 `CUSTOMER_NOT_FOUND`, including customers with access. Setting `deny_unknown_customers: false` changed nothing. The backend query itself worked, and returned the right answer for each customer. The message is misleading: the real cause is the missing Redis store. |
| M11 Billing | The subscription created a usage-based charge at $0.00001 per token. It invoices on 19 Dec 2026, at the end of the monthly period, and its booked total stays 0 until then. The v3 API has no "invoice now" call, so **no invoice was produced**. A shorter billing cadence (e.g. daily) would be needed to see one during a trial. |
| M12 Cost Management | Separately, the same traffic appeared as `ai.usage.v1` events in Cost Management (`/v1/ai-cost-management/events`) with no plugin. Cost Management and Metering are two different products with separate APIs. |

## What this means

- **Use Metering for chargeback and showback.** It's exact and cheap to set up: one plugin and two meters.
- **Don't treat a plan's "hard limit" as a hard limit on serverless.** Without Redis, nothing at the gateway acts on it. For real enforcement, use a hybrid data plane with Redis, or keep `ai-rate-limiting-advanced` as the gate (which is itself soft under concurrency; see C2 in [results.md](results.md)).
- Set `allow_status_codes` if rejected calls shouldn't be billed. Key customers by `consumer:<id>`.
- Metering events include client IP and user agent. Check that against your data-protection rules.

## Cleanup

Konnect gateway: delete entities tagged `metering-eval` (service `meter-ai`, its route and plugins, consumers `meter-alice` and `meter-bob`). Metering: cancel Alice's subscription, then delete the customers, plan `ai_starter`, feature `ai_tokens` and both meters (all labelled `eval=metering-eval`). Org: delete the system account `metering-eval-ingest`. Ingested events can't be deleted, but they expire with retention.
