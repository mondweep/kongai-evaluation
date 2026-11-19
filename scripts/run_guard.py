import json,sys,urllib.request,time
from corpus import *
GW="https://6efbd575d6.eu.serverless.gateways.konggateway.com"
def send(route,text,headers={}):
    r=urllib.request.Request(GW+route,data=json.dumps({"messages":[{"role":"user","content":text}]}).encode(),headers={"content-type":"application/json",**headers})
    try:
        with urllib.request.urlopen(r,timeout=30) as f: return f.status,f.read().decode()
    except urllib.error.HTTPError as e: return e.code,e.read().decode()
def run(route,sets):
    out={}
    for name,items in sets.items():
        res=[]
        for it in items:
            cat,t=it if isinstance(it,tuple) else ("-",it)
            s,b=send(route,t); res.append((cat,s,t,b[:160])); time.sleep(0.05)
        out[name]=res
    return out
if __name__=="__main__":
    route=sys.argv[1]
    sets={"pii":{"structured":PII_STRUCTURED,"unstructured":PII_UNSTRUCTURED,"benign":BENIGN},
          "inj":{"direct":INJ_DIRECT,"paraphrased":INJ_PARAPHRASED,"benign":BENIGN}}[sys.argv[2]]
    out=run(route,sets)
    json.dump(out,open(f"res_{sys.argv[2]}.json","w"),indent=1)
    for k,v in out.items():
        blocked=sum(1 for r in v if r[1]==400); print(k,f"blocked {blocked}/{len(v)}", "statuses",sorted(set(r[1] for r in v)))
        for r in v:
            if (k=="benign")==(r[1]==400) : print("   MISS/FP:",r[0],r[1],r[2][:70])
