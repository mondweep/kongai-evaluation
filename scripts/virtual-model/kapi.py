import json, os, urllib.request
B="https://eu.api.konghq.com/v2/control-planes/968bf452-4a30-4573-a9e1-41d3c7de5554/core-entities"
def k(method, path, body=None):
    req=urllib.request.Request(B+"/"+path, method=method, data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization":"Bearer "+os.environ["KCONNECT_TOKEN"],"content-type":"application/json"})
    try:
        with urllib.request.urlopen(req) as r: t=r.read(); return r.status, (json.loads(t) if t else None)
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b'null')
TAG=["virtual-model-demo"]
PROXY="https://6efbd575d6.eu.serverless.gateways.konggateway.com"
def targets(order=("gemini","mock"), weights=(100,10), mock_fail=False, alias="my-model"):
    T={"gemini":{"route_type":"llm/v1/chat","model":{"provider":"gemini","name":"gemini-2.5-flash","model_alias":alias,
               "options":{"input_cost":0.30,"output_cost":2.50}},
               "auth":{"param_name":"key","param_value":os.environ["GEMINI_API_KEY"],"param_location":"query"}},
       "mock":{"route_type":"llm/v1/chat","model":{"provider":"openai","name":"mock-b","model_alias":alias,
               "options":{"input_cost":0.15,"output_cost":0.60,
                 "upstream_url":PROXY+("/mock-llm/fail500" if mock_fail else "/mock-llm/b")+"/v1/chat/completions"}},
               "auth":{"header_name":"Authorization","header_value":"Bearer mock"}}}
    out=[]
    for name,w in zip(order,weights):
        t=dict(T[name]); t["weight"]=w; out.append(t)
    return out
