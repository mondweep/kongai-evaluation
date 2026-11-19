# Kong feature coverage: what we have evaluated

19 Nov 2026. Living version (with comments): https://claude.ai/artifact/8XdpnshtRftDasb9Bdq6Wf

## Summary

After the last round, 28 of the 32 Konnect menu items have been tested hands-on (5 of them only in part, and AI Models and Providers can't run on serverless). Two were only seen (Users and Catalog Integrations), and two can't be run on this trial: MCP Registries (no API) and Observability Reports (UI only). It started at 8 hands-on, was 11 after Metering & Billing and 22 after the gaps. Results: [gaps-evaluation.md](gaps-evaluation.md) and [remaining-evaluation.md](remaining-evaluation.md). What's left needs the owner (an email invite, third-party authorisation, an external IdP, the portal UI) or a self-hosted data plane.

Sources: this repo ([results.md](results.md), [validation-plan.md](validation-plan.md), [devportal-demo.md](devportal-demo.md)) [ruv-stack-evaluation.md](ruv-stack-evaluation.md), [virtual-model-evaluation.md](virtual-model-evaluation.md) and [mcp-management.md](mcp-management.md) (merged from PRs #1 to #3), plus a read-only API probe of the trial org ([results/coverage-api-probe.json](../results/coverage-api-probe.json), script [scripts/coverage/probe.py](../scripts/coverage/probe.py)). The menu list combines a menu from another Konnect org with the trial's own menu. Labels can differ between orgs.

## Coverage matrix

Status: **Hands-on** means we ran it and have results. **Partial** means part of it was run. **Seen** means we only looked at it in the trial org. **Not evaluated** means no work yet.

| Area | Feature | Status | Evidence | Link |
| --- | --- | --- | --- | --- |
| Catalog | Services | Hands-on | Two catalog services mapped to gateway services, plus an API mapping | [gaps-evaluation.md](gaps-evaluation.md) gap 8 |
| Catalog | MCP Registries | Can't run | No registry API on the trial (404 on EU and global). The catalog MCP entry was tested under AI > MCP Servers | [gaps-evaluation.md](gaps-evaluation.md) gap 4 |
| Catalog | Integrations | Seen | 16 listed. 12 need third-party authorisation and weren't connected | [gaps-evaluation.md](gaps-evaluation.md) gap 8 |
| Catalog | Scorecards | Hands-on | Scorecard from the Kong best-practices template selects services by label. Scores appeared later (33%). The auth check ignores route-level auth plugins | [gaps-evaluation.md](gaps-evaluation.md) gap 8, [remaining-evaluation.md](remaining-evaluation.md) |
| Catalog | Resources | Hands-on | All 11 gateway services discovered automatically | [gaps-evaluation.md](gaps-evaluation.md) gap 8 |
| Dev Portal | Portals | Hands-on | Demo portal with a published API, pages and portal MCP server. The portal MCP endpoint was probed read-only from a local machine | [devportal-demo.md](devportal-demo.md), [ruv-stack-evaluation.md](ruv-stack-evaluation.md) section 5 |
| Dev Portal | Application Auth | Partial | On a separate eval portal: strategy, auto-added `konnect-application-auth` (401 without a key), developer, app and approved registration via API. Key issue needs the portal itself, so it wasn't run | [gaps-evaluation.md](gaps-evaluation.md) gap 6 |
| Metering & Billing | Metering | Hands-on | `metering-and-billing` plugin feeds token and request events. Totals matched the request log exactly. Ignores `subject.field`, bills rejected requests by default | [metering-evaluation.md](metering-evaluation.md) |
| Metering & Billing | Product Catalog | Hands-on | Feature, plan with unit price and a 1,000-token metered entitlement. Over-limit flagged in seconds, but the gateway still served the customer | [metering-evaluation.md](metering-evaluation.md) |
| Metering & Billing | Billing | Hands-on | Built-in Sandbox app means no Stripe is needed. Cancelling a subscription produced a draft invoice, which was approved and paid ($0.02). Cadence can't be shorter than a week | [metering-evaluation.md](metering-evaluation.md), [remaining-evaluation.md](remaining-evaluation.md) |
| Metering & Billing | Cost Analytics | Hands-on | Cost by model, forecast and field values. No per-consumer split on serverless (subject is null) | [remaining-evaluation.md](remaining-evaluation.md) |
| Metering & Billing | Settings | Hands-on | Sandbox app, default billing profile (auto-advance, one-hour collection), currencies and tax codes. No notification channels | [remaining-evaluation.md](remaining-evaluation.md) |
| Observability | Summary | Partial | No API. The same figures (requests, p95 by status class) came from Konnect's MCP server | [remaining-evaluation.md](remaining-evaluation.md) |
| Observability | Dashboards | Hands-on | Five-tile dashboard (AI cost, tokens, MCP tools, latency, errors) created through `/v2/dashboards` | [gaps-evaluation.md](gaps-evaluation.md) gap 5 |
| Observability | Explorer | Hands-on | LLM, MCP and API usage queries run through Konnect's MCP server. No public REST endpoint | [gaps-evaluation.md](gaps-evaluation.md) gap 5 |
| Observability | Logs | Hands-on | Used as evidence: no prompt text stored by default (D4), retention 30 days (A4), MCP calls logged per tool | [results.md](results.md), [ruv-stack-evaluation.md](ruv-stack-evaluation.md) |
| Observability | Reports | Can't run | No API in REST or Konnect's MCP server. UI only | [remaining-evaluation.md](remaining-evaluation.md) |
| Observability | Requests | Hands-on | Each AI request logged with consumer, model, tokens, cost and latency (A2), queried through `/v2/api-requests` | [results.md](results.md) |
| Observability | Debugger | Hands-on | 45 s session on the serverless gateway captured per-plugin spans | [gaps-evaluation.md](gaps-evaluation.md) gap 5 |
| Identity | Identity (Kong Identity) | Hands-on | Auth server and per-agent clients; the gateway does client credentials. Client deletion took 232 s to bite | [gaps-evaluation.md](gaps-evaluation.md) gap 3 |
| AI | Models | Hands-on, can't run | AI Model `my-model` created, but no proxy URL appeared because it needs a self-hosted data plane. The same idea works on serverless through AI Proxy Advanced `model_alias` | [virtual-model-evaluation.md](virtual-model-evaluation.md) |
| AI | Providers | Hands-on, can't run | Created with the models above. Same limit | [virtual-model-evaluation.md](virtual-model-evaluation.md) |
| AI | MCP Servers | Hands-on | Catalog entry with tools works, but links only to AI Gateway 2.x MCP servers. `ai-mcp-proxy` conversion mode works, with per-consumer tool lists, but the REST route behind it bypasses the ACL | [gaps-evaluation.md](gaps-evaluation.md) gap 4, [ruv-stack-evaluation.md](ruv-stack-evaluation.md) |
| AI | Agents | Hands-on | Agent registered in `/v1/agents` and tied to a Kong Identity client | [gaps-evaluation.md](gaps-evaluation.md) gap 3 |
| AI | Gateways | Partial | AI gateway created and then deleted, never got nodes. All hands-on tests ran on the serverless API gateway | [virtual-model-evaluation.md](virtual-model-evaluation.md) |
| Access Management | Users | Seen | 1 user (owner) | |
| Access Management | Agents | Hands-on | Kong Identity principals of type agent, with gateway-checked API keys | [gaps-evaluation.md](gaps-evaluation.md) gap 2 |
| Access Management | Groups | Hands-on | Team with Viewer on one control plane: reads 200, writes 403. Removal took about 25 s to take full effect | [remaining-evaluation.md](remaining-evaluation.md) |
| Access Management | Identity Providers | Partial | Org settings read only. Kong Identity can't be an SSO provider (no authorization-code grant), so SSO needs an external IdP | [remaining-evaluation.md](remaining-evaluation.md) |
| Access Management | Token Vault | Partial | Secret stored write-only; one credential per provider. Only AI Gateway 2.x can use it. The Konnect config-store vault fixes S3c on serverless today | [gaps-evaluation.md](gaps-evaluation.md) gap 2 |
| Access Management | Virtual Keys | Hands-on | Principal API keys checked by `key-auth`. Revocation took 288 s to bite | [gaps-evaluation.md](gaps-evaluation.md) gap 2 |
| Cost Management | Cost Management | Hands-on | Gateway AI calls appear as `ai.usage.v1` events with no plugin. Budgets work but only as advisory (enforce is rejected); the gateway kept serving over budget | [remaining-evaluation.md](remaining-evaluation.md), [results.md](results.md) |

### Tested but not a menu item

| Capability | Status | Evidence | Link |
| --- | --- | --- | --- |
| AI Gateway plugins on serverless | Hands-on | ai-proxy, ai-proxy-advanced (failover, model alias), ai-prompt-guard, ai-semantic-prompt-guard, ai-semantic-cache, ai-rate-limiting-advanced, ai-mcp-proxy. ai-sanitizer with the PII service run locally (D2: misses NI numbers and most postcodes, alters 9/25 benign prompts) | [results.md](results.md) |
| Other `ai-*` plugins | Hands-on | Decorator, template, request and response transformers, custom guardrail and Lakera fail modes tested. A failing custom-guardrail expression fails open. Compressor, RAG injector, semantic response guard and cloud guardrails need external services | [gaps-evaluation.md](gaps-evaluation.md) gap 7 |
| Gateway auth, ACL, overhead | Hands-on | 401 and 403 correct, about 1 ms overhead, client key forwarded unless `hide_credentials` is on | [results.md](results.md) |
| Admin audit log webhook | Hands-on | Signed events arrive in about 1 s, but they don't say what changed. A 401 produced no event. Events were dropped while the webhook was disabled | [results.md](results.md) |
| System accounts | Hands-on | System account scoped to one control plane, which gave portals a 403 | [mcp-management.md](mcp-management.md) |
| Konnect MCP server | Hands-on | Created a service, route and plugin from Claude Desktop. Use the EU endpoint, because the global one 403s | [mcp-management.md](mcp-management.md) |
| Claude Code and rUv agents through Kong | Hands-on | Anthropic format, SSE and tool calls work. One model per route | [ruv-stack-evaluation.md](ruv-stack-evaluation.md) |
| Event Gateway, Mesh, Dedicated Cloud Gateways | Not evaluated | Event Gateway and Mesh are empty. The Dedicated Cloud Gateway API returns 404 on the trial | |

## What the trial and serverless gateway can't exercise

These limits are confirmed by tests or API calls unless marked "docs" or "unverified".

- **AI Models, Providers and AI Gateways (2.x):** you can create the config, but no proxy URL or nodes appear. A hybrid or self-managed data plane is needed (PR #2).
- **AI Sanitizer:** needs a self-hosted PII service that serverless can't host. It was tested (D2) with the service run on a laptop behind a tunnel. Without it, it fails closed by default, but with `stop_on_error: false` it passes PII through.
- **Dedicated Cloud Gateways:** the API returns 404 on this trial, so anything that needs one (private networking, region pinning) is out of reach.
- **Rate limits:** the `local` policy counts per node, so the real limit is N times higher. AI limits are soft under concurrency. Serverless is capped at 100 RPS (docs).
- **Data residency:** serverless says "same region not guaranteed" (docs), so A3 can't be shown on this tier.
- **Billing:** no Stripe needed, because a built-in Sandbox app handles payment, tax and invoicing. The first invoice only comes at the end of the billing period.
- **Entitlement enforcement:** the `entitlement-enforcement` plugin needs Redis, which serverless doesn't have. Without it the plugin lets everyone through, or blocks everyone, depending on `fail_policy`.
- **Token Vault, catalog MCP implementations:** need AI Gateway 2.x on a hybrid data plane. Identity, Virtual Keys and the Debugger do work on serverless. MCP Registries have no API on this org.
- **From the cloud sandbox:** `*.kongportals.com` and `*.mcp.konghq.com` are blocked, so portal-MCP and Konnect-MCP probes have to run on a local machine.

## Prioritised plan for the gaps

The order follows the five risk claims and what a client is likely to ask about first. Items 1 to 8 have now been run: see [metering-evaluation.md](metering-evaluation.md) and [gaps-evaluation.md](gaps-evaluation.md). Every step that writes to Konnect waits for the owner's OK, and each would use its own tag so cleanup is one delete by tag.

| # | Gap | What we'd test | Creates in Konnect | Effort |
| --- | --- | --- | --- | --- |
| 1 (done, see [metering-evaluation.md](metering-evaluation.md)) | Metering & Billing, Cost Analytics, Cost Management | A meter on AI tokens per consumer, fed from existing gateway traffic. A product plan with an entitlement (e.g. 10k tokens a month). Check whether usage matches Kong's request logs and whether an over-entitlement consumer is blocked or only flagged | Meter, feature, plan, customer (tag `metering-eval`) | Half a day |
| 2 | Token Vault and Virtual Keys | Move the provider key out of plain-text plugin config (fixes finding S3c). Check whether virtual keys give per-team budgets without a Kong consumer per agent | Vault entry, virtual keys (dummy provider key or mock) | 2 to 3 hours |
| 3 | AI Agents, Access Management Agents, Identity | Register an agent identity and issue it OAuth client credentials from a Kong Identity auth server. Check whether the gateway can enforce per-agent limits from that token | Auth server, client, agent (tag `agent-id-eval`) | Half a day |
| 4 | Konnect MCP Servers and MCP Registries | Register the AI MCP Proxy server as a Konnect MCP Server and list it in a registry. Check what a client sees and whether the ACL carries over | MCP server entity, registry if the trial allows it | 2 to 3 hours |
| 5 | Observability: Dashboards, Explorer, Reports, Debugger | Build an AI cost-per-consumer dashboard from existing traffic. Run one Debugger trace on a guarded route to see if it shows which plugin blocked | One dashboard, one debug session | 2 hours |
| 6 | Application Auth | Switch the demo portal API to key-auth, register an app as a developer, and call the API with the issued key. DCR or OIDC is optional | Auth link on the demo API, a test developer and app | 2 hours |
| 7 | Remaining AI plugins | RAG injector, prompt decorator and template, AWS or Azure guardrails against the existing corpus (mock LLM, no real data) | Plugins on the existing `validation` routes, or a new tag | Half a day |
| 8 | Catalog: Services, Scorecards, Integrations | Map the existing services into catalog services, add a scorecard, and connect GitHub (this repo). Low priority: it doesn't bear on the AI risk claims | Catalog services, a scorecard, a GitHub integration | 2 hours |

Done since the first draft: AI Sanitizer redaction quality (D2 in results.md) and a read-only Dev Portal MCP probe. Still open: portal MCP with developer login and writes.

Out of reach on this trial: AI Gateway 2.x traffic and Dedicated Cloud Gateways. Both need a self-managed data plane or a paid tier.

## What testing every feature systematically involves

Testing all 32 menu items plus the 23 `ai-*` plugins would take about 9 to 10 working sessions. It also needs two things the account owner has to provide: a self-hosted data plane with Redis (Docker on a local machine), and approval for Konnect writes. Without the data plane, about a quarter of the list stays untestable.

**1. One test card per feature.** Each card says: the claim (from Kong's docs or marketing), the setup, the test cases, pass criteria, the evidence level reached (claimed, documented, demonstrated, attested) and a cleanup tag. Test cases always cover the happy path, the defaults, a negative case and a misuse case. Defaults matter because most of our findings so far were unsafe defaults: failover, semantic guard threshold, cache scope and credential forwarding.

**2. A repeatable harness.** One folder per area under `scripts/`, a shared Konnect client, the existing mock LLM and synthetic corpora. A `run-all` script sets up by tag, runs, writes JSON to `results/` and tears down. Then the whole suite can re-run on each new Kong release as a regression check.

**3. Environments.**

| Environment | Covers | Status |
| --- | --- | --- |
| Trial org + serverless gateway | Catalog, Dev Portal, Metering, Observability, Identity, Access Management, most AI plugins | In place |
| Self-hosted data plane joined to Konnect (Docker, local) | AI Gateway 2.x Models and Providers traffic, AI Sanitizer with its PII service, `redis` rate-limit policy, vault backends, Debugger on a hybrid node | About 1 hour to set up |
| Sandbox billing app (built in) or Stripe test mode | Billing and invoices from metered usage | Sandbox works today |
| Redis reachable from the gateway | `entitlement-enforcement`, `redis` rate-limit policies | Needs a hybrid data plane or a hosted Redis |
| Paid tier or a Kong-provided sandbox | Dedicated Cloud Gateways, region pinning (data residency), possibly SSO and MCP Registries | Needs Kong |
| Local machine for network | Portal MCP and Konnect MCP probes (blocked in the cloud sandbox) | Works today |

**4. Phases and effort.**

| Phase | Work | Sessions |
| --- | --- | --- |
| 0 | Turn existing scripts into the harness, and write cards for everything already tested | 1 |
| 1 | Trial-only gaps (plan items 1 to 8 above) | 5 |
| 2 | Self-hosted data plane: AI Gateway 2.x, re-run the key gateway tests on hybrid | 2 |
| 3 | Paid-tier items, if Kong gives access | 1 |
| 4 | Scorecard per feature and per risk claim, plus a client-ready summary | 1 |

**5. Things to decide.** A standing approval for writes, limited to one tag per phase, would stop each step waiting for sign-off. The trial's expiry date is unknown and could cut Phase 1 short. The Gemini free tier rate-limits real-model tests, so most tests stay on the mock.
