from mk import *
s=call("POST","services",{"name":"val-ai","url":"https://example.com","tags":["validation"]})
ids={"service":s["id"]}
for r in ["chat","chat-pii","chat-rl","chat-guard","chat-lb","chat-auth"]:
    x=call("POST",f"services/{s['id']}/routes",{"name":"val-"+r,"paths":["/"+r],"tags":["validation"]})
    ids[r]=x["id"]
    call("POST",f"routes/{x['id']}/plugins",{"name":"ai-proxy","tags":["validation"],"config":proxy()}) if r!="chat-lb" else None
json.dump(ids,open("ids.json","w"),indent=1); print(ids)
