#!/usr/bin/env python3
"""Read-only probe of which Konnect feature APIs respond on this org.

Only GET requests. Needs KCONNECT_TOKEN in the environment.
Usage: python3 scripts/coverage/probe.py > results/coverage-api-probe.json
"""
import json, os, urllib.request, urllib.error, datetime

TOKEN = os.environ["KCONNECT_TOKEN"]
EU = "https://eu.api.konghq.com"
GLOBAL = "https://global.api.konghq.com"

PROBES = [
    ("Catalog", "Services", EU, "/v1/catalog-services"),
    ("Catalog", "Scorecards", EU, "/v1/scorecards"),
    ("Catalog", "Integrations", EU, "/v1/integrations"),
    ("Catalog", "Resources", EU, "/v1/resources"),
    ("Catalog", "MCP Registries", EU, "/v1/mcp-registries"),
    ("Dev Portal", "Portals", EU, "/v3/portals"),
    ("Dev Portal", "Application Auth", EU, "/v2/application-auth-strategies"),
    ("Dev Portal", "DCR providers", EU, "/v2/dcr-providers"),
    ("APIs", "APIs", EU, "/v3/apis"),
    ("Metering & Billing", "Meters", EU, "/v3/openmeter/meters"),
    ("Metering & Billing", "Features", EU, "/v3/openmeter/features"),
    ("Metering & Billing", "Plans", EU, "/v3/openmeter/plans"),
    ("Metering & Billing", "Customers", EU, "/v3/openmeter/customers"),
    ("Metering & Billing", "Entitlements", EU, "/v3/openmeter/entitlements"),
    ("Metering & Billing", "Apps", EU, "/v3/openmeter/apps"),
    ("Observability", "Dashboards", EU, "/v2/dashboards"),
    ("Identity", "Auth servers", EU, "/v1/auth-servers"),
    ("AI", "AI Gateways", EU, "/v1/ai-gateways"),
    ("AI", "AI Models", EU, "/v1/ai-models"),
    ("AI", "MCP Servers", EU, "/v1/mcp-servers"),
    ("AI", "Agents", EU, "/v1/agents"),
    ("Gateway", "Control planes", EU, "/v2/control-planes"),
    ("Gateway", "Dedicated Cloud Gateway networks", EU, "/v1/cloud-gateways/networks"),
    ("Other", "Event Gateways", EU, "/v1/event-gateways"),
    ("Other", "Mesh control planes", EU, "/v1/mesh/control-planes"),
    ("Access Management", "Users", GLOBAL, "/v3/users"),
    ("Access Management", "Teams", GLOBAL, "/v3/teams"),
    ("Access Management", "System accounts", GLOBAL, "/v3/system-accounts"),
    ("Access Management", "Identity provider", GLOBAL, "/v3/identity-provider"),
    ("Audit", "Audit log webhook", GLOBAL, "/v2/audit-log-webhook"),
]

def get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None

out = {"probed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "results": []}
for area, feature, base, path in PROBES:
    status, body = get(base + path)
    row = {"area": area, "feature": feature, "endpoint": base + path, "status": status}
    if isinstance(body, dict) and isinstance(body.get("data"), list):
        row["count"] = len(body["data"])
    elif isinstance(body, dict) and "enabled" in body:
        row["enabled"] = body["enabled"]  # audit webhook: no endpoint URL recorded
    out["results"].append(row)
print(json.dumps(out, indent=2))
