# Managing Konnect conversationally through MCP

Date: 2026-11-19. Konnect trial, EU region, control plane `serverless-api-gateway-demo`.

**Result:** Kong's hosted Konnect MCP server let Claude Desktop create a gateway service, route and rate-limiting plugin by plain-English request, with no Konnect UI. A system-account token kept the agent inside one control plane. Two gaps showed up: the documented "global" endpoint does not work for an EU org, and the Konnect audit log recorded the agent signing in but not what it changed.

Living research doc: https://claude.ai/artifact/S4E6sVcEyVYtmEZLmh7tby

## 1. What exists

| Option | Read / write | Notes |
|---|---|---|
| **Konnect MCP server** (hosted, `https://<region>.mcp.konghq.com/`) | Read and write | Official. Exposes ~1,417 Konnect API operations behind five meta-tools: `search`, `stemmed_search`, `tags`, `get_schema`, `execute`. Auth by OAuth, personal token (PAT) or system-account token (SPAT). |
| **KAi** (in the Konnect UI) | Read and write, with confirmation | Built on the same tools. Still the GUI. Can export decK, kongctl or Terraform files. |
| **kongctl 1.0** + Kong Skills | Read and write, through a reviewable plan | Declarative plan/apply. Better for changes that need review. |
| decK, Terraform provider | Write through files | GitOps path, no MCP. |
| `Kong/mcp-konnect` (local, Node) | Read-only | **Deprecated**, being archived. |

Org owners can turn MCP off, or turn off write tools, under Konnect AI Settings. Both are on by default.

## 2. Least-privilege setup

The owner's personal token has Admin on all control planes, APIs and portals, so it was not used. Instead:

- System account `mcp-demo-agent`, role **Admin on control plane `serverless-api-gateway-demo` only**.
- Token valid for 7 days (expires 2026-11-26).
- Checked before use: services on that control plane return 200, portals return 403, and only that one control plane is listed.

Claude Desktop's built-in custom connector signs in with OAuth as the user, which would carry the user's full rights. To use the scoped token, the server was added through the `mcp-remote` bridge in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "kong-konnect-demo": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://eu.mcp.konghq.com/",
               "--header", "Authorization:${KONNECT_AUTH}"],
      "env": { "KONNECT_AUTH": "Bearer <system-account token>" }
    }
  }
}
```

Other clients use the same URL: Claude Code (`claude mcp add --transport http ...`), VS Code (`servers` with `type: http`), Gemini CLI (`mcpServers` with `httpUrl`; not covered by Kong's docs and untested here).

## 3. Demo run

All steps ran through the MCP server's `execute` tool from a conversation. Entities are tagged `mcp-demo`.

| # | Request | Result |
|---|---|---|
| 1 | List control planes and their services | `serverless-api-gateway-demo` with 4 existing services |
| 2 | Create service `mcp-demo-httpbin` -> `https://httpbin.org/anything` | 201 Created |
| 3 | Add route `mcp-demo-route`, GET `/mcp-demo` | 201 Created |
| 4 | Add `rate-limiting` to the service, 5/minute, policy `local` | 201 Created |
| 5 | Show everything tagged `mcp-demo` with the proxy URL | 1 service, 1 route, 1 plugin; proxy `https://YOUR-GATEWAY.eu.serverless.gateways.konggateway.com/mcp-demo` |
| 6 | List Dev Portals | **403** "You do not have permission", as intended |

The route went live within about 20 seconds and returned 200.

## 4. Findings

1. **The "global" MCP endpoint fails for an EU org.** Kong's docs say `https://global.mcp.konghq.com/` works for every region. In practice, org-level calls worked but every control-plane call returned 403 "Requested region is not accessible". Switching to `https://eu.mcp.konghq.com/` fixed it.
2. **The scoped system account contained the agent.** Calls outside the one control plane (portals) were refused. This is the main control for an agent that can call any Konnect operation.
3. **The admin audit log shows the agent signing in, not what it did.** The audit webhook received four `AUTHENTICATION_OUTCOME_SUCCESS` events for the system account (12:13 UTC, token introspection, user agent `undici`) when the MCP session started. The three creates at ~12:15 produced **no events** (webhook status active, last response 200). This matches finding A1 in [results.md](results.md): Konnect admin audit logs record authentication, not entity changes. Who changed what has to come from elsewhere, such as the entity's timestamps or a kongctl/decK plan.
4. **`local` rate limiting is per node on serverless gateways.** Fifteen calls in two quick runs never hit 429, and the remaining-quota header jumped between 1 and 4. Each gateway node keeps its own counter, so the effective limit is 5 x the number of nodes. A strict limit needs a shared policy. The agent applied exactly what was asked, so this is a config risk, not an MCP one.
5. **The operation catalogue is huge.** About 1,417 tools across 200+ tags, from portals to billing. `search` and `get_schema` work well, but one misread request could reach any of them. Hence finding 2.

## 5. Recommendations

- Never give an MCP client an owner or org-admin token. Use a system account scoped to the control planes the agent should touch, with a short expiry.
- Use the regional endpoint (`eu.`, `us.` and so on) that matches your org.
- Keep per-call approval on in the client for writes. Turn off write tools in AI Settings when the goal is read-only exploration.
- Don't rely on the admin audit log to reconstruct agent changes. Use kongctl or decK plans for anything that needs a reviewed record.
- Tag everything an agent creates so it can be found and cleaned up.

## 6. Cleanup

Pending the owner's go-ahead: delete entities tagged `mcp-demo` and the `mcp-demo-agent` system account.
