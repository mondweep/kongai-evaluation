# Kong feature coverage: what we have evaluated

19 Nov 2026. Living version (with comments): https://claude.ai/artifact/8XdpnshtRftDasb9Bdq6Wf

## Summary

We have tested 8 of the 32 Konnect menu items hands-on, several only in part. Two more were only seen, and 22 haven't been touched. The depth is all in the AI Gateway plugins on the serverless gateway (eight `ai-*` plugins, auth, ACL, audit, failover), plus the Dev Portal and Konnect's MCP server. Those plugins don't have their own menu item. Metering & Billing, Catalog, Identity, the Observability dashboards and most of Access Management haven't been evaluated at all.

Sources: this repo ([results.md](results.md), [validation-plan.md](validation-plan.md), [devportal-demo.md](devportal-demo.md)) [ruv-stack-evaluation.md](ruv-stack-evaluation.md), [virtual-model-evaluation.md](virtual-model-evaluation.md) and [mcp-management.md](mcp-management.md) (merged from PRs #1 to #3), plus a read-only API probe of the trial org ([results/coverage-api-probe.json](../results/coverage-api-probe.json), script [scripts/coverage/probe.py](../scripts/coverage/probe.py)). The menu list combines a menu from another Konnect org with the trial's own menu. Labels can differ between orgs.

## Coverage matrix

Status: **Hands-on** means we ran it and have results. **Partial** means part of it was run. **Seen** means we only looked at it in the trial org. **Not evaluated** means no work yet.

| Area | Feature | Status | Evidence | Link |
| --- | --- | --- | --- | --- |
| Catalog | Services | Not evaluated | 0 catalog services in the trial org | |
| Catalog | MCP Registries | Not evaluated | No registry API found on the trial. It may be a newer or paid feature | |
| Catalog | Integrations | Not evaluated | 16 listed. Only the built-ins (gateway, API products, analytics, mesh) are on | |
| Catalog | Scorecards | Not evaluated | 0 scorecards | |
| Catalog | Resources | Seen | Gateway services appear here automatically | |
| Dev Portal | Portals | Hands-on | Demo portal with a published API, pages and portal MCP server. The portal MCP endpoint was probed read-only from a local machine | [devportal-demo.md](devportal-demo.md), [ruv-stack-evaluation.md](ruv-stack-evaluation.md) section 5 |
| Dev Portal | Application Auth | Partial | A key-auth strategy exists, but the API was published with no auth. App registration, DCR and OIDC weren't tried | [devportal-demo.md](devportal-demo.md) |
| Metering & Billing | Metering | Not evaluated | API reachable on the trial, 0 meters. Related: Kong's per-request token and cost figures matched Gemini and the price formula (C4, C4b) | [results.md](results.md) |
| Metering & Billing | Product Catalog | Not evaluated | 0 features, 0 plans | |
| Metering & Billing | Billing | Not evaluated | 0 customers. One payment app record exists | |
| Metering & Billing | Cost Analytics | Not evaluated | | |
| Metering & Billing | Settings | Not evaluated | | |
| Observability | Summary | Not evaluated | | |
| Observability | Dashboards | Not evaluated | 0 custom dashboards | |
| Observability | Explorer | Not evaluated | | |
| Observability | Logs | Hands-on | Used as evidence: no prompt text stored by default (D4), retention 30 days (A4), MCP calls logged per tool | [results.md](results.md), [ruv-stack-evaluation.md](ruv-stack-evaluation.md) |
| Observability | Reports | Not evaluated | | |
| Observability | Requests | Hands-on | Each AI request logged with consumer, model, tokens, cost and latency (A2), queried through `/v2/api-requests` | [results.md](results.md) |
| Observability | Debugger | Not evaluated | | |
| Identity | Identity (Kong Identity) | Not evaluated | 0 auth servers | |
| AI | Models | Hands-on, can't run | AI Model `my-model` created, but no proxy URL appeared because it needs a self-hosted data plane. The same idea works on serverless through AI Proxy Advanced `model_alias` | [virtual-model-evaluation.md](virtual-model-evaluation.md) |
| AI | Providers | Hands-on, can't run | Created with the models above. Same limit | [virtual-model-evaluation.md](virtual-model-evaluation.md) |
| AI | MCP Servers | Partial | The Konnect MCP Servers entity is untested. The gateway-side AI MCP Proxy plugin was tested: per-tool ACL gave 403, calls logged per tool, the handshake uses up rate-limit quota | [ruv-stack-evaluation.md](ruv-stack-evaluation.md) |
| AI | Agents | Not evaluated | 0 agents | |
| AI | Gateways | Partial | AI gateway created and then deleted, never got nodes. All hands-on tests ran on the serverless API gateway | [virtual-model-evaluation.md](virtual-model-evaluation.md) |
| Access Management | Users | Seen | 1 user (owner) | |
| Access Management | Agents | Not evaluated | | |
| Access Management | Groups | Not evaluated | Only the default teams exist | |
| Access Management | Identity Providers | Not evaluated | No SSO set up | |
| Access Management | Token Vault | Not evaluated | Relevant: the provider key was readable in plain text in plugin config (S3c) | [results.md](results.md) |
| Access Management | Virtual Keys | Not evaluated | | |
| Cost Management | Cost Management | Not evaluated | Related: token and cost limits (C1 to C3) and per-model cost caps were tested at the gateway | [results.md](results.md), [virtual-model-evaluation.md](virtual-model-evaluation.md) |

### Tested but not a menu item

| Capability | Status | Evidence | Link |
| --- | --- | --- | --- |
| AI Gateway plugins on serverless | Hands-on | ai-proxy, ai-proxy-advanced (failover, model alias), ai-prompt-guard, ai-semantic-prompt-guard, ai-semantic-cache, ai-rate-limiting-advanced, ai-mcp-proxy. ai-sanitizer with the PII service run locally (D2: misses NI numbers and most postcodes, alters 9/25 benign prompts) | [results.md](results.md) |
| Other `ai-*` plugins | Not evaluated | 23 are available. Not yet tried: prompt decorator, template and compressor, request and response transformers, RAG injector, AWS and Azure guardrails | |
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
- **Billing:** a real billing run needs a Stripe (or similar) account linked. Metering, plans and entitlements can be tried without one (unverified).
- **Debugger, Identity, Token Vault, Virtual Keys, MCP Registries:** it's unverified whether these work on a trial or with serverless. MCP Registries had no API endpoint on this org.
- **From the cloud sandbox:** `*.kongportals.com` and `*.mcp.konghq.com` are blocked, so portal-MCP and Konnect-MCP probes have to run on a local machine.

## Prioritised plan for the gaps

The order follows the five risk claims and what a client is likely to ask about first. Nothing below has been created yet. Every step that writes to Konnect waits for the owner's OK, and each would use its own tag so cleanup is one delete by tag.

| # | Gap | What we'd test | Creates in Konnect | Effort |
| --- | --- | --- | --- | --- |
| 1 | Metering & Billing, Cost Analytics, Cost Management | A meter on AI tokens per consumer, fed from existing gateway traffic. A product plan with an entitlement (e.g. 10k tokens a month). Check whether usage matches Kong's request logs and whether an over-entitlement consumer is blocked or only flagged | Meter, feature, plan, customer (tag `metering-eval`) | Half a day |
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

Testing all 32 menu items plus the 23 `ai-*` plugins would take about 9 to 10 working sessions. It also needs three things the account owner has to provide: a self-hosted data plane (Docker on a local machine), a Stripe test-mode account, and approval for Konnect writes. Without the data plane and Stripe, about a quarter of the list stays untestable.

**1. One test card per feature.** Each card says: the claim (from Kong's docs or marketing), the setup, the test cases, pass criteria, the evidence level reached (claimed, documented, demonstrated, attested) and a cleanup tag. Test cases always cover the happy path, the defaults, a negative case and a misuse case. Defaults matter because most of our findings so far were unsafe defaults: failover, semantic guard threshold, cache scope and credential forwarding.

**2. A repeatable harness.** One folder per area under `scripts/`, a shared Konnect client, the existing mock LLM and synthetic corpora. A `run-all` script sets up by tag, runs, writes JSON to `results/` and tears down. Then the whole suite can re-run on each new Kong release as a regression check.

**3. Environments.**

| Environment | Covers | Status |
| --- | --- | --- |
| Trial org + serverless gateway | Catalog, Dev Portal, Metering, Observability, Identity, Access Management, most AI plugins | In place |
| Self-hosted data plane joined to Konnect (Docker, local) | AI Gateway 2.x Models and Providers traffic, AI Sanitizer with its PII service, `redis` rate-limit policy, vault backends, Debugger on a hybrid node | About 1 hour to set up |
| Stripe test mode | Billing and invoices from metered usage | Needs a free Stripe account |
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
