"""Query the metering-eval meters grouped by customer and dimension."""
import json, sys
from kapi import call, EU
ids = json.load(open("catalog-ids.json"))
M = f"{EU}/v3/openmeter"
out = {}
for key, mid, dims in [("ai_tokens", ids["meter_tokens"], ["subject", "token_type", "model"]), ("api_requests", ids["meter_requests"], ["subject", "status"])]:
    s, r = call("POST", f"{M}/meters/{mid}/query", {"from": "2026-11-19T13:00:00Z", "group_by_dimensions": dims})
    out[key] = r
    print(key, s)
    for row in (r or {}).get("data", []):
        print("  ", row.get("value"), json.dumps(row.get("dimensions")))
if len(sys.argv) > 1:
    json.dump(out, open(sys.argv[1], "w"), indent=2)
