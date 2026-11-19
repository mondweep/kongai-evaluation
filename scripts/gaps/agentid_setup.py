"""Gap 3: agent identity with Kong Identity (auth server + client-credentials clients), enforced on the
serverless gateway with openid-connect and per-agent AI rate limits. Tag agent-id-eval."""
import json
from kapi import call, EU, CE, PROXY
T = "agent-id-eval"; L = {"eval": T}; out = {}
def ok(n, s, r):
    print(n, s, "" if s < 300 else json.dumps(r)[:600]); return r
a = ok("auth server", *call("POST", f"{EU}/v1/auth-servers", {"name": "agent-id-eval", "audience": "kong-agents", "labels": L}))
out["auth_server"] = a["id"]; out["issuer"] = a.get("issuer"); print("issuer", a.get("issuer"))
ok("scope", *call("POST", f"{EU}/v1/auth-servers/{a['id']}/scopes", {"name": "llm:chat", "enabled": True}))
out["clients"] = {}
for name in ["agent-alpha", "agent-beta"]:
    c = ok("client " + name, *call("POST", f"{EU}/v1/auth-servers/{a['id']}/clients", {"name": name, "grant_types": ["client_credentials"], "response_types": ["token"],
        "allow_all_scopes": True, "access_token_duration": 300, "labels": L}))
    out["clients"][name] = c
# Org-level agent registry entry (Access Management / AI Agents)
g = ok("agent registry", *call("POST", f"{EU}/v1/agents", {"slug": "agent-alpha", "display_name": "Agent Alpha (agent-id-eval)"}))
out["agent_registry"] = g
json.dump(out, open("secrets-agentid.json", "w"), indent=2)
