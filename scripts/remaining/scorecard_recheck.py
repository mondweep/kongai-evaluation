"""Re-check the catalog-eval scorecard from gap 8: overall score, per-criterion and per-service results."""
import json, pathlib
from kapi import call, EU
SID = "7431d615-a6a9-43b4-b8ae-23de5bd1c266"
OUT = pathlib.Path(__file__).resolve().parents[2] / "results/remaining-scorecard.json"
R = {}
s, b = call("GET", f"{EU}/v1/scorecards/{SID}"); R["scorecard"] = {"score": b.get("score"), "updated_at": b.get("updated_at")}
s, b = call("GET", f"{EU}/v1/scorecards/{SID}/criteria")
R["criteria"] = [{"name": c["name"], "evaluation": c.get("evaluation")} for c in b["data"]]
s, b = call("GET", f"{EU}/v1/scorecards/{SID}/catalog-services"); R["services"] = b
for c in R["criteria"]:
    pass
s, crit = call("GET", f"{EU}/v1/scorecards/{SID}/criteria")
R["per_criterion_services"] = {}
for c in crit["data"]:
    s, b = call("GET", f"{EU}/v1/scorecards/{SID}/criteria/{c['id']}/catalog-services")
    R["per_criterion_services"][c["name"]] = b
OUT.write_text(json.dumps(R, indent=2))
print(json.dumps(R, indent=1)[:3500])
