"""Billing: an hourly plan for meter-bob so an invoice is produced during the trial. Label eval=remaining-eval."""
import json, urllib.request, urllib.error
from kapi import call, EU, PROXY
M = f"{EU}/v3/openmeter"; L = {"eval": "remaining-eval"}; R = {}
ids = json.load(open("../metering/catalog-ids.json")); m = json.load(open("../metering/secrets.json"))
def rec(k, s, b): R[k] = {"status": s, "body": b}; print(k, s, json.dumps(b)[:500]); return b
for cad in ["PT1H", "P1D"]:
    s, p = call("POST", f"{M}/plans", {"key": f"ai_payg_{cad.lower()}", "name": f"AI pay-as-you-go {cad} (remaining-eval)", "currency": "USD",
        "billing_cadence": cad, "labels": L, "phases": [{"key": "default", "name": "Default", "rate_cards": [{
        "key": "ai_tokens", "name": "AI tokens", "feature": {"id": ids["feature"]}, "billing_cadence": cad,
        "price": {"type": "unit", "amount": "0.00001"}}]}]})
    rec(f"plan {cad}", s, p)
    if s < 300: break
plan = p
rec("publish", *call("POST", f"{M}/plans/{plan['id']}/publish", {}))
rec("subscribe bob", *call("POST", f"{M}/subscriptions", {"customer": {"id": ids["customer_meter-bob"]}, "plan": {"key": plan["key"]}, "labels": L}))
st = []
for i in range(5):
    req = urllib.request.Request(f"{PROXY}/meter-ai/chat", method="POST", headers={"Content-Type": "application/json", "apikey": m["consumers"]["meter-bob"]["key"]},
        data=json.dumps({"model": "gpt-4o-mini", "messages": [{"role": "user", "content": f"invoice probe {i}"}]}).encode())
    try:
        with urllib.request.urlopen(req, timeout=30) as r: st.append(r.status)
    except urllib.error.HTTPError as e: st.append(e.code)
R["bob_traffic"] = st; print("bob traffic", st)
json.dump(R, open("../../results/remaining-billing.json", "w"), indent=2)
json.dump({"plan": plan["id"], "plan_key": plan["key"], "subscription": R["subscribe bob"]["body"].get("id")}, open("secrets-billing.json", "w"))
