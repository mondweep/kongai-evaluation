import json
from kapi import call, EU
ids = json.load(open("catalog-ids.json"))
for c in ["meter-alice", "meter-bob"]:
    s, r = call("GET", f"{EU}/v3/openmeter/customers/{ids['customer_' + c]}/entitlement-access/features/ai_tokens/value")
    print(c, s, json.dumps(r)[:500])
