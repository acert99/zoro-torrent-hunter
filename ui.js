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
/* language: ui.html ships in Portuguese; its data-i18n / data-i18n-<attr> attributes name the keys below */
const STR = {
  pt: {
    locale: "pt-BR", other: "en", otherName: "English", otherLabel: "Switch to English",
    title: "Zoro - O caçador de Torrents", tagline: "O caçador de Torrents", theme: "Tema", themeLabel: "Alternar tema claro/escuro",
    logoAlt: "Logo do Zoro: três katanas", heading: "Buscar torrents",
    intro: "Consulta todos os sites marcados ao mesmo tempo, junta duplicados e ranqueia por seeds, downloads e confiança do uploader.",
    queryHint: "Nome, ano, qualidade… ex.: sintel 2010 1080p", queryLabel: "Termo de busca", category: "Categoria", search: "Buscar",
    summary: "Resumo", results: "Resultados", merged: "duplicados juntados", sites: "Sites", topSeeds: "Mais seeds", time: "Tempo",
    untilLast: "até o último site", sitesQueried: "Sites consultados", perSite: "Resultados por site nesta busca",
    all: "Todos", default: "Padrão", none: "Nenhum", filterHint: "Filtrar pelo nome…", filterLabel: "Filtrar pelo nome",
    minSeeds: "Seeds mínimos", trustedOnly: "Só confiáveis", name: "Nome", size: "Tamanho", sources: "Fontes", download: "Baixar",
    howto: "Como o score é calculado",
    howtoText: "(seeds + 0,25×leech + 10×log10(1+downloads)) × confiança: VIP ×2, TRUSTED ×1,5, LICENSED ×1,3, REMAKE ×0,3. Seeds vêm dos sites e podem estar desatualizados; 0 aparece em vermelho e \"—\" quando o site não informa.",
    cats: { all: "Tudo", movies: "Filmes", tv: "Séries", music: "Música", games: "Jogos", anime: "Anime", software: "Software", books: "Livros" },
    error: "erro", siteFailed: "site falhou ou fora do ar", connFailed: "falha de conexão", searching: "buscando…",
    someFailed: (ok, errs) => `${ok} ok · ${errs} com erro`, allAnswered: "todos responderam", answered: "responderam",
    noSearch: "nenhuma busca ainda", busy: (d, n) => `Buscando ${d}/${n}`, ready: "Pronto",
    of: (a, b) => `${a} de ${b}`, showing: (a, b) => `Mostrando ${a} de ${b}`,
    noResults: "Nenhum resultado", noResultsHint: "Tente menos palavras, sem ano ou qualidade, ou marque mais sites.",
    start: "Comece uma busca", startHint: "Digite o nome e aperte Enter. Atalho: /",
    badLink: "link inválido", copy: "Copiar magnet", openPage: "Abrir página", failed: "falhou", magnetFailed: "não foi possível obter o magnet",
  },
  en: {
    locale: "en-US", other: "pt", otherName: "Português", otherLabel: "Mudar para português",
    title: "Zoro - The Torrent Hunter", tagline: "The Torrent Hunter", theme: "Theme", themeLabel: "Toggle light/dark theme",
    logoAlt: "Zoro logo: three katanas", heading: "Search torrents",
    intro: "Queries every checked site at once, merges duplicates and ranks by seeds, downloads and uploader trust.",
    queryHint: "Name, year, quality… e.g. sintel 2010 1080p", queryLabel: "Search term", category: "Category", search: "Search",
    summary: "Summary", results: "Results", merged: "duplicates merged", sites: "Sites", topSeeds: "Most seeds", time: "Time",
    untilLast: "until the last site", sitesQueried: "Sites queried", perSite: "Results per site in this search",
    all: "All", default: "Default", none: "None", filterHint: "Filter by name…", filterLabel: "Filter by name",
    minSeeds: "Minimum seeds", trustedOnly: "Trusted only", name: "Name", size: "Size", sources: "Sources", download: "Download",
    howto: "How the score is calculated",
    howtoText: "(seeds + 0.25×leech + 10×log10(1+downloads)) × trust: VIP ×2, TRUSTED ×1.5, LICENSED ×1.3, REMAKE ×0.3. Seeds come from the sites and may be outdated; 0 is shown in red and \"—\" when the site doesn't report it.",
    cats: { all: "All", movies: "Movies", tv: "TV", music: "Music", games: "Games", anime: "Anime", software: "Software", books: "Books" },
    error: "error", siteFailed: "site failed or is down", connFailed: "connection failed", searching: "searching…",
    someFailed: (ok, errs) => `${ok} ok · ${errs} failed`, allAnswered: "all responded", answered: "responded",
    noSearch: "no search yet", busy: (d, n) => `Searching ${d}/${n}`, ready: "Ready",
    of: (a, b) => `${a} of ${b}`, showing: (a, b) => `Showing ${a} of ${b}`,
    noResults: "No results", noResultsHint: "Try fewer words, no year or quality, or check more sites.",
    start: "Start a search", startHint: "Type a name and press Enter. Shortcut: /",
    badLink: "invalid link", copy: "Copy magnet", openPage: "Open page", failed: "failed", magnetFailed: "couldn't get the magnet",
  },
};
let lang = "pt";
const tr = (k, ...a) => { const v = STR[lang][k]; return typeof v === "function" ? v(...a) : v; };

let meta = { engines: [], default: [], cats: [] };
let enabled = new Set(), engineState = {}, results = new Map();
let sortKey = "score", sortDir = -1, searchId = 0, progress = { done: 0, total: 0 }, started = 0, elapsed = 0, ctrl = null;

function human(n) {
  if (n == null || n < 0) return "—";
  const u = ["B", "KB", "MB", "GB", "TB"]; let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return n.toFixed(1) + " " + u[i];
}
const fmt = (n) => n.toLocaleString(tr("locale"));
// The server sends each magnet's infohash as lowercase hex (base32 already converted), so one torrent = one key.
const keyOf = (r) => r.infohash || r.link;

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
  renderCats();
  const saved = store.get("engines", null);
  enabled = new Set(saved ? saved.filter((e) => meta.engines.includes(e)) : meta.engines);
  renderSites(); renderStats(); renderTable();
}
function renderCats() {
  const cur = $("#cat").value;
  $("#cat").innerHTML = meta.cats.map((c) => `<option value="${esc(c)}">${esc(tr("cats")[c] || c)}</option>`).join("");
  if (cur) $("#cat").value = cur;
}

function applyLang(l) {
  lang = STR[l] ? l : "pt";
  document.documentElement.lang = tr("locale");
  document.title = tr("title");
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = tr(el.dataset.i18n); });
  for (const a of ["placeholder", "aria-label", "title", "alt"]) {
    document.querySelectorAll(`[data-i18n-${a}]`).forEach((el) => el.setAttribute(a, tr(el.getAttribute(`data-i18n-${a}`))));
  }
  const b = $("#lang"); b.textContent = tr("other").toUpperCase(); b.lang = tr("other");
  b.title = tr("otherName"); b.setAttribute("aria-label", tr("otherLabel"));
  renderCats(); render();
}
$("#lang").onclick = () => { const l = tr("other"); store.set("lang", l); applyLang(l); };
function saveEnabled() { store.set("engines", [...enabled]); }

function renderSites() {
  const max = Math.max(1, ...Object.values(engineState).map((s) => s.n || 0));
  $("#engines").innerHTML = meta.engines.map((e) => {
    const s = engineState[e] || {}, on = enabled.has(e);
    const metaTxt = s.state === "run" ? "…" : s.state ? `${s.state === "err" ? tr("error") : fmt(s.n)} · ${(s.ms / 1000).toFixed(0)}s` : "";
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

// 503 means the server is still busy with engines from an earlier search: wait and try again.
async function getJSON(url, signal) {
  for (let i = 1; ; i++) {
    const res = await fetch(url, { signal });
    if (res.status !== 503 || i === 4) return res.json();
    await new Promise((ok) => setTimeout(ok, 1000 * i));
  }
}

async function search(ev) {
  ev.preventDefault();
  const q = $("#q").value.trim(); if (!q) { $("#q").focus(); return; }
  const id = ++searchId; results = new Map(); engineState = {};
  // Drop the previous search's requests: the browser allows ~6 connections per host, so queued
  // ones would otherwise run before this search's.
  ctrl?.abort(); ctrl = new AbortController(); const { signal } = ctrl;
  const active = meta.engines.filter((e) => enabled.has(e));
  active.forEach((e) => { engineState[e] = { state: "run" }; });
  progress = { done: 0, total: active.length }; started = performance.now(); elapsed = 0;
  render();
  await Promise.all(active.map(async (e) => {
    try {
      const url = `/api/search?engine=${encodeURIComponent(e)}&q=${encodeURIComponent(q)}&cat=${encodeURIComponent($("#cat").value)}`;
      const d = await getJSON(url, signal);
      if (id !== searchId) return;
      (d.rows || []).forEach(add);
      engineState[e] = { state: d.error ? "err" : "ok", n: (d.rows || []).length, ms: d.ms, err: d.error ? tr("siteFailed") : "" };
    } catch (err) {
      if (id === searchId) engineState[e] = { state: "err", n: 0, ms: performance.now() - started, err: tr("connFailed") };
    }
    if (id === searchId) { progress.done++; elapsed = performance.now() - started; render(); }
  }));
}

function add(r) {
  const k = keyOf(r), cur = results.get(k);
  if (!cur) { results.set(k, { ...r, key: k, sources: [r.engine] }); return; }
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
  $("#st-sites-sub").textContent = busy ? tr("searching") : errs ? tr("someFailed", ok, errs) : progress.total ? tr("allAnswered") : tr("answered");
  let top = null; results.forEach((r) => { if (!top || r.seeds > top.seeds) top = r; });
  $("#st-seeds").textContent = top && top.seeds >= 0 ? fmt(top.seeds) : "—";
  $("#st-seeds-sub").textContent = top ? top.name : tr("noSearch");
  $("#st-time").textContent = progress.total ? `${(elapsed / 1000).toFixed(1)}s` : "—";
  $("#live-dot").className = "dot " + (busy ? "run" : "ok");
  $("#live-text").textContent = busy ? tr("busy", progress.done, progress.total) : tr("ready");
}

function renderTable() {
  const f = $("#filter").value.toLowerCase(), min = +$("#minseeds").value || 0, trustOnly = $("#trustonly").checked;
  const busy = progress.done < progress.total;
  let list = [...results.values()].filter((r) => r.name.toLowerCase().includes(f) && (min === 0 || r.seeds >= min) && (!trustOnly || (r.trust && r.trust !== "remake")));
  const val = (r) => sortKey === "sources" ? r.sources.length : (r[sortKey] ?? -1);
  list.sort((a, b) => sortDir * (sortKey === "name" ? b.name.localeCompare(a.name) : (val(b) > val(a) ? -1 : val(b) < val(a) ? 1 : 0)));
  const shown = list.slice(0, 500);
  $("#status").textContent = results.size ? tr("of", fmt(list.length), fmt(results.size)) : "";
  $("#foot-count").textContent = results.size ? tr("showing", fmt(shown.length), fmt(list.length)) : "";
  const top = Math.max(1, ...list.map((r) => r.score));
  if (!shown.length) {
    $("#rows").innerHTML = busy
      ? Array.from({ length: 6 }, () => `<tr><td><div class="skel" style="width:90px"></div></td><td><div class="skel" style="width:${40 + Math.random() * 45}%"></div></td><td class="num"><div class="skel" style="width:60px;margin-left:auto"></div></td><td class="num"><div class="skel" style="width:36px;margin-left:auto"></div></td><td class="num c-leech"><div class="skel" style="width:30px;margin-left:auto"></div></td><td class="num c-dl"><div class="skel" style="width:50px;margin-left:auto"></div></td><td class="num c-src"><div class="skel" style="width:16px;margin-left:auto"></div></td><td><div class="skel" style="width:80px;margin-left:auto"></div></td></tr>`).join("")
      : `<tr><td colspan="8" class="empty">${ICON.search.replace('class="i"', 'class="i"')}<strong>${tr(searchId ? "noResults" : "start")}</strong><span class="muted">${tr(searchId ? "noResultsHint" : "startHint")}</span></td></tr>`;
    return;
  }
  $("#rows").innerHTML = shown.map((r) => {
    const k = r.key, link = safeUrl(r.link);  // not keyOf(r): resolving a page link changes r.link
    const trust = r.trust ? `<span class="badge b-${esc(r.trust)}">${esc(r.trust.toUpperCase())}</span>` : "";
    const srcs = r.sources.map((s) => `<span class="badge badge-secondary">${esc(s)}</span>`).join("");
    let act;
    if (!link) act = `<span class="muted">${tr("badLink")}</span>`;
    else if (link.startsWith("magnet:")) act = `<a class="btn btn-primary btn-xs" href="${esc(link)}">${ICON.magnet}Magnet</a><button class="btn btn-ghost btn-icon btn-xs" data-copy="${esc(k)}" title="${tr("copy")}" aria-label="${tr("copy")}">${ICON.copy}</button>`;
    else if (r.torrent) act = `<a class="btn btn-outline btn-xs" href="${esc(link)}">${ICON.file}.torrent</a>`;
    else act = `<button class="btn btn-primary btn-xs" data-resolve="${esc(k)}">${ICON.magnet}Magnet</button><a class="btn btn-ghost btn-icon btn-xs" href="${esc(link)}" target="_blank" rel="noopener noreferrer" title="${tr("openPage")}" aria-label="${tr("openPage")}">${ICON.ext}</a>`;
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
    try { await navigator.clipboard.writeText(r.link); t.innerHTML = ICON.check; setTimeout(() => { t.innerHTML = ICON.copy; }, 1200); } catch { t.title = tr("failed"); }
  }
  if (t.dataset.resolve) {
    const r = results.get(t.dataset.resolve); t.textContent = "…";
    const d = await (await fetch(`/api/magnet?engine=${encodeURIComponent(r.engine)}&link=${encodeURIComponent(r.link)}`)).json();
    if (d.magnet && safeUrl(d.magnet).startsWith("magnet:")) { r.link = d.magnet; renderTable(); location.href = d.magnet; }
    else { t.textContent = tr("error"); t.title = tr("magnetFailed"); }
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
applyLang(store.get("lang", null) || (navigator.language.toLowerCase().startsWith("pt") ? "pt" : "en"));
init();
