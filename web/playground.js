'use strict';
/* UI/UX Playground — real Atlas components against the real local API.
   app.js cannot be imported (it binds to the app page's DOM on load), so the
   wiring here mirrors the app's semantics against the same endpoints and CSS
   classes. All dynamic text is set via textContent (web/AGENTS.md). */
const $ = id => document.getElementById(id);
function el(tag, text, cls) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; }
function button(text, fn) { const b = el('button', text); b.type = 'button'; b.addEventListener('click', fn); return b; }
async function api(path, params = {}) { const r = await fetch('/api/v1/' + path + '?' + new URLSearchParams(params)); const data = await r.json(); if (!r.ok) throw Error(data.error || `HTTP ${r.status}`); return data; }
function clock(s) { if (s === null || s === undefined) return '—'; s = ((s % 86400) + 86400) % 86400; let h = Math.floor(s / 3600); const m = Math.floor((s % 3600) / 60), ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return `${h}:${String(m).padStart(2, '0')} ${ap}`; }
function seconds(text) { const m = /^(\d{1,2}):(\d{2})\s*(AM|PM)?$/i.exec(text.trim()); if (!m) throw Error(`Time "${text}" should look like 8:00 AM.`); let h = Number(m[1]) % 12; if (/pm/i.test(m[3] || '')) h += 12; return h * 3600 + Number(m[2]) * 60; }
function run(fn) { Promise.resolve().then(fn).catch(e => { const n = el('p', e.message, 'notice'); $('pgPlanResults').replaceChildren(n); }); }
function routeColor(route) { let h = 0; const key = (route && (route.id || route)) || ''; for (const c of String(key)) h = (h * 31 + c.charCodeAt(0)) % 360; return `hsl(${h} 55% 38%)`; }

let meta = null, stops = new Map(), labels = new Map(), pgScope = '', map = null, drawLayer = null, bubbleLayer = null;
const mapHost = el('div'); mapHost.className = 'pgMapHost';
const mapEl = el('div'); mapEl.id = 'pgMap'; mapHost.append(mapEl);

function stopLabel(s) { return s.town ? `${s.name} · ${s.town}` : s.name; }
function resolveStop(id) { const input = $(id), value = input.value; const sid = input.dataset.stopId || labels.get(value) || (stops.has(value) ? value : null); if (!sid) throw Error('Choose a stop from the suggestions.'); return sid; }

/* ---- Section 1: the selector in both forms ------------------------------- */
function cityButtons(host, onPick) {
  meta.cities.forEach(([name, lat, lon]) => {
    const b = button(name, () => { onPick(name); map.setView([lat, lon], 13); $('pgCityStatus').textContent = `${name} · zoomed stops from loaded feeds`; });
    b.dataset.city = name; b.setAttribute('aria-pressed', 'false');
    host.append(b);
  });
}
function markCity(host, name) { host.querySelectorAll('button').forEach(b => { const on = b.dataset.city === name; b.setAttribute('aria-pressed', on ? 'true' : 'false'); b.classList.toggle('selected', on); }); }
function setScope(feed, source) {
  pgScope = feed;
  document.querySelectorAll('#pgAgencyList button').forEach(b => { const on = b.dataset.feed === feed; b.setAttribute('aria-pressed', on ? 'true' : 'false'); b.classList.toggle('selected', on); });
  const sel = $('pgScopeSelect'); if (sel && source !== 'select') sel.value = feed;
  renderRouteList();
}
function buildSidebarMount() {
  const wrap = el('div'); wrap.className = 'pgSideDemo';
  const nav = el('nav'); nav.id = 'citySidebar'; nav.setAttribute('aria-label', 'Cities and network scope');
  nav.append(el('div', 'CITIES', 'sideHead'));
  const cities = el('div'); cities.className = 'cities'; cities.id = 'pgCitiesSide';
  cityButtons(cities, name => markCity(cities, name));
  nav.append(cities);
  nav.append(el('div', 'NETWORK SCOPE', 'sideHead'));
  const list = el('div'); list.className = 'agencyList'; list.id = 'pgAgencyList';
  ['', ...new Set(meta.routes.map(r => r.feed))].forEach(f => { const b = button(f || 'All loaded networks', () => setScope(f, 'list')); b.dataset.feed = f; b.setAttribute('aria-pressed', f === '' ? 'true' : 'false'); if (f === '') b.classList.add('selected'); list.append(b); });
  nav.append(list);
  nav.append(el('p', 'Sidebar form: the shipped Job 5 layout, same CSS.', 'small sideNote'));
  wrap.append(nav, mapHost);
  return wrap;
}
function buildStripMount() {
  const wrap = el('div'); wrap.className = 'pgStripDemo';
  const rel = el('div'); rel.className = 'pgStripWrap';
  const cities = el('div'); cities.className = 'cities'; cities.id = 'pgCitiesStrip';
  cityButtons(cities, name => markCity(cities, name));
  rel.append(mapHost, cities);
  const row = el('div'); row.className = 'pgScopeRow';
  row.append(el('label', 'NETWORK')); row.querySelector('label').htmlFor = 'pgScopeSelect';
  const sel = el('select'); sel.id = 'pgScopeSelect'; sel.append(new Option('All loaded networks', ''));
  [...new Set(meta.routes.map(r => r.feed))].forEach(f => sel.append(new Option(f, f)));
  sel.value = pgScope; sel.addEventListener('change', () => setScope(sel.value, 'select'));
  row.append(sel, el('span', 'Previous form: floating strip over the map + a Network select, as the app was before Job 5.', 'small'));
  wrap.append(rel, row);
  return wrap;
}
let currentForm = 'sidebar';
function showForm(form) {
  currentForm = form;
  $('formSidebar').setAttribute('aria-pressed', form === 'sidebar' ? 'true' : 'false');
  $('formStrip').setAttribute('aria-pressed', form === 'strip' ? 'true' : 'false');
  $('pgSelectorMount').replaceChildren(form === 'sidebar' ? buildSidebarMount() : buildStripMount());
  setScope(pgScope, 'rebuild');
  setTimeout(() => map && map.invalidateSize(), 60);
}

/* ---- Section 2: plan ------------------------------------------------------ */
function renderItinerary(result, title) {
  const card = el('section', undefined, 'resultCard'); card.append(el('h3', title));
  if (!result.found) { card.append(el('p', result.message || 'No itinerary found in the loaded schedules.')); return card; }
  card.append(el('p', `${clock(result.departure)} → ${clock(result.arrival)}`));
  for (const leg of result.legs) {
    const a = stops.get(leg.from_stop), b = stops.get(leg.to_stop), row = el('div', undefined, 'leg');
    row.append(el('b', leg.kind === 'transit' ? `${leg.route} · ${leg.headsign || ''}` : `${leg.kind} · estimated`),
      el('p', `${a ? a.name : leg.from_stop} → ${b ? b.name : leg.to_stop}`),
      el('p', `${clock(leg.departure)} → ${clock(leg.arrival)}`));
    card.append(row);
  }
  return card;
}
async function doPlan() {
  const params = { from: resolveStop('pgFrom'), to: resolveStop('pgTo'), date: $('pgDate').value, time: seconds($('pgTime').value), mode: 'walk', radius: 500, buffer: 300, kind: 'depart' };
  $('pgPlanResults').replaceChildren(el('p', 'Searching the published schedules…'));
  const data = await api('plan', params);
  $('pgPlanResults').replaceChildren(renderItinerary(data, 'Outbound journey'));
  bubbleLayer.clearLayers();
  for (const leg of data.legs || []) { const a = stops.get(leg.from_stop), b = stops.get(leg.to_stop); if (a) L.circleMarker([a.lat, a.lon], { radius: 6, color: '#143e39' }).addTo(bubbleLayer); if (b) L.circleMarker([b.lat, b.lon], { radius: 6, color: '#143e39' }).addTo(bubbleLayer); }
}

/* ---- Section 3: bubble ---------------------------------------------------- */
async function doBubble() {
  const params = { from: resolveStop('pgBubbleFrom'), date: $('pgDate').value, time: seconds($('pgTime').value), budget: Number($('pgBudget').value), visit: 0, mode: 'walk', radius: 500, buffer: 300 };
  $('pgBubbleResults').replaceChildren(el('p', 'Computing the bubble…'));
  const data = await api('bubble', params);
  bubbleLayer.clearLayers();
  data.reachable.forEach(s => { const stop = stops.get(s.id); if (stop) L.circleMarker([stop.lat, stop.lon], { radius: 4, color: '#26776b', fillColor: '#dce69a', fillOpacity: .9 }).addTo(bubbleLayer); });
  const card = el('section', undefined, 'resultCard');
  card.append(el('h3', `${data.reachable.length} stops in the bubble`), el('p', `${data.unreachable_count} loaded stops were evaluated as not reachable in the window. First stops: ${data.reachable.slice(0, 10).map(s => (stops.get(s.id) || {}).name || s.id).join(', ')}`, 'small'));
  $('pgBubbleResults').replaceChildren(card);
  if (data.reachable.length) { const first = stops.get(data.reachable[0].id); if (first) map.setView([first.lat, first.lon], 11); }
}

/* ---- Section 4: routes in scope + draw ------------------------------------ */
function renderRouteList() {
  const list = $('pgRouteList'); list.replaceChildren();
  const scoped = meta.routes.filter(r => !pgScope || r.feed === pgScope);
  $('pgRouteStatus').textContent = `${scoped.length} routes in scope ${pgScope ? `(${pgScope})` : '(all networks)'}.`;
  scoped.slice(0, 120).forEach(r => { const row = el('div', `${r.short || r.id} · ${r.name} (${r.feed})`); row.className = 'pgRouteRow'; list.append(row); });
  if (scoped.length > 120) list.append(el('p', `…and ${scoped.length - 120} more (list capped for the playground).`, 'small'));
}
async function drawScoped() {
  const scoped = meta.routes.filter(r => !pgScope || r.feed === pgScope);
  const queue = scoped.slice(0, 90);
  drawLayer.clearLayers();
  let drawn = 0, empty = 0, next = 0;
  $('pgRouteStatus').textContent = `Drawing ${queue.length} routes…`;
  async function worker() {
    while (next < queue.length) {
      const r = queue[next++];
      try {
        const data = await api('route', { id: r.id, date: $('pgDate').value });
        let any = false;
        for (const shape of data.shapes) if (shape.length) { L.polyline(shape, { color: routeColor(r), weight: 4, opacity: .85 }).addTo(drawLayer); any = true; }
        if (any) drawn++; else empty++;
      } catch { empty++; }
      $('pgRouteStatus').textContent = `Drawing… ${drawn + empty}/${queue.length} routes (${drawn} with geometry)`;
    }
  }
  await Promise.all(Array.from({ length: 6 }, worker));
  $('pgRouteStatus').textContent = `Drawn: ${drawn} routes with published geometry · ${empty} without geometry for ${$('pgDate').value} (a data gap, labelled as such — not hidden).`;
}

/* ---- Switches -------------------------------------------------------------- */
function wireSwitches() {
  $('formSidebar').addEventListener('click', () => showForm('sidebar'));
  $('formStrip').addEventListener('click', () => showForm('strip'));
  document.querySelectorAll('[data-theme-set]').forEach(b => b.addEventListener('click', () => {
    document.documentElement.dataset.theme = b.dataset.themeSet;
    document.querySelectorAll('[data-theme-set]').forEach(x => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
  }));
  const stage = $('pgStage');
  const presets = { desktop: { width: '100%', zoom: '' }, tablet: { width: '768px', zoom: '' }, phone: { width: '400px', zoom: '' }, zoom67: { width: '100%', zoom: '0.67' } };
  document.querySelectorAll('[data-preset]').forEach(b => b.addEventListener('click', () => {
    const p = presets[b.dataset.preset];
    stage.style.width = p.width; stage.style.zoom = p.zoom;
    document.querySelectorAll('[data-preset]').forEach(x => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
    setTimeout(() => map && map.invalidateSize(), 80);
  }));
  $('pgPlan').addEventListener('click', () => run(doPlan));
  $('pgBubble').addEventListener('click', () => run(doBubble));
  $('pgDraw').addEventListener('click', () => run(drawScoped));
  $('pgClearDraw').addEventListener('click', () => { drawLayer.clearLayers(); $('pgRouteStatus').textContent = 'Drawing cleared.'; });
  ['pgFrom', 'pgTo', 'pgBubbleFrom'].forEach(id => $(id).addEventListener('input', () => {
    const input = $(id), sid = labels.get(input.value); if (sid) input.dataset.stopId = sid; else delete input.dataset.stopId;
  }));
}

/* ---- Init ------------------------------------------------------------------- */
async function init() {
  meta = await api('meta');
  stops = new Map(meta.stops.map(s => [s.id, s]));
  const dl = $('pgStopList');
  meta.stops.forEach(s => { const label = stopLabel(s); labels.set(label, s.id); const o = new Option(label, label); dl.append(o); });
  map = L.map(mapEl).setView([42, -72.4], 8);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap contributors' }).addTo(map);
  drawLayer = L.layerGroup().addTo(map); bubbleLayer = L.layerGroup().addTo(map);
  wireSwitches();
  showForm('sidebar');
  $('pgCityStatus').textContent = `${meta.cities.length} cities · ${meta.routes.length} routes · ${meta.stops.length.toLocaleString()} stops loaded from the live API.`;
  renderRouteList();
}
run(init);
