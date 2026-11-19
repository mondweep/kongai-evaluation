import fs from 'fs';
import { AnthropicToOpenRouterProxy } from './node_modules/agentic-flow/dist/proxy/anthropic-to-openrouter.js';
const keys = JSON.parse(fs.readFileSync('./keys.json'));
const GW = 'https://6efbd575d6.eu.serverless.gateways.konggateway.com';
const out = {};
let port = 3101;
for (const [agent, key] of Object.entries(keys)) {
  const p = new AnthropicToOpenRouterProxy({ openrouterApiKey: key, openrouterBaseUrl: GW + '/ruv-chat', defaultModel: 'gemini-2.5-flash', authToken: 'local-' + agent });
  p.start(port, '127.0.0.1');
  out[agent] = { port, token: 'local-' + agent };
  port++;
}
fs.writeFileSync('proxies.json', JSON.stringify(out));
