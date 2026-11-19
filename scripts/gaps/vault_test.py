"""Gap 2 tests: vault-referenced provider key and Kong Identity API keys on /vault-eval/chat."""
import json, sys, urllib.request, urllib.error
from kapi import PROXY
out = json.load(open("secrets-vault.json"))
def chat(key, label):
    h = {"Content-Type": "application/json"}
    if key: h["apikey"] = key
    body = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello vault"}]}
    req = urllib.request.Request(f"{PROXY}/vault-eval/chat", data=json.dumps(body).encode(), method="POST", headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode(); hdr = dict(r.headers)
            return {"case": label, "status": r.status, "canary_seen_by_upstream": "canary-provider-key-7731" in raw,
                    "body_excerpt": raw[:300]}
    except urllib.error.HTTPError as e:
        return {"case": label, "status": e.code, "body": e.read().decode()[:200]}
res = [chat(out["principals"]["agent-a"]["key"]["secret"], "agent-a key"),
       chat(out["principals"]["agent-b"]["key"]["secret"], "agent-b key"),
       chat("not-a-real-key", "wrong key"), chat(None, "no key")]
print(json.dumps(res, indent=1))
if len(sys.argv) > 1: json.dump(res, open(sys.argv[1], "w"), indent=2)
