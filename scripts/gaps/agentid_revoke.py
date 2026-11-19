"""Delete agent-beta's client at the auth server, then poll until the gateway refuses it."""
import json, time, base64, urllib.request, urllib.error
from kapi import call, EU, PROXY
out = json.load(open("secrets-agentid.json")); c = out["clients"]["agent-beta"]
auth = "Basic " + base64.b64encode(f"{c['id']}:{c['client_secret']}".encode()).decode()
def st():
    req = urllib.request.Request(f"{PROXY}/agent-id/chat", data=b'{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}', method="POST", headers={"Content-Type": "application/json", "Authorization": auth})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status
    except urllib.error.HTTPError as e: return e.code
print("before", st()); t0 = time.time()
print("delete client", call("DELETE", f"{EU}/v1/auth-servers/{out['auth_server']}/clients/{c['id']}")[0])
log = []
while time.time() - t0 < 420:
    s = st(); log.append({"t": round(time.time() - t0), "status": s})
    if s == 401: break
    time.sleep(15)
res = {"seconds_until_refused": log[-1]["t"] if log[-1]["status"] == 401 else None, "log": log}
print(json.dumps(res)); json.dump(res, open("../../results/gap3-client-revocation.json", "w"), indent=2)
