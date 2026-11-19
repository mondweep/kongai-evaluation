# Kong Konnect and AI Gateway: hands-on evaluation

Kong markets its AI Gateway (Konnect) as addressing five risks: data exposure, uncontrolled costs, compliance and audit, operational risk, and security. This repository holds a hands-on test of those claims, plus a wider evaluation: how much of Konnect works on a trial, how Kong fits with rUv's agent stack, and how Kong's virtual models compare with Cognitum's MetaLLM. Marketing pages are treated as claims to test, not as evidence. The summary is under [What we evaluated](#what-we-evaluated).

Documents:

- [docs/report.md](docs/report.md): **the report**: verdicts, key findings and recommended production settings
- [docs/validation-plan.md](docs/validation-plan.md): the tests, with their pass/fail criteria
- [docs/results.md](docs/results.md): results so far
- [docs/ruv-stack-evaluation.md](docs/ruv-stack-evaluation.md): Kong in front of rUv's agent stack (ruflo, agentic-flow, Cognitum One), with hands-on results; probes in [ruv-stack/](ruv-stack/)
- [docs/mcp-management.md](docs/mcp-management.md): managing Konnect conversationally through Kong's MCP server (demo and findings)
- [docs/feature-coverage.md](docs/feature-coverage.md): which Konnect features have been evaluated, what the trial can't test, and the plan for the rest
- [docs/devportal-demo.md](docs/devportal-demo.md): Dev Portal demo setup and findings
- [docs/virtual-model-evaluation.md](docs/virtual-model-evaluation.md): Kong "virtual models" (AI Model entity and AI Proxy Advanced `model_alias`), switching, fallback and per-model cost caps
- [docs/metallm-findings.md](docs/metallm-findings.md): Cognitum MetaLLM tier test, and Kong in front of MetaLLM
- [docs/metering-evaluation.md](docs/metering-evaluation.md): Metering & Billing test (token meters, entitlements, enforcement, sandbox billing)
- [docs/gaps-evaluation.md](docs/gaps-evaluation.md): closing the remaining gaps (Token Vault and virtual keys, agent identity, MCP catalog, observability, application auth, other AI plugins, Service Catalog)
- [docs/remaining-evaluation.md](docs/remaining-evaluation.md): the last menu items (Cost Management and Analytics, Billing, Metering Settings, Groups, Identity Providers, Observability Summary and Reports)
- Living plan doc: https://claude.ai/artifact/FQJeKYkXHUhksYZXqTdK1s

## What we evaluated

Everything ran on 19 Nov 2026 on a Konnect trial (EU region) with one serverless gateway (Kong 3.16), using synthetic data. Each row links to the full write-up.

| Evaluation | Question | Answer in one line |
|---|---|---|
| [Five AI risk claims](docs/report.md) | Does Kong's AI Gateway address data exposure, cost, compliance, operational risk and security? | The controls are real, but most only work once configured carefully, and several fail open or leak with their defaults |
| [Feature coverage](docs/feature-coverage.md) | How much of Konnect have we tested? | 28 of 32 menu items hands-on (5 in part). The rest need the owner, the UI or a hybrid data plane |
| [Kong with rUv's agent stack](docs/ruv-stack-evaluation.md) | Does Kong compete with or complement ruflo, agentic-flow and Cognitum One? | It complements them: rUv's stack is the agent harness, Kong is the enforcement point outside it, as long as it is the agents' only route out |
| [Virtual models](docs/virtual-model-evaluation.md) and [MetaLLM](docs/metallm-findings.md) | How do Kong's "virtual models" compare with Cognitum's MetaLLM router? | Kong lets you choose the models and rules. MetaLLM picks for you, but leaked the vendor model and billed failed calls. Kong in front of MetaLLM works unchanged |
| [Managing Konnect through MCP](docs/mcp-management.md) | Can an agent run Konnect in plain English, safely? | Yes, with a scoped system account and the regional endpoint. The audit log doesn't record what the agent changed |
| [Dev Portal](docs/devportal-demo.md) | Can we publish APIs and expose them to agents? | Yes. The portal's MCP server is a read-only catalogue for agents, not a proxy |
| [Metering & Billing](docs/metering-evaluation.md) | Can usage be metered and billed per customer? | Metering is exact, but a plan's hard limit isn't enforced on serverless (it needs Redis) |
| [Remaining gaps](docs/gaps-evaluation.md) | Token Vault, agent identity, MCP catalog, observability, app auth, other AI plugins, Service Catalog | Mostly works. Revocation takes about 5 minutes, the MCP tool ACL can be bypassed, and broken guardrails fail open |
| [Remaining menu items](docs/remaining-evaluation.md) | Cost budgets and analytics, billing, metering settings, teams and roles, SSO, observability summary and reports | Budgets are advisory only, a real invoice was issued, roles scope correctly, and Kong Identity can't be an SSO provider |

### Five AI risk claims

| Risk | Verdict |
|---|---|
| Data exposure | **Partly demonstrated.** PII filters miss UK identifiers, reworded data and non-user messages. The client's key is forwarded to the provider by default |
| Uncontrolled costs | **Demonstrated, with a caveat.** Token and cost accounting is exact. Limits are soft: a concurrent burst reached 3.9x the limit |
| Compliance and audit | **Partly demonstrated.** Good per-request AI log with no prompts stored. The admin audit trail is signed but incomplete, and it lost events |
| Operational risk | **Demonstrated, not with the defaults.** Failover needs non-default settings and never happens on DNS failures. Overhead is about 1 ms |
| Security | **Partly demonstrated.** Auth and ACLs are solid. Regex injection filters are easy to bypass, and the semantic guard needs the right threshold |

### Kong with rUv's agent stack

- **Different layers:** ruflo, agentic-flow and ruOS choose agents and models and police themselves from inside the agent. Kong enforces keys, budgets, audit and access outside the agent, where the agent can't switch it off. Cognitum One sells no gateway.
- **Guards together beat either alone:** on the same corpus, Kong's prompt guard caught 14 of 15 direct injections and AIDefence 11, together 15. On reworded attacks Kong caught 0 of 15 and AIDefence 5. Kong caught 24 of 25 structured PII items, AIDefence 9.
- **agentic-flow and Claude Code work through Kong:** this held for the Anthropic and OpenAI formats, tool calls and streaming. Each agent has its own Kong key and never holds the provider key.
- **But one Kong route serves one model,** so agentic-flow's own model router conflicts with Kong's model pinning. One of them must own model choice.
- **Kong as a governed MCP server:** per-tool ACLs work, but the MCP handshake uses up rate-limit quota.

### Virtual models and MetaLLM

- **Kong:** one alias, such as `my-model`, maps to several real models through AI Proxy Advanced, and this works on serverless. Switching backends and per-model cost caps work. Fallback fails with the default settings, and an unknown model returns 500. The newer AI Model entity needs a self-hosted data plane.
- **MetaLLM (12 live calls, $0.023):** it routes requests to fixed tiers.
  - It leaked the vendor model ID (`z-ai/glm-5.3-flash`), although its spec says it doesn't.
  - Failed calls were billed: 72% of the spend.
  - The cache crossed tiers.
  - The test key never left the low tier.
- **Together:** Kong in front of MetaLLM needed no code changes, and Kong's cost estimate matched Cognitum's receipts exactly. Kong still passes the vendor ID through to the client.

### Feature coverage

| Status | Konnect menu items |
|---|---|
| Hands-on | Portals, Logs, Requests, Metering, Product Catalog, Billing, Cost Analytics, Metering Settings, Cost Management, Dashboards, Explorer, Debugger, Kong Identity, MCP Servers, Agents (AI and Access Management), Virtual Keys, Groups, Catalog Services, Resources, Scorecards, plus AI Models and Providers (built, but they can't run on serverless) |
| Partial | Application Auth, Token Vault, AI Gateways, Observability Summary, Identity Providers |
| Seen only | Catalog Integrations, Users |
| Can't run on the trial | MCP Registries (no API), Observability Reports (UI only) |

## How we did it

1. **Plan first, with pass/fail bars.** Each of Kong's claims became a test with a written pass/fail bar before anything ran ([docs/validation-plan.md](docs/validation-plan.md)). Later rounds followed the same pattern. First a coverage matrix of the Konnect menu, then a prioritised plan for the gaps ([docs/feature-coverage.md](docs/feature-coverage.md)), then one write-up per area.
2. **Grade the evidence.** Every result is graded:
   - **claimed:** marketing or a README says so
   - **documented:** vendor docs explain how it works
   - **demonstrated:** our test passed
   - **attested:** an independent party vouches for it
   
   For third-party code we also used **read in code** (we inspected the published package). Nothing here is attested.
3. **Use a mock LLM so most tests cost nothing.** An echo mock runs on the gateway itself ([mock/mock-llm.lua](mock/mock-llm.lua)). It returns exactly what reached the "model", so leaks and transformations are visible. Real-model calls went to a free-tier Gemini key, with synthetic data only, and only where a real provider mattered (token accuracy, embeddings, LLM-backed plugins).
4. **Synthetic data only.** The PII, injection and benign corpora are generated ([scripts/corpus.py](scripts/corpus.py)). No real personal or customer data was used.
5. **Tag everything we create.** Each evaluation used its own tag or label, such as `validation`, `devportal-demo`, `mcp-demo`, `ruv-eval`, `virtual-model-demo`, `metering-eval` or `*-eval` for the gaps. Cleanup is then one delete per tag, and one thread can't break another's setup.
6. **Ask before changing anything.** Nothing was created or changed in Konnect, Supabase or anywhere else without the owner's OK. Read-only probes ran freely. Where Konnect access was given to an agent, it used a system account scoped to one control plane, not the owner's token.
7. **Keep secrets out.** Tokens and keys live in environment variables or git-ignored files (`keys.json`, `secrets*.json`, `*.pem`). Keys echoed back in results were redacted before commit. Provider keys stored in Konnect for a test were removed afterwards.
8. **Record everything.** Scripts are in `scripts/` and `ruv-stack/`, raw outputs in `results/`, and one doc per evaluation in `docs/`. Each round was merged through its own pull request.

## External platforms used

| Platform | What we used it for | Notes |
|---|---|---|
| **Kong Konnect** (trial, EU) | The system under test: a serverless gateway (Kong 3.16), Dev Portal, Metering & Billing, Kong Identity, Service Catalog, Observability, and the built-in Sandbox billing app | Admin API through a personal token for setup. Two scoped system accounts: one for the MCP demo, one ingest-only for metering |
| **Kong Konnect MCP server** (`eu.mcp.konghq.com`) | Managing Konnect from Claude Desktop in plain English. Also the only scripted route to Explorer queries and Debugger sessions | Connected through the `mcp-remote` bridge with the scoped system-account token. The global endpoint 403s for an EU org |
| **Supabase** (existing project, schema `kongai`) | pgvector store for the semantic prompt guard and the semantic cache. An edge function (`kongai-audit-receiver`) that received Konnect's audit-log webhooks | Low-privilege `kongai_user` role. No new project was created |
| **Google Gemini** (free tier) | Real-model checks: token and cost accuracy, embeddings for the semantic plugins, the LLM behind the request and response transformers and the LLM judge | Dummy data only, because free-tier prompts may be used by Google |
| **Laptop** (macOS, Docker via Colima, cloudflared) | Ran Kong's PII service (`kong/ai-pii-service`) for the AI Sanitizer test, reached by the cloud gateway through a Cloudflare quick tunnel. Ran Claude Desktop for the Konnect MCP demo | The serverless gateway can't host the PII service. The tunnel and container were stopped after the test |
| **Vercel** | Planned as a host for the mock LLM or PII service | Not used: the connector was read-only, and the mock ran on the gateway instead |
| **Cognitum One / MetaLLM** (`api.cognitum.one`) | The MetaLLM tier test (12 calls, $0.023), and Kong in front of MetaLLM | The owner's API key, on a sponsored grant. The temporary Kong route and stored key were deleted the same day |
| **npm registry** | Installing and reading rUv's packages (ruflo, agentic-flow, AIDefence) | Installed with `--ignore-scripts` |
| **httpbin.org** | A neutral echo upstream for non-LLM routes (portal API, MCP tools, application auth, guardrail call-outs) | |
| **Lakera Guard API** | Fail-mode test of `ai-lakera-guard` | Called with a deliberately invalid key, so no Lakera account was used |
| **GitHub** (`mondweep/kongai-evaluation`) | This repository: docs, scripts, results and the pull requests for each round | |
| **Claude** (Claude Code cloud sessions, Claude Desktop, Claude Docs) | Ran the tests and wrote them up. Living plan and research docs are Claude Docs (links in each write-up) | |

## Setup

- Konnect trial, EU region, one **serverless** gateway (Kong 3.16 Enterprise).
- **Mock LLM:** an OpenAI-compatible mock runs on the gateway itself as a `pre-function` plugin ([mock/mock-llm.lua](mock/mock-llm.lua)). It echoes back exactly what it received, so we can see what leaves the gateway. It also returns token usage (`x-mock-completion-tokens` header) and fails on demand (`/fail500`, `/fail429` paths). No outside hosting is needed.
- **Real model:** a free-tier Gemini key, used only for checks that need a real provider. Synthetic data only.
- **Tagging:** every Konnect entity is tagged `validation`. [konnect/validation-entities.json](konnect/validation-entities.json) is a snapshot of them. Credentials are excluded, and upstream auth is a dummy value.

## Scripts

| Path | Purpose |
|---|---|
| `scripts/mk.py`, `scripts/k.sh` | Small Konnect API helpers (read `KCONNECT_TOKEN` from the environment) |
| `scripts/setup1.py` | Creates the AI service, routes and AI Proxy plugins for the risk tests |
| `scripts/corpus.py` | Synthetic PII, benign and prompt-injection corpora |
| `scripts/run_guard.py` | Runs a corpus against a guarded route: `python3 run_guard.py /chat-piiguard pii` |
| `scripts/rl.py`, `scripts/lb.py` | Token-limit tests (sequential and concurrent) and failover tests |
| `scripts/pii_san.py`, `scripts/pii_extra.py` | AI Sanitizer redaction quality (D2) |
| `scripts/semguard.py`, `scripts/semsweep.py`, `scripts/sims.py`, `scripts/recreate_sem.sh` | Semantic prompt guard on Supabase pgvector, threshold sweep, offline similarities |
| `scripts/semcache.py`, `scripts/cachetest.py` | Semantic cache setup and the cross-user leak test |
| `scripts/virtual-model/` | Virtual model demo: alias switching, fallback, per-model cost cap |
| `scripts/coverage/probe.py` | Read-only API probe of which Konnect features exist on the trial |
| `scripts/metering/` | Metering & Billing: meters, plan, entitlements, traffic, enforcement, request-log comparison |
| `scripts/gaps/` | Gaps 2 to 8: vault and virtual keys, Kong Identity, MCP catalog and gateway MCP, dashboards and Debugger, application auth, other AI plugins, Service Catalog |
| `scripts/remaining/` | The last menu items: cost budgets and queries, metering settings, forcing and issuing an invoice, teams and roles, identity providers, scorecard re-check |
| `ruv-stack/` | Kong in front of rUv's agent stack (see its README) |
| `mock/mock-llm.lua` | The echo mock LLM |

Raw results for every test are in [results/](results/).

Secrets never go in this repo. `KCONNECT_TOKEN` and `GEMINI_API_KEY` come from the environment. Consumer keys (`keys.json`), `secrets*.json` and `*.pem` files are git-ignored, and keys echoed in results are redacted.

## Headline findings so far

### The five risk claims

1. **AI Sanitizer needs a self-hosted PII service and is uneven.** Serverless can't host it (fails closed by default; with `stop_on_error: false` PII passes silently). With the service running, it fully removed PII from 14/25 structured and 7/15 unstructured prompts, missed every UK NI number, skipped system and assistant messages, and altered 9/25 harmless prompts ("capital of PLACEHOLDER1").
2. **Prompt Guard is regex only.** It blocked 24/25 structured PII items and 14/15 direct injections, but 0/15 unstructured PII items and 0/15 paraphrased injections. System and assistant messages aren't checked by default.
3. **Token and cost limits are soft.** Sequential overshoot is one request. A burst of 10 concurrent requests reached 3.9x the limit.
4. **Failover doesn't work with the default settings** for LLM POSTs. You need `non_idempotent` plus the HTTP codes. DNS failures never fail over.
5. **The client's gateway API key is forwarded to the LLM provider by default** (fix: `hide_credentials: true`). Client IPs and headers go too.
6. **Token and cost accounting is accurate.** Gemini prompt tokens matched 8/8, cost matched the formula, and hidden reasoning tokens are counted.
7. **Gateway overhead is about 1 ms.** Auth and ACL behaved correctly (401/403).
8. **Per-request AI audit data is good** (consumer, model, tokens, cost), and prompts are not stored by default. Admin audit logs are available only by webhook.
9. **The semantic prompt guard blocks nothing with a plausible-looking config.** Setting only `search.threshold` leaves the real threshold (`vectordb.threshold`) empty. With `vectordb.threshold` 0.4 it blocked 30/30 attacks (direct and paraphrased) with 0/25 false positives.
10. **The semantic cache leaks answers between users** with its default route-wide scope: consumer B got consumer A's answer about a different account. A loose threshold also returns wrong answers.
11. **Admin audit events are signed and fast (about 1 s), but incomplete.** Consumer create and delete showed only an authentication event, a 401 produced no event, and when the receiver failed Konnect disabled the webhook and dropped events until it was re-enabled by hand.

### Wider feature coverage

28 of the 32 Konnect menu items have now been tested hands-on. See [docs/feature-coverage.md](docs/feature-coverage.md).

12. **Metering is exact, but a plan's "hard limit" isn't enforced on serverless.** Token totals matched the request log exactly. Blocking needs the `entitlement-enforcement` plugin with Redis, and without Redis it lets everyone through or blocks everyone. Rejected requests are metered by default ([metering-evaluation.md](docs/metering-evaluation.md)).
13. **Revocation takes minutes.** A revoked virtual key or deactivated agent kept working for 288 s, and a deleted Kong Identity client for 232 s ([gaps-evaluation.md](docs/gaps-evaluation.md)).
14. **Provider keys can be kept out of plugin config on serverless** with a Konnect config-store vault. Token Vault, AI Models and catalog MCP links need AI Gateway 2.x on a hybrid data plane.
15. **The MCP proxy's per-tool ACL can be bypassed** through the REST route its tool calls use, unless that route has its own ACL.
16. **Guardrails can fail open silently.** A custom-guardrail expression that errors doesn't block, even with `stop_on_error: true`. Lakera with `stop_on_error: false` passes everything when its service fails.
17. **Virtual models work on serverless through `model_alias`,** but fallback fails with the default `failover_criteria`, and an unknown model gives a 500 ([virtual-model-evaluation.md](docs/virtual-model-evaluation.md)).
18. **Observability is strong but split.** Dashboards have a REST API. Explorer and the Debugger can be scripted only through Konnect's MCP server.
19. **Cost budgets only report on this org.** `posture: enforce` is rejected, and the gateway kept serving after a budget was exceeded. Cost events have no consumer on serverless ([remaining-evaluation.md](docs/remaining-evaluation.md)).
20. **Billing works end to end in the Sandbox.** Cancelling a subscription produced a draft invoice, which was approved and paid ($0.02). Billing cycles can't be shorter than a week.
21. **Team roles scope correctly and take effect fast.** A Viewer role allowed reads and blocked writes, and removal took full effect in about 25 s. Kong Identity can't be an SSO provider for people, so SSO needs an external IdP.
22. **Scorecards miss route-level auth.** The "has an authentication plugin" check only counts plugins on the service, so routes protected by `key-auth` still score as unauthenticated.

## Cleanup

Nothing below has been deleted yet. Ask the owner first.

- **Risk tests:** Konnect entities tagged `validation`, and the audit-log webhook. In Supabase: the `kongai` schema, the `kongai_user` role and the `kongai-audit-receiver` function.
- **Dev Portal demo:** entities tagged `devportal-demo`, the "Wipro Demo Portal" portal and its published API.
- **MCP management demo:** entities tagged `mcp-demo`, and the system account `mcp-demo-agent`.
- **Metering:** entities tagged `metering-eval`, the Metering objects labelled `eval=metering-eval` (cancel the subscription first) and the system account `metering-eval-ingest`.
- **Gaps 2 to 8:** entities tagged `vault-eval`, `agent-id-eval`, `mcpreg-eval`, `appauth-eval` and `aiplug-eval`, plus the Konnect-level objects listed in [docs/gaps-evaluation.md](docs/gaps-evaluation.md#cleanup) (vault, directory, auth server, catalog MCP, dashboard, the `appauth-eval-portal`, catalog services and the scorecard).
- **Remaining menu items:** the advisory budget labelled `eval=remaining-eval`, team `remaining-eval-team` and system account `remaining-eval-sa` ([docs/remaining-evaluation.md](docs/remaining-evaluation.md#cleanup)).
- The `ruv-eval` and `virtual-model-demo` entities were already deleted.
