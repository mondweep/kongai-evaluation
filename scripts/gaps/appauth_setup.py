"""Gap 6: Application Auth end to end on a separate portal (appauth-eval-portal) and a separate API. Label/tag appauth-eval."""
import json, time
from kapi import call, EU, CE, CP
L = {"eval": "appauth-eval"}; T = ["appauth-eval"]; S = {}; R = {}
def ok(k, s, b, keep=True):
    print(k, s, json.dumps(b)[:400]); R[k] = {"status": s, "body": b}
    if s >= 400: json.dump(R, open("../../results/gap6-appauth-setup.json", "w"), indent=2); json.dump(S, open("secrets-appauth.json", "w"), indent=2); raise SystemExit(k)
    return b
s, b = call("GET", f"{EU}/v3/portals?filter[name][eq]=appauth-eval-portal"); S["portal"] = b["data"][0]["id"]; S["portal_host"] = b["data"][0]["default_domain"]
svc = ok("service", *call("POST", f"{CE}/services", {"name": "appauth-eval-httpbin", "url": "https://httpbin.org/anything", "tags": T})); S["service"] = svc["id"]
rt = ok("route", *call("POST", f"{CE}/services/{svc['id']}/routes", {"name": "appauth-eval", "paths": ["/appauth-eval"], "tags": T})); S["route"] = rt["id"]
st = ok("strategy", *call("POST", f"{EU}/v2/application-auth-strategies", {"name": "appauth-eval-key", "display_name": "AppAuth eval key",
        "strategy_type": "key_auth", "configs": {"key-auth": {"key_names": ["apikey"]}}, "labels": L})); S["strategy"] = st["id"]
api = ok("api", *call("POST", f"{EU}/v3/apis", {"name": "AppAuth Eval API", "version": "v1", "description": "Eval API for application auth", "labels": L})); S["api"] = api["id"]
ok("implementation", *call("POST", f"{EU}/v3/apis/{api['id']}/implementations", {"service": {"control_plane_id": CP, "id": svc["id"]}}))
ok("publication", *call("PUT", f"{EU}/v3/apis/{api['id']}/publications/{S['portal']}", {"auth_strategy_ids": [st["id"]], "visibility": "public"}))
dev = ok("developer", *call("POST", f"{EU}/v3/portals/{S['portal']}/developers", {"email": "appauth-eval-dev@example.com", "full_name": "AppAuth Eval Dev", "status": "approved", "send_invitation_email": False})); S["developer"] = dev["id"]
app = ok("application", *call("POST", f"{EU}/v3/portals/{S['portal']}/applications", {"name": "appauth-eval-app", "auth_strategy_id": st["id"], "owner": {"type": "developer", "id": dev["id"]}, "labels": L})); S["application"] = app["id"]
reg = ok("registration", *call("POST", f"{EU}/v3/portals/{S['portal']}/applications/{app['id']}/registrations", {"api_id": api["id"], "status": "approved"})); S["registration"] = reg["id"]
ok("credentials", *call("GET", f"{EU}/v3/portals/{S['portal']}/applications/{app['id']}/credentials"))
s, b = call("GET", f"{CE}/plugins?size=1000")
R["service_plugins"] = [{"name": p["name"], "id": p["id"], "config": p["config"]} for p in b["data"] if (p.get("service") or {}).get("id") == svc["id"]]
print("plugins on service", [p["name"] for p in R["service_plugins"]])
json.dump(R, open("../../results/gap6-appauth-setup.json", "w"), indent=2); json.dump(S, open("secrets-appauth.json", "w"), indent=2)
