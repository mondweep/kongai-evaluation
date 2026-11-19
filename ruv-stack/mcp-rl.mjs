import fs from 'fs';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
const keys = JSON.parse(fs.readFileSync('./keys.json'));
const url = new URL('https://6efbd575d6.eu.serverless.gateways.konggateway.com/ruv-mcp');
async function run(agent, calls) {
  const c = new Client({ name: 'rl-test', version: '0' });
  const out = [];
  try { await c.connect(new StreamableHTTPClientTransport(url, { requestInit: { headers: { apikey: keys[agent] } } })); out.push('connect ok'); }
  catch (e) { return [agent, 'connect failed: ' + e.message.slice(0, 90)]; }
  for (let i = 0; i < calls; i++) {
    try { const r = await c.callTool({ name: 'list_orders', arguments: {} }); out.push(r.isError ? 'tool-error' : 'ok'); }
    catch (e) { out.push('refused:' + ((e.message.match(/API rate limit exceeded/) ? '429 rate limit' : e.message.replace(/\s+/g,' ').slice(0, 80)))); }
  }
  return [agent, out.join(', ')];
}
console.log(...await run('ruv-agent-a', 6));
console.log(...await run('ruv-agent-b', 1));
