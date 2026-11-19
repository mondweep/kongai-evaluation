"""Gap 4 part 3: an AI Gateway MCP server (ai-mcp-proxy conversion-listener) on a new route, tag mcpreg-eval,
with key-auth and per-tool ACL; then link it to the catalog entry as an implementation."""
import json, secrets
from kapi import call, EU, CE, CP
T = ["mcpreg-eval"]; S = {}
def ok(k, s, b):
    print(k, s, json.dumps(b)[:300]); assert s in (200, 201), k; return b
svc = ok("service", *call("POST", f"{CE}/services", {"name": "mcpreg-eval-orders", "url": "https://httpbin.org", "tags": T}))
rt = ok("route", *call("POST", f"{CE}/services/{svc['id']}/routes", {"name": "mcpreg-eval-mcp", "paths": ["/mcpreg-eval/mcp"], "strip_path": True, "tags": T}))
ok("key-auth", *call("POST", f"{CE}/routes/{rt['id']}/plugins", {"name": "key-auth", "config": {"key_names": ["apikey"]}, "tags": T}))
for u in ["mcp-reader", "mcp-admin"]:
    c = ok("consumer " + u, *call("POST", f"{CE}/consumers", {"username": u, "tags": T}))
    k = "mcpreg-" + secrets.token_hex(8)
    ok("key " + u, *call("POST", f"{CE}/consumers/{c['id']}/key-auth", {"key": k, "tags": T}))
    S[u] = {"id": c["id"], "key": k}
idp = {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
cfg = {"mode": "conversion-listener", "logging": {"log_statistics": True, "log_payloads": False},
       "default_acl": [{"scope": "tools", "allow": ["mcp-reader", "mcp-admin"]}],
       "tools": [
         {"name": "get_order", "description": "Fetch an order by id", "method": "GET", "path": "/anything/orders/{id}",
          "parameters": [idp], "annotations": {"read_only_hint": True}},
         {"name": "cancel_order", "description": "Cancel an order", "method": "POST", "path": "/anything/orders/{id}/cancel",
          "parameters": [idp], "annotations": {"destructive_hint": True},
          "acl": {"allow": ["mcp-admin"]}}]}
s, b = call("POST", f"{CE}/routes/{rt['id']}/plugins", {"name": "ai-mcp-proxy", "config": cfg, "tags": T})
if s >= 400:
    print("plugin err", json.dumps(b)[:1500])
    # retry with annotation key names from the plugin schema if needed
    raise SystemExit
S.update(service=svc["id"], route=rt["id"], plugin=b["id"])
json.dump(S, open("secrets-mcpreg.json", "w"), indent=2)
print("plugin", b["id"])
