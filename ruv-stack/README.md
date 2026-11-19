# Probes: Kong in front of rUv's agent stack

Write-up: [../docs/ruv-stack-evaluation.md](../docs/ruv-stack-evaluation.md). Everything here creates Konnect entities tagged `ruv-eval` on the serverless control plane; `cleanup.py` deletes them all.

Setup: `KCONNECT_TOKEN` set, `npm install --ignore-scripts` in this folder, and the corpus exported once:
`python3 -c "import sys,json; sys.path.insert(0,'../scripts'); import corpus as c; json.dump({k:getattr(c,k) for k in dir(c) if k.isupper()}, open('corpus.json','w'))"`

| Step | Command | What it shows |
|---|---|---|
| AIDefence vs corpus (local, no Konnect) | `node score.mjs` | Detection counts per set; writes `results.json` |
| Round 1 entities | `python3 setup_round1.py` | LLM route + MCP route, consumers `ruv-agent-a/b`, keys in `keys.json` |
| agentic-flow proxies | `node run-proxies.mjs` | One Anthropic-to-OpenRouter proxy per agent on ports 3101/3102, pointed at Kong |
| Swarm burst | `bash burst.sh 3101 a 60` | Token limit under concurrency |
| MCP via SDK client | `node mcpclient.mjs` | Tool discovery and per-tool ACL per agent |
| MCP by hand | `bash mcp.sh <key> tools/list '{}'` | Raw JSON-RPC over streamable HTTP |
| Round 2 entities | `python3 cleanup.py && python3 setup_round2.py` | Anthropic-native route and a rate-limited MCP route |
| MCP rate limit | `node mcp-rl.mjs` | Handshake counts against the limit |
| Clean up | `python3 cleanup.py` | Deletes everything tagged `ruv-eval` |
