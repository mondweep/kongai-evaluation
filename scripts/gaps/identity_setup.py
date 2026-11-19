"""Gap 2 part B: Kong Identity directory, principals and API keys (virtual keys)."""
import json
from kapi import call, EU, CE, CP
T = "vault-eval"; L = {"eval": T}
out = json.load(open("secrets-vault.json"))
def ok(n, s, r):
    print(n, s, "" if s < 300 else json.dumps(r)[:500]); return r

# B. Kong Identity directory with principals and API keys ("virtual keys")
dr = ok("directory", *call("POST", f"{EU}/v2/directories", {"name": "vault-eval", "description": "vault-eval test directory",
    "allow_all_control_planes": True, "ttl_secs": 300, "negative_ttl_secs": 300, "labels": L}))
out["directory"] = dr["id"]
out["principals"] = {}
for name in ["agent-a", "agent-b"]:
    pr = ok("principal " + name, *call("POST", f"{EU}/v2/directories/{dr['id']}/principals", {"display_name": name, "type": "agent", "labels": L}))
    if pr.get("id") is None:
        pr = ok("principal(no type) " + name, *call("POST", f"{EU}/v2/directories/{dr['id']}/principals", {"display_name": name, "labels": L}))
    k = ok("api key " + name, *call("POST", f"{EU}/v2/directories/{dr['id']}/principals/{pr['id']}/api-keys", {"type": "v1", "name": f"{name}-key"}))
    out["principals"][name] = {"id": pr["id"], "key": k}
p = ok("key-auth principals", *call("POST", f"{CE}/routes/{out["route"]}/plugins", {"name": "key-auth", "tags": [T], "config": {
    "key_names": ["apikey"], "hide_credentials": True, "identity_realms": [], "principals": {"enabled": True, "directory": "vault-eval", "error_on_miss": True}}}))
out["key_auth"] = p.get("id")
json.dump(out, open("secrets-vault.json", "w"), indent=2)
