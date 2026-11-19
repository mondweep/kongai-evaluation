"""Gap 4 part 3b: conversion-listener calls tool paths back through Kong, so add a REST route and repoint the tools."""
import json
from kapi import call, CE
S = json.load(open("secrets-mcpreg.json"))
s, rt = call("POST", f"{CE}/services/{S['service']}/routes", {"name": "mcpreg-eval-rest", "paths": ["/mcpreg-eval/api"], "strip_path": True, "tags": ["mcpreg-eval"]})
print("rest route", s); S["rest_route"] = rt["id"]
s, p = call("GET", f"{CE}/plugins/{S['plugin']}")
for t in p["config"]["tools"]: t["path"] = "/mcpreg-eval/api" + t["path"]
s, b = call("PATCH", f"{CE}/plugins/{S['plugin']}", {"config": {"tools": p["config"]["tools"]}})
print("patch", s, [t["path"] for t in b["config"]["tools"]] if s == 200 else b)
json.dump(S, open("secrets-mcpreg.json", "w"), indent=2)
