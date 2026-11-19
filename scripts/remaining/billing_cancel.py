"""Billing: cancel Alice's metering-eval subscription immediately to force the final usage invoice (it was due for cleanup anyway)."""
import json, time
from kapi import call, EU
M = f"{EU}/v3/openmeter"; R = {}
ids = json.load(open("../metering/catalog-ids.json")); sid = ids["subscription_alice"]
def rec(k, s, b): R[k] = {"status": s, "body": b}; print(k, s, json.dumps(b)[:700]); return b
rec("before", *call("GET", f"{M}/subscriptions/{sid}"))
rec("cancel", *call("POST", f"{M}/subscriptions/{sid}/cancel", {"timing": "immediate"}))
time.sleep(20)
rec("invoices", *call("GET", f"{M}/billing/invoices"))
json.dump(R, open("../../results/remaining-billing.json", "w"), indent=2)
