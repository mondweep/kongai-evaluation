local path = kong.request.get_path()
local raw = kong.request.get_raw_body() or ""
if string.find(path, "fail500", 1, true) then return kong.response.exit(500, {error={message="mock upstream failure"}}) end
if string.find(path, "fail429", 1, true) then return kong.response.exit(429, {error={message="mock rate limited"}}, {["Retry-After"]="1"}) end
local ct = tonumber(kong.request.get_header("x-mock-completion-tokens") or "") or 20
local pt = math.ceil(#raw / 4)
local tag = "mock"
if string.find(path, "/b/", 1, true) then tag = "mock-b" end
return kong.response.exit(200, {
  id = "chatcmpl-mock", object = "chat.completion", created = ngx.time(), model = tag,
  choices = {{ index = 0, finish_reason = "stop", message = { role = "assistant", content = "RECEIVED:" .. raw }}},
  usage = { prompt_tokens = pt, completion_tokens = ct, total_tokens = pt + ct }
}, {["X-Mock-Upstream"]=tag})
