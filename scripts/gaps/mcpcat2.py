"""Gap 4 part 2: version with tools and a remote, implementation link attempts."""
import json, uuid
from kapi import call, EU, CP, PROXY
R = json.load(open("../../results/gap4-mcp-catalog.json"))
mid = R["create"]["body"]["id"]
def rec(k, s, b): R[k] = {"status": s, "body": b}; print(k, s, json.dumps(b)[:400])
tools = [{"name": "get_order", "description": "Fetch an order by id",
          "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
          "annotations": {"read_only_hint": True}},
         {"name": "cancel_order", "description": "Cancel an order",
          "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
          "annotations": {"destructive_hint": True}}]
body = {"version": "1.0.0", "tools": tools, "resources": [], "prompts": [], "packages": [],
        "remotes": [{"type": "streamable-http", "url": f"{PROXY}/mcpreg-eval/mcp"}]}
rec("version", *call("POST", f"{EU}/v1/mcp-servers/{mid}/versions", body))
body["version"] = "1.1.0"
rec("second_version", *call("POST", f"{EU}/v1/mcp-servers/{mid}/versions", body))
fake = str(uuid.uuid4())
rec("impl_fake_server", *call("POST", f"{EU}/v1/mcp-servers/{mid}/implementations",
    {"implementation": {"type": "ai-gateway", "config": {"gateway_control_plane_id": CP, "gateway_mcp_server_id": fake}}}))
rec("versions", *call("GET", f"{EU}/v1/mcp-servers/{mid}/versions"))
rec("impls", *call("GET", f"{EU}/v1/mcp-servers/{mid}/implementations"))
json.dump(R, open("../../results/gap4-mcp-catalog.json", "w"), indent=2)
