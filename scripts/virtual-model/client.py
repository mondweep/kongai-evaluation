import json, time, urllib.request, sys
URL="https://6efbd575d6.eu.serverless.gateways.konggateway.com/vm-chat"
def call(model="my-model", text="Reply with the single word: pong", key="vm-demo-key-3141"):
    body={"messages":[{"role":"user","content":text}]}
    if model is not None: body["model"]=model
    req=urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
        headers={"content-type":"application/json","apikey":key})
    t=time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as r: st=r.status; h=dict(r.headers); b=json.loads(r.read())
    except urllib.error.HTTPError as e: st=e.code; h=dict(e.headers); b=e.read().decode()[:200]
    ms=int((time.time()-t)*1000)
    m=b.get("model") if isinstance(b,dict) else None
    txt=(b["choices"][0]["message"]["content"][:40] if isinstance(b,dict) and b.get("choices") else b if isinstance(b,str) else "")
    return {"status":st,"ms":ms,"resp_model":m,"x_kong_llm_model":h.get("X-Kong-LLM-Model") or h.get("x-kong-llm-model"),
            "upstream":h.get("X-Mock-Upstream"),"text":txt.replace("\n"," ")}
if __name__=="__main__":
    for model in sys.argv[1:]:
        print(model, call(None if model=="NONE" else model))
