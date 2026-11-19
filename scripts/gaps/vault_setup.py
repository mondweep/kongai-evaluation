"""Gap 2: Konnect Config Store vault for the provider key, and Kong Identity virtual keys (tag vault-eval)."""
import json
from kapi import call, EU, CE, CP, PROXY
T = "vault-eval"; L = {"eval": T}
out = {}
def ok(n, s, r):
    print(n, s, "" if s < 300 else json.dumps(r)[:500]); return r

# A. Config store + konnect vault + secret, used by ai-proxy
cs = ok("config store", *call("POST", f"{EU}/v2/control-planes/{CP}/config-stores", {"name": "vault-eval-store"}))
out["config_store"] = cs["id"]
ok("secret", *call("POST", f"{EU}/v2/control-planes/{CP}/config-stores/{cs['id']}/secrets", {"key": "mock-provider-key", "value": "Bearer canary-provider-key-7731"}))
v = ok("vault", *call("POST", f"{CE}/vaults", {"name": "konnect", "prefix": "veval", "config": {"config_store_id": cs["id"]}, "tags": [T]}))
out["vault"] = v.get("id")
svc = ok("service", *call("POST", f"{CE}/services", {"name": "vault-eval-ai", "url": f"{PROXY}/mock-llm/v1/chat/completions", "tags": [T]}))
rt = ok("route", *call("POST", f"{CE}/services/{svc['id']}/routes", {"name": "vault-eval-chat", "paths": ["/vault-eval/chat"], "methods": ["POST"], "tags": [T]}))
out["service"], out["route"] = svc["id"], rt["id"]
p = ok("ai-proxy", *call("POST", f"{CE}/routes/{rt['id']}/plugins", {"name": "ai-proxy", "tags": [T], "config": {
    "route_type": "llm/v1/chat", "auth": {"header_name": "Authorization", "header_value": "{vault://veval/mock-provider-key}"},
    "model": {"provider": "openai", "name": "gpt-4o-mini", "options": {"upstream_url": f"{PROXY}/mock-llm/v1/chat/completions"}},
    "logging": {"log_statistics": True}}}))
out["ai_proxy"] = p.get("id")

json.dump(out, open("secrets-vault.json", "w"), indent=2)
