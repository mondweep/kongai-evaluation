"""Send chat requests through /meter-ai/chat as each consumer. Usage: traffic.py <consumer> <n> [words]"""
import json, sys, time, urllib.request, urllib.error
from kapi import PROXY
sec = json.load(open("secrets.json"))
who, n = sys.argv[1], int(sys.argv[2])
words = int(sys.argv[3]) if len(sys.argv) > 3 else 20
out = []
for i in range(n):
    body = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": " ".join(["hello"] * words) + f" request {i}"}]}
    req = urllib.request.Request(f"{PROXY}/meter-ai/chat", data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json", "apikey": sec["consumers"][who]["key"]})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read()); u = d.get("usage", {})
            out.append({"i": i, "status": r.status, "prompt": u.get("prompt_tokens"), "completion": u.get("completion_tokens"), "total": u.get("total_tokens")})
    except urllib.error.HTTPError as e:
        out.append({"i": i, "status": e.code, "body": e.read().decode()[:200]})
print(json.dumps(out))
