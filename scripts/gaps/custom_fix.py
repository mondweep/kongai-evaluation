import json, sys, time, urllib.request, urllib.error
from kapi import call, CE, PROXY
S = json.load(open("secrets-aiplug.json")); pid = S["routes"]["custom"]["plugins"]["ai-custom-guardrail"]
def setresp(block, msg):
    s, p = call("GET", f"{CE}/plugins/{pid}")
    p["config"]["response"] = {"block": block, "block_message": msg}
    s, b = call("PUT", f"{CE}/plugins/{pid}", {k: p[k] for k in ["name", "config", "tags", "route", "enabled", "protocols"]}); return s
def hit(txt):
    req = urllib.request.Request(f"{PROXY}/aiplug/custom", method="POST", headers={"Content-Type": "application/json"},
        data=json.dumps({"model": "gpt-4o-mini", "messages": [{"role": "user", "content": txt}]}).encode())
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status, r.read().decode()[:300]
    except urllib.error.HTTPError as e: return e.code, e.read().decode()[:300]
print(setresp(sys.argv[1], sys.argv[2])); time.sleep(8)
print(hit("this contains forbidden-word here")); print(hit("harmless"))
