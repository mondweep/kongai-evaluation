local m = kong.request.get_method()
local hdrs = {}
for k, v in pairs(kong.request.get_headers()) do hdrs[k] = v end
if m == "DELETE" then return kong.response.exit(200, {deleted = kong.request.get_query_arg("id"), seen_headers = hdrs}) end
return kong.response.exit(200, {orders = {{id = "A-1", item = "widget", qty = 2}, {id = "A-2", item = "gadget", qty = 1}}, seen_headers = hdrs})
