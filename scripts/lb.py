from mk import *; import sys,time,urllib.request,collections
ids=json.load(open("ids.json"))
def tgt(path,name):
    p=proxy(name,path); return {"route_type":"llm/v1/chat","auth":p["auth"],"logging":p["logging"],"model":p["model"]}
def cfg(criteria, fail="fail500"):
    c={"targets":[tgt(f"/mock-llm/{fail}/v1/chat/completions","mock-a"),tgt("/mock-llm/b/v1/chat/completions","mock-b")],
       "balancer":{"algorithm":"round-robin","retries":3}}
    if criteria: c["balancer"]["failover_criteria"]=criteria
    return c
def apply(c):
    if "lb" in ids: return patch_plugin(ids["lb"],c)
    p=call("POST",f"routes/{ids['chat-lb']}/plugins",{"name":"ai-proxy-advanced","tags":["validation"],"config":c}); ids["lb"]=p["id"]; json.dump(ids,open("ids.json","w"),indent=1)
def probe(n=20):
    out=collections.Counter()
    for i in range(n):
        r=urllib.request.Request(GW+"/chat-lb",data=b'{"messages":[{"role":"user","content":"hi"}]}',headers={"content-type":"application/json"})
        try:
            with urllib.request.urlopen(r,timeout=30) as f: out[(f.status,f.headers.get("X-Mock-Upstream"))]+=1
        except urllib.error.HTTPError as e: out[(e.code,None)]+=1
    return dict(out)
for name,crit,fail in [("default criteria, A returns 500",None,"fail500"),("+http_500",["error","timeout","http_500"],"fail500"),("+http_500+non_idempotent",["error","timeout","http_500","non_idempotent"],"fail500"),("A returns 429, +http_429+non_idempotent",["error","timeout","http_429","non_idempotent"],"fail429")]:
    apply(cfg(crit,fail)); time.sleep(15); print(name, probe())
