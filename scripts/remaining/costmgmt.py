"""Cost Management: budgets (advisory and enforce), balances, query, forecast, exports. Label eval=remaining-eval.
Traffic goes to the metering route (/meter-ai/chat, mock LLM priced at $0.15/$0.60 per 1M tokens)."""
import json, time, urllib.request, urllib.error
from kapi import call, EU, PROXY
m = json.load(open("../metering/secrets.json")); KEY = m["consumers"]["meter-alice"]["key"]
L = {"eval": "remaining-eval"}; R = {}; S = {}
def rec(k, s, b): R[k] = {"status": s, "body": b}; print(k, s, json.dumps(b)[:500]); return b
def chat(n):
    out = []
    for i in range(n):
        req = urllib.request.Request(f"{PROXY}/meter-ai/chat", method="POST", headers={"Content-Type": "application/json", "apikey": KEY},
            data=json.dumps({"model": "gpt-4o-mini", "messages": [{"role": "user", "content": f"budget probe {i} " + "x " * 40}]}).encode())
        try:
            with urllib.request.urlopen(req, timeout=30) as r: out.append(r.status)
        except urllib.error.HTTPError as e: out.append(e.code)
    return out
WIN = {"type": "fixed", "interval": "P1D", "anchored_at": "2026-11-19T00:00:00+00:00[Europe/London]"}
for name, posture in [("remaining-eval advisory", "advisory"), ("remaining-eval enforce", "enforce")]:
    b = rec(f"create {posture}", *call("POST", f"{EU}/v1/ai-cost-management/budgets", {"name": name, "labels": L, "effect": "limit",
        "scope": {"filters": [{"field": "model", "op": "eq", "value": "mock"}]},
        "limit": {"value": "0.000001", "currency": "USD"}, "window": WIN, "posture": posture}))
    S[posture] = b.get("id") if isinstance(b, dict) else None
R["traffic_1"] = chat(6); print("traffic", R["traffic_1"])
time.sleep(45)
for p, i in S.items():
    if i: rec(f"balance {p}", *call("GET", f"{EU}/v1/ai-cost-management/budgets/{i}/balance"))
R["traffic_2_after_limit"] = chat(4); print("after limit", R["traffic_2_after_limit"])
rec("balances", *call("GET", f"{EU}/v1/ai-cost-management/budget-balances"))
rec("query", *call("POST", f"{EU}/v1/ai-cost-management/events/query", {"time_range": {"start": "2026-11-19T00:00:00Z", "end": "2026-11-19T23:59:59Z"},
    "group_by": ["model"]}))
rec("forecast", *call("GET", f"{EU}/v1/ai-cost-management/events/forecast"))
rec("field-values model", *call("GET", f"{EU}/v1/ai-cost-management/events/field-values?field=model"))
json.dump(S, open("secrets-cost.json", "w")); json.dump(R, open("../../results/remaining-cost-management.json", "w"), indent=2)
