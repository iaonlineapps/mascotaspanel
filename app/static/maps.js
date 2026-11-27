// Mapas de las páginas públicas (Leaflet + OpenStreetMap, sin claves ni cuentas).
(() => {
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const tiles = m => L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 18,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'}).addTo(m);
const pin = (icon, lost) => L.divIcon({className: 'pin' + (lost ? ' lost' : ''), html: `<span>${icon}</span>`, iconSize: [38, 38], iconAnchor: [19, 38], popupAnchor: [0, -34]});

// Inicio: todas las mascotas perdidas que tienen sitio
const box = document.getElementById('lostMap'), dataEl = document.getElementById('mapData');
if (box && dataEl && window.L) {
  const d = JSON.parse(dataEl.textContent), q = d.lang === 'en' ? '?lang=en' : '';
  const m = L.map(box, {scrollWheelZoom: false}); tiles(m);
  const pts = d.pins.map(p => {
    L.marker([p.lat, p.lng], {icon: pin(p.icon, true)}).addTo(m).bindPopup(
      `<a class="pop" href="/m/${encodeURIComponent(p.code)}${q}">${p.photo ? `<img src="${esc(p.photo)}" alt="">` : ''}<b>${esc(p.name)}</b><small>${esc(d.since)} ${esc(p.when)}</small><span>${esc(d.see)} →</span></a>`);
    return [p.lat, p.lng];
  });
  if (pts.length === 1) m.setView(pts[0], 14); else m.fitBounds(pts, {padding: [40, 40], maxZoom: 14});
}
// Ficha: la zona donde se perdió (un círculo, no un punto exacto)
const pm = document.getElementById('petMap');
if (pm && window.L) {
  const ll = [Number(pm.dataset.lat), Number(pm.dataset.lng)];
  const m = L.map(pm, {scrollWheelZoom: false, dragging: !L.Browser.mobile, tap: false}).setView(ll, 15); tiles(m);
  L.circle(ll, {radius: 250, color: '#dc2626', fillColor: '#dc2626', fillOpacity: .18, weight: 2}).addTo(m);
}
// «Busca tu pipicán»: todos los pipicanes, con foto y cómo llegar
const km = document.getElementById('parkMap'), kd = document.getElementById('parkData');
if (km && kd && window.L) {
  const d = JSON.parse(kd.textContent);
  const m = L.map(km, {scrollWheelZoom: false}); tiles(m);
  const pts = d.pins.map(p => {
    L.marker([p.lat, p.lng], {icon: L.divIcon({className: 'pin park', html: '<span></span>', iconSize: [38, 38], iconAnchor: [19, 38], popupAnchor: [0, -34]})}).addTo(m).bindPopup(
      `<div class="pop">${p.photo ? `<img src="${esc(p.photo)}" alt="">` : ''}<b>${esc(p.name)}</b>${p.notes ? `<small>${esc(p.notes)}</small>` : ''}` +
      `<a href="https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lng}" target="_blank" rel="noopener">🧭 ${esc(d.go)} →</a><a class="ed" href="/panel#k${p.id}">✏️ ${esc(d.edit || 'Cambiar')}</a></div>`);
    return [p.lat, p.lng];
  });
  if (!pts.length) m.setView([40.2, -3.7], 5);
  else if (pts.length === 1) m.setView(pts[0], 15); else m.fitBounds(pts, {padding: [40, 40], maxZoom: 15});
  // Dónde estoy: GPS del móvil; en un ordenador sin GPS la posición sale por internet y puede fallar muchos km,
  // así que se enseña el círculo de error, se avisa y se deja buscar el pueblo a mano (o ir a la zona de tu cuenta).
  const msg = document.getElementById('pfMsg'), say = (t) => { if (msg) msg.textContent = t || ''; };
  let me = null, ring = null;
  const mark = (ll, acc) => {
    if (me) { me.remove(); me = null; } if (ring) { ring.remove(); ring = null; }
    if (acc) ring = L.circle(ll, {radius: acc, color: '#2563eb', fillColor: '#2563eb', fillOpacity: .08, weight: 1}).addTo(m);
    me = L.circleMarker(ll, {radius: 8, color: '#2563eb', fillColor: '#2563eb', fillOpacity: .9}).addTo(m);
    // estás en un pipicán que no sale: apúntalo desde aquí (abre tu panel con el sitio ya puesto)
    if (d.add && acc > 0 && acc <= 2000) me.bindPopup(`<div class="pop"><small>${esc(d.here)}</small><a href="/panel#nuevo=${ll[0].toFixed(5)},${ll[1].toFixed(5)}">➕ ${esc(d.add)}</a></div>`).openPopup();
    m.setView(ll, acc > 2000 ? 11 : 14); km.scrollIntoView({behavior: 'smooth', block: 'center'});
  };
  const near = document.getElementById('nearMe');
  if (near) near.onclick = () => {
    if (!navigator.geolocation) return say(d.nogps);
    navigator.geolocation.getCurrentPosition(p => {
      const acc = p.coords.accuracy || 0; mark([p.coords.latitude, p.coords.longitude], acc);
      say(acc > 2000 ? d.rough.replace('{km}', Math.round(acc / 1000)) : '');
    }, () => say(d.nogps), {enableHighAccuracy: true, timeout: 15000, maximumAge: 0});
  };
  const geo = async (q) => {
    const r = await fetch('https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=es&accept-language=' + (d.lang || 'es') + '&q=' + encodeURIComponent(q));
    const j = await r.json(); return j[0] ? [Number(j[0].lat), Number(j[0].lon)] : null;
  };
  const form = document.getElementById('pfForm');
  if (form) form.onsubmit = async (e) => {
    e.preventDefault(); const q = document.getElementById('pfQ').value.trim(); if (!q) return;
    try { const ll = await geo(q); if (ll) { mark(ll, 0); m.setView(ll, 14); say(''); } else say(d.notfound); } catch (err) { say(d.notfound); }
  };
  // la zona de tu cuenta, si has entrado
  const homeB = document.getElementById('pfHome');
  if (homeB) fetch('/api/me', {credentials: 'same-origin'}).then(r => r.json()).then(i => {
    const z = i && i.user && (i.user.zone || '').trim(); if (!z) return;
    homeB.textContent = '🏠 ' + d.home + ': ' + z; homeB.hidden = false;
    homeB.onclick = () => { document.getElementById('pfQ').value = z; form.requestSubmit(); };
  }).catch(() => {});
}
})();
