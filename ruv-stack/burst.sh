port=$1; a=$2; n=$3
seq $n | xargs -P $n -I{} curl -sS -m 60 -o /dev/null -w "%{http_code}\n" -H "x-api-key: local-ruv-agent-$a" -H 'anthropic-version: 2023-06-01' -H 'content-type: application/json' http://127.0.0.1:$port/v1/messages -d '{"model":"claude-sonnet-4","max_tokens":50,"messages":[{"role":"user","content":"swarm task {} from agent '$a'"}]}' | sort | uniq -c
