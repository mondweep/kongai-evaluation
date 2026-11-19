"""Add (or update) entitlement-enforcement on the metering-eval route. Usage: enforce.py <fail_policy> [redis_host]"""
import json, os, sys
from kapi import call, EU, CE, TAG
sec = json.load(open("secrets.json"))
cfg = {"entitlement_access_endpoint": f"{EU}/v3/openmeter/entitlement-access/query", "api_token": sec["ingest_token"],
       "customer": {"look_up_value_in": "consumer"}, "feature": {"key": "ai_tokens"}, "credit_balance_required": False,
       "fail_policy": sys.argv[1], "refresh_interval": 5,
       "deny_unknown_customers": os.environ.get("DENY_UNKNOWN", "true") == "true"}
if len(sys.argv) > 2:
    cfg["redis"] = {"host": sys.argv[2], "port": 6379}
else:
    cfg["redis"] = {}
body = {"name": "entitlement-enforcement", "tags": [TAG], "config": cfg}
pid = sec.get("enforce_plugin_id")
if pid:
    s, r = call("PUT", f"{CE}/routes/{sec['route_id']}/plugins/{pid}", body)
else:
    s, r = call("POST", f"{CE}/routes/{sec['route_id']}/plugins", body)
    if s < 300:
        sec["enforce_plugin_id"] = r["id"]; json.dump(sec, open("secrets.json", "w"), indent=2)
print(s, json.dumps(r)[:800] if s >= 300 else "ok")
