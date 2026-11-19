"""Gap 4 part 5: put key-auth on the REST route and re-test (does the MCP inner call still pass, does the bypass close?)."""
import json, time, urllib.request, urllib.error, subprocess
from kapi import call, CE, PROXY
S = json.load(open("secrets-mcpreg.json"))
s, b = call("POST", f"{CE}/routes/{S['rest_route']}/plugins", {"name": "key-auth", "config": {"key_names": ["apikey"]}, "tags": ["mcpreg-eval"]})
print("rest key-auth", s); S["rest_keyauth"] = b.get("id"); json.dump(S, open("secrets-mcpreg.json", "w"), indent=2)
time.sleep(15)
def direct(key=None):
    h = {"apikey": key} if key else {}
    req = urllib.request.Request(f"{PROXY}/mcpreg-eval/api/anything/orders/A-1/cancel", data=b"", method="POST", headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status
    except urllib.error.HTTPError as e: return e.code
R = json.load(open("../../results/gap4-mcp-gateway.json"))
R["hardened"] = {"direct_no_key": direct(), "direct_reader_key": direct(S["mcp-reader"]["key"])}
print(R["hardened"])
json.dump(R, open("../../results/gap4-mcp-gateway.json", "w"), indent=2)
