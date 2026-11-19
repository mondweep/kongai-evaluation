import fs from 'fs';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
const keys = JSON.parse(fs.readFileSync('./keys.json'));
for (const agent of ['ruv-agent-a', 'ruv-agent-b']) {
  const t = new StreamableHTTPClientTransport(new URL('https://6efbd575d6.eu.serverless.gateways.konggateway.com/ruv-mcp'), { requestInit: { headers: { apikey: keys[agent] } } });
  const c = new Client({ name: 'sdk-test', version: '0' });
  await c.connect(t);
  const tools = (await c.listTools()).tools.map(x => x.name);
  const r = await c.callTool({ name: 'list_orders', arguments: {} });
  let d; try { d = await c.callTool({ name: 'delete_order', arguments: { query_id: 'A-1' } }); d = d.isError ? 'tool error' : 'ok'; } catch (e) { d = 'refused: ' + e.message.slice(0, 80); }
  console.log(agent, 'server', c.getServerVersion()?.name, 'tools', tools, 'list_orders', r.isError ? 'error' : 'ok', 'delete_order', d);
  await c.close();
}
