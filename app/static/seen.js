// Ficha de una mascota perdida: «📍 Lo he visto aquí» y el mapa con dónde se perdió, su localizador y quién la ha visto.
(() => {
const box = document.getElementById('seenBox'), dataEl = document.getElementById('seenData');
if (!box || !dataEl) return;
// pet.js define luego otra «L» (sus textos): guardamos aquí la de Leaflet
const LF = window.L;
const D = JSON.parse(dataEl.textContent), EN = D.lang === 'en', T = (es, en) => (EN ? en : es);
const $ = id => document.getElementById(id);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const loc = EN ? 'en-GB' : 'es-ES';
function when(t) {
  const d = new Date(t * 1000), now = new Date(), min = Math.round((now - d) / 60000);
  const hm = d.toLocaleTimeString(loc, {hour: '2-digit', minute: '2-digit'});
  const same = d.toDateString() === now.toDateString();
  const yest = new Date(now - 86400000).toDateString() === d.toDateString();
  const ago = min < 1 ? T('ahora mismo', 'just now') : min < 60 ? T(`hace ${min} min`, `${min} min ago`)
    : min < 24 * 60 ? T(`hace ${Math.round(min / 60)} h`, `${Math.round(min / 60)} h ago`) : '';
  const day = same ? T('hoy', 'today') : yest ? T('ayer', 'yesterday') : d.toLocaleDateString(loc, {day: 'numeric', month: 'short'});
  return `${day}, ${hm}${ago ? ' · ' + ago : ''}`;
}
const gmaps = (lat, lng) => `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;

// ---------- mapa ----------
let map = null, layer = null, pick = null, picked = null;
const tiles = m => LF.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'}).addTo(m);
const dot = (cls, txt) => LF.divIcon({className: 'spin ' + cls, html: `<span>${txt}</span>`, iconSize: [30, 30], iconAnchor: [15, 15], popupAnchor: [0, -14]});
function ensureMap() {
  if (map || !LF) return map;
  $('seenMap').hidden = false;
  map = LF.map('seenMap', {scrollWheelZoom: false, tap: false}); tiles(map);
  layer = LF.layerGroup().addTo(map);
  map.on('click', e => { if (!$('seenForm').hidden) setPick(e.latlng.lat, e.latlng.lng); });
  return map;
}
function draw(fit) {
  const pts = [];
  const legend = [];
  if (D.zone) pts.push(D.zone);
  if (D.tracker) pts.push([D.tracker.lat, D.tracker.lng]);
  D.seen.forEach(s => pts.push([s.lat, s.lng]));
  if (!pts.length && $('seenForm').hidden) { $('seenMap').hidden = true; $('seenLegend').hidden = true; return; }
  if (!ensureMap()) return;
  layer.clearLayers();
  if (D.zone) { LF.circle(D.zone, {radius: 250, color: '#dc2626', fillColor: '#dc2626', fillOpacity: .15, weight: 2}).addTo(layer)
    .bindPopup(T('Se perdió por esta zona', 'It got lost around here')); legend.push(`<li><i class="lz"></i>${T('Se perdió por aquí', 'Got lost around here')}</li>`); }
  if (D.tracker) { LF.marker([D.tracker.lat, D.tracker.lng], {icon: dot('trk', '📡'), zIndexOffset: 500}).addTo(layer)
    .bindPopup(`<b>${T('Su localizador', 'Its tracker')}</b><br>${esc(when(D.tracker.at))}`); legend.push(`<li><i class="lt">📡</i>${T('Su localizador', 'Its tracker')}</li>`); }
  const n = D.seen.length;
  D.seen.forEach((s, i) => LF.marker([s.lat, s.lng], {icon: dot(i === 0 ? 'seen last' : 'seen', String(n - i)), zIndexOffset: 1000 - i}).addTo(layer)
    .bindPopup(`<b>👀 ${T('Lo han visto', 'Seen')}</b><br>${esc(when(s.at))}${s.note ? '<br>' + esc(s.note) : ''}`));
  if (n) legend.push(`<li><i class="ls">${n}</i>${T('Lo han visto (el número más alto es lo último)', 'Seen (the highest number is the latest)')}</li>`);
  $('seenLegend').innerHTML = legend.join(''); $('seenLegend').hidden = !legend.length;
  if (fit !== false) {
    if (!pts.length) map.setView([40.2, -3.7], 5);
    else if (pts.length === 1) map.setView(pts[0], 15); else map.fitBounds(pts, {padding: [30, 30], maxZoom: 16});
  }
  setTimeout(() => map.invalidateSize(), 50);
}
function list() {
  const it = [];
  if (D.tracker) it.push({at: D.tracker.at, html: `<b>📡 ${T('Su localizador lo situó aquí', 'Its tracker placed it here')}</b>`, lat: D.tracker.lat, lng: D.tracker.lng, trk: true});
  D.seen.forEach(s => it.push({at: s.at, html: `<b>👀 ${T('Lo han visto aquí', 'Seen here')}</b>${s.note ? ` <q>${esc(s.note)}</q>` : ''}`, lat: s.lat, lng: s.lng, id: s.id}));
  it.sort((a, b) => b.at - a.at);
  $('seenList').innerHTML = it.length ? it.map(x => `<li class="${x.trk ? 'trk' : ''}"><span>${x.html}<small>${esc(when(x.at))}</small></span>`
    + `<a href="${gmaps(x.lat, x.lng)}" target="_blank" rel="noopener" title="Google Maps">🗺️</a></li>`).join('')
    : `<li class="none">${T('Todavía nadie ha dicho que lo ha visto. Si lo ves, pulsa el botón y márcalo en el mapa.', "Nobody has reported seeing it yet. If you see it, press the button and mark it on the map.")}</li>`;
}

// ---------- «📍 Lo he visto aquí» ----------
function setPick(lat, lng, fly) {
  picked = [lat, lng];
  if (pick) pick.setLatLng(picked);
  else pick = LF.marker(picked, {icon: dot('pick', '📍'), draggable: true, zIndexOffset: 2000}).addTo(map).on('dragend', e => { const p = e.target.getLatLng(); picked = [p.lat, p.lng]; });
  if (fly) map.setView(picked, 17);
  $('seenHint').textContent = T('Punto marcado. Si no es ahí, toca el sitio correcto o arrastra el 📍.', 'Point marked. If it is not right, tap the correct spot or drag the 📍.');
}
function here(auto) {
  if (!navigator.geolocation || !window.isSecureContext) { if (!auto) say(T('Este navegador no da la ubicación. Toca el mapa a mano.', "This browser can't give the location. Tap the map instead.")); return; }
  $('seenHere').disabled = true;
  navigator.geolocation.getCurrentPosition(p => {
    $('seenHere').disabled = false; setPick(p.coords.latitude, p.coords.longitude, true);
    if ((p.coords.accuracy || 0) > 1500) say(T('La ubicación es aproximada. Comprueba el punto en el mapa.', 'The location is approximate. Check the point on the map.'));
  }, () => { $('seenHere').disabled = false; if (!auto) say(T('No he podido saber dónde estás. Toca el mapa en el sitio.', "I couldn't find where you are. Tap the spot on the map.")); },
  {enableHighAccuracy: true, timeout: 12000, maximumAge: 30000});
}
const say = (t, ok) => { $('seenMsg').textContent = t || ''; $('seenMsg').classList.toggle('ok', !!ok); };
$('seenBtn').onclick = () => {
  $('seenForm').hidden = false; $('seenBtn').hidden = true; say('');
  draw(!map); box.scrollIntoView({behavior: 'smooth', block: 'start'});
  if (!picked) here(true);
};
$('seenCancel').onclick = () => {
  $('seenForm').hidden = true; $('seenBtn').hidden = false;
  if (pick) { pick.remove(); pick = null; } picked = null; draw(false);
};
$('seenHere').onclick = () => here(false);
$('seenWhen').onchange = () => {
  const other = $('seenWhen').value === 'other', i = $('seenAt'); i.hidden = !other;
  if (other && !i.value) { const d = new Date(Date.now() - new Date().getTimezoneOffset() * 60000); i.value = d.toISOString().slice(0, 16); i.max = i.value; }
};
$('seenForm').onsubmit = async e => {
  e.preventDefault();
  if (!picked) return say(T('Primero marca en el mapa dónde lo has visto.', 'First mark on the map where you saw it.'));
  const w = $('seenWhen').value;
  let at = Date.now() / 1000;
  if (w === 'other') { const v = $('seenAt').value; if (!v) return say(T('Pon el día y la hora.', 'Set the day and time.')); at = new Date(v).getTime() / 1000; }
  else at -= Number(w) * 60;
  const b = $('seenForm').querySelector('[type=submit]'); b.disabled = true; say(T('Guardando…', 'Saving…'), true);
  try {
    const r = await fetch('/api/seen/' + D.code, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-MascotasPanel': '1'},
      body: JSON.stringify({lat: picked[0], lng: picked[1], at, note: $('seenNote').value})});
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.detail || 'Error');
    D.seen.unshift(d); D.seen.sort((a, b) => b.at - a.at);
    if (pick) { pick.remove(); pick = null; } picked = null;
    $('seenForm').hidden = true; $('seenBtn').hidden = false; $('seenNote').value = ''; $('seenWhen').value = '0'; $('seenAt').hidden = true;
    draw(); list();
    $('seenList').insertAdjacentHTML('beforebegin', `<p class="fmsg ok" id="seenOk">✅ ${T('¡Gracias! Ya sale en el mapa y le hemos avisado a su familia.', 'Thank you! It now shows on the map and we have told its family.')}</p>`);
    setTimeout(() => { const o = $('seenOk'); if (o) o.remove(); }, 8000);
  } catch (err) { say(err.message); } finally { b.disabled = false; }
};

// ---------- solo para el dueño: abrir su localizador ----------
const to = $('trkOpen');
if (to && window.Tracker) {
  const k = Tracker.pick(to.dataset.kind);
  to.textContent = '📡 ' + (k === 'apple' ? T('Abrir mi AirTag (app Buscar)', 'Open my AirTag (Find My)') : T('Abrir mi localizador de Google', 'Open my Google tracker'));
  $('trkHint').textContent = Tracker.hint(to.dataset.kind, D.lang);
  to.onclick = () => Tracker.open(to.dataset.kind);
}
draw(); list();
})();
