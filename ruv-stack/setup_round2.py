# Probe round 2: Anthropic-native route (what Claude Code / ruflo send) and a rate-limited MCP route. All tagged ruv-eval.
import json,secrets
import sys
sys.path.insert(0, "../scripts")
from mk import call, GW
T=["ruv-eval"]; ids={}
host=GW.split("//")[1]
anth_lua=open('anth-mock.lua').read()  # returns SSE when the request asks to stream
orders_lua=open('orders.lua').read()
s=call("POST","services",{"name":"ruv-eval-mock","url":"http://localhost:9","tags":T}); ids['svc_mock']=s['id']
r=call("POST",f"services/{s['id']}/routes",{"name":"ruv-eval-mock-anthropic","paths":["/ruv-mock-anthropic"],"tags":T})
call("POST",f"routes/{r['id']}/plugins",{"name":"pre-function","tags":T,"config":{"access":[anth_lua]}})
r=call("POST",f"services/{s['id']}/routes",{"name":"ruv-eval-orders-backend","paths":["/ruv-orders-backend"],"tags":T})
call("POST",f"routes/{r['id']}/plugins",{"name":"pre-function","tags":T,"config":{"access":[orders_lua]}})
# Anthropic-native LLM route
s=call("POST","services",{"name":"ruv-eval-anthropic","url":"https://example.com","tags":T})
r=call("POST",f"services/{s['id']}/routes",{"name":"ruv-eval-anthropic","paths":["/ruv-anthropic"],"tags":T}); ids['rt_anth']=r['id']
call("POST",f"routes/{r['id']}/plugins",{"name":"key-auth","tags":T,"config":{"key_names":["x-api-key"],"hide_credentials":True}})
call("POST",f"routes/{r['id']}/plugins",{"name":"ai-proxy","tags":T,"config":{"route_type":"llm/v1/chat","llm_format":"anthropic",
  "auth":{"header_name":"x-api-key","header_value":"dummy-anthropic-provider-key"},
  "logging":{"log_statistics":True,"log_payloads":False},
  "model":{"provider":"anthropic","name":"claude-sonnet-4-5","options":{"upstream_url":GW+"/ruv-mock-anthropic/v1/messages","anthropic_version":"2023-06-01","input_cost":3,"output_cost":15}}}})
# MCP route with a per-consumer rate limit of 5 requests/minute
s=call("POST","services",{"name":"ruv-eval-orders-api","url":GW+"/ruv-orders-backend","tags":T})
r=call("POST",f"services/{s['id']}/routes",{"name":"ruv-eval-mcp","paths":["/ruv-mcp"],"tags":T}); ids['rt_mcp']=r['id']
call("POST",f"routes/{r['id']}/plugins",{"name":"key-auth","tags":T,"config":{"key_names":["apikey"],"hide_credentials":True}})
call("POST",f"routes/{r['id']}/plugins",{"name":"rate-limiting","tags":T,"config":{"minute":5,"limit_by":"consumer","policy":"local"}})
call("POST",f"routes/{r['id']}/plugins",{"name":"ai-mcp-proxy","tags":T,"config":{"mode":"conversion-listener",
 "logging":{"log_statistics":True,"log_payloads":False,"log_audits":True},
 "default_acl":[{"scope":"tools","allow":["ruv-agent-a","ruv-agent-b"]}],
 "tools":[{"name":"list_orders","description":"List all customer orders","method":"GET","scheme":"https","host":host,"path":"/ruv-orders-backend","annotations":{"read_only_hint":True}}]}})
keys={}
for c in ["ruv-agent-a","ruv-agent-b"]:
    x=call("POST","consumers",{"username":c,"tags":T})
    k="ruv-"+c[-1]+"-"+secrets.token_hex(12)
    call("POST",f"consumers/{x['id']}/key-auth",{"key":k,"tags":T}); keys[c]=k
json.dump(ids,open('ids.json','w'),indent=1); json.dump(keys,open('keys.json','w'))
print("ok")
