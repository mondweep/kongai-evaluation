"""Identity Providers: read the org SSO settings (read-only, never changed), then configure OIDC SSO on the
separate eval portal (appauth-eval-portal) with Kong Identity (auth server agent-id-eval) as the issuer.
The client secret is kept only in git-ignored secrets-idp.json."""
import json, pathlib
from kapi import call, GLOBAL, EU
PORTAL = "a36164b2-f7e2-4e94-a310-7397a35427a7"
AS = "50478391-ccf5-49d1-b89a-9482aa81ba3e"
ISSUER = "https://w2b7i65jrecupo4h.eu.identity.konghq.com/auth"
OUT = pathlib.Path(__file__).resolve().parents[2] / "results/remaining-idp.json"
SEC = pathlib.Path(__file__).with_name("secrets-idp.json")
R = {}
def rec(k, s, b, hide=()):
    if isinstance(b, dict):
        b = {x: ("[redacted]" if x in hide else y) for x, y in b.items()}
    R[k] = {"status": s, "body": b}; print(k, s, json.dumps(b)[:500])

rec("org_auth_settings", *call("GET", f"{GLOBAL}/v3/authentication-settings"))
rec("org_idps", *call("GET", f"{GLOBAL}/v3/identity-providers"))
s, p = call("GET", f"{EU}/v3/portals/{PORTAL}"); host = p.get("default_domain") or p.get("canonical_domain"); R["portal_host"] = host
cb = f"https://{host}/login"
s, c = call("POST", f"{EU}/v1/auth-servers/{AS}/clients", {"name": "portal-sso", "grant_types": ["authorization_code"],
        "response_types": ["code"], "redirect_uris": [cb], "allow_all_scopes": True, "labels": {"eval": "remaining-eval"}})
rec("create_client_authcode", s, c, hide=("client_secret",))
if s >= 300:
    raise SystemExit
SEC.write_text(json.dumps({"client_id": c["id"], "client_secret": c["client_secret"]}))
s, idp = call("POST", f"{EU}/v3/portals/{PORTAL}/identity-providers", {"type": "oidc", "enabled": True,
        "config": {"issuer_url": ISSUER, "client_id": c["id"], "client_secret": c["client_secret"], "scopes": ["openid", "email", "profile"]}})
rec("create_portal_idp", s, idp)
rec("portal_auth_settings_before", *call("GET", f"{EU}/v3/portals/{PORTAL}/authentication-settings"))
rec("enable_oidc_on_eval_portal", *call("PATCH", f"{EU}/v3/portals/{PORTAL}/authentication-settings", {"oidc_auth_enabled": True}))
rec("portal_idps", *call("GET", f"{EU}/v3/portals/{PORTAL}/identity-providers"))
s, d = call("GET", f"{ISSUER}/.well-known/openid-configuration", token="none")
R["issuer_discovery_from_sandbox"] = s if not isinstance(d, dict) else {"status": s, "grant_types_supported": d.get("grant_types_supported"), "scopes_supported": d.get("scopes_supported")}
print("discovery", R["issuer_discovery_from_sandbox"])
OUT.write_text(json.dumps(R, indent=2, default=str))
