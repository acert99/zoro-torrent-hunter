const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
                set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} } };
// Plugin data is untrusted: only these schemes may reach an href (blocks javascript:, data:, file:).
const safeUrl = (u) => /^(magnet:\?|https?:\/\/)/i.test(String(u)) ? u : "";
const ICON = {
  magnet: '<svg class="i" viewBox="0 0 24 24"><path d="m6 15-4-4 6.75-6.77a7.79 7.79 0 0 1 11 11L13 22l-4-4 6.39-6.36a2.14 2.14 0 0 0-3-3L6 15"/><path d="m5 8 4 4m3 3 4 4"/></svg>',
  file: '<svg class="i" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5M12 15V3"/></svg>',
  copy: '<svg class="i" viewBox="0 0 24 24"><rect x="8" y="8" width="14" height="14" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>',
  check: '<svg class="i" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>',
  ext: '<svg class="i" viewBox="0 0 24 24"><path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>',
  search: '<svg class="i" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
  sun: '<svg class="i" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2m-7.07-14.93 1.41 1.41m11.32 11.32 1.41 1.41M2 12h2m16 0h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
  moon: '<svg class="i" viewBox="0 0 24 24"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>',
};

let meta = { engines: [], default: [], cats: [] };
let enabled = new Set(), engineState = {}, results = new Map();
let sortKey = "score", sortDir = -1, searchId = 0, progress = { done: 0, total: 0 }, started = 0, elapsed = 0;

function human(n) {
  if (n == null || n < 0) return "—";
  const u = ["B", "KB", "MB", "GB", "TB"]; let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return n.toFixed(1) + " " + u[i];
}
const fmt = (n) => n.toLocaleString("pt-BR");
// Same torrent, same key: base32 infohashes (32 chars) become hex, like infohash() in torrent_search.py.
function b32hex(s) {
  const A = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"; let bits = "", out = "";
  for (const c of s.toUpperCase()) { const v = A.indexOf(c); if (v < 0) return ""; bits += v.toString(2).padStart(5, "0"); }
  for (let i = 0; i < bits.length; i += 4) out += parseInt(bits.slice(i, i + 4), 2).toString(16);
  return out;
}
function keyOf(r) {
  const m = /btih:([a-z0-9]+)/i.exec(r.link); if (!m) return r.link;
  return (m[1].length === 32 && b32hex(m[1])) || m[1].toLowerCase();
}

/* theme */
function applyTheme(t) {
  if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme;
  const dark = t ? t === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  $("#theme").innerHTML = dark ? ICON.sun : ICON.moon;
  const logo = dark ? "/logo-dark.png" : "/logo-light.png";
  $("#logo").src = logo;
  $("link[rel=icon]").href = logo;
}
$("#theme").onclick = () => {
  const dark = document.documentElement.dataset.theme
    ? document.documentElement.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  const next = dark ? "light" : "dark"; store.set("theme", next); applyTheme(next);
};
applyTheme(store.get("theme", null));

async function init() {
  meta = await (await fetch("/api/engines")).json();
  $("#cat").innerHTML = meta.cats.map((c) => `<option value="${esc(c)}">${esc(catLabel(c))}</option>`).join("");
  const saved = store.get("engines", null);
  enabled = new Set(saved ? saved.filter((e) => meta.engines.includes(e)) : meta.engines);
  renderSites(); renderStats(); renderTable();
}
function catLabel(c) {
  return { all: "Tudo", movies: "Filmes", tv: "Séries", music: "Música", games: "Jogos", anime: "Anime", software: "Software", books: "Livros" }[c] || c;
}
function saveEnabled() { store.set("engines", [...enabled]); }

function renderSites() {
  const max = Math.max(1, ...Object.values(engineState).map((s) => s.n || 0));
  $("#engines").innerHTML = meta.engines.map((e) => {
    const s = engineState[e] || {}, on = enabled.has(e);
    const metaTxt = s.state === "run" ? "…" : s.state ? `${s.state === "err" ? "erro" : fmt(s.n)} · ${(s.ms / 1000).toFixed(0)}s` : "";
    return `<li class="site${on ? "" : " off"}" title="${esc(s.err || "")}">
      <label><input class="cb" type="checkbox" value="${esc(e)}" ${on ? "checked" : ""}><span class="site-name">${esc(e)}</span></label>
      <span class="site-meta">${esc(metaTxt)}<span class="dot ${s.state || ""}"></span></span>
      <span class="minibar"><i style="--w:${Math.round(100 * (s.n || 0) / max)}%"></i></span></li>`;
  }).join("");
}
$("#engines").addEventListener("change", (ev) => {
  if (!ev.target.matches(".cb")) return;
  ev.target.checked ? enabled.add(ev.target.value) : enabled.delete(ev.target.value);
  saveEnabled(); renderSites();
});
const setEnabled = (fn) => { enabled = new Set(meta.engines.filter(fn)); saveEnabled(); renderSites(); };
$("#all").onclick = () => setEnabled(() => true);
$("#none").onclick = () => setEnabled(() => false);
$("#def").onclick = () => setEnabled((e) => meta.default.includes(e) || e === "archive");

async function search(ev) {
  ev.preventDefault();
  const q = $("#q").value.trim(); if (!q) { $("#q").focus(); return; }
  const id = ++searchId; results = new Map(); engineState = {};
  const active = meta.engines.filter((e) => enabled.has(e));
  active.forEach((e) => { engineState[e] = { state: "run" }; });
  progress = { done: 0, total: active.length }; started = performance.now(); elapsed = 0;
  render();
  await Promise.all(active.map(async (e) => {
    try {
      const url = `/api/search?engine=${encodeURIComponent(e)}&q=${encodeURIComponent(q)}&cat=${encodeURIComponent($("#cat").value)}`;
      const d = await (await fetch(url)).json();
      if (id !== searchId) return;
      (d.rows || []).forEach(add);
      engineState[e] = { state: d.error ? "err" : "ok", n: (d.rows || []).length, ms: d.ms, err: d.error };
    } catch (err) {
      if (id === searchId) engineState[e] = { state: "err", n: 0, ms: performance.now() - started, err: "falha de conexão" };
    }
    if (id === searchId) { progress.done++; elapsed = performance.now() - started; render(); }
  }));
}

function add(r) {
  const k = keyOf(r), cur = results.get(k);
  if (!cur) { results.set(k, { ...r, sources: [r.engine] }); return; }
  if (!cur.sources.includes(r.engine)) cur.sources.push(r.engine);
  const best = r.score > cur.score ? r : cur;
  const dl = [cur.downloads, r.downloads].filter((x) => x != null);
  Object.assign(cur, { seeds: Math.max(cur.seeds, r.seeds), leech: Math.max(cur.leech, r.leech),
    downloads: dl.length ? Math.max(...dl) : null, trust: cur.trust || r.trust, score: Math.max(cur.score, r.score),
    link: best.link.startsWith("magnet:") ? best.link : (cur.link.startsWith("magnet:") ? cur.link : best.link),
    engine: best.engine, name: best.name, size: cur.size > 0 ? cur.size : r.size });
}

function render() { renderSites(); renderStats(); renderTable(); }

function renderStats() {
  const busy = progress.done < progress.total;
  const ok = Object.values(engineState).filter((s) => s.state === "ok").length;
  const errs = Object.values(engineState).filter((s) => s.state === "err").length;
  $("#st-res").textContent = fmt(results.size);
  $("#st-sites").textContent = `${progress.done}/${progress.total}`;
  $("#st-sites-sub").textContent = busy ? "buscando…" : errs ? `${ok} ok · ${errs} com erro` : progress.total ? "todos responderam" : "responderam";
  let top = null; results.forEach((r) => { if (!top || r.seeds > top.seeds) top = r; });
  $("#st-seeds").textContent = top && top.seeds >= 0 ? fmt(top.seeds) : "—";
  $("#st-seeds-sub").textContent = top ? top.name : "nenhuma busca ainda";
  $("#st-time").textContent = progress.total ? `${(elapsed / 1000).toFixed(1)}s` : "—";
  $("#live-dot").className = "dot " + (busy ? "run" : "ok");
  $("#live-text").textContent = busy ? `Buscando ${progress.done}/${progress.total}` : "Pronto";
}

function renderTable() {
  const f = $("#filter").value.toLowerCase(), min = +$("#minseeds").value || 0, trustOnly = $("#trustonly").checked;
  const busy = progress.done < progress.total;
  let list = [...results.values()].filter((r) => r.name.toLowerCase().includes(f) && (min === 0 || r.seeds >= min) && (!trustOnly || (r.trust && r.trust !== "remake")));
  const val = (r) => sortKey === "sources" ? r.sources.length : (r[sortKey] ?? -1);
  list.sort((a, b) => sortDir * (sortKey === "name" ? b.name.localeCompare(a.name) : (val(b) > val(a) ? -1 : val(b) < val(a) ? 1 : 0)));
  const shown = list.slice(0, 500);
  $("#status").textContent = results.size ? `${fmt(list.length)} de ${fmt(results.size)}` : "";
  $("#foot-count").textContent = results.size ? `Mostrando ${fmt(shown.length)} de ${fmt(list.length)}` : "";
  const top = Math.max(1, ...list.map((r) => r.score));
  if (!shown.length) {
    $("#rows").innerHTML = busy
      ? Array.from({ length: 6 }, () => `<tr><td><div class="skel" style="width:90px"></div></td><td><div class="skel" style="width:${40 + Math.random() * 45}%"></div></td><td class="num"><div class="skel" style="width:60px;margin-left:auto"></div></td><td class="num"><div class="skel" style="width:36px;margin-left:auto"></div></td><td class="num c-leech"><div class="skel" style="width:30px;margin-left:auto"></div></td><td class="num c-dl"><div class="skel" style="width:50px;margin-left:auto"></div></td><td class="num c-src"><div class="skel" style="width:16px;margin-left:auto"></div></td><td><div class="skel" style="width:80px;margin-left:auto"></div></td></tr>`).join("")
      : `<tr><td colspan="8" class="empty">${ICON.search.replace('class="i"', 'class="i"')}<strong>${searchId ? "Nenhum resultado" : "Comece uma busca"}</strong><span class="muted">${searchId ? "Tente menos palavras, sem ano ou qualidade, ou marque mais sites." : "Digite o nome e aperte Enter. Atalho: /"}</span></td></tr>`;
    return;
  }
  $("#rows").innerHTML = shown.map((r) => {
    const k = keyOf(r), link = safeUrl(r.link);
    const trust = r.trust ? `<span class="badge b-${esc(r.trust)}">${esc(r.trust.toUpperCase())}</span>` : "";
    const srcs = r.sources.map((s) => `<span class="badge badge-secondary">${esc(s)}</span>`).join("");
    let act;
    if (!link) act = `<span class="muted">link inválido</span>`;
    else if (link.startsWith("magnet:")) act = `<a class="btn btn-primary btn-xs" href="${esc(link)}">${ICON.magnet}Magnet</a><button class="btn btn-ghost btn-icon btn-xs" data-copy="${esc(k)}" title="Copiar magnet" aria-label="Copiar magnet">${ICON.copy}</button>`;
    else if (link.endsWith(".torrent")) act = `<a class="btn btn-outline btn-xs" href="${esc(link)}">${ICON.file}.torrent</a>`;
    else act = `<button class="btn btn-primary btn-xs" data-resolve="${esc(k)}">${ICON.magnet}Magnet</button><a class="btn btn-ghost btn-icon btn-xs" href="${esc(link)}" target="_blank" rel="noopener noreferrer" title="Abrir página" aria-label="Abrir página">${ICON.ext}</a>`;
    return `<tr>
      <td><div class="score-cell"><span class="score-bar"><i style="--w:${Math.round(100 * r.score / top)}%"></i></span><span class="score-val">${r.score}</span></div></td>
      <td class="name"><div class="name-main">${esc(r.name)}</div><div class="name-sub">${trust}${srcs}</div></td>
      <td class="num">${human(r.size)}</td>
      <td class="num${r.seeds === 0 ? " dead" : ""}">${r.seeds < 0 ? "—" : fmt(r.seeds)}</td>
      <td class="num c-leech">${r.leech < 0 ? "—" : fmt(r.leech)}</td>
      <td class="num c-dl">${r.downloads == null ? "—" : fmt(r.downloads)}</td>
      <td class="num c-src">${r.sources.length}</td>
      <td><div class="actions">${act}</div></td></tr>`;
  }).join("");
}

document.addEventListener("click", async (ev) => {
  const t = ev.target.closest("button, th");
  if (!t) return;
  if (t.dataset.copy) {
    const r = results.get(t.dataset.copy);
    try { await navigator.clipboard.writeText(r.link); t.innerHTML = ICON.check; setTimeout(() => { t.innerHTML = ICON.copy; }, 1200); } catch { t.title = "falhou"; }
  }
  if (t.dataset.resolve) {
    const r = results.get(t.dataset.resolve); t.textContent = "…";
    const d = await (await fetch(`/api/magnet?engine=${encodeURIComponent(r.engine)}&link=${encodeURIComponent(r.link)}`)).json();
    if (d.magnet && safeUrl(d.magnet).startsWith("magnet:")) { r.link = d.magnet; renderTable(); location.href = d.magnet; }
    else { t.textContent = "erro"; t.title = d.error || ""; }
  }
  if (t.tagName === "TH" && t.dataset.k) sortBy(t);
});
function sortBy(th) {
  sortDir = sortKey === th.dataset.k ? -sortDir : (th.dataset.k === "name" ? 1 : -1);
  sortKey = th.dataset.k;
  document.querySelectorAll("th[data-k]").forEach((h) => h.setAttribute("aria-sort", h === th ? (sortDir < 0 ? "descending" : "ascending") : "none"));
  renderTable();
}
document.addEventListener("keydown", (ev) => {
  if (ev.key === "/" && !["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName)) { ev.preventDefault(); $("#q").focus(); $("#q").select(); }
  if ((ev.key === "Enter" || ev.key === " ") && ev.target.tagName === "TH" && ev.target.dataset.k) { ev.preventDefault(); sortBy(ev.target); }
});
["#filter", "#minseeds", "#trustonly"].forEach((s) => $(s).addEventListener("input", renderTable));
$("#f").addEventListener("submit", search);
init();
