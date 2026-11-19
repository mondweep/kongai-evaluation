local raw = kong.request.get_raw_body() or ""
local it = math.ceil(#raw / 4)
if string.find(raw, '"stream":true', 1, true) then
  local ev = {
    'event: message_start\ndata: {"type":"message_start","message":{"id":"msg_mock","type":"message","role":"assistant","model":"claude-mock","content":[],"stop_reason":null,"usage":{"input_tokens":' .. it .. ',"output_tokens":1}}}\n\n',
    'event: content_block_start\ndata: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}\n\n',
    'event: content_block_delta\ndata: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"streamed hello"}}\n\n',
    'event: content_block_stop\ndata: {"type":"content_block_stop","index":0}\n\n',
    'event: message_delta\ndata: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":20}}\n\n',
    'event: message_stop\ndata: {"type":"message_stop"}\n\n'}
  return kong.response.exit(200, table.concat(ev), {["Content-Type"]="text/event-stream"})
end
local hdrs = ""
for k, v in pairs(kong.request.get_headers()) do hdrs = hdrs .. k .. "=" .. tostring(v) .. ";" end
return kong.response.exit(200, {id = "msg_mock", type = "message", role = "assistant", model = "claude-mock",
  content = {{type = "text", text = "RECEIVED:" .. raw .. " HEADERS:" .. hdrs}}, stop_reason = "end_turn",
  usage = {input_tokens = it, output_tokens = 20}})
