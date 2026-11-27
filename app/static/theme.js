// Apariencia (en este dispositivo): claro / oscuro / automático, color y fondo con patitas.
// Va en el <head> para que la página no parpadee al cargar.
(() => {
const KEY = 'mascotaspanel-tema';
const COLORS = {naranja: '#ea580c', azul: '#2563eb', verde: '#16a34a', morado: '#7c3aed', rosa: '#db2777', turquesa: '#0d9488', rojo: '#dc2626', marron: '#92400e'};
let s = {}; try { s = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) {}
const r = document.documentElement;
const apply = v => {
  s = {mode: 'auto', color: 'naranja', paws: true, ...v};
  if (s.mode === 'auto') r.removeAttribute('data-theme'); else r.dataset.theme = s.mode;
  r.style.setProperty('--or', COLORS[s.color] || COLORS.naranja);
  r.dataset.paws = s.paws ? '1' : '0';
};
apply(s);
window.Tema = {COLORS, get: () => ({...s}), set: v => { apply({...s, ...v}); try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {} }};
})();
