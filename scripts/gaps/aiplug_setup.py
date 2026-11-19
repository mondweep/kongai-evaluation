"""Gap 7: remaining ai-* plugins, one route each, tag aiplug-eval. LLM upstream is the mock (echoes body+headers);
Gemini (dummy data only) is used where a plugin needs its own LLM. Guardrail vendors get dummy credentials to observe fail mode."""
import json, os, sys
from kapi import call, CE, PROXY
T = ["aiplug-eval"]; S = {"routes": {}}
MOCK = {"route_type": "llm/v1/chat", "auth": {"header_name": "Authorization", "header_value": "Bearer dummy-not-a-real-key"},
        "model": {"provider": "openai", "name": "gpt-4o-mini", "options": {"upstream_url": f"{PROXY}/mock-llm/v1/chat/completions"}},
        "logging": {"log_statistics": True, "log_payloads": False}}
GEM = {"route_type": "llm/v1/chat", "auth": {"header_name": "x-goog-api-key", "header_value": os.environ["GEMINI_API_KEY"]},
       "model": {"provider": "gemini", "name": "gemini-2.5-flash"}}
svc = call("POST", f"{CE}/services", {"name": "aiplug-eval", "url": "https://httpbin.org/anything", "tags": T})[1]; S["service"] = svc["id"]
def route(name, plugins, mock=True):
    s, rt = call("POST", f"{CE}/services/{svc['id']}/routes", {"name": f"aiplug-{name}", "paths": [f"/aiplug/{name}"], "tags": T})
    assert s == 201, rt
    out = {"route": rt["id"], "plugins": {}}
    if mock: plugins = plugins + [("ai-proxy", MOCK)]
    for pn, cfg in plugins:
        s, p = call("POST", f"{CE}/routes/{rt['id']}/plugins", {"name": pn, "config": cfg, "tags": T})
        out["plugins"][pn] = p.get("id") if s == 201 else {"error": s, "body": p}
        print(name, pn, s, "" if s == 201 else json.dumps(p)[:500])
    S["routes"][name] = out
route("decorator", [("ai-prompt-decorator", {"prompts": {"prepend": [{"role": "system", "content": "EVAL-SYSTEM: answer in one line."}],
                                                          "append": [{"role": "user", "content": "EVAL-SUFFIX: cite no personal data."}]}})])
route("template", [("ai-prompt-template", {"allow_untemplated_requests": False,
                     "templates": [{"name": "greet", "template": '{"messages":[{"role":"user","content":"Write a greeting for {{name}} in {{lang}}"}]}'}]})])
route("reqxform", [("ai-request-transformer", {"prompt": "You receive a JSON request body. Return the same JSON object with the value of the field 'city' replaced by the string REDACTED. Return only JSON, no code fences.", "llm": GEM})], mock=False)
route("respxform", [("ai-response-transformer", {"prompt": "You receive a JSON HTTP response. Return a JSON object {\"summary\": <one short sentence describing the request method and url>}. Return only JSON, no code fences.", "llm": GEM})], mock=False)
route("judge", [("ai-llm-as-judge", {"llm": GEM, "sampling_rate": 1})])
route("custom", [("ai-custom-guardrail", {"guarding_mode": "INPUT", "text_source": "last_message",
                   "request": {"url": "https://httpbin.org/anything", "body": {"input": "$(content)"}},
                   "response": {"block": "$(resp.json and resp.json.input and string.find(resp.json.input, 'forbidden%-word') ~= nil)",
                                "block_message": "blocked by custom guardrail"}})])
route("lakera-closed", [("ai-lakera-guard", {"api_key": "dummy-invalid-key", "stop_on_error": True})])
route("lakera-open", [("ai-lakera-guard", {"api_key": "dummy-invalid-key", "stop_on_error": False})])
json.dump(S, open("secrets-aiplug.json", "w"), indent=2)
