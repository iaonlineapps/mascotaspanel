// Ficha del QR: formulario «Avisar a su familia» (el aviso llega al panel del dueño).
(() => {
const f = document.getElementById('found'); if (!f) return;
const EN = document.documentElement.lang === 'en';
const T = (es, en) => (EN ? en : es);
const btn = document.getElementById('showFound');
if (btn) btn.onclick = () => { f.hidden = false; btn.hidden = true; f.scrollIntoView({behavior: 'smooth', block: 'start'}); };
const out = document.getElementById('fMsg');
const where = () => new Promise(ok => {
  const l = document.getElementById('fLoc'); if (!l || !l.checked || !navigator.geolocation || !window.isSecureContext) return ok(null);
  navigator.geolocation.getCurrentPosition(p => ok(p.coords), () => ok(null), {enableHighAccuracy: true, timeout: 8000, maximumAge: 60000});
});
f.onsubmit = async e => {
  e.preventDefault();
  const b = f.querySelector('button[type=submit]'); b.disabled = true; out.textContent = T('Enviando…', 'Sending…');
  const c = await where();
  const body = {text: document.getElementById('fText').value, contact: document.getElementById('fContact').value};
  if (c) { body.lat = c.latitude; body.lng = c.longitude; }
  try {
    const r = await fetch('/api/found/' + f.dataset.code, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-MascotasPanel': '1'}, body: JSON.stringify(body)});
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.detail || 'Error');
    f.innerHTML = f.dataset.adopt ? `<h2>✅ ${T('¡Mensaje enviado!', 'Message sent!')}</h2><p>${T('La asociación lo verá en cuanto entre en la app y te contestará.', 'The association will see it as soon as they open the app and will reply.')}</p>`
      : `<h2>✅ ${T('¡Aviso enviado! Muchas gracias.', 'Notice sent! Thank you so much.')}</h2><p>${T('Su familia lo verá en cuanto entre en la app.', 'Its family will see it as soon as they open the app.')}</p>`;
  } catch (err) { b.disabled = false; out.textContent = err.message; }
};
})();
