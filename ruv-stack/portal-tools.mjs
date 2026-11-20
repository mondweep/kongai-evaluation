import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
const c = new Client({ name: 'portal-probe', version: '0' });
await c.connect(new StreamableHTTPClientTransport(new URL('https://YOUR-PORTAL.eu.kongportals.com/api/v3/mcp')));
console.log('SERVER', JSON.stringify(c.getServerVersion()));
const t = await c.listTools();
for (const x of t.tools) console.log('TOOL', x.name, '|', (x.description||'').replace(/\s+/g,' ').slice(0,300), '| schema', JSON.stringify(x.inputSchema).slice(0,300));
try { const p = await c.listPrompts(); console.log('PROMPTS', p.prompts.map(x=>x.name)); } catch(e) { console.log('PROMPTS err', e.message.slice(0,80)); }
try { const r = await c.listResources(); console.log('RESOURCES', r.resources.map(x=>x.uri).slice(0,20)); } catch(e) { console.log('RESOURCES err', e.message.slice(0,80)); }
await c.close();
