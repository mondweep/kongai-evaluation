import fs from 'fs';
import { createAIDefence } from '@claude-flow/aidefence';
import pkg from 'aidefence';
const { InjectionDetector } = pkg;
const C = JSON.parse(fs.readFileSync(new URL('./corpus.json', import.meta.url)));
const cf = createAIDefence({ enableLearning: false });
const inj = new InjectionDetector();
const txt = x => Array.isArray(x) ? x[1] : x;
const out = {};
for (const [set, items] of Object.entries(C)) {
  const rows = [];
  for (const it of items) {
    const p = txt(it);
    const d = await cf.detect(p);
    const r = inj.detect(p);
    rows.push({ cat: Array.isArray(it) ? it[0] : '', p, cf_threat: !d.safe, cf_types: (d.threats||[]).map(t=>t.type), cf_pii: cf.hasPII(p), aid_threat: !r.safe, aid_ids: r.threats.map(t=>t.id) });
  }
  out[set] = rows;
  const n = rows.length, c = k => rows.filter(r => r[k]).length;
  console.log(set.padEnd(17), `n=${n}`, `cf.detect flagged=${c('cf_threat')}`, `cf.hasPII=${c('cf_pii')}`, `aidefence3.2.1 flagged=${c('aid_threat')}`, `any=${rows.filter(r=>r.cf_threat||r.cf_pii||r.aid_threat).length}`);
}
fs.writeFileSync(new URL('./results.json', import.meta.url), JSON.stringify(out, null, 1));
