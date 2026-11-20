import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
const c = new Client({ name: 'portal-probe', version: '0' });
await c.connect(new StreamableHTTPClientTransport(new URL('https://YOUR-PORTAL.eu.kongportals.com/api/v3/mcp')));
const txt = r => (r.content||[]).map(x => x.text || JSON.stringify(x)).join('\n') + (r.isError ? ' [isError]' : '');
const call = async (name, args, n=2500) => { try { const r = await c.callTool({ name, arguments: args }); console.log(`\n=== ${name} ${JSON.stringify(args).slice(0,160)}\n` + txt(r).slice(0, n)); } catch (e) { console.log(`\n=== ${name} ERROR ${e.message.slice(0,200)}`); } };
for (const q of process.argv.slice(2)) await call(...JSON.parse(q));
await c.close();
