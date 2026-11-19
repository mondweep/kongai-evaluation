"""Gap 4 part 4: call the gateway MCP server over streamable HTTP as two consumers; link it in the catalog."""
import json, time, urllib.request, urllib.error
from kapi import call, EU, CP, PROXY
S = json.load(open("secrets-mcpreg.json")); R = {}
URL = f"{PROXY}/mcpreg-eval/mcp"
def rpc(key, method, params=None, i=1):
    body = {"jsonrpc": "2.0", "id": i, "method": method, "params": params or {}}
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if key: h["apikey"] = key
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r: raw = r.read().decode(); st = r.status
    except urllib.error.HTTPError as e: raw = e.read().decode(); st = e.code
    if raw.startswith("event:") or "\ndata:" in raw or raw.startswith("data:"):
        raw = "\n".join(l[5:].strip() for l in raw.splitlines() if l.startswith("data:"))
    try: raw = json.loads(raw)
    except Exception: pass
    return st, raw
time.sleep(1)
for who in ["mcp-reader", "mcp-admin"]:
    k = S[who]["key"]
    R[f"{who} initialize"] = rpc(k, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "eval", "version": "1"}})
    R[f"{who} tools/list"] = rpc(k, "tools/list", i=2)
    R[f"{who} get_order"] = rpc(k, "tools/call", {"name": "get_order", "arguments": {"path_id": "A-1"}}, i=3)
    R[f"{who} cancel_order"] = rpc(k, "tools/call", {"name": "cancel_order", "arguments": {"path_id": "A-1"}}, i=4)
R["no key tools/list"] = rpc(None, "tools/list")
for k, v in R.items(): print(k, v[0], json.dumps(v[1])[:350])
cat = json.load(open("../../results/gap4-mcp-catalog.json")); mid = cat["create"]["body"]["id"]
s, b = call("POST", f"{EU}/v1/mcp-servers/{mid}/implementations",
    {"implementation": {"type": "ai-gateway", "config": {"gateway_control_plane_id": CP, "gateway_mcp_server_id": S["plugin"]}}})
print("impl link", s, json.dumps(b)[:400]); R["impl_link"] = [s, b]
R["impls_after"] = list(call("GET", f"{EU}/v1/mcp-servers/{mid}/implementations"))
json.dump(R, open("../../results/gap4-mcp-gateway.json", "w"), indent=2)
