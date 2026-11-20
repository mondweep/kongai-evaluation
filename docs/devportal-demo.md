# Dev Portal demo (19 Nov 2026)

Konnect trial, EU region. Every entity is tagged `devportal-demo` and named with the prefix `demo-`.

## What was set up

| Item | Detail |
|---|---|
| Portal | "Wipro Demo Portal" (`wipro-demo-portal`), public, no developer sign-in |
| Pages | `/` (home) and `/apis`. A new portal returns 404 at its root until a published page with slug `/` exists |
| API | "Demo HTTPBin API" 1.0.0, linked to gateway service `demo-httpbin` (route `/demo-httpbin`), published to the portal |
| Portal MCP server | Switched on. It first needed Connected Apps enabled for the portal (`PATCH /v1/connected-apps/portals/{id}` with `enabled` and `default_url`) |
| AI route | Service `demo-ai`, route `POST /demo-ai/chat`, `ai-proxy` to Gemini 2.5 Flash plus `key-auth` (header `apikey`). 200 with a key, 401 without |

## Findings

- To publish with no auth strategy, send `auth_strategy_ids: null`. An empty list is rejected.
- A key-auth application auth strategy exists in the org, but the demo API isn't linked to it. App registration, DCR and OIDC were not tested.
- The portal MCP endpoint (`/api/v3/mcp` on the portal host) can't be reached from the cloud sandbox. It was probed read-only from a local machine: see section 5 of [ruv-stack-evaluation.md](ruv-stack-evaluation.md).

## Cleanup

Delete entities tagged `devportal-demo`, the portal and the published API.
