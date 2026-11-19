"""Groups (teams and roles): a team with Viewer on the serverless control plane,
a system account in it, and checks of what its token can and can't do.
Token is kept only in git-ignored secrets-groups.json and deleted at the end."""
import json, time, datetime, pathlib
from kapi import call, GLOBAL, EU, CP, CE

OUT = pathlib.Path(__file__).resolve().parents[2] / "results/remaining-groups.json"
SEC = pathlib.Path(__file__).with_name("secrets-groups.json")
R = {}

def probe(tok, label):
    checks = {
        "list_services": call("GET", f"{CE}/services?size=1", token=tok)[0],
        "create_service": call("POST", f"{CE}/services", {"name": "remaining-eval-should-fail", "url": "http://example.com", "tags": ["remaining-eval"]}, token=tok)[0],
        "list_control_planes": None,
        "openmeter_meters": call("GET", f"{EU}/v3/openmeter/meters", token=tok)[0],
        "list_teams": call("GET", f"{GLOBAL}/v3/teams", token=tok)[0],
    }
    s, b = call("GET", f"{EU}/v2/control-planes", token=tok)
    checks["list_control_planes"] = s
    if s == 200:
        checks["control_planes_visible"] = [c["name"] for c in b.get("data", [])]
    R[label] = checks
    print(label, checks)
    return checks

s, team = call("POST", f"{GLOBAL}/v3/teams", {"name": "remaining-eval-team", "description": "remaining-eval: Viewer on serverless CP", "labels": {"eval": "remaining-eval"}})
print("team", s); R["create_team"] = s; tid = team["id"]
s, b = call("POST", f"{GLOBAL}/v3/teams/{tid}/assigned-roles", {"role_name": "Viewer", "entity_id": CP, "entity_type_name": "Control Planes", "entity_region": "eu"})
print("role", s, b); R["assign_viewer"] = s
s, sa = call("POST", f"{GLOBAL}/v3/system-accounts", {"name": "remaining-eval-sa", "description": "remaining-eval groups test"})
print("sa", s); R["create_sa"] = s; said = sa["id"]
s, b = call("POST", f"{GLOBAL}/v3/teams/{tid}/system-accounts", {"id": said})
print("add to team", s); R["add_sa_to_team"] = s
exp = (datetime.datetime.utcnow() + datetime.timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
s, t = call("POST", f"{GLOBAL}/v3/system-accounts/{said}/access-tokens", {"name": "remaining-eval-token", "expires_at": exp})
print("token", s); tok = t["token"]; tokid = t["id"]
SEC.write_text(json.dumps({"team": tid, "sa": said, "token_id": tokid, "token": tok}))
R["ids"] = {"team": tid, "system_account": said, "token_id": tokid}

time.sleep(5)
probe(tok, "in_team")

s, _ = call("DELETE", f"{GLOBAL}/v3/teams/{tid}/system-accounts/{said}")
print("remove from team", s); R["remove_from_team"] = s
t0 = time.time()
while True:
    c = probe(tok, "after_removal")
    if c["list_services"] != 200 or time.time() - t0 > 360:
        break
    time.sleep(20)
R["removal_effective_after_s"] = round(time.time() - t0)

s, _ = call("DELETE", f"{GLOBAL}/v3/system-accounts/{said}/access-tokens/{tokid}")
R["delete_token"] = s
time.sleep(3)
R["after_token_delete"] = call("GET", f"{CE}/services?size=1", token=tok)[0]
print("after token delete", R["after_token_delete"])
OUT.write_text(json.dumps(R, indent=2))
