"""Create the metering-eval gateway entities and an ingest-only system account.
Writes credentials to ./secrets.json (git-ignored)."""
import json
from kapi import call, GLOBAL, EU, CE, PROXY, TAG

sec = {}
# 1. System account with Metering: Ingest + Entitlement Access only
s, sa = call("POST", f"{GLOBAL}/v3/system-accounts", {
    "name": "metering-eval-ingest",
    "description": "metering-eval: gateway usage ingest only. Delete after the test.",
    "konnect_managed": False})
print("system account", s)
for role in ["Ingest", "Entitlement Access"]:
    s, r = call("POST", f"{GLOBAL}/v3/system-accounts/{sa['id']}/assigned-roles", {
        "role_name": role, "entity_type_name": "Metering", "entity_id": "*", "entity_region": "eu"})
    print("role", role, s, r if s >= 300 else "")
s, t = call("POST", f"{GLOBAL}/v3/system-accounts/{sa['id']}/access-tokens", {
    "name": "metering-eval-3d", "expires_at": "2026-11-22T00:00:00Z"})
print("token", s)
sec["system_account_id"] = sa["id"]
sec["ingest_token"] = t["token"]

# 2. Service + route on the mock LLM with key-auth, ai-proxy and metering-and-billing
s, svc = call("POST", f"{CE}/services", {"name": "meter-ai", "url": f"{PROXY}/mock-llm/v1/chat/completions", "tags": [TAG]})
print("service", s)
s, rt = call("POST", f"{CE}/services/{svc['id']}/routes", {"name": "meter-ai-chat", "paths": ["/meter-ai/chat"], "methods": ["POST"], "tags": [TAG]})
print("route", s)
sec["service_id"], sec["route_id"] = svc["id"], rt["id"]
s, p = call("POST", f"{CE}/routes/{rt['id']}/plugins", {"name": "key-auth", "tags": [TAG],
    "config": {"key_names": ["apikey"], "hide_credentials": True}})
print("key-auth", s)
s, p = call("POST", f"{CE}/routes/{rt['id']}/plugins", {"name": "ai-proxy", "tags": [TAG], "config": {
    "route_type": "llm/v1/chat",
    "auth": {"header_name": "Authorization", "header_value": "Bearer dummy-not-a-real-key"},
    "model": {"provider": "openai", "name": "gpt-4o-mini", "options": {
        "upstream_url": f"{PROXY}/mock-llm/v1/chat/completions", "input_cost": 0.15, "output_cost": 0.6}},
    "logging": {"log_statistics": True, "log_payloads": False}}})
print("ai-proxy", s, p if s >= 300 else "")
s, p = call("POST", f"{CE}/routes/{rt['id']}/plugins", {"name": "metering-and-billing", "tags": [TAG], "config": {
    "ingest_endpoint": f"{EU}/v3/openmeter/events", "api_token": sec["ingest_token"], "ssl_verify": True,
    "subject": {"look_up_value_in": "consumer", "field": "username"},
    "meter_api_requests": True, "meter_ai_token_usage": True}})
print("metering-and-billing", s, p if s >= 300 else "")
sec["metering_plugin_id"] = p.get("id") if isinstance(p, dict) else None

# 3. Two consumers
sec["consumers"] = {}
for name in ["meter-alice", "meter-bob"]:
    s, c = call("POST", f"{CE}/consumers", {"username": name, "tags": [TAG]})
    s2, k = call("POST", f"{CE}/consumers/{c['id']}/key-auth", {"tags": [TAG]})
    print("consumer", name, s, s2)
    sec["consumers"][name] = {"id": c["id"], "key": k["key"]}
json.dump(sec, open("secrets.json", "w"), indent=2)
