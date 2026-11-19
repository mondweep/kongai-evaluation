"""Compare Konnect request-log totals for the metering-eval route with the meter totals."""
import json
from collections import defaultdict
from kapi import call, EU, CP
sec = json.load(open("secrets.json"))
s, r = call("POST", f"{EU}/v2/api-requests", {"time_range": {"type": "relative", "time_range": "1H"},
    "filters": [{"field": "route", "operator": "in", "value": [f"{CP}:{sec['route_id']}"]}], "size": 1000})
rows = r["results"]
ai_keys = sorted({k for x in rows for k in x if k.startswith("ai") or "token" in k or "consumer" in k})
agg = defaultdict(lambda: {"requests": 0, "prompt": 0, "completion": 0})
for x in rows:
    c = x.get("consumer")
    c = c.split(":")[-1] if isinstance(c, str) else str(c)
    a = agg[(c, x["response_http_status"])]
    a["requests"] += 1
    for ai in x.get("ai") or []:
        a["prompt"] += ai.get("promptTokens") or 0
        a["completion"] += ai.get("completionTokens") or 0
out = {"log_rows": len(rows), "ai_fields": ai_keys, "by_consumer_status": {f"{k[0]} {k[1]}": v for k, v in agg.items()}}
print(json.dumps(out, indent=1))
json.dump(out, open("../../results/metering-request-log-totals.json", "w"), indent=2)
