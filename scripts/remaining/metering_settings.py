"""Metering & Billing settings (read) and an attempt to issue Alice's pending invoice early via /advance."""
import json
from kapi import call, EU
R = {}
def rec(k, s, b): R[k] = {"status": s, "body": b}; print(k, s, json.dumps(b)[:600]); return b
for k in ["apps", "profiles", "currencies", "tax-codes", "notification/channels", "billing/invoices"]:
    rec(k, *call("GET", f"{EU}/v3/openmeter/{k}"))
inv = R["billing/invoices"]["body"]
items = inv.get("data", inv.get("items", [])) if isinstance(inv, dict) else []
for i in items[:3]:
    iid = i["id"]; print("invoice", iid, i.get("status"), i.get("totals", {}).get("total") if isinstance(i.get("totals"), dict) else "")
    rec(f"advance {iid}", *call("POST", f"{EU}/v3/openmeter/billing/invoices/{iid}/advance", {}))
    rec(f"after {iid}", *call("GET", f"{EU}/v3/openmeter/billing/invoices/{iid}"))
json.dump(R, open("../../results/remaining-metering-settings.json", "w"), indent=2)
