/* Desktop atlas controller. All feed/user text is rendered as text, never HTML. */
const $ = id => document.getElementById(id);
const el = (tag, text, cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
const button = (text, fn) => { const n = el('button', text); n.addEventListener('click', () => run(fn)); return n; };
const clock = seconds => `${Math.floor(seconds / 3600) % 24}`.padStart(2, '0') + ':' + `${Math.floor(seconds / 60) % 60}`.padStart(2, '0') + (seconds >= 86400 ? ` (+${Math.floor(seconds / 86400)} day)` : '');
const seconds = value => { const [h,m] = value.split(':').map(Number); if (!Number.isFinite(h+m)) throw Error('Choose a valid time.'); return h*3600+m*60; };
let meta, map, layers, nearby, stops = new Map(), routes = new Map(), labels = new Map(), request = 0, selectedRoute = null;
const storageKey = 'transit-atlas-v1';
const preferenceKey = 'transit-atlas-preferences-v1';
let preferences = {theme:'system',units:'imperial'};
try { const p=JSON.parse(localStorage.getItem(preferenceKey)); if(['system','light','dark'].includes(p?.theme))preferences.theme=p.theme; if(['imperial','metric'].includes(p?.units))preferences.units=p.units; } catch {}
const feetPerMeter=3.280839895;
const distanceText = meters => preferences.units==='imperial'
 ? (meters*feetPerMeter < 528 ? `${Math.round(meters*feetPerMeter)} ft` : `${(meters/1609.344).toFixed(2)} mi`)
 : (meters < 1000 ? `${Math.round(meters)} m` : `${(meters/1000).toFixed(2)} km`);
function updatePreferences(){
 document.documentElement.dataset.theme=preferences.theme;
 $('theme').value=preferences.theme; $('units').value=preferences.units;
 $('radiusLabel').textContent=preferences.units==='imperial'?'MAX LINK (FEET)':'MAX LINK (METERS)';
 $('mode').options[0].textContent=preferences.units==='imperial'?'Walking · estimated 2.8 mph':'Walking · estimated 4.5 km/h';
 $('mode').options[1].textContent=preferences.units==='imperial'?'Scooter · estimated 7.5 mph':'Scooter · estimated 12 km/h';
 $('radius').max=preferences.units==='imperial'?'9843':'3000';
}
function savePreferences(){localStorage.setItem(preferenceKey,JSON.stringify(preferences));updatePreferences();}

let personal = {version:1, bookmarks:[], notes:[]};
try { const saved = JSON.parse(localStorage.getItem(storageKey)); if (saved) personal = validatePersonal(saved); } catch { /* Preserve unreadable storage until an explicit save. */ }
function validatePersonal(value) {
 if (value?.version !== 1 || !Array.isArray(value.bookmarks) || !Array.isArray(value.notes)) throw Error('Not an atlas backup.');
 if (value.bookmarks.length > 1000 || value.notes.length > 1000) throw Error('Backup exceeds 1,000 entries per section.');
 for (const b of value.bookmarks) if (typeof b.from !== 'string' || typeof b.to !== 'string' || typeof b.date !== 'string' || typeof b.time !== 'string') throw Error('Invalid saved search.');
 for (const n of value.notes) if (typeof n.title !== 'string' || typeof n.text !== 'string') throw Error('Invalid journal entry.');
 return value;
}
function save() { localStorage.setItem(storageKey, JSON.stringify(personal)); renderPersonal(); }
async function api(path, params={}) { const r = await fetch('/api/v1/'+path+'?'+new URLSearchParams(params)); const data = await r.json(); if (!r.ok) throw Error(data.error || `HTTP ${r.status}`); return data; }
async function run(fn) { try { $('errorNotice').hidden = true; await fn(); } catch (e) { $('errorNotice').textContent = e.message; $('errorNotice').hidden = false; $('loading').hidden = true; } }
function view(name) { document.querySelectorAll('.view').forEach(n => n.hidden = n.id !== name); document.querySelectorAll('nav [data-tab]').forEach(n => n.classList.toggle('selected', n.dataset.tab === name)); if(name === 'explore') setTimeout(() => map?.invalidateSize(), 0); }
function stopLabel(s) { return `${s.name} [${s.id}]`; }
function resolve(id) { const value = $(id).value; const sid = labels.get(value) || (stops.has(value) ? value : null); if (!sid) throw Error(`Choose a ${id === 'from' ? 'departure' : 'destination'} stop from the suggestions or map.`); return sid; }
function sourceLink(feed) { const source = meta.sources.find(s => s.id === feed); const n = el('a', `Source: ${feed}`); if(source && /^https?:\/\//.test(source.url)) { n.href = source.url; n.target = '_blank'; n.rel = 'noopener'; } return n; }
function marker(s, group=layers, color='#26776b') {
 const popup = el('div'); popup.append(el('b', s.name), el('p', s.id));
 popup.append(button('Start here', () => { $('from').value=stopLabel(s); map.closePopup(); }), button('Go here', () => { $('to').value=stopLabel(s); map.closePopup(); }), button('Departures', () => departures(s)));
 return L.circleMarker([s.lat,s.lon], {radius:5,color,weight:2,fillOpacity:.8}).bindPopup(popup).addTo(group);
}
function fit() { if(layers.getLayers().length) { const b = layers.getBounds(); if(b.isValid()) map.fitBounds(b,{padding:[40,40],maxZoom:14}); } }
function nearbyStops() { nearby.clearLayers(); if(map.getZoom()<12) return; let n=0; for(const s of stops.values()) if(map.getBounds().contains([s.lat,s.lon]) && n++<600) marker(s, nearby, '#657b74'); }
function renderRoutes() { const search = $('routeSearch').value.toLowerCase(), feed=$('agency').value; $('routeList').replaceChildren(); for(const r of meta.routes) if((!feed||r.feed===feed) && `${r.short} ${r.name} ${r.feed}`.toLowerCase().includes(search)) { const b=button(`${r.short || r.id} · ${r.name} (${r.feed})`, () => showRoute(r.id)); b.className='routeButton'; $('routeList').append(b); } }
async function showRoute(id) {
 const token=++request; const r=routes.get(id); $('results').replaceChildren(el('p','Loading route…')); const data=await api('route',{id,date:$('date').value}); if(token!==request)return;
 selectedRoute=id; layers.clearLayers(); for(const shape of data.shapes) if(shape.length) L.polyline(shape,{color:'#26776b',weight:4}).addTo(layers); data.stops.forEach(s=>marker(s)); fit();
 const card=el('section',undefined,'resultCard'); card.append(el('h3',`${r.short} ${r.name}`),sourceLink(r.feed),el('p',`${data.trips.length} scheduled trips on ${$('date').value}. Stops show the published route footprint; not every trip serves every stop.`),el('p', data.geometry,'small'));
 for(const c of data.comparison) card.append(el('p',`${c.label} · ${c.date}: ${c.trips} trips`));
 if(!data.trips.length)card.append(el('p','No trips on this date in the loaded schedule. This may indicate expired or missing data.','notice'));
 const select=el('select'); select.setAttribute('aria-label','Scheduled trip'); select.append(new Option('Choose a trip timetable…','')); data.trips.forEach(t=>select.append(new Option(`${t.headsign || 'Trip'} · ${t.id}`,t.id))); select.onchange=()=>run(()=>tripTable(select.value,card)); card.append(select); $('results').replaceChildren(card); $('mapStatus').textContent=`${r.short} · ${r.feed} · ${$('date').value}`;
}
async function tripTable(id, parent) { if(!id)return; const rows=await api('trip',{id}); parent.querySelector('.tableWrap')?.remove(); const wrap=el('div',undefined,'tableWrap'),table=el('table'); const head=el('tr'); ['Stop','Arrival','Departure'].forEach(x=>head.append(el('th',x))); table.append(head); rows.forEach(s=>{const tr=el('tr');[s.name,clock(s.arr),clock(s.dep)].forEach(x=>tr.append(el('td',x)));table.append(tr);});wrap.append(table);parent.append(wrap); }
async function departures(s) { const data=await api('departures',{stop:s.id,date:$('date').value}); const card=el('section',undefined,'resultCard');card.append(el('h3',s.name),el('p',`Departures · ${$('date').value}`)); if(!data.departures.length)card.append(el('p','No departures in the loaded schedule for this date.','notice')); for(const d of data.departures) {const row=el('div',undefined,'leg'); row.append(button(`${clock(d.departure)} · ${routes.get(d.route)?.short || d.route} · ${d.headsign}`,()=>tripTable(d.trip,card)),sourceLink(d.source));card.append(row);} $('results').replaceChildren(card);map.closePopup(); }
function options() { const time=seconds($('time').value),deadline=seconds($('deadline').value); if(deadline<time)throw Error('Home-by must be after departure on the selected day.'); return {from:resolve('from'),date:$('date').value,time,deadline,mode:$('mode').value,radius:Math.round(Number($('radius').value)*(preferences.units==='imperial'?1/feetPerMeter:1)),buffer:Number($('buffer').value)*60}; }
function coverageNotice(coverage) { const missing=coverage.filter(s=>!s.in_service_period||s.status!=='imported').map(s=>s.feed); return el('p',`Experimental scheduled results, not guaranteed connections or seat availability. ${missing.length?'Missing/out-of-period feeds: '+missing.join(', ')+'. ':''}Other unlisted agencies are missing. Check operators before travel.`, 'notice'); }
function itinerary(result,title) {
 const card=el('section',undefined,'resultCard');card.append(el('h3',title)); if(!result.found){card.append(el('p',result.message||'No return found in the loaded schedules.'));return card;}
 card.append(el('p',`${clock(result.departure)} → ${clock(result.arrival)}`)); if(result.precision)card.append(el('p',result.precision,'small'));
 for(const leg of result.legs) { const a=stops.get(leg.from_stop),b=stops.get(leg.to_stop), row=el('div',undefined,'leg'); const transit=leg.kind==='transit'; row.append(el('b',transit?`${routes.get(leg.route)?.short || leg.route} · ${leg.headsign}`:`${leg.kind} · estimated ${distanceText(leg.meters)}`),el('p',`${a.name} → ${b.name}`),el('p',`${clock(leg.departure)} → ${clock(leg.arrival)}`)); if(transit)row.append(sourceLink(leg.source));card.append(row); marker(a);marker(b); if(!transit)L.polyline([[a.lat,a.lon],[b.lat,b.lon]],{color:'#b95d38',dashArray:'5 7'}).addTo(layers); }
 return card;
}
async function plan(kind='depart') {
 const params={...options(),to:resolve('to'),kind,return:$('return').checked?'1':'0',visit:Number($('visit').value)*60}; const token=++request; selectedRoute=null; $('results').replaceChildren(el('p','Searching the published schedules…')); const data=await api('plan',params); if(token!==request)return;layers.clearLayers();$('results').replaceChildren(coverageNotice(data.coverage),itinerary(data,'Outbound journey'));if(data.return)$('results').append(itinerary(data.return,'Return journey'));if(data.latest_return?.found)$('results').append(el('p',`Latest return start: ${clock(data.latest_return.latest_start_minute)} (one-minute precision)`,'notice'));fit();
}
async function bubble() {const params=options();delete params.deadline;params.budget=3600;params.visit=0;const token=++request;const data=await api('bubble',params);if(token!==request)return;layers.clearLayers();data.reachable.forEach(s=>marker(stops.get(s.id)));fit();const unknown=data.unknown.feeds.map(f=>f.feed).join(', ');$('results').replaceChildren(el('h3',`${data.reachable.length} stops in your 60-minute mobility bubble`),coverageNotice(data.coverage),el('p',`Every stop shown also has a feasible way home by ${clock(data.deadline)} with no visit time counted - pure travel, out and back inside the hour. ${data.unreachable_count} loaded stops were evaluated as not reachable in the window.${unknown?' Cannot be evaluated at all (missing data is not proof of no service): '+unknown+'.':''} Includes estimated ground links. Click a stop for departures.`));}
async function reach() {const params=options();params.deadline=Math.min(Number(params.deadline),params.time+7200);const token=++request;const data=await api('reachability',params);if(token!==request)return;layers.clearLayers();data.stops.forEach(s=>marker(stops.get(s.id)));fit();$('results').replaceChildren(el('h3',`${data.stops.length} stops reachable within two hours`),coverageNotice(data.coverage),el('p','Includes estimated ground links. Click a stop for departures.'));}
function renderSources() { $('sourceCards').replaceChildren(); for(const s of meta.sources){const card=el('article',undefined,'card'); card.append(el('h2',s.id),el('span',s.status,'badge'),sourceLink(s.id)); for(const [key,label] of [['retrieved_at','Retrieved'],['service_start','Service begins'],['service_end','Service ends'],['scope','Coverage'],['refresh_error','Refresh error']])card.append(el('p',`${label}: ${s[key] || 'Not recorded'}`));card.append(el('p',`Validation: ${JSON.stringify(s.validation || 'Not recorded')}`,'small'));$('sourceCards').append(card);} }
function renderPersonal() {
 $('journalCount').textContent=personal.notes.length; $('bookmarks').replaceChildren();$('notes').replaceChildren();
 personal.bookmarks.forEach((b,i)=>{const row=el('div',undefined,'note');row.append(button(`${b.from} → ${b.to}`,()=>{for(const key of ['from','to','date','time'])$(key).value=b[key];view('explore');updateDate();}),button('Delete',()=>{personal.bookmarks.splice(i,1);save();}));$('bookmarks').append(row);});
 personal.notes.forEach((n,i)=>{const row=el('article',undefined,'note');row.append(el('h3',n.title),el('p',n.text),button('Delete',()=>{personal.notes.splice(i,1);save();}));$('notes').append(row);});
}
function updateDate(){ const d=$('date').value; $('dayLabel').textContent=d?new Date(d+'T12:00:00').toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'}):'Choose a travel date'; }
async function init() {
 updatePreferences();
 $('theme').onchange=()=>{preferences.theme=$('theme').value;savePreferences();};
 $('units').onchange=()=>{const meters=Number($('radius').value)*(preferences.units==='imperial'?1/feetPerMeter:1);preferences.units=$('units').value;updatePreferences();$('radius').value=Math.round(meters*(preferences.units==='imperial'?feetPerMeter:1));savePreferences();};
 const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date()); $('date').value=['year','month','day'].map(k=>parts.find(p=>p.type===k).value).join('-');updateDate();
 meta=await api('meta');stops=new Map(meta.stops.map(s=>[s.id,s]));routes=new Map(meta.routes.map(r=>[r.id,r]));
 map=L.map('map',{preferCanvas:true}).setView([42,-72.4],8);layers=L.featureGroup().addTo(map);nearby=L.layerGroup().addTo(map);
 L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).on('tileerror',()=>$('tileNotice').hidden=false).addTo(map);map.on('moveend',nearbyStops);
 const fragment=document.createDocumentFragment(); for(const s of meta.stops){const label=stopLabel(s);labels.set(label,s.id);fragment.append(new Option(label,label));} $('stopList').append(fragment);
 meta.cities.forEach(([name,lat,lon])=>{ $('cities').append(button(name,()=>{map.setView([lat,lon],13);$('mapStatus').textContent=`${name} · zoomed stops from loaded feeds`; })); L.circleMarker([lat,lon],{radius:3,color:'#143e39'}).bindTooltip(name,{permanent:true,direction:'right',className:'cityMarker'}).addTo(map); });
 [...new Set(meta.routes.map(r=>r.feed))].forEach(f=>$('agency').append(new Option(f,f)));renderRoutes();renderSources();renderPersonal();$('counts').textContent=`${meta.routes.length} routes · ${meta.stops.length.toLocaleString()} published stops · incomplete coverage`;
 document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>view(b.dataset.tab));$('planTab').onclick=()=>{$('planner').hidden=false;$('browser').hidden=true;$('planTab').classList.add('selected');$('browseTab').classList.remove('selected');};$('browseTab').onclick=()=>{$('planner').hidden=true;$('browser').hidden=false;$('browseTab').classList.add('selected');$('planTab').classList.remove('selected');};
 $('routeSearch').oninput=renderRoutes;$('agency').onchange=renderRoutes;$('date').onchange=()=>{updateDate();if(selectedRoute)run(()=>showRoute(selectedRoute));};$('swap').onclick=()=>{const a=$('from').value;$('from').value=$('to').value;$('to').value=a;};$('resetMap').onclick=()=>map.setView([42,-72.4],8);
 $('plan').onclick=()=>run(()=>plan());$('latest').onclick=()=>run(()=>plan('latest'));$('reach').onclick=()=>run(reach);$('bubble').onclick=()=>run(bubble);
 $('bookmark').onclick=()=>run(()=>{resolve('from');resolve('to');personal.bookmarks.push(Object.fromEntries(['from','to','date','time'].map(k=>[k,$(k).value])));save();$('results').replaceChildren(el('p','Search saved in My discoveries.','notice'));});
 $('saveNote').onclick=()=>run(()=>{if(!$('noteTitle').value.trim())throw Error('Give your note a title.');personal.notes.push({title:$('noteTitle').value,text:$('noteText').value});save();$('noteTitle').value='';$('noteText').value='';});
 $('export').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(personal,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download='transit-atlas-discoveries.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 $('importFile').onchange=()=>run(async()=>{const f=$('importFile').files[0];if(!f)return;if(f.size>2000000)throw Error('Backup is too large (maximum 2 MB).');const data=validatePersonal(JSON.parse(await f.text()));personal=validatePersonal({version:1,bookmarks:[...personal.bookmarks,...data.bookmarks],notes:[...personal.notes,...data.notes]});save();$('importFile').value='';});
 $('loading').hidden=true;$('results').append(el('p','Desktop proof of concept. Browse a route, or zoom into a city and click stops to build a journey. Schedules and transfer calculations are experimental; coverage is incomplete.','notice'));
}
run(init);
