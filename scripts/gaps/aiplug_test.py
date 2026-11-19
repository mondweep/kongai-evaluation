"""Gap 7 tests. Dummy data only."""
import json, time, urllib.request, urllib.error
from kapi import PROXY
R = {}
def post(path, body):
    req = urllib.request.Request(f"{PROXY}/aiplug/{path}", data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as r: st, raw = r.status, r.read().decode()
    except urllib.error.HTTPError as e: st, raw = e.code, e.read().decode()
    try: raw = json.loads(raw)
    except Exception: pass
    return {"status": st, "ms": round((time.time() - t) * 1000), "body": raw}
chat = lambda txt: {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": txt}]}
def echoed_messages(r):
    try:
        c = r["body"]["choices"][0]["message"]["content"]
        j = json.loads(c); return j.get("messages") or j.get("body", {}).get("messages") or j
    except Exception: return None
time.sleep(10)
r = post("decorator", chat("hello")); R["decorator"] = r; print("decorator", r["status"], json.dumps(r["body"])[:700])
R["template_ok"] = post("template", {"messages": "{template://greet}", "properties": {"name": "Ada", "lang": "French"}})
R["template_untemplated"] = post("template", chat("free text"))
R["template_missing_prop"] = post("template", {"messages": "{template://greet}", "properties": {"name": "Ada"}})
R["reqxform"] = post("reqxform", {"order": "A-1", "city": "Testville", "note": "dummy"})
R["respxform"] = post("respxform", {"ping": "dummy"})
R["judge"] = post("judge", chat("What is 2+2?"))
R["custom_clean"] = post("custom", chat("a harmless question"))
R["custom_block"] = post("custom", chat("this contains forbidden-word here"))
R["lakera_closed"] = post("lakera-closed", chat("hello"))
R["lakera_open"] = post("lakera-open", chat("hello"))
for k, v in R.items(): print(k, v["status"], v["ms"], json.dumps(v["body"])[:400])
json.dump(R, open("../../results/gap7-ai-plugins.json", "w"), indent=2)
