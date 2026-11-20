import json,os,sys,urllib.request
B="https://eu.api.konghq.com/v2/control-planes/YOUR-CONTROL-PLANE-ID/core-entities/"
def call(m,p,d=None):
    r=urllib.request.Request(B+p,method=m,data=json.dumps(d).encode() if d is not None else None,headers={"Authorization":"Bearer "+os.environ["KCONNECT_TOKEN"],"content-type":"application/json"})
    try:
        with urllib.request.urlopen(r) as f: t=f.read(); return json.loads(t) if t else {}
    except urllib.error.HTTPError as e: print("ERR",m,p,e.code,e.read()[:600].decode()); raise
GW="https://YOUR-GATEWAY.eu.serverless.gateways.konggateway.com"
def proxy(name="mock",path="/mock-llm/v1/chat/completions"):
    return {"route_type":"llm/v1/chat","auth":{"header_name":"Authorization","header_value":"Bearer dummy"},
      "logging":{"log_statistics":True,"log_payloads":False},
      "model":{"provider":"openai","name":name,"options":{"upstream_url":GW+path,"input_cost":1000,"output_cost":2000}}}
def patch_plugin(pid, cfg, **extra):
    p=call("GET",f"plugins/{pid}")
    for k,v in cfg.items(): p["config"][k]=v
    p.update(extra)
    for k in ("created_at","updated_at"): p.pop(k,None)
    return call("PUT",f"plugins/{pid}",p)
