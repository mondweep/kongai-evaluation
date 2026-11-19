from mk import *; import os,sys
sys.argv=["x","aws-0-eu-west-1.pooler.supabase.com"]
exec(open("semguard.py").read().split("deny=[")[0])
ids=json.load(open("ids.json"))
v=vdb(); v["threshold"]=float(os.environ.get("TH","0.1"))
if "chat-cache" not in ids:
    x=call("POST",f"services/{ids['service']}/routes",{"name":"val-chat-cache","paths":["/chat-cache"],"tags":["validation"]}); ids["chat-cache"]=x["id"]
    call("POST",f"routes/{x['id']}/plugins",{"name":"ai-proxy","tags":["validation"],"config":proxy()})
if "semcache" in ids: call("DELETE","plugins/"+ids.pop("semcache"))
p=call("POST",f"routes/{ids['chat-cache']}/plugins",{"name":"ai-semantic-cache","tags":["validation","contains-secret"],"config":{"embeddings":emb(),"vectordb":v,"cache_ttl":600}})
ids["semcache"]=p["id"]; json.dump(ids,open("ids.json","w"),indent=1); print("ok")
