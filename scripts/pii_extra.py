import json,time,urllib.request
from mk import *
from pii_san import got
from run_guard import GW
PID='7a285149-7c9b-4653-84a1-325d42818f72'
def post(msgs):
    r=urllib.request.Request(GW+"/chat-pii",data=json.dumps({"messages":msgs}).encode(),headers={"content-type":"application/json"})
    t=time.time()
    try:
        with urllib.request.urlopen(r,timeout=30) as f: s,b=f.status,f.read().decode()
    except urllib.error.HTTPError as e: s,b=e.code,e.read().decode()
    return s,b,round((time.time()-t)*1000)
T="My name is John Smith and my email is john@example.com."
def show(label,msgs):
    s,b,ms=post(msgs); 
    try: c=json.loads(b)["choices"][0]["message"]["content"]
    except Exception: c=b
    print(f"--- {label}: {s} {ms}ms\n   LLM saw: {got(b)}\n   client got (start): {c[:120]}")
show("system+assistant roles",[{"role":"system","content":"Customer is Jane Roe, jane.roe@example.com"},{"role":"assistant","content":"Hello Jane Roe, card 4111 1111 1111 1111 noted"},{"role":"user","content":"hi"}])
patch_plugin(PID,{"redact_type":"synthetic"}); time.sleep(20)
show("synthetic",[{"role":"user","content":T}])
patch_plugin(PID,{"redact_type":"placeholder","recover_redacted":True}); time.sleep(20)
show("recover_redacted=true",[{"role":"user","content":T}])
patch_plugin(PID,{"recover_redacted":False,"block_if_detected":True}); time.sleep(20)
show("block_if_detected",[{"role":"user","content":T}])
show("block_if_detected benign",[{"role":"user","content":"What is the capital of France?"}])
patch_plugin(PID,{"block_if_detected":False})
