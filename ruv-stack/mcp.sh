# usage: mcp.sh KEY METHOD PARAMS_JSON [SESSION]
U=https://YOUR-GATEWAY.eu.serverless.gateways.konggateway.com/ruv-mcp
H=(-H 'content-type: application/json' -H 'accept: application/json, text/event-stream' -H 'mcp-protocol-version: 2025-06-18')
[ -n "$1" ] && H+=(-H "apikey: $1"); [ -n "$4" ] && H+=(-H "mcp-session-id: $4")
curl -sS -m 30 -D hdr.txt "${H[@]}" $U -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"$2\",\"params\":$3}" -w " [%{http_code}]"; echo
