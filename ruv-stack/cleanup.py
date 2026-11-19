# Delete every Konnect entity tagged ruv-eval (plugins, routes, consumers + their credentials, services).
import sys
sys.path.insert(0, "../scripts")
from mk import call
def tagged(kind): return call("GET", f"{kind}?tags=ruv-eval&size=100")["data"]
for kind in ("plugins", "routes", "consumers", "services"):
    for e in tagged(kind): call("DELETE", f"{kind}/{e['id']}")
print({k: len(tagged(k)) for k in ("plugins", "routes", "consumers", "services")})
