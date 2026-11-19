"""Gap 5: steady MCP traffic on /mcpreg-eval/mcp for ~100 s so a debug session has traces."""
import json, time, urllib.request, urllib.error
from kapi import PROXY
S = json.load(open("secrets-mcpreg.json"))
def rpc(key, method, params):
    req = urllib.request.Request(f"{PROXY}/mcpreg-eval/mcp", method="POST",
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "apikey": key})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status
    except urllib.error.HTTPError as e: return e.code
t0 = time.time(); n = 0
while time.time() - t0 < 100:
    rpc(S["mcp-admin"]["key"], "tools/call", {"name": "get_order", "arguments": {"path_id": f"O-{n}"}})
    rpc(S["mcp-reader"]["key"], "tools/call", {"name": "cancel_order", "arguments": {"path_id": "X"}})
    n += 1; time.sleep(3)
print("sent pairs", n)
