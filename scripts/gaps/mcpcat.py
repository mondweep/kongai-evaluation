"""Gap 4: Konnect MCP Servers catalog (/v1/mcp-servers) and registry probe. Label eval=mcpreg-eval."""
import json
from kapi import call, EU, GLOBAL, CP
R = {}
def rec(k, s, b): R[k] = {"status": s, "body": b}; print(k, s, json.dumps(b)[:300])

s, b = call("POST", f"{EU}/v1/mcp-servers", {"name": "mcpreg-eval-orders", "display_name": "Orders MCP (eval)",
    "description": "Catalog entry for the eval orders MCP server", "labels": {"eval": "mcpreg-eval"}})
rec("create", s, b); mid = (b or {}).get("id")
if mid:
    tools = [{"name": "get_order", "description": "Fetch an order by id",
              "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
              "annotations": {"readOnlyHint": True}},
             {"name": "cancel_order", "description": "Cancel an order",
              "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
              "annotations": {"destructiveHint": True}}]
    s, b = call("POST", f"{EU}/v1/mcp-servers/{mid}/versions", {"version": "1.0.0", "tools": tools})
    rec("version", s, b)
    s, b = call("POST", f"{EU}/v1/mcp-servers/{mid}/versions", {"version": "1.1.0", "tools": tools[:1]})
    rec("second_version", s, b)
    s, b = call("POST", f"{EU}/v1/mcp-servers/{mid}/implementations", {"type": "ai-gateway"})
    rec("impl_empty", s, b)
    for k, u in [("get", f"{EU}/v1/mcp-servers/{mid}"), ("versions", f"{EU}/v1/mcp-servers/{mid}/versions"),
                 ("impls", f"{EU}/v1/mcp-servers/{mid}/implementations"), ("list", f"{EU}/v1/mcp-servers")]:
        rec(k, *call("GET", u))
for p in ["/v1/mcp-registries", "/v1/registries", "/v1/mcp-registry", "/v2/mcp-registries", "/v1/ai-gateways", "/v1/ai-mcp-servers"]:
    for base in (EU, GLOBAL):
        s, b = call("GET", base + p); R[f"probe {base[8:10]}{p}"] = s; print(base[8:10], p, s)
json.dump(R, open("../../results/gap4-mcp-catalog.json", "w"), indent=2)
