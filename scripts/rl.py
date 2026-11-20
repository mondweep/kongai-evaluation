import json,sys,urllib.request,time,concurrent.futures as cf
GW="https://YOUR-GATEWAY.eu.serverless.gateways.konggateway.com"
keys=json.load(open("keys.json"))
def send(key,ct=100,route="/chat-rl"):
    r=urllib.request.Request(GW+route,data=json.dumps({"messages":[{"role":"user","content":"count to three"}]}).encode(),headers={"content-type":"application/json","apikey":key,"x-mock-completion-tokens":str(ct)})
    try:
        with urllib.request.urlopen(r,timeout=30) as f:
            b=json.loads(f.read()); return f.status, b["usage"]["total_tokens"], {k:v for k,v in f.headers.items() if "ratelimit" in k.lower()}
    except urllib.error.HTTPError as e: return e.code,0,{k:v for k,v in e.headers.items() if "ratelimit" in k.lower() or k.lower()=="retry-after"}
mode=sys.argv[1] if len(sys.argv)>1 else ""
if mode=="seq":
    used=0
    for i in range(15):
        s,t,h=send(keys["val-bronze"]); used+=t; print(i+1,s,t,"cum",used,h)
        if s==429: break
elif mode=="conc":
    with cf.ThreadPoolExecutor(10) as ex: res=list(ex.map(lambda _: send(keys["val-bronze2"]),range(10)))
    ok=[r for r in res if r[0]==200]; print("200s",len(ok),"429s",sum(r[0]==429 for r in res),"tokens passed",sum(r[1] for r in ok),"limit 300")
