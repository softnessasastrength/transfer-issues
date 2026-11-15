/* Desktop atlas controller. All feed/user text is rendered as text, never HTML. */
const $ = id => document.getElementById(id);
const el = (tag, text, cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
const button = (text, fn) => { const n = el('button', text); n.addEventListener('click', () => run(fn)); return n; };
const clock = seconds => { const day=Math.floor(seconds/86400), total=Math.floor(seconds/60)%1440, hour24=Math.floor(total/60), minute=total%60, suffix=hour24<12?'AM':'PM', hour=hour24%12||12; return `${hour}:${String(minute).padStart(2,'0')} ${suffix}${day?` (+${day} day${day===1?'':'s'})`:''}`; };
const seconds = value => { const match=String(value||'').trim().match(/^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?$/i); if(!match)throw Error('Use a time such as 8:00 AM.'); let h=Number(match[1]),m=Number(match[2]||0),suffix=match[3]?.toUpperCase(); if(m>59)throw Error('Choose a valid time.'); if(suffix){if(h<1||h>12)throw Error('Use an hour from 1 to 12.');h=(h%12)+(suffix==='PM'?12:0);}else if(h>23)throw Error('Choose a valid time.'); return h*3600+m*60; };
let meta, map, layers, nearby, stops = new Map(), routes = new Map(), labels = new Map(), request = 0, selectedRoute = null, routeChain = [];
const feedPalette = {cttransit:'#d85d4a',hartford:'#2f78c4',pvta:'#a64f9f',wrta:'#d58b2a',mbta:'#7556a8',amtrak:'#2f8a86'};
function routeColor(route) {
 const published=route?.color && /^[0-9a-f]{6}$/i.test(route.color) ? `#${route.color}` : '';
 return published && published.toLowerCase() !== '#ffffff' ? published : (feedPalette[route?.feed] || '#26776b');
}
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
function configureTimeField(id,fallback){ const input=$(id); if(!input)return; input.type='text';input.inputMode='text';input.autocomplete='off';input.placeholder='8:00 AM';if(!input.value||/^\d{2}:\d{2}$/.test(input.value))input.value=fallback; }
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
function stopLabel(s) { return `${s.name}${s.station_code?` [${s.station_code}]`:''} · ${s.feed.toUpperCase()}`; }
function resolve(id) { const input=$(id), value=input.value, sid=input.dataset.stopId || labels.get(value) || (stops.has(value) ? value : null); if (!sid) throw Error(`Choose a ${id === 'from' || id === 'outingFrom' ? 'departure' : 'destination'} stop from the suggestions.`); return sid; }
function rankedStops(value) {
 const query=value.trim().toLowerCase(); if(!query)return [];
 const terms=query.split(/\s+/).filter(Boolean);
 return [...stops.values()].map(s=>{
  const name=s.name.toLowerCase(), feed=s.feed.toLowerCase(), words=name.split(/[^a-z0-9]+/);
  let score=99;
  if(name===query)score=0; else if(name.startsWith(query))score=1; else if(words.some(w=>w.startsWith(query)))score=2; else if(name.includes(query))score=3; else if(terms.every(t=>name.includes(t)||feed.includes(t)))score=4;
  return {s,score};
 }).filter(x=>x.score<99).sort((a,b)=>a.score-b.score || a.s.name.localeCompare(b.s.name) || a.s.id.localeCompare(b.s.id)).slice(0,10).map(x=>x.s);
}
function setupStopPicker(id) {
 const input=$(id); let panel=$(id+'Suggestions'); if(!panel){panel=el('div');panel.id=id+'Suggestions';panel.className='stopSuggestions';panel.hidden=true;input.parentNode.insertBefore(panel,input.nextSibling);} input.setAttribute('role','combobox');input.setAttribute('aria-autocomplete','list');input.setAttribute('aria-controls',panel.id); let matches=[], active=-1;
 const close=()=>{panel.hidden=true;active=-1;};
 const choose=s=>{input.value=stopLabel(s);input.dataset.stopId=s.id;close();};
 const render=()=>{matches=rankedStops(input.value);active=-1;panel.replaceChildren();if(!matches.length){if(input.value.trim()){panel.append(el('div','No matching stop. Try a station code, city, or operator.','emptyState'));panel.hidden=false;}else close();return;}matches.forEach((s,i)=>{const b=button('',()=>choose(s));b.type='button';b.className='stopSuggestion';b.setAttribute('role','option');b.dataset.index=i;b.append(el('span',s.name),el('small',s.feed.toUpperCase()));panel.append(b);});panel.hidden=false;};
 input.addEventListener('input',()=>{delete input.dataset.stopId;render();});input.addEventListener('focus',render);
 input.addEventListener('keydown',event=>{if(panel.hidden)return;if(event.key==='ArrowDown'){event.preventDefault();active=Math.min(active+1,matches.length-1);}else if(event.key==='ArrowUp'){event.preventDefault();active=Math.max(active-1,0);}else if(event.key==='Enter'&&active>=0){event.preventDefault();choose(matches[active]);}else if(event.key==='Escape')close();panel.querySelectorAll('.stopSuggestion').forEach((b,i)=>b.classList.toggle('active',i===active));});
 document.addEventListener('click',event=>{if(!input.parentElement.contains(event.target))close();});
}
function sourceLink(feed) { const source = meta.sources.find(s => s.id === feed); const n = el('a', `Source: ${feed}`); if(source && /^https?:\/\//.test(source.url)) { n.href = source.url; n.target = '_blank'; n.rel = 'noopener'; } return n; }
function marker(s, group=layers, color='#26776b') {
 const popup = el('div'); popup.append(el('b', s.name), el('p', s.id));
 popup.append(button('Start here', () => { $('from').value=stopLabel(s); map.closePopup(); }), button('Go here', () => { $('to').value=stopLabel(s); map.closePopup(); }), button('Meet here', () => { $('outingTo').value=stopLabel(s);$('outingTo').dataset.stopId=s.id;map.closePopup();run(()=>verifyOuting(s.id)); }), button('Departures', () => departures(s)));
 const surface=getComputedStyle(document.documentElement).getPropertyValue('--atlas-surface').trim() || '#fffdf7';
 return L.circleMarker([s.lat,s.lon], {radius:7,color,weight:2.5,fillColor:surface,fillOpacity:1}).bindPopup(popup).addTo(group);
}
function outingMarker(stop, status, select) {
 const icon=L.divIcon({className:`outingMapIcon ${status}`,html:'<span aria-hidden="true"></span>',iconSize:[28,28],iconAnchor:[14,14]});
 const label=`${stop.name}: ${outingStatusLabel(status)}. Select outing stop`;
 const pin=L.marker([stop.lat,stop.lon],{icon,keyboard:true,title:label}).addTo(layers);
 pin.getElement().setAttribute('role','button');
 pin.getElement().setAttribute('aria-label',label);
 pin.getElement().addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();select();}});
 pin.on('click',select);
 return pin;
}
function outingStatusLabel(status){return status==='verified'?'Verified round trip':status==='ruled_out'?'Ruled out by schedule':'Cannot determine';}
function fit() { if(layers.getLayers().length) { const b = layers.getBounds(); if(b.isValid()) map.fitBounds(b,{padding:[40,40],maxZoom:14}); } }
function nearbyStops() { nearby.clearLayers(); if(map.getZoom()<12) return; let n=0; for(const s of stops.values()) if(map.getBounds().contains([s.lat,s.lon]) && n++<600) marker(s, nearby, '#657b74'); }
function chainLabel(id){const r=routes.get(id);return r?`${r.short || id} · ${r.feed}`:id;}
function renderChain(){const host=$('routeChainItems');if(!host)return;host.replaceChildren();if(!routeChain.length){host.append(el('p','No routes chained yet. Add routes from Browse routes.','small'));return;}routeChain.forEach((id,i)=>{const row=el('div',undefined,'chainItem');row.style.setProperty('--route-color',routeColor(routes.get(id)));row.append(el('b',String(i+1).padStart(2,'0')),el('span',chainLabel(id)));const up=button('↑',()=>{if(i){[routeChain[i-1],routeChain[i]]=[routeChain[i],routeChain[i-1]];renderChain();}});const down=button('↓',()=>{if(i<routeChain.length-1){[routeChain[i+1],routeChain[i]]=[routeChain[i],routeChain[i+1]];renderChain();}});const remove=button('×',()=>{routeChain.splice(i,1);renderChain();});[up,down,remove].forEach(b=>{b.className='chainAction';row.append(b);});host.append(row);if(i<routeChain.length-1)host.append(el('span','↓ transfer','chainArrow'));});}
function addToChain(id){if(routeChain[routeChain.length-1]===id)return;routeChain.push(id);renderChain();view('explore');$('browser').hidden=false;$('planner').hidden=true;$('browseTab').classList.add('selected');$('planTab').classList.remove('selected');}
function installRouteChain(){const browser=$('browser'),list=$('routeList'),panel=el('section',undefined,'routeChainPanel');panel.append(el('div','BUILD A ROUTE CHAIN','eyebrow'),el('h3','Ride this, then this'),el('p','Try odd combinations like 905 → 30 → 24. Percival will explore the loaded timetable and show exactly where the chain works or breaks.','small'));const items=el('div');items.id='routeChainItems';panel.append(items);const clear=button('Clear chain',()=>{routeChain=[];renderChain();});clear.className='quiet';panel.append(clear);browser.insertBefore(panel,list);renderChain();}
function renderRoutes() { const search = $('routeSearch').value.toLowerCase(), feed=$('agency').value; $('routeList').replaceChildren(); let count=0; for(const r of meta.routes) if((!feed||r.feed===feed) && `${r.short} ${r.name} ${r.feed}`.toLowerCase().includes(search)) { const row=el('div',undefined,'routePickRow');const b=button(`${r.short || r.id} · ${r.name} (${r.feed})`, () => showRoute(r.id)); b.className='routeButton'; b.dataset.routeId=r.id; b.style.setProperty('--route-color',routeColor(r));const add=button('+ chain',()=>addToChain(r.id));add.className='chainAdd';row.append(b,add);$('routeList').append(row); count++; } if(!count){const empty=el('div',undefined,'emptyState');empty.append(el('b','No loaded route matches that search.'),el('span','Try a route number, operator, or clear the network filter.'));$('routeList').append(empty);} }
async function showRoute(id) {
 const token=++request; const r=routes.get(id); $('results').replaceChildren(el('p','Loading route…')); const data=await api('route',{id,date:$('date').value}); if(token!==request)return;
 selectedRoute=id; clearAllRoutes(); layers.clearLayers(); for(const shape of data.shapes) if(shape.length) L.polyline(shape,{color:'#26776b',weight:4}).addTo(layers); data.stops.forEach(s=>marker(s)); fit();
 const card=el('section',undefined,'resultCard'); card.append(el('h3',`${r.short} ${r.name}`),sourceLink(r.feed),el('p',`${data.trips.length} scheduled trips on ${$('date').value}. Stops show the published route footprint; not every trip serves every stop.`),el('p', data.geometry,'small'));
 for(const c of data.comparison) card.append(el('p',`${c.label} · ${c.date}: ${c.trips} trips`));
 if(!data.trips.length)card.append(el('p','No trips on this date in the loaded schedule. This may indicate expired or missing data.','notice'));
 const select=el('select'); select.setAttribute('aria-label','Scheduled trip'); select.append(new Option('Choose a trip timetable…','')); data.trips.forEach(t=>select.append(new Option(`${t.headsign || 'Trip'} · ${t.id}`,t.id))); select.onchange=()=>run(()=>tripTable(select.value,card)); card.append(select); $('results').replaceChildren(card); $('mapStatus').textContent=`${r.short} · ${r.feed} · ${$('date').value}`;
}
async function tripTable(id, parent) { if(!id)return; const rows=await api('trip',{id}); parent.querySelector('.tableWrap')?.remove(); const wrap=el('div',undefined,'tableWrap'),table=el('table'); const head=el('tr'); ['Stop','Arrival','Departure'].forEach(x=>head.append(el('th',x))); table.append(head); rows.forEach(s=>{const tr=el('tr');[s.name,clock(s.arr),clock(s.dep)].forEach(x=>tr.append(el('td',x)));table.append(tr);});wrap.append(table);parent.append(wrap); }
async function departures(s) { const data=await api('departures',{stop:s.id,date:$('date').value}); const card=el('section',undefined,'resultCard');card.append(el('h3',s.name),el('p',`Departures · ${$('date').value}`)); if(!data.departures.length)card.append(el('p','No departures in the loaded schedule for this date.','notice')); for(const d of data.departures) {const row=el('div',undefined,'leg'); row.append(button(`${clock(d.departure)} · ${routes.get(d.route)?.short || d.route} · ${d.headsign}`,()=>tripTable(d.trip,card)),sourceLink(d.source));card.append(row);} $('results').replaceChildren(card);map.closePopup(); }
function options() { const time=seconds($('time').value),deadline=seconds($('deadline').value); if(deadline<time)throw Error('Home-by must be after departure on the selected day.'); return {from:resolve('from'),date:$('date').value,time,deadline,mode:$('mode').value,radius:Math.round(Number($('radius').value)*(preferences.units==='imperial'?1/feetPerMeter:1)),buffer:Number($('buffer').value)*60,include_optional:$('includeOptional')?.checked?'1':'0',routes:routeChain.join(',')}; }
function coverageNotice(coverage) { const missing=coverage.filter(s=>!s.in_service_period||s.status!=='imported').map(s=>s.feed); return el('p',`Experimental scheduled results, not guaranteed connections or seat availability. ${missing.length?'Missing/out-of-period feeds: '+missing.join(', ')+'. ':''}Other unlisted agencies are missing. Check operators before travel.`, 'notice'); }
function fareNotice(fare) { if(!fare)return null; if(fare.status==='supported')return el('p',`Estimated fare: $${fare.amount} · ${fare.product}.`, 'fare'); if(fare.status==='partial')return el('p',`Fare estimate: ${fare.supported_legs?.length?'$'+fare.supported_legs.reduce((sum,x)=>sum+Number(x.amount||0),0).toFixed(2):'partial'} · ${fare.unknown_reasons.join(' ')}`, 'fare notice'); return el('p',`Fare unavailable: ${fare.reason || fare.unknown_reasons?.join(' ') || 'unsupported fare combination.'}`, 'fare notice'); }
function chainNotice(result){if(!routeChain.length)return null;const wanted=routeChain.map(chainLabel).join(' → ');if(!result.found)return el('p',`Route chain requested: ${wanted}. No matching itinerary was found in the selected window.`,'notice');return el('p',result.route_chain_matched?`Route chain matched: ${wanted}. Transfers remain schedule-based estimates.`:`Route chain requested: ${wanted}. The loaded itinerary did not match the full sequence.`,'notice');}
function itinerary(result,title) {
 const card=el('section',undefined,'resultCard');card.append(el('h3',title)); if(!result.found){card.append(el('p',result.message||'No return found in the loaded schedules.'));return card;}
 card.append(el('p',`${clock(result.departure)} → ${clock(result.arrival)}`)); if(result.precision)card.append(el('p',result.precision,'small'));const fare=fareNotice(result.fare);if(fare)card.append(fare);
 for(const leg of result.legs) { const a=stops.get(leg.from_stop),b=stops.get(leg.to_stop), row=el('div',undefined,'leg'); const transit=leg.kind==='transit', route=routes.get(leg.route); row.append(el('b',transit?`${route?.short || leg.route} · ${leg.headsign}`:`${leg.kind} · estimated ${distanceText(leg.meters)}`),el('p',`${a.name} → ${b.name}`),el('p',`${clock(leg.departure)} → ${clock(leg.arrival)}`)); if(transit)row.append(sourceLink(leg.source));card.append(row); marker(a,layers,transit?routeColor(route):'#c76f43');marker(b,layers,transit?routeColor(route):'#c76f43'); if(!transit)L.polyline([[a.lat,a.lon],[b.lat,b.lon]],{color:'#c76f43',weight:3,dashArray:'6 8',opacity:.9}).addTo(layers); }
 return card;
}
async function plan(kind='depart') {
 const params={...options(),to:resolve('to'),kind,return:$('return').checked?'1':'0',visit:Number($('visit').value)*60}; const token=++request; selectedRoute=null; clearAllRoutes(); $('results').replaceChildren(el('p','Searching the published schedules…')); const data=await api('plan',params); if(token!==request)return;layers.clearLayers();$('results').replaceChildren(coverageNotice(data.coverage),itinerary(data,'Outbound journey'));if(data.return)$('results').append(itinerary(data.return,'Return journey'));if(data.latest_return?.found)$('results').append(el('p',`Latest return start: ${clock(data.latest_return.latest_start_minute)} (one-minute precision)`,'notice'));fit();
}
async function reach() {const params=options();params.deadline=Math.min(Number(params.deadline),params.time+7200);const token=++request;clearAllRoutes();const data=await api('reachability',params);if(token!==request)return;layers.clearLayers();data.stops.forEach(s=>marker(stops.get(s.id)));fit();$('results').replaceChildren(el('h3',`${data.stops.length} stops reachable within two hours`),coverageNotice(data.coverage),el('p','Includes estimated ground links. Click a stop for departures.'));}
function renderSources() { $('sourceCards').replaceChildren(); for(const s of meta.sources){const card=el('article',undefined,'card'); card.append(el('h2',s.id),el('span',s.status,'badge'),sourceLink(s.id)); for(const [key,label] of [['retrieved_at','Retrieved'],['service_start','Service begins'],['service_end','Service ends'],['scope','Coverage'],['refresh_error','Refresh error']])card.append(el('p',`${label}: ${s[key] || 'Not recorded'}`));card.append(el('p',`Validation: ${JSON.stringify(s.validation || 'Not recorded')}`,'small'));$('sourceCards').append(card);} }
function liveCard(data) { const card=el('section',undefined,`resultCard liveCard ${data.status}`); const providerName=data.provider==='mbta_v3'?'MBTA V3':data.provider==='cttransit_json'?'CTtransit JSON':'No verified live adapter'; card.append(el('h2',data.status==='live'?'LIVE · provider response':'UNKNOWN · no verified realtime response'),el('p',providerName),el('p',data.as_of?`Checked ${new Date(data.as_of).toLocaleString()}`:'No provider timestamp available.','small')); if(data.status==='live'){const board=el('div',undefined,'liveBoard');if(!data.predictions.length)board.append(el('p','The provider returned no matching predictions.','notice'));data.predictions.forEach(p=>{const row=el('div',undefined,'liveRow');row.append(el('b',p.route?.data?.id||p.route_id||p.id||'Vehicle'),el('span',p.departure_time||p.arrival_time||p.time||'Time unavailable'),el('small',p.status||'prediction'));board.append(row);});card.append(el('h3','Predictions'),board,el('h3',`Alerts · ${data.alerts.length}`));if(data.alerts.length)data.alerts.forEach(a=>card.append(el('p',a.header||a.short_header||a.description||'Alert text unavailable','notice')));else card.append(el('p','No alerts returned for this filter.','small'));}const limitations=el('div',undefined,'notice');limitations.append(el('b','Read this as status, not a promise.'));data.limitations.forEach(x=>limitations.append(el('p',x)));card.append(limitations);return card; }
function liveCountdown(value){ const when=typeof value==='number'?new Date(value*1000):new Date(value);if(Number.isNaN(when.getTime()))return String(value||'Time unavailable');const delta=Math.round((when-Date.now())/60000);if(Math.abs(delta)<=1)return 'NOW';if(delta>0)return `in ${delta} min`;return `${Math.abs(delta)} min ago`; }
function decorateLiveBoard(){ document.querySelectorAll('.liveRow span').forEach(node=>{const raw=node.textContent;if(/^in |NOW$| min ago$/.test(raw))return;node.title=raw;node.textContent=liveCountdown(raw);}); }
async function refreshLive(){ const data=await api('live',{provider:$('liveProvider').value,route:$('liveRoute').value.trim(),stop:$('liveStop').value.trim(),alerts:'1'});$('liveResults').replaceChildren(liveCard(data));decorateLiveBoard(); }
function installLiveView(){ const page=el('section');page.id='live';page.className='view page';page.hidden=true;page.append(el('div','OPTIONAL REALTIME OVERLAY','eyebrow'),el('h1','What’s moving now.'),el('p','Live provider data sits beside the published schedule. It never changes route feasibility.'));const controls=el('div',undefined,'liveControls');const provider=el('select');provider.id='liveProvider';provider.append(new Option('MBTA V3','mbta'),new Option('CTtransit · not verified','cttransit'),new Option('PVTA · not verified','pvta'));const route=el('input');route.id='liveRoute';route.placeholder='Red or mbta:Red';const stop=el('input');stop.id='liveStop';stop.placeholder='place-pktrm or mbta:place-pktrm';[['PROVIDER',provider],['ROUTE (OPTIONAL)',route],['STOP (OPTIONAL)',stop]].forEach(([label,node])=>{controls.append(el('label',label),node);});const refresh=button('Check live status ↗',refreshLive);refresh.id='liveRefresh';refresh.className='primary';controls.append(refresh);page.append(controls);const results=el('div');results.id='liveResults';results.setAttribute('aria-live','polite');results.append(el('p','Choose a provider and check status. “Unknown” means this app cannot verify realtime data right now.','notice'));page.append(results,el('p','Live data may be delayed, incomplete, or unavailable. It is not a guarantee of arrival, boarding, transfer, accessibility, or seat availability.','small'));document.querySelector('main').after(page);const tab=el('button','Live board');tab.dataset.tab='live';document.querySelector('nav').insertBefore(tab,document.querySelector('nav [data-tab="sources"]'));tab.onclick=()=>view('live'); }
function renderPersonal() {
 $('journalCount').textContent=personal.notes.length; $('bookmarks').replaceChildren();$('notes').replaceChildren();
 personal.bookmarks.forEach((b,i)=>{const row=el('div',undefined,'note');row.append(button(`${b.from} → ${b.to}`,()=>{for(const key of ['from','to','date','time'])$(key).value=b[key];view('explore');updateDate();}),button('Delete',()=>{personal.bookmarks.splice(i,1);save();}));$('bookmarks').append(row);});
 personal.notes.forEach((n,i)=>{const row=el('article',undefined,'note');row.append(el('h3',n.title),el('p',n.text),button('Delete',()=>{personal.notes.splice(i,1);save();}));$('notes').append(row);});
}
function updateDate(){ const d=$('date').value; $('dayLabel').textContent=d?new Date(d+'T12:00:00').toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'}):'Choose a travel date'; }
async function init() {
 $('locate').onclick=toggleLocation;
 $('followLocation').onclick=toggleFollow;
 updatePreferences();
 configureTimeField('time','8:00 AM');configureTimeField('deadline','11:59 PM');configureTimeField('outingTime','8:00 AM');configureTimeField('outingHomeBy','10:00 PM');
 $('theme').onchange=()=>{preferences.theme=$('theme').value;savePreferences();};
 $('units').onchange=()=>{const meters=Number($('radius').value)*(preferences.units==='imperial'?1/feetPerMeter:1);preferences.units=$('units').value;updatePreferences();$('radius').value=Math.round(meters*(preferences.units==='imperial'?feetPerMeter:1));savePreferences();};
 const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date()),today=['year','month','day'].map(k=>parts.find(p=>p.type===k).value).join('-'); $('date').value=today;$('outingDate').value=today;updateDate();
 meta=await api('meta');const sourceNotice=document.querySelector('#sources .notice');if(sourceNotice)sourceNotice.textContent='Coverage is incomplete. Check each source card for its service dates and import status. Published schedules do not confirm a seat, booking, or live operation. Some local and on-demand services have no usable timetable in this planner.';stops=new Map(meta.stops.map(s=>[s.id,s]));routes=new Map(meta.routes.map(r=>[r.id,r]));setupStopPicker('from');setupStopPicker('to');setupStopPicker('outingFrom');setupStopPicker('outingTo');if(meta.sources.some(s=>s.optional)){const optionalToggle=el('label','Include optional feeds','check'),optionalInput=el('input');optionalInput.type='checkbox';optionalInput.id='includeOptional';optionalToggle.prepend(optionalInput);document.querySelector('#planner details').append(optionalToggle);}
 map=L.map('map',{preferCanvas:true}).setView([42,-72.4],8);layers=L.featureGroup().addTo(map);nearby=L.layerGroup().addTo(map);
 L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).on('tileerror',()=>$('tileNotice').hidden=false).addTo(map);map.on('moveend',nearbyStops);
 const fragment=document.createDocumentFragment(); for(const s of meta.stops){const label=stopLabel(s);labels.set(label,s.id);fragment.append(new Option(label,label));} $('stopList').append(fragment);
 meta.cities.forEach(([name,lat,lon])=>{ $('cities').append(button(name,()=>{map.setView([lat,lon],13);$('mapStatus').textContent=`${name} · zoomed stops from loaded feeds`; })); L.circleMarker([lat,lon],{radius:3,color:'#143e39'}).bindTooltip(name,{permanent:true,direction:'right',className:'cityMarker'}).addTo(map); });
 [...new Set(meta.routes.map(r=>r.feed))].forEach(f=>{$('agency').append(new Option(f,f));$('allRoutesAgency').append(new Option(f,f));});
 $('allRoutes').onclick=()=>run(showAllRoutes);
 $('allRoutesAgency').onchange=()=>{if(allRoutesVisible)run(async()=>{clearAllRoutes();await showAllRoutes();});};renderRoutes();renderSources();renderPersonal();$('counts').textContent=`${meta.routes.length} routes · ${meta.stops.length.toLocaleString()} published stops · incomplete coverage`;
 document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>view(b.dataset.tab));$('planTab').onclick=()=>{$('planner').hidden=false;$('browser').hidden=true;$('planTab').classList.add('selected');$('browseTab').classList.remove('selected');};$('browseTab').onclick=()=>{$('planner').hidden=true;$('browser').hidden=false;$('browseTab').classList.add('selected');$('planTab').classList.remove('selected');};
 $('routeSearch').oninput=renderRoutes;$('agency').onchange=renderRoutes;$('date').onchange=()=>{updateDate();if(selectedRoute)run(()=>showRoute(selectedRoute));};$('swap').onclick=()=>{const a=$('from').value;$('from').value=$('to').value;$('to').value=a;};$('resetMap').onclick=()=>{following=false;$('followLocation').textContent='Follow: off';$('followLocation').setAttribute('aria-pressed','false');map.setView([42,-72.4],8);};
 $('plan').onclick=()=>run(()=>plan());$('latest').onclick=()=>run(()=>plan('latest'));$('reach').onclick=()=>run(reach);
 $('bookmark').onclick=()=>run(()=>{resolve('from');resolve('to');personal.bookmarks.push(Object.fromEntries(['from','to','date','time'].map(k=>[k,$(k).value])));save();$('results').replaceChildren(el('p','Search saved in My discoveries.','notice'));});
 $('saveNote').onclick=()=>run(()=>{if(!$('noteTitle').value.trim())throw Error('Give your note a title.');personal.notes.push({title:$('noteTitle').value,text:$('noteText').value});save();$('noteTitle').value='';$('noteText').value='';});
 $('export').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(personal,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download='transit-atlas-discoveries.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 $('importFile').onchange=()=>run(async()=>{const f=$('importFile').files[0];if(!f)return;if(f.size>2000000)throw Error('Backup is too large (maximum 2 MB).');const data=validatePersonal(JSON.parse(await f.text()));personal=validatePersonal({version:1,bookmarks:[...personal.bookmarks,...data.bookmarks],notes:[...personal.notes,...data.notes]});save();$('importFile').value='';});
 $('loading').hidden=true;$('results').append(el('p','Desktop proof of concept. Browse a route, or zoom into a city and click stops to build a journey. Schedules and transfer calculations are experimental; coverage is incomplete.','notice'));
}
run(init);
