"""Create meters, feature, plan, customers and a subscription (all labelled eval=metering-eval)."""
import json
from kapi import call, EU
M = f"{EU}/v3/openmeter"
L = {"eval": "metering-eval"}
sec = json.load(open("secrets.json"))
ids = {}

def ok(name, s, r):
    print(name, s, "" if s < 300 else json.dumps(r)[:600])
    return r

r = ok("meter ai_tokens", *call("POST", f"{M}/meters", {"key": "ai_tokens", "name": "AI tokens (metering-eval)", "aggregation": "sum",
    "event_type": "kong.llm_request", "value_property": "$.tokens",
    "dimensions": {"token_type": "$.type", "model": "$.model", "provider": "$.provider", "route_id": "$.route_id"}, "labels": L}))
ids["meter_tokens"] = r["id"]
r = ok("meter api_requests", *call("POST", f"{M}/meters", {"key": "api_requests", "name": "API requests (metering-eval)", "aggregation": "count",
    "event_type": "kong.api_request", "dimensions": {"route": "$.route_name", "status": "$.response_http_status"}, "labels": L}))
ids["meter_requests"] = r["id"]
r = ok("feature", *call("POST", f"{M}/features", {"key": "ai_tokens", "name": "AI tokens", "meter": {"id": ids["meter_tokens"]}, "labels": L}))
ids["feature"] = r["id"]
r = ok("plan", *call("POST", f"{M}/plans", {"key": "ai_starter", "name": "AI Starter (metering-eval)", "currency": "USD", "billing_cadence": "P1M", "labels": L,
    "phases": [{"key": "default", "name": "Default", "rate_cards": [{
        "key": "ai_tokens", "name": "AI tokens", "feature": {"id": ids["feature"]}, "billing_cadence": "P1M",
        "price": {"type": "unit", "amount": "0.00001"},
        "entitlement": {"type": "metered", "limit": 1000, "usage_period": "P1M", "is_soft_limit": False}}]}]}))
ids["plan"] = r["id"]
ok("publish", *call("POST", f"{M}/plans/{ids['plan']}/publish", {}))
for name in ["meter-alice", "meter-bob"]:
    r = ok("customer " + name, *call("POST", f"{M}/customers", {"key": name, "name": name, "currency": "USD", "labels": L,
        "usage_attribution": {"subject_keys": ["consumer:" + sec["consumers"][name]["id"]]}}))
    ids["customer_" + name] = r["id"]
r = ok("subscription alice", *call("POST", f"{M}/subscriptions", {"customer": {"id": ids["customer_meter-alice"]}, "plan": {"key": "ai_starter"}, "labels": L}))
ids["subscription_alice"] = r.get("id") if isinstance(r, dict) else None
json.dump(ids, open("catalog-ids.json", "w"), indent=2)
