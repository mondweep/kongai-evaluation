"""Delete agent-b's API key and deactivate agent-a, then poll until each gets 401. Writes results JSON."""
import json, time, urllib.request, urllib.error
from kapi import call, EU, PROXY
out = json.load(open("secrets-vault.json")); D = out["directory"]
def status(key):
    body = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]}
    req = urllib.request.Request(f"{PROXY}/vault-eval/chat", data=json.dumps(body).encode(), method="POST", headers={"Content-Type": "application/json", "apikey": key})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status
    except urllib.error.HTTPError as e: return e.code
a, b = out["principals"]["agent-a"], out["principals"]["agent-b"]
print("before", status(a["key"]["secret"]), status(b["key"]["secret"]))
t0 = time.time()
s1, _ = call("DELETE", f"{EU}/v2/directories/{D}/principals/{b['id']}/api-keys/{b['key']['id']}")
s2, _ = call("PATCH", f"{EU}/v2/directories/{D}/principals/{a['id']}", {"active": False})
print("delete key", s1, "deactivate principal", s2)
log = []; done = {"a": None, "b": None}
while time.time() - t0 < 420 and None in done.values():
    sa, sb = status(a["key"]["secret"]), status(b["key"]["secret"])
    el = round(time.time() - t0)
    log.append({"t": el, "agent_a_deactivated": sa, "agent_b_key_deleted": sb})
    if sa == 401 and done["a"] is None: done["a"] = el
    if sb == 401 and done["b"] is None: done["b"] = el
    time.sleep(15)
res = {"seconds_until_401": done, "log": log}
print(json.dumps(res))
json.dump(res, open("../../results/gap2-identity-revocation.json", "w"), indent=2)
