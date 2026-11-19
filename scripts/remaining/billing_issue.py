"""Billing: inspect Alice's draft invoice and try to issue it now (snapshot quantities, then advance or approve)."""
import json, time
from kapi import call, EU
M = f"{EU}/v3/openmeter"; R = json.load(open("../../results/remaining-billing.json"))
inv = R["invoices"]["body"]["data"][0]; iid = inv["id"]
def rec(k, s, b): R[k] = {"status": s, "body": b}; print(k, s, json.dumps(b)[:400]); return b
print("actions", json.dumps(inv["status_details"].get("available_actions"))); print("totals", json.dumps(inv.get("totals")))
for act in ["snapshot-quantities", "advance", "approve"]:
    rec(act, *call("POST", f"{M}/billing/invoices/{iid}/{act}", {}))
    time.sleep(5)
b = rec("final", *call("GET", f"{M}/billing/invoices/{iid}?expand=lines"))
print("STATUS", b.get("status"), "NUMBER", b.get("number"), "TOTALS", json.dumps(b.get("totals")))
for l in (b.get("lines") or [])[:5]: print("line", l.get("name"), json.dumps(l.get("quantity") or l.get("usage_based", {}).get("quantity")), json.dumps(l.get("totals", {}).get("total")))
json.dump(R, open("../../results/remaining-billing.json", "w"), indent=2)
