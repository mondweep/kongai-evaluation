import json, sys, time
from kapi import call, EU
R = json.load(open("../../results/gap8-catalog.json")); S = json.load(open("secrets-catalog.json"))
cat = sys.argv[1]
crit = [{"name": "Error rate under 5% (30d)", "enabled": True, "template_name": "gateway_manager_error_rate", "section_name": "Observability",
         "template_parameters": {"relative_window": "30d", "threshold": 5}},
        {"name": "p95 latency under 1500 ms (30d)", "enabled": True, "template_name": "gateway_manager_response_latency", "section_name": "Observability",
         "template_parameters": {"metric": "response_latency_p95", "relative_window": "30d", "threshold": 1500}},
        {"name": f"Has a {cat} plugin", "enabled": True, "template_name": "gateway_manager_has_plugin", "section_name": "Gateway Configuration",
         "template_parameters": {"category": cat}}]
s, b = call("POST", f"{EU}/v1/scorecards", {"name": "catalog-eval best practices", "description": "Eval scorecard",
     "scorecard_template": "kong_best_practices", "criteria": crit,
     "entity_selector": {"selector": "label", "selector_parameters": {"label_key": "eval", "operator": "eq", "value": "catalog-eval"}}})
print(s, json.dumps(b)[:800]); R["scorecard"] = {"status": s, "body": b}
if s == 201:
    S["scorecard"] = b["id"]; time.sleep(30)
    for k, u in [("scorecard services", f"/v1/scorecards/{b['id']}/catalog-services"), ("scorecard criteria", f"/v1/scorecards/{b['id']}/criteria"),
                 ("scores ai-chat", f"/v1/catalog-services/{S['catalog-eval-ai-chat']}/scorecards"),
                 ("scores orders-mcp", f"/v1/catalog-services/{S['catalog-eval-orders-mcp']}/scorecards")]:
        s2, b2 = call("GET", EU + u); R[k] = {"status": s2, "body": b2}; print(k, s2, json.dumps(b2)[:900])
json.dump(S, open("secrets-catalog.json", "w"), indent=2); json.dump(R, open("../../results/gap8-catalog.json", "w"), indent=2)
