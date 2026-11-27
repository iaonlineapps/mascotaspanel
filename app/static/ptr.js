// Tirar hacia abajo para recargar, solo dentro de la app de Android (en el navegador ya lo hace el propio navegador).
// No salta si arrastras un mapa, un diálogo o un control deslizante, ni si la página no está arriba del todo.
(() => {
  if (!window.MascotasPanelAndroid) return;
  const MAX = 110, FIRE = 80;
  const es = (document.documentElement.lang || 'es').startsWith('es');
  const ind = document.createElement('div');
  ind.setAttribute('aria-hidden', 'true');
  ind.style.cssText = 'position:fixed;top:0;left:50%;z-index:9999;width:44px;height:44px;margin-left:-22px;border-radius:50%;' +
    'background:#fff;color:#ea580c;box-shadow:0 2px 10px rgba(0,0,0,.25);display:grid;place-items:center;font:700 22px/1 system-ui;' +
    'transform:translateY(-60px);transition:transform .2s;pointer-events:none';
  ind.textContent = '↻';
  const add = () => document.body && document.body.appendChild(ind);
  if (document.body) add(); else document.addEventListener('DOMContentLoaded', add);
  let y0 = null, d = 0;
  const blocked = t => t.closest && t.closest('.leaflet-container,dialog[open],input[type=range],canvas,.ticker,textarea,select,.map');
  addEventListener('touchstart', e => {
    y0 = (scrollY <= 0 && e.touches.length === 1 && !blocked(e.target)) ? e.touches[0].clientY : null; d = 0;
    ind.style.transition = 'none';
  }, {passive: true});
  addEventListener('touchmove', e => {
    if (y0 === null) return;
    d = Math.min(MAX, Math.max(0, (e.touches[0].clientY - y0) * 0.5));
    if (scrollY > 0) { y0 = null; d = 0; }
    ind.style.transform = `translateY(${d - 60 + 16}px) rotate(${d * 3}deg)`;
    ind.style.opacity = String(Math.min(1, d / FIRE));
  }, {passive: true});
  addEventListener('touchend', () => {
    if (y0 === null) return;
    ind.style.transition = 'transform .2s';
    if (d >= FIRE) {
      ind.style.transform = 'translateY(24px)'; ind.title = es ? 'Recargando…' : 'Reloading…';
      ind.animate([{transform: 'translateY(24px) rotate(0deg)'}, {transform: 'translateY(24px) rotate(360deg)'}], {duration: 700, iterations: Infinity});
      setTimeout(() => location.reload(), 150);
    } else ind.style.transform = 'translateY(-60px)';
    y0 = null; d = 0;
  }, {passive: true});
})();
