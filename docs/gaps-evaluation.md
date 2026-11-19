# Closing the coverage gaps (19 Nov 2026)

These are plan items 2 to 8 from [feature-coverage.md](feature-coverage.md). Everything ran on the Konnect trial (EU region) and the serverless gateway (Kong 3.16), with the owner's approval. Each gap used its own tag or label, so cleanup is one sweep per tag (see Cleanup). LLM traffic went to the mock LLM. Gemini was used only where a plugin needs its own LLM, and only with dummy data. Scripts are in [`scripts/gaps/`](../scripts/gaps/), and raw results are in `results/gap*.json`. Credentials stay in git-ignored `secrets*.json` and `*.pem` files, and keys echoed in responses were redacted.

## Bottom line

| Gap | Verdict | The one thing to know |
|---|---|---|
| 2 Token Vault and Virtual Keys | Works | Revoking a key or deactivating an agent took **about 5 minutes** (288 s) to bite at the gateway |
| 3 Agent identity (Kong Identity) | Works | Per-agent OAuth client credentials and per-agent token limits work. Deleting a client took **about 4 minutes** (232 s) to stop it |
| 4 MCP Servers and Registries | Partial | The catalog entry works, but it can only be linked to an AI Gateway (2.x) MCP server, not to the serverless `ai-mcp-proxy`. There is no MCP Registry API on the trial. **The per-tool ACL can be bypassed** through the REST route that the MCP tool calls |
| 5 Observability | Works | Dashboards have a public API. Explorer and the Debugger work, but only through the UI or Konnect's MCP server, not the public REST API |
| 6 Application Auth | Partial | The admin API can create the developer, app and approved registration, and the gateway enforces it. Only the developer can mint the key, on the portal itself, so the last step wasn't run |
| 7 Other AI plugins | Works, with one trap | Decorator, template, request and response transformers, and the custom guardrail all work. **A custom-guardrail expression that errors fails open** without any error |
| 8 Catalog | Works | Catalog services, resource mapping, API mapping and a scorecard work. Scorecard scores hadn't appeared after a few minutes |

## Gap 2: Token Vault, Konnect vault and Virtual Keys (tag `vault-eval`)

| Test | Result |
|---|---|
| V1 Konnect Config Store vault | A secret in a config store, referenced as `{vault://veval/mock-provider-key}` in `ai-proxy`. The upstream received the canary value, and the plugin config shows only the reference. This fixes S3c (provider key readable in plugin config). |
| V2 Kong Identity directory | The trial allows **one** directory, and it must allow all control planes. Principals of type `agent` were created as `agent-a` and `agent-b`. |
| V3 Virtual keys (principal API keys) | `key-auth` with `principals.enabled`, directory `vault-eval`. Both agents got 200, a wrong key and a missing key got 401. `principals` and `identity_realms` are mutually exclusive, so `identity_realms` must be `[]`. Minimum key TTL is 300 s. |
| V4 What the upstream sees | `x-credential-identifier`, but not the principal's name. |
| V5 Revocation | Deleting agent-b's key and deactivating agent-a both took **288 s** to return 401. Requests kept succeeding until then. |
| V6 Token Vault | A public key must be registered before a static secret can be stored. The secret is write-only (never returned on read), and a second credential on the same provider returns 409. **The gateway can't use Token Vault on serverless**: it's consumed by AI Gateway 2.x auth strategies, which need a hybrid data plane. |

## Gap 3: Agent identity with Kong Identity (tag `agent-id-eval`)

| Test | Result |
|---|---|
| A1 Auth server and clients | Auth server `agent-id-eval` (issuer on `*.eu.identity.konghq.com`), scope `llm:chat`, one client per agent. The agent is also registered in the org agent registry (`/v1/agents`). |
| A2 Gateway | `openid-connect` does the client-credentials exchange itself, so agents send their client ID and secret and never handle tokens. The cloud sandbox can't reach the identity host directly. Consumers are mapped by `custom_id` = client ID. |
| A3 Identity reaches the upstream | The upstream saw `x-agent-sub` (the token subject) and the consumer username. |
| A4 Per-agent limits | `ai-rate-limiting-advanced` at 200 tokens a minute per consumer: alpha got 429 from its third request, while beta, sharing the route, was unaffected. |
| A5 Bad credentials | A wrong secret and no credentials both returned 401. |
| A6 Revocation | Deleting agent-beta's client took **232 s** to stop it: the gateway keeps using its cached token. |

## Gap 4: MCP Servers catalog and gateway MCP (label/tag `mcpreg-eval`)

| Test | Result |
|---|---|
| M1 Catalog MCP server | `/v1/mcp-servers` entry `mcpreg-eval-orders` with version 1.0.0 (two tools with `read_only_hint` and `destructive_hint`, and a streamable-HTTP remote). Only one version is allowed; a second returns 409 "alias: latest already exists". |
| M2 Implementation link | Accepts only an **AI Gateway (2.x) MCP server**. Linking the serverless `ai-mcp-proxy` plugin returned 404 "AI Gateway MCP server not found", and `/v1/ai-gateways` is empty on the trial. |
| M3 MCP Registries | No API. `/v1/mcp-registries` and similar paths return 404 on EU and global. |
| M4 Gateway MCP server | `ai-mcp-proxy` in `conversion-listener` mode turned two REST endpoints into MCP tools with `key-auth`. `initialize`, `tools/list` and `tools/call` work over streamable HTTP. Tool arguments are renamed (`id` becomes `path_id`). |
| M5 Per-tool ACL | `tools/list` is filtered per consumer: the reader sees only `get_order`, the admin sees both. The reader calling `cancel_order` gets 403. |
| M6 **ACL bypass** | Tool calls re-enter Kong through a REST route (the tool path is a Kong path). With no auth on that route, anyone could call `cancel_order` directly (200). With `key-auth` on it, anonymous calls get 401, but **the reader can still cancel with their own key (200)**, because the per-tool ACL only applies on the MCP route. The REST route needs its own ACL, or must not be reachable from outside. |
| M7 Credential forwarding | The client's API key, consumer ID and username are forwarded to the upstream API. Set `hide_credentials` on `key-auth`. |

## Gap 5: Observability (label `obs-eval`)

| Test | Result |
|---|---|
| O1 Custom dashboard | Created through `POST /v2/dashboards` with five tiles: AI cost by consumer, tokens by model over time, MCP tool calls, p95 latency by route, error rate. Datasources: `llm_usage`, `agentic_usage` and `api_usage`. |
| O2 Explorer | No public REST endpoint (explore, reports and debug-session paths return 404). The same queries run through Konnect's MCP server (`query_llm_analytics`, `query_mcp_analytics`, `query_analytics`): cost and tokens per consumer, p95 latency per route, and MCP calls per tool and consumer all came back. |
| O3 MCP analytics | Calls were attributed to the right tool and consumer. The reader's denied `cancel_order` calls were **not** attributed to the tool name. |
| O4 Debugger | A 45-second session on `/mcpreg-eval/mcp` was started through Konnect's MCP server and captured traces. The data plane reported support for traces, logs and payload sanitisation. Spans showed `ai-mcp-proxy` taking about 50 ms in the access phase and the inner REST call about 99 ms, while `key-auth` took 0.4 ms. |
| O5 Reports | No API found. Not tested. |

## Gap 6: Application Auth (label/tag `appauth-eval`, separate portal)

The demo portal was left untouched. A second portal, `appauth-eval-portal`, was created; the trial allowed it.

| Test | Result |
|---|---|
| P1 Setup | A `key_auth` strategy, the API "AppAuth Eval API" linked to its own gateway service, and a publication to the eval portal with that strategy. |
| P2 Gateway plugin | Publishing with a strategy **automatically added `konnect-application-auth`** to the implementing service (`auth_type: v2-strategies`, scoped to the API). Without a key: 401. With a wrong key: 401. |
| P3 Developer, app, registration | All three were created through the admin API (the developer approved, with no invitation email; the registration approved). |
| P4 Credential | **Not run.** The admin API can't create an app credential (405). Only the developer can, on the portal, which the cloud sandbox can't reach. To finish: sign up on the eval portal, create an app, register it for the API, and call `/appauth-eval/get` with the key. |
| P5 Small issue | App labels were accepted on create but came back empty. |

## Gap 7: Other AI plugins (tag `aiplug-eval`)

| Plugin | Result |
|---|---|
| `ai-prompt-decorator` | Works. The system message was prepended and the suffix appended before the request reached the model. |
| `ai-prompt-template` | Works, and is strict: with `allow_untemplated_requests: false`, free text gets 400, and a missing template variable gets 400 "missing template parameters: [lang]". |
| `ai-request-transformer` (Gemini) | Works: the LLM replaced `city` with `REDACTED` before the request reached the upstream. Adds about 1 s. |
| `ai-response-transformer` (Gemini) | Works: it rewrote the upstream's response into a one-line summary. When Gemini returned 429 (free-tier limit), the client got **400** "failed to introspect request", so it fails closed. |
| `ai-llm-as-judge` (Gemini) | Ran without error. The score was not visible in the request log, so it was not verified. |
| `ai-custom-guardrail` | Works with a call-out to an HTTP service: `$(content)` holds the prompt and `resp` the parsed reply. **Trap:** the first block expression used `string.find`, which isn't available in the sandbox. It silently evaluated as "don't block", so a forbidden prompt went through, even with `stop_on_error: true`. The method form `input:find(...)` worked (400 for forbidden, 200 for clean). Test every guardrail expression with a positive case. |
| `ai-lakera-guard` | With an invalid key: `stop_on_error: true` gives 500 (fails closed), and `stop_on_error: false` gives 200 (**fails open**, unguarded). |
| Not run | `ai-prompt-compressor` (needs a compressor service), `ai-rag-injector` and `ai-semantic-response-guard` (need a vector DB), AWS, Azure and GCP guardrails (need cloud accounts). All 18 plugin schemas exist on the serverless gateway. |

## Gap 8: Service Catalog (label `catalog-eval`)

| Test | Result |
|---|---|
| C1 Resources | All 11 gateway services were discovered automatically as `gateway_svc` resources. |
| C2 Catalog services | Two created and mapped to their gateway services. The AppAuth eval API was mapped to one of them. |
| C3 Scorecard | Created from the `kong_best_practices` template, selecting services by label: error rate under 5% and p95 under 1,500 ms over 30 days, and "has an Authentication plugin". The template's own criteria are rejected as they are (missing `threshold` and `category`), so they must be filled in. Both services were selected, but **no scores had appeared** after a few minutes. |
| C4 Integrations | 16 are listed. 12 need third-party authorisation (GitHub, PagerDuty, Datadog and others) and were not connected. |

## What this means

- **Revocation is not instant.** Budget for about 5 minutes between revoking an agent or key and the gateway refusing it. For incidents, also disable the consumer or route.
- **Keep provider keys in a vault.** The Konnect config-store vault works on serverless today. Token Vault and Virtual Keys for AI providers need AI Gateway 2.x on a hybrid data plane.
- **Lock down REST routes behind MCP tools.** Put the same ACL on them, or make them internal. Otherwise the per-tool ACL is advisory.
- **Test every guardrail with a case that should block,** and prefer `stop_on_error: true`. Expression errors and vendor outages can quietly fail open.
- **Observability is strong, but the API is split.** Dashboards are scriptable through REST. Explorer and the Debugger are scriptable only through Konnect's MCP server.

## Cleanup

Delete by tag on the control plane: `vault-eval`, `agent-id-eval`, `mcpreg-eval`, `appauth-eval`, `aiplug-eval`. Konnect objects:
- Config store `vault-eval-store` and vault `veval`.
- Directory `vault-eval` (it holds the principals, Token Vault key and credential).
- Auth server `agent-id-eval` and agent `agent-alpha` in `/v1/agents`.
- Catalog MCP `mcpreg-eval-orders`.
- Dashboard "obs-eval AI and MCP overview".
- Portal `appauth-eval-portal` (with its developer and app), API "AppAuth Eval API" and strategy `appauth-eval-key`.
- Catalog services `catalog-eval-*` and scorecard "catalog-eval best practices".
