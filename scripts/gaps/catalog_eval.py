"""Gap 8: Service Catalog. Two catalog services (label eval=catalog-eval) mapped to auto-discovered gateway-service
resources, an API mapping, and a scorecard from the kong_best_practices template. Read-only look at integrations."""
import json, time
from kapi import call, EU
L = {"eval": "catalog-eval"}; R = {}; S = {}
def rec(k, s, b): R[k] = {"status": s, "body": b}; print(k, s, json.dumps(b)[:350]); return b
s, res = call("GET", f"{EU}/v1/resources?page[size]=100"); res = res["data"]
byname = {r["name"]: r for r in res}
R["resources_discovered"] = [{"name": r["name"], "type": r["type"]} for r in res]
print("discovered", len(res), sorted(byname)[:40])
svcs = {"catalog-eval-ai-chat": ("AI chat (eval)", "aiplug-eval"), "catalog-eval-orders-mcp": ("Orders MCP (eval)", "mcpreg-eval-orders")}
for name, (dn, gw) in svcs.items():
    b = rec(f"create {name}", *call("POST", f"{EU}/v1/catalog-services", {"name": name, "display_name": dn, "labels": L,
        "description": f"Eval catalog entry for gateway service {gw}"}))
    S[name] = b.get("id")
    if gw in byname:
        rec(f"map {name}", *call("POST", f"{EU}/v1/resource-mappings", {"service": b["id"], "resource": byname[gw]["id"]}))
# API mapping: link the AppAuth eval API to the chat entry, if the API exists
s, apis = call("GET", f"{EU}/v3/apis")
api = next((a for a in apis["data"] if a["name"] == "AppAuth Eval API"), None)
if api:
    rec("api-mapping", *call("POST", f"{EU}/v1/catalog-services/{S['catalog-eval-ai-chat']}/api-mappings", {"api_id": api["id"]}))
s, t = call("GET", f"{EU}/v1/scorecard-templates"); tpl = next(x for x in t["data"] if x["name"] == "kong_best_practices")
crit = [{"name": c["template_name"], "enabled": True, "template_name": c["template_name"], "template_parameters": c["template_parameters"],
         "section_name": c["section_name"]} for c in tpl["criteria"]]
sc = rec("scorecard", *call("POST", f"{EU}/v1/scorecards", {"name": "catalog-eval best practices", "description": "Eval scorecard",
     "scorecard_template": "kong_best_practices", "criteria": crit,
     "entity_selector": {"selector": "label", "selector_parameters": {"label_key": "eval", "operator": "eq", "value": "catalog-eval"}}}))
S["scorecard"] = sc.get("id")
time.sleep(20)
if S["scorecard"]:
    rec("scorecard services", *call("GET", f"{EU}/v1/scorecards/{S['scorecard']}/catalog-services"))
    rec("scorecard criteria", *call("GET", f"{EU}/v1/scorecards/{S['scorecard']}/criteria"))
for n, i in S.items():
    if n.startswith("catalog-eval"): rec(f"scores {n}", *call("GET", f"{EU}/v1/catalog-services/{i}/scorecards"))
json.dump(S, open("secrets-catalog.json", "w"), indent=2)
json.dump(R, open("../../results/gap8-catalog.json", "w"), indent=2)
