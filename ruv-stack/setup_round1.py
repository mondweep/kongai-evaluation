# Round 1: agentic-flow -> Kong LLM route, and Kong AI MCP Proxy with per-tool ACLs. All entities tagged ruv-eval.
# Needs KCONNECT_TOKEN. Uses ../scripts/mk.py helpers. Writes keys.json (consumer keys; git-ignored).
import json, secrets, sys
sys.path.insert(0, "../scripts")
from mk import call, GW, proxy
T = ["ruv-eval"]
host = GW.split("//")[1]
lua = open("../mock/mock-llm.lua").read()
orders_lua = open("orders.lua").read()
s = call("POST", "services", {"name": "ruv-eval-mock", "url": "http://localhost:9", "tags": T})
r = call("POST", f"services/{s['id']}/routes", {"name": "ruv-eval-mock-llm", "paths": ["/ruv-mock-llm"], "tags": T})
call("POST", f"routes/{r['id']}/plugins", {"name": "pre-function", "tags": T, "config": {"access": [lua]}})
r = call("POST", f"services/{s['id']}/routes", {"name": "ruv-eval-orders-backend", "paths": ["/ruv-orders-backend"], "tags": T})
call("POST", f"routes/{r['id']}/plugins", {"name": "pre-function", "tags": T, "config": {"access": [orders_lua]}})
# LLM route: agentic-flow sends "Authorization: Bearer <key>", so key-auth reads the whole header value.
s = call("POST", "services", {"name": "ruv-eval-ai", "url": "https://example.com", "tags": T})
r = call("POST", f"services/{s['id']}/routes", {"name": "ruv-eval-chat", "paths": ["/ruv-chat"], "tags": T})
call("POST", f"routes/{r['id']}/plugins", {"name": "key-auth", "tags": T, "config": {"key_names": ["authorization"], "hide_credentials": True}})
call("POST", f"routes/{r['id']}/plugins", {"name": "ai-proxy", "tags": T, "config": proxy(path="/ruv-mock-llm/v1/chat/completions")})
call("POST", f"routes/{r['id']}/plugins", {"name": "ai-rate-limiting-advanced", "tags": T, "config": {"identifier": "consumer",
     "llm_providers": [{"name": "openai", "limit": [2000], "window_size": [60]}], "strategy": "local", "sync_rate": -1}})
# MCP route: two REST endpoints exposed as MCP tools; delete_order only for ruv-agent-a.
s = call("POST", "services", {"name": "ruv-eval-orders-api", "url": GW + "/ruv-orders-backend", "tags": T})
r = call("POST", f"services/{s['id']}/routes", {"name": "ruv-eval-mcp", "paths": ["/ruv-mcp"], "tags": T})
call("POST", f"routes/{r['id']}/plugins", {"name": "key-auth", "tags": T, "config": {"key_names": ["apikey"], "hide_credentials": True}})
call("POST", f"routes/{r['id']}/plugins", {"name": "ai-mcp-proxy", "tags": T, "config": {"mode": "conversion-listener",
     "logging": {"log_statistics": True, "log_payloads": False, "log_audits": True},
     "default_acl": [{"scope": "tools", "allow": ["ruv-agent-a", "ruv-agent-b"]}],
     "tools": [
       {"name": "list_orders", "description": "List all customer orders", "method": "GET", "scheme": "https", "host": host,
        "path": "/ruv-orders-backend", "annotations": {"read_only_hint": True}},
       {"name": "delete_order", "description": "Delete a customer order by id", "method": "DELETE", "scheme": "https", "host": host,
        "path": "/ruv-orders-backend", "parameters": [{"name": "id", "in": "query", "required": True, "schema": {"type": "string"}, "description": "Order id"}],
        "annotations": {"destructive_hint": True}, "acl": {"allow": ["ruv-agent-a"]}}]}})
keys = {}
for c in ["ruv-agent-a", "ruv-agent-b"]:
    x = call("POST", "consumers", {"username": c, "tags": T})
    k = "ruv-" + c[-1] + "-" + secrets.token_hex(12)
    call("POST", f"consumers/{x['id']}/key-auth", {"key": "Bearer " + k, "tags": T})  # LLM route
    call("POST", f"consumers/{x['id']}/key-auth", {"key": k, "tags": T})              # MCP route
    keys[c] = k
json.dump(keys, open("keys.json", "w"))
print("ok")
