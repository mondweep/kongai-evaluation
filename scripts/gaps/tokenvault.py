"""Gap 2: Token Vault on the vault-eval directory: vault key, static-secret provider and shared credential."""
import json, subprocess
from kapi import call, EU
out = json.load(open("secrets-vault.json")); D = out["directory"]; res = {}
subprocess.run("openssl ecparam -name prime256v1 -genkey -noout -out tv.pem && openssl ec -in tv.pem -pubout -out tv.pub.pem", shell=True, check=True, capture_output=True)
pub = open("tv.pub.pem").read()
s, r = call("GET", f"{EU}/v2/directories/{D}/vault/providers"); res["providers_before"] = (s, r)
s, r = call("POST", f"{EU}/v2/directories/{D}/vault/keys", {"public_key": pub}); res["add_key"] = (s, r if s >= 300 else {"id": r.get("id")}); print("key", s, json.dumps(r)[:300])
s, r = call("POST", f"{EU}/v2/directories/{D}/vault/providers", {"template_name": "static_secret", "name": "mock-llm-key", "credential_type": "shared"}); print("provider", s, json.dumps(r)[:600]); res["provider"] = (s, r)
if s < 300:
    pid = r["id"]
    s, c = call("POST", f"{EU}/v2/directories/{D}/vault/providers/{pid}/credentials", {"secret": "canary-tokenvault-secret-4410"}); print("credential", s, json.dumps(c)[:400]); res["credential"] = (s, c)
    s, g = call("GET", f"{EU}/v2/directories/{D}/vault/providers/{pid}/credentials"); res["credential_list"] = (s, g)
    print("secret visible on read:", "canary-tokenvault-secret-4410" in json.dumps(g)); res["secret_visible_on_read"] = "canary-tokenvault-secret-4410" in json.dumps(g)
    s2, c2 = call("POST", f"{EU}/v2/directories/{D}/vault/providers/{pid}/credentials", {"secret": "second"}); print("second credential", s2); res["second_credential_status"] = s2
json.dump(res, open("../../results/gap2-token-vault.json", "w"), indent=2, default=str)
