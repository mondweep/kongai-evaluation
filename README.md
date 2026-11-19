# Kong AI Gateway: evaluation of the five AI risk claims

Kong markets its AI Gateway (Konnect) as addressing five risks: data exposure, uncontrolled costs, compliance and audit, operational risk, and security. This repository holds a hands-on test of those claims. Marketing pages are treated as claims to test, not as evidence.

- [docs/validation-plan.md](docs/validation-plan.md): the tests, with their pass/fail criteria
- [docs/results.md](docs/results.md): results so far
- Living plan doc: https://claude.ai/artifact/FQJeKYkXHUhksYZXqTdK1s

## Setup

- Konnect trial, EU region, one **serverless** gateway (Kong 3.16 Enterprise).
- **Mock LLM:** an OpenAI-compatible mock runs on the gateway itself as a `pre-function` plugin ([mock/mock-llm.lua](mock/mock-llm.lua)). It echoes back exactly what it received, so we can see what leaves the gateway. It also returns token usage (`x-mock-completion-tokens` header) and fails on demand (`/fail500`, `/fail429` paths). No outside hosting is needed.
- **Real model:** a free-tier Gemini key, used only for checks that need a real provider. Synthetic data only.
- **Tagging:** every Konnect entity is tagged `validation`. [konnect/validation-entities.json](konnect/validation-entities.json) is a snapshot of them. Credentials are excluded, and upstream auth is a dummy value.

## Scripts (`scripts/`)

| File | Purpose |
|---|---|
| `mk.py`, `k.sh` | Small Konnect API helpers (read `KCONNECT_TOKEN` from the environment) |
| `setup1.py` | Creates the AI service, routes and AI Proxy plugins |
| `corpus.py` | Synthetic PII, benign and prompt-injection corpora |
| `run_guard.py` | Runs a corpus against a guarded route: `python3 run_guard.py /chat-piiguard pii` |
| `rl.py` | Token-limit tests, sequential and concurrent |
| `lb.py` | Failover tests with different `failover_criteria` |

Secrets never go in this repo. `KCONNECT_TOKEN` and `GEMINI_API_KEY` come from the environment, and consumer keys (`keys.json`) are git-ignored.

## Headline findings so far

1. **AI Sanitizer can't run on serverless.** It needs a self-hosted PII service. It fails closed by default, but with `stop_on_error: false` it passes PII through silently.
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

## Cleanup

Delete all Konnect entities tagged `validation`, the audit-log webhook, and in Supabase the `kongai` schema, the `kongai_user` role and the `kongai-audit-receiver` function.
