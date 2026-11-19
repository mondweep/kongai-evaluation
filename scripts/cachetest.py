import json,urllib.request,time
GW="https://6efbd575d6.eu.serverless.gateways.konggateway.com"
def send(t):
    r=urllib.request.Request(GW+"/chat-cache",data=json.dumps({"messages":[{"role":"user","content":t}]}).encode(),headers={"content-type":"application/json"})
    try:
        with urllib.request.urlopen(r,timeout=60) as f:
            h=dict(f.headers); return f.status, h.get("X-Cache-Status"), h.get("X-Mock-Upstream"), h.get("X-Cache-Key","")[:20]
    except urllib.error.HTTPError as e: return e.code, e.read()[:200]
tests=[("first","What is the capital of France?"),("exact repeat","What is the capital of France?"),
("paraphrase","Which city is the capital of France?"),("related but different","What is the capital of Germany?"),
("unrelated","Write a haiku about autumn."),("dangerous near-miss","What is the capital of France? Answer in Spanish.")]
for name,t in tests: print(f"{name:22}",send(t)); time.sleep(1)
