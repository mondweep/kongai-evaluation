"""Tiny Konnect API helper. Reads KCONNECT_TOKEN from the environment."""
import json, os, urllib.request, urllib.error

EU = "https://eu.api.konghq.com"
GLOBAL = "https://global.api.konghq.com"
CP = "YOUR-CONTROL-PLANE-ID"
CE = f"{EU}/v2/control-planes/{CP}/core-entities"
PROXY = "https://YOUR-GATEWAY.eu.serverless.gateways.konggateway.com"
TAG = "metering-eval"


def call(method, url, body=None, token=None, headers=None):
    h = {"Authorization": f"Bearer {token or os.environ['KCONNECT_TOKEN']}",
         "Content-Type": "application/json", "Accept": "application/json"}
    h.update(headers or {})
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw.decode(errors="replace")
