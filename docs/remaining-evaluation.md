# The remaining Konnect menu items (19 Nov 2026)

This round covered the menu items left after [gaps-evaluation.md](gaps-evaluation.md): Cost Analytics, Cost Management budgets, Metering Settings, Billing, Groups, Identity Providers, Observability Summary and Reports, and a re-check of the Catalog scorecard. Everything ran on the Konnect trial (EU region) with the owner's approval. New objects use the tag or label `remaining-eval`. Traffic went to the mock LLM. Scripts are in [`scripts/remaining/`](../scripts/remaining/), and raw results are in `results/remaining-*.json`. Tokens and secrets stay in git-ignored `secrets*.json` files.

With this round, **28 of the 32 menu items have been tested hands-on** (5 of them in part). Two were only seen (Users, Catalog Integrations) and two can't be run on this trial (MCP Registries, Reports). See [feature-coverage.md](feature-coverage.md).

## Bottom line

| Item | Verdict | The one thing to know |
|---|---|---|
| Cost Management (budgets) | Works, advisory only | **Budgets can only be advisory on this org.** `posture: enforce` is rejected, and the gateway kept serving after the budget was exceeded |
| Cost Analytics | Works | Cost by model, forecast and field values all work, but usage has **no subject** on serverless, so cost can't be split by consumer here |
| Metering Settings | Works | The built-in Sandbox app covers payment, tax and invoicing, and the default billing profile auto-advances invoices |
| Billing | Works | **A real invoice was issued:** cancelling the subscription produced a draft, which was approved and paid in the Sandbox ($0.02) |
| Groups (teams and roles) | Works | A Viewer team role gave read-only access to one control plane. Removing the account from the team took **about 25 seconds** to take full effect |
| Identity Providers | Partial | **Kong Identity can't be an SSO provider** (no authorization-code grant). SSO needs an external IdP such as Okta or Entra ID |
| Observability Summary | Partial | The page has no API, but the same numbers came from Konnect's MCP server |
| Observability Reports | Can't run | No API in REST or in Konnect's MCP server. UI only |
| Catalog scorecard (re-check) | Works | Scores appeared, at 33% for both services. **The auth check ignores route-level auth plugins** |

## Cost Management and Cost Analytics (label `eval=remaining-eval`)

| Test | Result |
|---|---|
| CM1 Budget | Budget "remaining-eval advisory" for model `mock`, a $0.000001 daily limit, `effect: limit`. The window needs `anchored_at` with a zone, such as `2026-11-19T00:00:00+00:00[Europe/London]`. |
| CM2 Enforce | `posture: enforce` returned 400 "must be `advisory`". Enforcing budgets isn't available on this org. |
| CM3 Over the budget | The balance showed $50.91 consumed against the limit, so it was well over. **Four more requests still got 200.** An advisory budget only reports. |
| CA1 Cost query | Grouped by model: 620 events, 8 unpriced, 15,128 input tokens, $39.33 reported cost for `mock` today. `filters` must be an object, not an array. |
| CA2 Attribution | `subject` is null on every event. Attribution plugins exist only for AI Gateway 2.x, so on serverless cost can't be split per consumer here. Metering ([metering-evaluation.md](metering-evaluation.md)) does attribute per consumer. |
| CA3 Forecast | Returned `insufficient_history` (needs more than one day of data). |
| CA4 Field values | Seven models seen, including `claude-mock`, `cognitum-auto` and `gemini-2.5-flash` from earlier rounds. |
| Open question | The budget's consumed value ($50.91) is higher than the query's reported cost for the same model and day ($39.33). We didn't find out why. It may include estimated cost for unpriced events. |

## Metering Settings and Billing

| Test | Result |
|---|---|
| MS1 Apps and profile | One app, Konnect's built-in **Sandbox** (payment, tax and invoicing, no credentials). The default billing profile `openmeter-sandbox` uses it, with a one-hour collection interval, auto-advance and progressive billing. |
| MS2 Other settings | Currencies and tax codes are listed (tax codes carry Stripe mappings). No notification channels exist. |
| B1 Short billing cycle | Not allowed. Plan cadences must be one of P1W, P2W, P4W, P1M, P3M, P6M, P12M or P1Y. Hourly and daily return 400. |
| B2 Forcing an invoice | Cancelling Alice's `metering-eval` subscription immediately created a draft invoice for the usage so far. |
| B3 Issuing it | `snapshot-quantities` 200, `advance` 400 (the draft was waiting for auto-approval), `approve` 200. Invoice **OM-SANDBOX-METE-1** was issued and marked paid: one line, "AI tokens", **$0.02**. |

## Groups: teams and roles (tag `remaining-eval`)

A team `remaining-eval-team` was given the **Viewer** role on the serverless control plane. A system account `remaining-eval-sa` was added to it, with a six-hour token.

| Test | In the team | After removal from the team |
|---|---|---|
| List gateway services | 200 | 200 for about 20 s, then 403 |
| Create a gateway service | 403 | 403 |
| List control planes | 200 (only the one it has a role on) | 403 at once |
| Metering meters | 403 | 403 |
| List teams | 200 | 200 |

- Roles are scoped correctly: Viewer is read-only, and nothing else in the org was readable apart from the team list.
- **Removal isn't instant everywhere.** The control-plane list stopped at once, but gateway reads continued for about 20 s. That is much faster than the 4 to 5 minutes seen for gateway credentials in gap 2 and 3.
- Any account can list the org's teams.
- Deleting the token gave 403 straight away, and 401 within a minute.

## Identity Providers

- The org settings were only read, never changed: basic auth on, OIDC and SAML off, no identity providers set up.
- The plan was to set up OIDC SSO on the separate eval portal with Kong Identity as the provider. **Kong Identity refused an authorization-code client** (400 "authorization code grant type is not allowed"). It only issues machine tokens (client credentials), so it can't sign in people.
- To finish this, the owner needs an external IdP (Okta, Entra ID, Google or Auth0) and a portal or org SSO setup. Testing the sign-in needs a browser.

## Observability Summary and Reports

- **Summary:** no REST or MCP endpoint. The same numbers came from Konnect's MCP server (`query_analytics`, last 24 hours): 2,128 requests at 2xx (p95 764 ms), 258 at 4xx (p95 733 ms) and 140 at 5xx (p95 1,748 ms).
- **Reports:** nothing in the REST API or among the 1,417 tools of Konnect's MCP server. Reports can only be tried in the UI.

## Catalog scorecard re-check

The scorecard from gap 8 now has scores: **33%** for both catalog services.

| Criterion | AI chat (`aiplug-eval`) | Orders MCP (`mcpreg-eval-orders`) |
|---|---|---|
| Error rate under 5% (30 days) | Fail, 47% | Fail, 28% |
| p95 latency under 1,500 ms | Pass, 1,203 ms | Pass, 350 ms |
| Has an authentication plugin | Fail, 0 plugins | Fail, 0 plugins |

The high error rates are our own deliberate 4xx tests. **The authentication check failed even though both services' routes have `key-auth`.** It only counts plugins on the service itself, so a route-level auth design scores as "no auth".

## Still not done, and what each needs

| Item | What it needs |
|---|---|
| Users | Inviting a user sends a real email, so we didn't. Needs the owner's OK and an address |
| Catalog Integrations | Each one needs the owner to authorise a third-party app (GitHub, PagerDuty, Datadog and others) |
| Application Auth key | The developer has to create the key on the portal, which the cloud sandbox can't reach |
| Identity Providers sign-in | An external IdP and a browser |
| Observability Reports | The Konnect UI |
| AI Gateways, Models and Providers in use, Token Vault in use, catalog MCP link, entitlement enforcement with Redis | A self-hosted (hybrid) data plane, such as Kong and Redis in Docker on a laptop |
| MCP Registries | Not available on this trial |

## Cleanup

- Budget "remaining-eval advisory" (`/v1/ai-cost-management`, label `eval=remaining-eval`).
- Team `remaining-eval-team` and system account `remaining-eval-sa` (its token is already deleted).
- Alice's `metering-eval` subscription is now cancelled, and invoice OM-SANDBOX-METE-1 is paid in the Sandbox. Invoices can't be deleted.
