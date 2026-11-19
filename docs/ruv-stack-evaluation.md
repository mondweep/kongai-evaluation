# Kong AI Gateway with rUv's agent stack

19 Nov 2026. Living version (with comments): https://claude.ai/artifact/SRzpY3kAQB2xy5rJQAKUS6

Evidence levels: **claimed** (README or marketing), **read in code** (published npm package inspected), **documented** (vendor docs), **demonstrated** (our test).

## Bottom line

Kong and rUv's stack sit at different layers. Ruflo, agentic-flow and ruOS are the **agent harness**: they pick agents and models, keep memory, and police themselves from inside the agent process. Kong is the **network chokepoint**: keys, budgets, audit and access control enforced outside the agent, where the agent can't switch them off. Kong adds real value in front of rUv's agents, but only if it is the agents' *only* route to models and tools. Cognitum One, rUv's company, sells no gateway, so Kong doesn't compete with it.

## What rUv's stack is

| Piece | What it does | Evidence |
|---|---|---|
| Ruflo (formerly claude-flow, 3.78.0) | Meta-harness inside Claude Code and Codex: ~100 agents, swarms, hooks, AgentDB memory, MCP server, plugins (AIDefence, cost tracker, federation) | claimed |
| agentic-flow 3.5.5 | Agent runtime with an LLM router and local proxies that turn Anthropic Messages calls into OpenRouter/OpenAI or Gemini calls. Reads `ANTHROPIC_BASE_URL`, `OPENROUTER_BASE_URL`, `GEMINI_BASE_URL` | read in code |
| AgentDB / RuVector | Vector and graph memory | claimed |
| ruflo-aidefence | Pattern-pack prompt-injection and PII scanner exposed as MCP tools | claimed, then tested |
| ruflo-cost-tracker | Reads session logs after the fact; budget alerts | claimed |
| Federation | Agent-to-agent messaging (mTLS + ed25519) with outbound PII filter | claimed |
| Cognitum One, Inc. (cognitum.one) | rUv's commercial company: ruOS (MCP-native agent OS on customer infrastructure, Oct 2026), commercial RuVector, ruPro. Press releases cite GDPR/HIPAA/DORA, which are claims, not certifications | claimed |

## Fit, overlaps and conflicts

- **Kong adds:** enforcement outside the agent; agents never hold provider keys; per-agent identity and central logs; budgets enforced before spend; governed MCP tools (AI MCP Proxy) and API discovery (Dev Portal MCP server).
- **Overlap:** prompt-injection and PII guards exist on both sides, and both are pattern based. Cost tracking (ruflo after the fact, Kong in the path) is complementary.
- **Conflict:** agentic-flow's model router vs Kong's model pinning and load balancing. One of them must own model choice.
- **Risks:** bypass if agents can reach providers directly; AI MCP Proxy has no guardrails of its own and can't share a route with other AI plugins; identity headers reach the provider; fast-moving rUv releases (pin versions); ruflo plugins run with the user's permissions.

## Hands-on results

All data synthetic. Every Konnect entity was tagged `ruv-eval` and deleted afterwards. The Gemini key was in Konnect for about three minutes. Scripts are in [`ruv-stack/`](../ruv-stack/).

### 1. AIDefence vs Kong Prompt Guard (same 95-prompt corpus)

| Set | Kong Prompt Guard | AIDefence | Either |
|---|---|---|---|
| Direct injection (15) | 14 | 11 | **15** |
| Reworded, encoded, foreign or indirect (15) | 0 | 5 | **5** |
| Benign, false positives (25) | 0 | 0 | 0 |
| Structured PII (25) | 24 | 9 (cards, emails only) | 24 |
| Unstructured PII (15) | 0 | 0 | 0 |

AIDefence caught leetspeak, base64, Spanish and hidden-in-a-document attacks that Kong missed. Both missed role-play, false authority and polite rewording. AIDefence has no UK PII patterns. Raw data: [`results/ruv-aidefence-corpus.json`](../results/ruv-aidefence-corpus.json).

### 2. agentic-flow through Kong

- Anthropic Messages request (Claude Code's format) → agentic-flow's Anthropic-to-OpenRouter proxy → Kong (OpenAI format) → mock LLM, then Gemini 2.5 Flash (4 real calls). Tool calls survived both translations.
- Each agent had its own Kong key; Kong swapped it for the provider key. Agents never held the Gemini key. No key gave 401.
- agentic-flow sends `Authorization: Bearer <key>`; key-auth accepted the whole header value as the credential, so no custom auth code was needed.
- Konnect logged each call per agent with model, tokens and cost.
- Budget 2,000 tokens/min per agent: a burst of 60 concurrent requests from one agent all passed (about 2.2x the limit), then 429s. The other agent was unaffected.
- Asking for a model other than the configured one gave 400 "cannot use own model". agentic-flow's router can't choose models through a single Kong route.
- Kong forwarded consumer id and username to the upstream; agentic-flow adds `x-title`, `http-referer` and its own default system prompt.

### 3. Kong as a governed MCP server (AI MCP Proxy, serverless)

- Two REST endpoints became MCP tools (`list_orders`, `delete_order`) over streamable HTTP. Tested with the official MCP TypeScript SDK client 1.32.2, the transport Claude Code uses for remote servers.
- Per-tool ACL: agent A saw both tools; agent B saw only `list_orders`, and calling `delete_order` anyway gave HTTP 403. Unknown tool: JSON-RPC error. Arguments were schema-checked, and `A-2&id=ALL` reached the API as one value.
- Konnect's request log records MCP traffic per consumer, with JSON-RPC method, tool name, latency and session id ([`results/ruv-mcp-konnect-log.json`](../results/ruv-mcp-konnect-log.json)). The refused (403) call is logged without the tool name.

### 4. Second round of probes

- **Claude Code's own format straight into Kong, no agentic-flow:** an `ai-proxy` route with `llm_format: anthropic` accepted Anthropic Messages requests with the agent's key in `x-api-key` (what `ANTHROPIC_API_KEY` sends), swapped in the provider key, passed system prompt and tool definitions through unchanged, and passed streaming (SSE) through. So ruflo inside Claude Code can point `ANTHROPIC_BASE_URL` at Kong directly. Caveats: a Bearer token (`ANTHROPIC_AUTH_TOKEN` style) got 401 with `key_names: [x-api-key]`, so add `authorization` too; and Kong again refused any model other than the configured one, which matters because Claude Code also calls a small fast model. Tested against a mock Anthropic upstream; a full Claude Code session couldn't be run from the cloud sandbox because its Claude Code is managed by the host and ignored the test key.
- **Rate limit on MCP tools:** with 5 requests/minute per consumer, an agent's MCP connection handshake used up 3 of them, so only 2 tool calls got through before 429. The other agent was unaffected. Budget for the handshake (and pings) when setting MCP limits.

### 5. Dev Portal MCP server (Wipro Demo Portal, read-only probes)

Probed `https://c07265dd25b4.eu.kongportals.com/api/v3/mcp` with the MCP SDK client (`ruv-stack/portal-tools.mjs`, `portal-call.mjs`). Nothing was written.

- **It's a "code mode" server.** It exposes 3 meta-tools rather than ~22 tools: `search` (find tools), `get_schema` (their parameters) and `execute` (run a Python block that chains `await call_tool(...)` calls on Kong's side). Server reports itself as `portal-mcp` 3.4.2. An agent needs to be comfortable writing small Python snippets; Claude and ruflo agents are, simpler agents may not be.
- **Anonymous read works on a public portal.** With no login, an agent could list the published API (Demo HTTPBin API), its spec versions, the portal pages, and run full-text search across operations and docs (it found `POST /anything`, "Echo a JSON body").
- **Developer-only and app tools refuse.** `list_applications`, `list_application_auth_strategies`, `get_api_actions` and `portal_list_mcp_registries` returned 404 without a signed-in developer.
- **Write tools are hidden, not just blocked.** With "MCP server write operations" off, `create_application` and `delete_application` don't exist (`get_schema` says "Tools not found"), so an agent can't even try them.
- **What it is not:** it doesn't proxy calls to the APIs and issues no API keys. It's a governed catalogue. For rUv's agents it's the discovery step; the calls themselves would then go through a Kong route (or AI MCP Proxy) with the agent's own consumer key.

### Not tested

- A live Claude Code + ruflo session against Kong (run it on a laptop: `ANTHROPIC_BASE_URL=<gateway>/<route> ANTHROPIC_API_KEY=<kong consumer key> claude`, and `claude mcp add --transport http portal https://<portal>/api/v3/mcp`).
- Portal MCP with developer login (OAuth) and write operations on, since the demo portal is public with writes off.
- agentic-flow's own agents with a remote MCP server (its loader only starts stdio servers, so it needs a bridge).

## What this changes

- Use both guards: AIDefence inside the agent and Kong Prompt Guard at the gateway. Neither handles reworded attacks or unstructured PII.
- Kong's value is demonstrated: per-agent keys, provider key isolation, central per-agent logs, per-tool MCP access control, and direct support for Claude Code's request format.
- Plan around: budgets overshooting under swarm bursts, one model per route, MCP handshakes counting against rate limits, and identity headers reaching the provider.
