"""Gap 3 gateway side: route /agent-id/chat with openid-connect (client credentials against the Kong Identity
auth server, done by the gateway), consumer mapping per agent, and a per-agent AI token limit."""
import json
from kapi import call, CE, PROXY
T = "agent-id-eval"; out = json.load(open("secrets-agentid.json"))
def ok(n, s, r):
    print(n, s, "" if s < 300 else json.dumps(r)[:700]); return r
svc = ok("service", *call("POST", f"{CE}/services", {"name": "agent-id-ai", "url": f"{PROXY}/mock-llm/v1/chat/completions", "tags": [T]}))
rt = ok("route", *call("POST", f"{CE}/services/{svc['id']}/routes", {"name": "agent-id-chat", "paths": ["/agent-id/chat"], "methods": ["POST"], "tags": [T]}))
out["service"], out["route"] = svc["id"], rt["id"]
for name, c in out["clients"].items():
    co = ok("consumer " + name, *call("POST", f"{CE}/consumers", {"username": name, "custom_id": c["id"], "tags": [T]}))
    out.setdefault("consumers", {})[name] = co["id"]
ok("openid-connect", *call("POST", f"{CE}/routes/{rt['id']}/plugins", {"name": "openid-connect", "tags": [T], "config": {
    "issuer": out["issuer"], "auth_methods": ["client_credentials", "bearer"], "client_credentials_param_type": ["header"],
    "consumer_claim": ["sub"], "consumer_by": ["custom_id", "username"], "consumer_optional": False,
    "audience_required": ["kong-agents"], "upstream_headers_claims": ["sub"], "upstream_headers_names": ["x-agent-sub"],
    "cache_tokens": True}}))
ok("ai-proxy", *call("POST", f"{CE}/routes/{rt['id']}/plugins", {"name": "ai-proxy", "tags": [T], "config": {
    "route_type": "llm/v1/chat", "auth": {"header_name": "Authorization", "header_value": "Bearer dummy-not-a-real-key"},
    "model": {"provider": "openai", "name": "gpt-4o-mini", "options": {"upstream_url": f"{PROXY}/mock-llm/v1/chat/completions"}},
    "logging": {"log_statistics": True}}}))
ok("ai-rate-limiting-advanced", *call("POST", f"{CE}/routes/{rt['id']}/plugins", {"name": "ai-rate-limiting-advanced", "tags": [T], "config": {
    "identifier": "consumer", "strategy": "local", "llm_providers": [{"name": "openai", "limit": [200], "window_size": [60]}]}}))
json.dump(out, open("secrets-agentid.json", "w"), indent=2)
