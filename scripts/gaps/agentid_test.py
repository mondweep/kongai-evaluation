"""Gap 3 tests: each agent authenticates with its client id/secret (Basic), gateway gets the token.
Sends n requests per agent and records status, the upstream-visible identity and rate-limit headers."""
import json, sys, base64, urllib.request, urllib.error
from kapi import PROXY
out = json.load(open("secrets-agentid.json"))
def chat(auth, label):
    h = {"Content-Type": "application/json"}
    if auth: h["Authorization"] = auth
    body = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello from an agent"}]}
    req = urllib.request.Request(f"{PROXY}/agent-id/chat", data=json.dumps(body).encode(), method="POST", headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode(); c = json.loads(raw)["choices"][0]["message"]["content"]
            i = c.find("x-agent-sub="); sub = c[i:i+60].split(";")[0] if i >= 0 else None
            j = c.find("x-consumer-username="); cu = c[j:j+50].split(";")[0] if j >= 0 else None
            return {"case": label, "status": r.status, "upstream_saw": [sub, cu],
                    "remaining": {k: v for k, v in r.headers.items() if "ratelimit" in k.lower()}}
    except urllib.error.HTTPError as e:
        return {"case": label, "status": e.code, "body": e.read().decode()[:160]}
def basic(name):
    c = out["clients"][name]; return "Basic " + base64.b64encode(f"{c['id']}:{c['client_secret']}".encode()).decode()
res = []
n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
for i in range(n): res.append(chat(basic("agent-alpha"), f"alpha #{i}"))
res.append(chat(basic("agent-beta"), "beta #0"))
c = out["clients"]["agent-beta"]
res.append(chat("Basic " + base64.b64encode(f"{c['id']}:wrong-secret".encode()).decode(), "beta wrong secret"))
res.append(chat(None, "no credentials"))
print(json.dumps(res, indent=1))
if len(sys.argv) > 2: json.dump(res, open(sys.argv[2], "w"), indent=2)
