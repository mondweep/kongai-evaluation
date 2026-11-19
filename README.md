# Kong AI Gateway: evaluation of the five AI risk claims

Kong markets its AI Gateway (Konnect) as addressing five risks: data exposure, uncontrolled costs, compliance and audit, operational risk, and security. This repository holds a hands-on test of those claims. Marketing pages are treated as claims to test, not as evidence.

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
- Living plan doc: https://claude.ai/artifact/FQJeKYkXHUhksYZXqTdK1s

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

22 of the 32 Konnect menu items have now been tested hands-on. See [docs/feature-coverage.md](docs/feature-coverage.md).

12. **Metering is exact, but a plan's "hard limit" isn't enforced on serverless.** Token totals matched the request log exactly. Blocking needs the `entitlement-enforcement` plugin with Redis, and without Redis it lets everyone through or blocks everyone. Rejected requests are metered by default ([metering-evaluation.md](docs/metering-evaluation.md)).
13. **Revocation takes minutes.** A revoked virtual key or deactivated agent kept working for 288 s, and a deleted Kong Identity client for 232 s ([gaps-evaluation.md](docs/gaps-evaluation.md)).
14. **Provider keys can be kept out of plugin config on serverless** with a Konnect config-store vault. Token Vault, AI Models and catalog MCP links need AI Gateway 2.x on a hybrid data plane.
15. **The MCP proxy's per-tool ACL can be bypassed** through the REST route its tool calls use, unless that route has its own ACL.
16. **Guardrails can fail open silently.** A custom-guardrail expression that errors doesn't block, even with `stop_on_error: true`. Lakera with `stop_on_error: false` passes everything when its service fails.
17. **Virtual models work on serverless through `model_alias`,** but fallback fails with the default `failover_criteria`, and an unknown model gives a 500 ([virtual-model-evaluation.md](docs/virtual-model-evaluation.md)).
18. **Observability is strong but split.** Dashboards have a REST API. Explorer and the Debugger can be scripted only through Konnect's MCP server.

## Cleanup

Nothing below has been deleted yet. Ask the owner first.

- **Risk tests:** Konnect entities tagged `validation`, and the audit-log webhook. In Supabase: the `kongai` schema, the `kongai_user` role and the `kongai-audit-receiver` function.
- **Dev Portal demo:** entities tagged `devportal-demo`, the "Wipro Demo Portal" portal and its published API.
- **MCP management demo:** entities tagged `mcp-demo`, and the system account `mcp-demo-agent`.
- **Metering:** entities tagged `metering-eval`, the Metering objects labelled `eval=metering-eval` (cancel the subscription first) and the system account `metering-eval-ingest`.
- **Gaps 2 to 8:** entities tagged `vault-eval`, `agent-id-eval`, `mcpreg-eval`, `appauth-eval` and `aiplug-eval`, plus the Konnect-level objects listed in [docs/gaps-evaluation.md](docs/gaps-evaluation.md#cleanup) (vault, directory, auth server, catalog MCP, dashboard, the `appauth-eval-portal`, catalog services and the scorecard).
- The `ruv-eval` and `virtual-model-demo` entities were already deleted.
