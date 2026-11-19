# D2: AI Sanitizer redaction quality. Sends each corpus prompt to /chat-pii (sanitizer -> echo mock) and
# records what the upstream LLM actually received. recover_redacted must be false so the echo shows it.
import json,re,sys,time
from corpus import PII_STRUCTURED,PII_UNSTRUCTURED,BENIGN
from run_guard import send
def got(b):
    try:
        c=json.loads(b)["choices"][0]["message"]["content"]; m=re.search(r'RECEIVED:(\{.*\}) HEADERS:',c,re.S)
        return json.loads(m.group(1))["messages"][-1]["content"]
    except Exception: return None
def main():
  out={}
  for name,items in {"structured":PII_STRUCTURED,"unstructured":PII_UNSTRUCTURED,"benign":[("-",t) for t in BENIGN]}.items():
      res=[]
      for cat,t in items:
          s,b=send(sys.argv[1] if len(sys.argv)>1 else "/chat-pii",t); g=got(b)
          res.append({"cat":cat,"status":s,"sent":t,"llm_saw":g if g is not None else b[:200],"changed":g is not None and g!=t}); time.sleep(0.1)
      out[name]=res
  json.dump(out,open(sys.argv[2] if len(sys.argv)>2 else "res_sanitizer.json","w"),indent=1)
  for k,v in out.items():
      print(f"== {k}: changed {sum(r['changed'] for r in v)}/{len(v)}")
      for r in v: print(f"  {r['status']} {r['cat']:10} {'*' if r['changed'] else ' '} {r['llm_saw'][:110]}")

if __name__=="__main__": main()
