(() => {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let D, C;

  // ---------- theme
  const root = document.documentElement;
  try { const t = localStorage.getItem("theme"); if (t) root.dataset.theme = t; } catch (e) {}
  $("#theme").addEventListener("click", () => {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("theme", root.dataset.theme); } catch (e) {}
  });

  // ---------- helpers
  const verdictClass = (v) => /not with the defaults|partly/i.test(v) ? "warn" : /demonstrated/i.test(v) ? "good" : "neutral";
  const pct = (v, of) => Math.round((v / of) * 100);
  const docLink = (file, text) => `<a data-doc="${esc(file)}">${esc(text || "Read the write-up")}</a>`;

  function whenVisible(el, fn) {
    if (!("IntersectionObserver" in window)) return fn();
    const io = new IntersectionObserver((ents) => {
      if (ents.some((e) => e.isIntersecting)) { io.disconnect(); fn(); }
    }, { threshold: 0.25 });
    io.observe(el);
  }
  function countUp(el, to, suffix = "") {
    if (reduced) { el.textContent = to + suffix; return; }
    const t0 = performance.now(), dur = 1100;
    const step = (t) => {
      const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(to * e) + suffix;
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }
  const fillBars = (scope) => requestAnimationFrame(() => $$(".bar > i[data-w], .fillb[data-w]", scope).forEach((i) => (i.style.width = i.dataset.w)));

  // ---------- hero
  function hero() {
    $("#hero-meta").textContent = `${C.date} · ${C.env}`;
    $("#hero-title").textContent = C.hero.title;
    $("#hero-lede").textContent = C.hero.lede;
    const stats = C.hero.stats.map((s) => {
      if (/of 32/.test(s.label) && D.coverage.tested) s = { ...s, value: D.coverage.tested, label: `of ${D.coverage.total} Konnect features tried hands-on` };
      if (/findings/.test(s.label)) s = { ...s, value: D.findings.length };
      return s;
    });
    $("#hero-stats").innerHTML = stats.map((s) => `<div class="stat"><b data-to="${s.value}" data-suffix="${esc(s.suffix)}">0</b><span>${esc(s.label)}</span></div>`).join("");
    whenVisible($("#hero-stats"), () => $$("#hero-stats b").forEach((b) => countUp(b, +b.dataset.to, b.dataset.suffix)));
    for (const id of ["#repo-link", "#foot-repo"]) $(id).href = D.repo;
  }

  // ---------- claims
  function claims() {
    const tabs = $("#claim-tabs");
    tabs.innerHTML = D.risks.map((r, i) => `
      <button class="claim-tab" role="tab" aria-selected="${i === 0}" data-i="${i}">
        <strong>${i + 1}. ${esc(r.risk)}</strong>
        <span class="pill ${verdictClass(r.verdict)}">${esc(r.verdict)}</span>
      </button>`).join("");
    const show = (i) => {
      $$(".claim-tab", tabs).forEach((b) => b.setAttribute("aria-selected", b.dataset.i == i));
      const r = D.risks[i], x = C.risks[r.risk] || {};
      const level = C.verdictScale[r.verdict] ?? 2;
      $("#claim-panel").innerHTML = `
        <span class="pill ${verdictClass(r.verdict)}">${esc(r.verdict)}</span>
        <div class="verdict-scale" title="Strength of evidence">${[1, 2, 3, 4].map((n) => `<i class="${n <= level ? "on" : ""}"></i>`).join("")}</div>
        <h3 style="font-size:1.5rem;margin-top:.6rem">${esc(r.risk)}</h3>
        ${x.claim ? `<p class="claimq">Kong's claim: “${esc(x.claim)}”</p>` : ""}
        <p>${esc(r.summary)}</p>
        ${(x.metrics || []).map((m) => {
          const p = pct(m.value, m.of), good = p >= 80, unit = m.unit === "%";
          const bad = /passed a limit|NI numbers|Unstructured|Reworded|said what changed|default settings/i.test(m.label);
          const col = bad ? "var(--bad)" : good ? "var(--good)" : "var(--warn)";
          return `<div class="meter"><div class="meter-top"><span>${esc(m.label)}</span><b>${unit ? m.value + "%" : `${m.value} / ${m.of}`}</b></div>
            <div class="bar"><i data-w="${p}%" style="background:${col}"></i></div></div>`;
        }).join("")}
        ${x.fix ? `<div class="fix"><b>What to do</b>${esc(x.fix)}</div>` : ""}
        <p class="note">${docLink(x.doc || "report.md", "Read the full test report")}</p>`;
      fillBars($("#claim-panel"));
    };
    tabs.addEventListener("click", (e) => { const b = e.target.closest(".claim-tab"); if (b) show(+b.dataset.i); });
    tabs.addEventListener("keydown", (e) => {
      if (!["ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight"].includes(e.key)) return;
      const cur = +$(".claim-tab[aria-selected=true]", tabs).dataset.i;
      const n = (cur + (/Down|Right/.test(e.key) ? 1 : -1) + D.risks.length) % D.risks.length;
      show(n); $$(".claim-tab", tabs)[n].focus(); e.preventDefault();
    });
    whenVisible($("#claim-panel"), () => show(0));
  }

  // ---------- defaults toggle
  function defaults() {
    $("#defaults-intro").textContent = C.defaults.intro;
    const grid = $("#defaults-grid"), sw = $("#harden");
    const render = (hard) => {
      grid.innerHTML = C.defaults.rows.map((r) => {
        const ok = hard || !r.defaultBad;
        return `<div class="dcard ${ok ? "ok" : ""}">
          <h4>${esc(r.name)}</h4>
          <div class="outcome flip ${ok ? "good" : "bad"}">${esc(hard ? r.hardened : r.default)}</div>
          <div class="setting">${hard ? `Setting: <code>${esc(r.setting)}</code>` : "With Kong's default settings"} · ${docLink(r.doc, "source")}</div>
        </div>`;
      }).join("");
      $("#lbl-default").classList.toggle("on", !hard);
      $("#lbl-hard").classList.toggle("on", hard);
    };
    sw.addEventListener("click", () => {
      const v = sw.getAttribute("aria-checked") !== "true";
      sw.setAttribute("aria-checked", v); render(v);
    });
    render(false);
  }

  // ---------- cost
  function cost() {
    $("#limits-intro").textContent = C.limits.intro;
    const max = Math.max(...C.limits.bars.map((b) => b.x)) * 1.05;
    $("#limit-chart").innerHTML = C.limits.bars.map((b) => `
      <div class="limit-row"><span class="lbl">${esc(b.label)}</span>
        <div class="limit-track"><div class="fillb ${b.x > 2 ? "big" : ""}" data-w="${(b.x / max) * 100}%"></div><div class="cap" style="left:${(1 / max) * 100}%"></div></div>
        <span class="x">${b.x.toFixed(b.x < 2 ? 2 : 1)}×</span></div>`).join("");
    whenVisible($("#limit-chart"), () => fillBars($("#limit-chart")));

    const B = C.budget;
    $("#budget").innerHTML = `
      <span class="pill bad">New finding</span>
      <h3 style="margin-top:.6rem">${esc(B.title)}</h3>
      <p class="muted">${esc(B.body)}</p>
      <div class="gauge"><div class="meter-top"><span>Daily budget $${B.limit}</span><b>Spent $${B.consumed}</b></div>
        <div class="bar"><i data-w="100%"></i></div></div>
      <div class="small muted">Requests sent after the budget was blown:</div>
      <div class="reqs">${B.afterRequests.map((s) => `<span class="req">HTTP ${s}</span>`).join("")}</div>
      <p class="note">${docLink(B.doc)}</p>`;
    whenVisible($("#budget"), () => {
      fillBars($("#budget"));
      $$(".req", $("#budget")).forEach((r, i) => setTimeout(() => r.classList.add("show"), reduced ? 0 : 700 + i * 350));
    });

    // revocation race
    const R = C.revocation, maxS = Math.max(...R.items.map((i) => i.seconds));
    $("#revocation-intro").textContent = R.intro;
    $("#race-lanes").innerHTML = R.items.map((it, k) => `
      <div class="lane" data-k="${k}"><div class="lane-top"><span>${esc(it.label)} · ${docLink(it.doc, "source")}</span><span class="state">still works</span></div>
      <div class="bar"><i style="width:0"></i></div></div>`).join("");
    let raf;
    const run = () => {
      cancelAnimationFrame(raf);
      const lanes = $$(".lane"), speed = reduced ? 1e9 : 30; // 30 simulated seconds per real second
      lanes.forEach((l) => { l.classList.remove("done"); $(".state", l).textContent = "still works"; });
      const t0 = performance.now();
      const tick = (t) => {
        const s = Math.min(maxS, ((t - t0) / 1000) * speed);
        $("#race-clock").textContent = `${Math.floor(s)} s`;
        lanes.forEach((l) => {
          const it = R.items[l.dataset.k], done = s >= it.seconds;
          $(".bar > i", l).style.width = `${(Math.min(s, it.seconds) / maxS) * 100}%`;
          if (done && !l.classList.contains("done")) { l.classList.add("done"); $(".state", l).textContent = `blocked after ${it.seconds} s`; }
        });
        if (s < maxS) raf = requestAnimationFrame(tick);
      };
      raf = requestAnimationFrame(tick);
    };
    $("#race").addEventListener("click", run);
    whenVisible($("#revocation-card"), run);
  }

  // ---------- coverage
  function coverage() {
    const items = D.coverage.items;
    const KEYS = [["hands-on", "Hands-on"], ["partial", "Partial"], ["seen", "Seen only"], ["cant", "Can't run on the trial"]];
    const counts = Object.fromEntries(KEYS.map(([k]) => [k, items.filter((i) => i.key === k).length]));
    $("#coverage-intro").textContent = `${D.coverage.tested} of ${D.coverage.total} Konnect menu items were tested hands-on (some only in part). What's left needs the account owner, the UI or a self-hosted data plane.`;

    // donut
    const colors = { "hands-on": "var(--good)", partial: "var(--warn)", seen: "var(--accent)", cant: "var(--muted)" };
    const r = 48, circ = 2 * Math.PI * r; let off = 0;
    $("#coverage-donut").innerHTML = KEYS.map(([k]) => {
      const len = (counts[k] / items.length) * circ;
      const s = `<circle cx="60" cy="60" r="${r}" fill="none" stroke="${colors[k]}" stroke-width="16" stroke-dasharray="${len} ${circ - len}" stroke-dashoffset="${-off}" transform="rotate(-90 60 60)"/>`;
      off += len; return s;
    }).join("") + `<text x="60" y="58" text-anchor="middle" font-size="22" font-weight="800" fill="currentColor">${D.coverage.tested}/${D.coverage.total}</text><text x="60" y="76" text-anchor="middle" font-size="9" fill="currentColor" opacity=".6">hands-on</text>`;
    $("#coverage-donut").setAttribute("aria-label", KEYS.map(([k, l]) => `${l}: ${counts[k]}`).join(", "));

    const areas = [...new Set(items.map((i) => i.area))];
    let fKey = null, fArea = null;
    $("#coverage-filters").innerHTML =
      KEYS.map(([k, l]) => `<button class="chip" data-key="${k}" aria-pressed="false"><span class="sw k-${k}"></span>${esc(l)} (${counts[k]})</button>`).join("") +
      areas.map((a) => `<button class="chip" data-area="${esc(a)}" aria-pressed="false">${esc(a)}</button>`).join("");
    const tiles = $("#coverage-tiles");
    tiles.innerHTML = items.map((it, i) => `<button class="tile k-${it.key}" data-i="${i}" aria-pressed="false"><small>${esc(it.area)}</small><strong>${esc(it.feature)}</strong></button>`).join("");
    const apply = () => {
      $$(".tile", tiles).forEach((t) => {
        const it = items[t.dataset.i];
        t.classList.toggle("dim", (fKey && it.key !== fKey) || (fArea && it.area !== fArea));
      });
      $$("#coverage-filters .chip").forEach((c) => c.setAttribute("aria-pressed", c.dataset.key ? c.dataset.key === fKey : c.dataset.area === fArea));
    };
    $("#coverage-filters").addEventListener("click", (e) => {
      const c = e.target.closest(".chip"); if (!c) return;
      if (c.dataset.key) fKey = fKey === c.dataset.key ? null : c.dataset.key;
      else fArea = fArea === c.dataset.area ? null : c.dataset.area;
      apply();
    });
    tiles.addEventListener("click", (e) => {
      const t = e.target.closest(".tile"); if (!t) return;
      const it = items[t.dataset.i], det = $("#tile-detail");
      const was = t.getAttribute("aria-pressed") === "true";
      $$(".tile", tiles).forEach((x) => x.setAttribute("aria-pressed", "false"));
      if (was) { det.hidden = true; return; }
      t.setAttribute("aria-pressed", "true");
      det.hidden = false;
      det.innerHTML = `<div class="row-between"><div><small class="muted">${esc(it.area)}</small><h3>${esc(it.feature)}</h3></div><span class="pill ${it.key === "hands-on" ? "good" : it.key === "partial" ? "warn" : "neutral"}">${esc(it.status)}</span></div>
        <p>${esc(it.evidence)}</p>${it.docs.length ? `<p class="note">${[...new Set(it.docs)].map((d) => docLink(d, docTitle(d))).join(" · ")}</p>` : ""}`;
      if (innerWidth < 860) det.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "nearest" });
    });
  }

  // ---------- beyond
  function beyond() {
    // Virtual models
    const vm = D.virtualModels;
    const dots = (runs, cls) => runs.map((r, i) => `<span class="dot ${cls(r)}" title="Request ${i + 1}: HTTP ${r.status}${r.model ? " from " + esc(r.model) : ""}">${r.status}</span>`).join("");
    const okcls = (r) => (r.status === 200 ? "ok" : "err");
    const ok = (runs) => runs.filter((r) => r.status === 200).length;
    const fd = vm.runs.fallback_default || [], fe = vm.runs.fallback_explicit || [];
    const cheapAt = vm.costCap.findIndex((r) => /cheap/.test(r.model));
    $("#sub-vm").innerHTML = `
      <div class="grid2">
        <div class="card"><h3>One name, many models</h3>
          <p class="muted">Apps ask for a model alias such as <code>my-model</code>. Kong decides which real model answers. It works on the serverless gateway through AI Proxy Advanced, but fallback fails until you change the defaults.</p>
          <b>Primary target returns 500, default failover settings</b>
          <div class="dots">${dots(fd, okcls)}</div>
          <b>Same, with explicit failover criteria</b>
          <div class="dots">${dots(fe, okcls)}</div>
          <div class="legend"><span><i style="background:var(--good)"></i>${ok(fd)}/${fd.length} then ${ok(fe)}/${fe.length} succeeded</span><span><i style="background:var(--bad)"></i>error (the 503 came from Gemini itself)</span></div>
        </div>
        <div class="card"><h3>A per-model cost cap that reroutes</h3>
          <p class="muted">A cost budget on the expensive target. Once it ran out, Kong sent requests to the cheap target instead of refusing them.</p>
          <div class="dots">${vm.costCap.map((r) => `<span class="dot ${/cheap/.test(r.model) ? "ok" : "alt"}" title="Request ${r.i}: ${esc(r.model)}">#${r.i}</span>`).join("")}</div>
          <div class="legend"><span><i style="background:var(--accent)"></i>expensive model</span><span><i style="background:var(--good)"></i>cheap model${cheapAt >= 0 ? `, from request ${cheapAt + 1}` : ""}</span></div>
          <ul class="clean"><li>An unknown model name returns HTTP 500, not a 4xx.</li><li>The newer AI Model entity needs a self-hosted data plane.</li></ul>
          <p class="note">${docLink("virtual-model-evaluation.md")}</p>
        </div>
      </div>`;

    // MetaLLM
    const M = C.metallm, failedPct = Math.round((M.failedSpend / M.spend) * 100);
    $("#sub-metallm").innerHTML = `
      <div class="grid2">
        <div class="card"><h3>Cognitum MetaLLM: a router that picks for you</h3>
          <div class="big-num">$${M.spend.toFixed(4)}</div><div class="muted">spent on ${M.calls} live calls</div>
          <div class="spendbar" title="${failedPct}% of spend went on failed calls"><i style="width:${failedPct}%;background:var(--bad)"></i><i style="width:${100 - failedPct}%;background:var(--good)"></i></div>
          <div class="legend"><span><i style="background:var(--bad)"></i>${failedPct}% billed for failed calls</span><span><i style="background:var(--good)"></i>${100 - failedPct}% for answers</span></div>
          <ul class="clean">${M.issues.map((s) => `<li>${esc(s)}</li>`).join("")}</ul>
          <p><b>Together:</b> ${esc(M.stacked)}</p>
          <p class="note">${docLink(M.doc)}</p>
        </div>
        <div class="card"><h3>Every call</h3>
          <p class="muted small">Requested tier versus the tier that answered.</p>
          <div style="overflow-x:auto"><table class="mini prose"><thead><tr><th>#</th><th>Asked</th><th>Prompt</th><th>Result</th><th>Price</th></tr></thead><tbody>
          ${D.metallm.map((r) => `<tr><td>${esc(r.n)}</td><td>${esc(r.requested)}</td><td>${esc(r.prompt)}</td><td>${/^200/.test(r.result) ? '<span class="pill good">200</span>' : '<span class="pill bad">' + esc(r.result.split(" ")[0]) + "</span>"}</td><td>${esc(r.price)}</td></tr>`).join("")}
          </tbody></table></div>
        </div>
      </div>`;

    // MCP chat replay
    const P = C.mcp;
    $("#sub-mcp").innerHTML = `
      <div class="grid2">
        <div class="card"><h3>Replay the conversation</h3><p class="muted">${esc(P.intro)}</p>
          <div class="chat" id="chat"></div>
          <div class="chat-controls"><button class="btn primary" id="chat-next">Next message ▶</button><button class="btn" id="chat-reset">Restart</button></div>
        </div>
        <div class="card"><h3>What we learned</h3><ul class="clean">${P.findings.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
          <div class="fix"><b>Recommendation</b>Never give an MCP client an owner token. Use a system account scoped to the control planes it should touch, with a short expiry.</div>
          <p class="note">${docLink(P.doc)}</p></div>
      </div>`;
    let step = 0;
    const chat = $("#chat");
    const next = () => {
      if (step >= P.steps.length) return;
      const s = P.steps[step++];
      chat.insertAdjacentHTML("beforeend", `<div class="msg user">${esc(s.ask)}</div>`);
      setTimeout(() => {
        chat.insertAdjacentHTML("beforeend", `<div class="msg bot ${s.ok ? "" : "denied"}">${esc(s.reply)}</div>`);
        if (step >= P.steps.length) $("#chat-next").disabled = true;
      }, reduced ? 0 : 450);
    };
    $("#chat-next").addEventListener("click", next);
    $("#chat-reset").addEventListener("click", () => { chat.innerHTML = ""; step = 0; $("#chat-next").disabled = false; next(); });
    next();

    // rUv
    const U = C.ruv, G = C.guards;
    $("#sub-ruv").innerHTML = `
      <div class="grid2">
        <div class="card"><h3>Different layers</h3><p class="muted">${esc(U.intro)}</p>
          <div class="layers">${U.layers.map((l, i) => `${i ? '<div class="arrow">↓</div>' : ""}<div class="layer ${/Kong/.test(l.who) ? "kong" : ""}"><b>${esc(l.name)}: ${esc(l.who)}</b><em>${esc(l.does)}</em></div>`).join("")}</div>
          <ul class="clean">${U.points.map((p) => `<li>${esc(p)}</li>`).join("")}</ul>
          <p class="note">${docLink(U.doc)}</p></div>
        <div class="card guards-chart"><h3>Guards together beat either alone</h3><p class="muted">${esc(G.intro)}</p>
          ${G.sets.map((s) => `<div class="grow"><div class="gl"><b>${esc(s.set)}</b> <span class="muted">(${s.of})</span></div>
            ${[["Kong", s.kong, "kong"], ["AIDefence", s.aidefence, "aid"], ["Both", s.either, "both"]].filter((x) => x[1] !== null).map(([n, v, c]) => `
            <div class="gbar"><span>${n}</span><div class="bar"><i class="${c}" data-w="${pct(v, s.of)}%"></i></div><b>${v}/${s.of}</b></div>`).join("")}</div>`).join("")}
        </div>
      </div>`;

    // All evaluations
    $("#sub-all").innerHTML = `<div class="evals">${D.evaluations.map((e) => `
      <div class="eval"><div><b>${esc(e.name)}</b><div class="note">${e.docs.map((d) => docLink(d, "Write-up")).join(" · ")}</div></div>
      <div><div class="q">${esc(e.question)}</div>${esc(e.answer)}</div></div>`).join("")}</div>`;

    const tabs = $("#subtabs");
    tabs.addEventListener("click", (e) => {
      const b = e.target.closest("button"); if (!b) return;
      $$("button", tabs).forEach((x) => x.setAttribute("aria-selected", x === b));
      $$(".subpanel").forEach((p) => (p.hidden = p.id !== "sub-" + b.dataset.tab));
      fillBars($("#sub-" + b.dataset.tab));
    });
  }

  // ---------- findings
  function findings() {
    const list = $("#finding-list"), q = $("#find-q");
    const sections = [...new Set(D.findings.map((f) => f.section))];
    let sec = null;
    $("#find-sections").innerHTML = sections.map((s) => `<button class="chip" data-s="${esc(s)}" aria-pressed="false">${esc(s)}</button>`).join("");
    const hl = (text, term) => {
      const t = esc(text);
      if (!term) return t;
      const re = new RegExp("(" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
      return t.replace(re, "<mark>$1</mark>");
    };
    const render = () => {
      const term = q.value.trim();
      const items = D.findings.filter((f) => (!sec || f.section === sec) && (!term || (f.title + " " + f.body).toLowerCase().includes(term.toLowerCase())));
      list.innerHTML = items.length ? items.map((f) => `
        <li class="finding ${term ? "open" : ""}"><button aria-expanded="${!!term}"><span class="num">${String(f.n).padStart(2, "0")}</span><span class="t">${hl(f.title, term)}</span><span class="chev">›</span></button>
        <div class="b">${hl(f.body, term)}${f.docs.length ? `<div class="note">${f.docs.map((d) => docLink(d, docTitle(d))).join(" · ")}</div>` : ""}</div></li>`).join("")
        : `<li class="muted">No findings match “${esc(term)}”.</li>`;
    };
    q.addEventListener("input", render);
    $("#find-sections").addEventListener("click", (e) => {
      const c = e.target.closest(".chip"); if (!c) return;
      sec = sec === c.dataset.s ? null : c.dataset.s;
      $$("#find-sections .chip").forEach((x) => x.setAttribute("aria-pressed", x.dataset.s === sec));
      render();
    });
    list.addEventListener("click", (e) => {
      const b = e.target.closest(".finding > button"); if (!b) return;
      const li = b.parentElement; li.classList.toggle("open"); b.setAttribute("aria-expanded", li.classList.contains("open"));
    });
    render();
  }

  // ---------- library + reader
  const docTitle = (f) => (D.library.find((d) => d.file === f) || {}).title || f;
  function library() {
    $("#library-list").innerHTML = D.library.map((d) => `<button class="doc-card" data-doc="${esc(d.file)}"><strong>${esc(d.title)}</strong><br><small>docs/${esc(d.file)}</small></button>`).join("");
    $("#method").innerHTML = C.method.map((m) => `<div><b>${esc(m.title)}</b><p>${esc(m.body)}</p></div>`).join("");
  }
  const drawer = $("#drawer");
  async function openDoc(file) {
    if (!D.library.some((d) => d.file === file)) return;
    $("#drawer-title").textContent = docTitle(file);
    $("#drawer-gh").href = `${D.repo}/blob/main/docs/${file}`;
    $("#drawer-body").innerHTML = '<p class="muted">Loading…</p>';
    drawer.classList.add("open"); drawer.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    if (location.hash !== "#doc=" + file) history.pushState(null, "", "#doc=" + file);
    try {
      const md = await (await fetch("docs/" + file)).text();
      const html = window.marked ? marked.parse(md) : "<pre>" + esc(md) + "</pre>";
      $("#drawer-body").innerHTML = window.DOMPurify ? DOMPurify.sanitize(html) : esc(md);
      // Rewrite links: other write-ups open in the drawer, repo paths go to GitHub
      $$("#drawer-body a[href]").forEach((a) => {
        const h = a.getAttribute("href");
        const m = h.match(/^(?:\.\/)?([\w.-]+\.md)(#.*)?$/);
        if (m && D.library.some((d) => d.file === m[1])) { a.removeAttribute("href"); a.dataset.doc = m[1]; }
        else if (!/^(https?:|#|mailto:)/.test(h)) { a.href = `${D.repo}/blob/main/docs/${h}`; a.target = "_blank"; a.rel = "noopener"; }
        else if (/^https?:/.test(h)) { a.target = "_blank"; a.rel = "noopener"; }
      });
      $("#drawer-body").scrollTop = 0;
      $(".drawer-panel [data-close]").focus();
    } catch (e) {
      $("#drawer-body").innerHTML = `<p>Couldn't load this write-up. <a href="${D.repo}/blob/main/docs/${esc(file)}" target="_blank" rel="noopener">Read it on GitHub</a>.</p>`;
    }
  }
  function closeDoc() {
    drawer.classList.remove("open"); drawer.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    if (location.hash.startsWith("#doc=")) history.pushState(null, "", location.pathname);
  }
  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-doc]");
    if (a) { e.preventDefault(); openDoc(a.dataset.doc); return; }
    if (e.target.closest("[data-close]")) closeDoc();
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && drawer.classList.contains("open")) closeDoc(); });
  addEventListener("popstate", () => { const m = location.hash.match(/^#doc=(.+)$/); m ? openDoc(m[1]) : drawer.classList.contains("open") && closeDoc(); });

  // ---------- scroll progress + nav
  function chrome() {
    const bar = $("#progress"), links = $$("#nav a"), secs = links.map((a) => $(a.getAttribute("href")));
    const on = () => {
      const h = document.documentElement;
      bar.style.width = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100 + "%";
      let cur = -1; secs.forEach((s, i) => { if (s && s.getBoundingClientRect().top < 120) cur = i; });
      links.forEach((a, i) => a.classList.toggle("active", i === cur));
    };
    addEventListener("scroll", on, { passive: true }); on();
  }

  // ---------- boot
  fetch("data.json").then((r) => r.json()).then((data) => {
    D = data; C = data.content;
    hero(); claims(); defaults(); cost(); coverage(); beyond(); findings(); library(); chrome();
    const m = location.hash.match(/^#doc=(.+)$/); if (m) openDoc(m[1]);
  }).catch((e) => {
    document.querySelector("main").insertAdjacentHTML("afterbegin", `<p style="padding:2rem">Couldn't load the findings data (${esc(e.message)}).</p>`);
  });
})();
