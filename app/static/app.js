// Panel de MascotasPanel: JavaScript sin frameworks.
(() => {
const $ = id => document.getElementById(id);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const SP = {perro: ['Perro', '🐶'], gato: ['Gato', '🐱'], conejo: ['Conejo', '🐰'], huron: ['Hurón', '🦦'], pajaro: ['Pájaro', '🐦'], loro: ['Loro', '🦜'], gallina: ['Gallina', '🐔'], hamster: ['Hámster', '🐹'], cobaya: ['Cobaya', '🐹'], raton: ['Ratón o rata', '🐭'], erizo: ['Erizo', '🦔'], tortuga: ['Tortuga', '🐢'], reptil: ['Reptil', '🦎'], pez: ['Pez', '🐟'], caballo: ['Caballo', '🐴'], burro: ['Burro', '🐴'], cerdo: ['Cerdo', '🐷'], cabra: ['Cabra u oveja', '🐐'], otro: ['Otro', '🐾']};
window.SP = SP;
let info = null, me = null, pets = [], P = null, toastT, newPhoto;

async function api(path, opts = {}) {
  const o = {method: opts.method || 'GET', headers: {'X-MascotasPanel': '1'}, credentials: 'same-origin'};
  if (opts.body !== undefined) { o.headers['Content-Type'] = 'application/json'; o.body = JSON.stringify(opts.body); }
  const r = await fetch(path, o);
  let d = null; try { d = await r.json(); } catch (e) {}
  if (!r.ok) {
    if (r.status === 401 && path !== '/api/login') showAuth();
    throw new Error(d && d.detail ? (typeof d.detail === 'string' ? t(d.detail) : t('Datos no válidos')) : 'Error ' + r.status);
  }
  return d;
}
function toast(msg) {
  $('toastMsg').textContent = t(msg); $('toast').classList.add('show'); clearTimeout(toastT);
  toastT = setTimeout(() => $('toast').classList.remove('show'), 2600);
}

// ---------- entrar ----------
let registering = false;
function showAuth(adding = false) {
  $('app').hidden = true; $('auth').hidden = false; $('accMenu').hidden = true;
  registering = !!(info && info.first_user) && !adding;
  setAuthMode();
  $('authCancel').hidden = !adding;
  if (adding) { $('uLogin').value = ''; $('uPass').value = ''; $('authLead').textContent = 'Añadir otra cuenta'; }
  paintAuthAccounts(adding);
}
function setAuthMode() {
  $('authBtn').textContent = registering ? 'Crear cuenta' : 'Entrar';
  $('authSwitch').textContent = registering ? 'Ya tengo cuenta' : 'Crear cuenta';
  $('authSwitch').hidden = !info.allow_register || info.first_user;
  $('acceptRow').hidden = $('regFields').hidden = !registering;
  $('loginFields').hidden = $('forgotBtn').hidden = registering;
  $('uLogin').required = !registering;
  $('authForm').hidden = false; $('recForm').hidden = true;
  $('uPass').autocomplete = registering ? 'new-password' : 'current-password';
  $('authLead').textContent = info.first_user
    ? 'Bienvenido. Crea la primera cuenta: será la del administrador.'
    : (registering ? 'Crea tu cuenta gratis. Solo pedimos lo justo.' : 'Registro libre de mascotas.');
  $('authErr').textContent = '';
}
$('authSwitch').onclick = () => { registering = !registering; setAuthMode(); };
let regKind = 'person';
$('uKind').onclick = e => {
  const b = e.target.closest('[data-kind]'); if (!b) return; regKind = b.dataset.kind;
  $('uKind').querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b));
  $('orgFields').hidden = regKind !== 'org';
  $('uNameLbl').innerHTML = esc(t(regKind === 'org' ? 'Tu nombre (la persona que lleva la cuenta)' : 'Tu nombre')) + ` <span class="opt">${esc(t('(solo el nombre, sin apellidos)'))}</span>`;
};
$('authForm').onsubmit = async e => {
  e.preventDefault();
  const body = {login: registering ? $('uUser').value.trim() : $('uLogin').value.trim(), password: $('uPass').value};
  try {
    let code = '';
    if (registering) {
      code = (await api('/api/register', {method: 'POST', body: {username: $('uUser').value.trim(), email: $('uEmail').value.trim(),
        password: body.password, name: $('uNameR').value, phone: $('uPhone').value, zone: $('uZone').value, accept: $('uAccept').checked,
        age_ok: $('uAge').checked, kind: regKind, org_name: $('uOrg').value,
        org_legal: $('uOrgLegal').value, org_cif: $('uOrgCif').value, org_reg: $('uOrgReg').value, org_zoo: $('uOrgZoo').value}})).recovery;
    }
    const adding = !$('authCancel').hidden;
    await api('/api/login', {method: 'POST', body});
    $('uPass').value = '';
    if (code) await showCode(code);
    if (adding) return location.reload();
    start();
  } catch (err) { $('authErr').textContent = err.message; }
};
// ---------- recuperar la cuenta ----------
function showCode(code, user) {
  $('codeVal').textContent = code;
  const msg = `${t('Código de recuperación de MascotasPanel')}${user || $('uUser').value ? ' (' + t('usuario') + ' ' + (user || $('uUser').value) + ')' : ''}: ${code}\n${location.origin}/panel`;
  codeMsg = msg;
  $('codeWa').href = 'https://wa.me/?text=' + encodeURIComponent(msg);
  $('codeTg').href = 'https://t.me/share/url?url=' + encodeURIComponent(location.origin + '/panel') + '&text=' + encodeURIComponent(msg);
  $('codeMail').href = 'mailto:?subject=' + encodeURIComponent(t('Código de recuperación de MascotasPanel')) + '&body=' + encodeURIComponent(msg);
  $('codeShare').hidden = !(navigator.share || window.MascotasPanelAndroid);
  $('codeUser').textContent = user ? t('Tu usuario es:') + ' ' + user : '';
  $('codeDlg').showModal();
  return new Promise(ok => { $('codeOk').onclick = () => { $('codeDlg').close(); ok(); }; });
}
$('codeDlg').addEventListener('cancel', e => e.preventDefault());
let codeMsg = '';
$('codeCopy').onclick = async () => { if (window.MascotasPanelAndroid) return window.MascotasPanelAndroid.copy(codeMsg); try { await navigator.clipboard.writeText(codeMsg); toast('Código copiado'); } catch (e) { toast($('codeVal').textContent); } };
$('codeShare').onclick = () => window.MascotasPanelAndroid ? window.MascotasPanelAndroid.share(codeMsg, 'MascotasPanel') : navigator.share({title: 'MascotasPanel', text: codeMsg}).catch(() => {});
$('codeTxt').onclick = () => download(new Blob([codeMsg + '\n'], {type: 'text/plain'}), 'mascotaspanel-codigo-recuperacion.txt');
$('forgotBtn').onclick = () => { $('authForm').hidden = true; $('recForm').hidden = false; $('authAccs').hidden = true; $('recErr').textContent = ''; $('rLogin').value = $('uLogin').value; };
$('recBack').onclick = () => { setAuthMode(); paintAuthAccounts(false); };
$('recForm').onsubmit = async e => {
  e.preventDefault(); $('recErr').textContent = '';
  try {
    const r = await api('/api/recover', {method: 'POST', body: {login: $('rLogin').value.trim(), code: $('rCode').value, password: $('rPass').value}});
    await showCode(r.recovery, r.username);
    $('uLogin').value = r.username; $('uPass').value = ''; $('recForm').reset();
    setAuthMode(); toast('Contraseña cambiada. Ya puedes entrar.');
  } catch (err) { $('recErr').textContent = err.message; }
};
$('logout').onclick = async () => { await api('/api/logout', {method: 'POST'}); location.reload(); };

// ---------- cambio rápido de usuario ----------
async function getAccounts() { try { return (await api('/api/accounts')).accounts || []; } catch (e) { return []; } }
const accInitial = n => esc(String(n || '?')[0].toUpperCase());
const accRow = (a, forget) => `<div class="accrow"><button type="button" class="ghost accpick" data-user="${esc(a.username)}" translate="no"><span class="accav">${accInitial(a.name)}</span><span>${esc(a.name)}<small>@${esc(a.username)}</small></span></button>` +
  (forget ? `<button type="button" class="ghost small accforget" data-forget="${esc(a.username)}" title="Quitar de este dispositivo" aria-label="Quitar de este dispositivo">✕</button>` : '') + `</div>`;
async function paintAuthAccounts(adding) {
  const list = adding || (info && info.first_user) ? [] : await getAccounts();
  $('authAccs').hidden = !list.length;
  $('authAccList').innerHTML = list.map(a => accRow(a, true)).join('');
}
async function switchAccount(username) {
  try { await api('/api/accounts/switch', {method: 'POST', body: {username}}); }
  catch (err) { showAuth(); $('authErr').textContent = err.message; $('uLogin').value = username; $('uPass').focus(); return; }
  location.reload();
}
$('authAccList').onclick = async e => {
  const f = e.target.closest('[data-forget]');
  if (f) { await api('/api/accounts/forget', {method: 'POST', body: {username: f.dataset.forget}}).catch(() => {}); return paintAuthAccounts(false); }
  const p = e.target.closest('[data-user]'); if (p) switchAccount(p.dataset.user);
};
$('authCancel').onclick = () => location.reload();
$('accBtn').onclick = async () => {
  const m = $('accMenu');
  if (!m.hidden) { m.hidden = true; $('accBtn').setAttribute('aria-expanded', 'false'); return; }
  const list = await getAccounts();
  $('accList').innerHTML = list.map(a => accRow(a, false)).join('');
  $('accSec').hidden = $('logoutAll').hidden = !list.length;
  m.hidden = false; $('accBtn').setAttribute('aria-expanded', 'true');
};
document.addEventListener('click', e => { if (!e.target.closest('.accwrap')) $('accMenu').hidden = true; });
$('accList').onclick = e => { const p = e.target.closest('[data-user]'); if (p) switchAccount(p.dataset.user); };
$('accAdd').onclick = () => showAuth(true);
$('accMenu').addEventListener('click', e => {
  const b = e.target.closest('[data-go]'); if (!b) return;
  $('accMenu').hidden = true; $('accBtn').setAttribute('aria-expanded', 'false');
  const go = b.dataset.go;
  if (['home', 'pets', 'inbox', 'parks', 'account', 'admin'].includes(go)) return showTab(go);
  showTab('account'); const el = $(go); el.scrollIntoView({block: 'start'}); if (go === 'pwSec') $('pwOld').focus();
});
$('logoutAll').onclick = async () => { await api('/api/logout', {method: 'POST', body: {all: true}}); location.reload(); };

// ---------- arranque ----------
async function start() {
  info = await api('/api/me');
  me = info.user;
  if (!me) return showAuth();
  $('auth').hidden = true; $('app').hidden = false;
  $('adminTab').hidden = !me.is_admin;
  if (me.is_admin) api('/api/admin/orgs').then(paintOrgAdm).catch(() => {});
  requestAnimationFrame(tabsHint);
  paintMe(); paintVersions(); newsIfUpdated(); buildHeadings(); paintBadge(info.unread || 0); loadAdopt(); transfers = info.transfers || []; paintTransfers();
  await loadPets();
  const m = /^#m(\d+)$/.exec(location.hash);
  const kh = /^#k(\d+)$/.exec(location.hash), kn = /^#nuevo=(-?[\d.]+),(-?[\d.]+)$/.exec(location.hash);
  if (kh) { showTab('parks'); kEdit(Number(kh[1])); }
  else if (kn) { showTab('parks'); setTimeout(() => kAddHere(Number(kn[1]), Number(kn[2])), 300); history.replaceState(null, '', '/panel#pipicanes'); }
  else if (m && pets.find(p => p.id === Number(m[1]))) openPet(Number(m[1])); else showTab(location.hash === '#pipicanes' ? 'parks' : location.hash === '#asociaciones' ? 'orgs' : location.hash === '#mascotas' ? 'pets' : me.is_admin ? 'admin' : 'home');
}
function paintMe() {
  $('goAdmin').hidden = !me.is_admin;
  $('accMe').innerHTML = `<b translate="no">${esc(me.name)}</b><small translate="no">@${esc(me.username)} · ${esc(me.email)}</small>` +
    (me.is_admin ? `<span class="tag">${esc(t('Administrador'))}</span>` : '');
  $('accName').textContent = me.name;
  const av = me.avatar || (me.org && me.org.logo) || '';
  $('accAv').innerHTML = av ? `<img src="${esc(av)}" alt="">` : '🐾'; $('accAv').classList.toggle('img', !!av);
  $('mAvatar').innerHTML = me.avatar ? `<img src="${esc(me.avatar)}" alt="">` : '<span>🐾</span>'; $('mAvatarDel').hidden = !me.avatar;
  $('mName').value = me.name; $('mUser').value = me.username; $('mEmail').value = me.email; $('mPhone').value = me.phone; $('mZone').value = me.zone;
  paintOrg();
}

$('mAvatarIn').onchange = async e => {
  const f = e.target.files[0]; e.target.value = ''; if (!f) return;
  try { const d = await cropPhoto(f, 512); if (!d) return; me = await api('/api/me/avatar', {method: 'POST', body: {data: d}}); paintMe(); toast('Foto guardada'); }
  catch (err) { toast(err.message); }
};
$('mAvatarDel').onclick = async () => { try { me = await api('/api/me/avatar', {method: 'POST', body: {data: ''}}); paintMe(); toast('Foto quitada'); } catch (err) { toast(err.message); } };

// ---------- asociación ----------
const isOrg = () => me && me.kind === 'org' && me.org;
function paintOrg() {
  $('orgSec').hidden = !isOrg(); if (!isOrg()) return;
  const o = me.org;
  $('orgState').textContent = t(o.verified ? '✔ Verificada' : 'Pendiente de verificar');
  $('orgState').className = 'tag ' + (o.verified ? 'ok' : 'wait');
  $('oName').value = o.name; $('oCity').value = o.city; $('oAbout').value = o.about; $('oWeb').value = o.web;
  $('oPhone').value = o.phone; $('oShowPhone').checked = o.show_phone; $('oWa').checked = o.whatsapp;
  $('oTg').value = o.telegram ? '@' + o.telegram : ''; $('oEmail').value = o.email; $('oShowEmail').checked = o.show_email;
  $('oLegal').value = o.legal_name || ''; $('oCif').value = o.cif || ''; $('oReg').value = o.reg_number || ''; $('oZoo').value = o.zoo_number || '';
  $('oLogo').innerHTML = o.logo ? `<img src="${esc(o.logo)}" alt="">` : '<span>🏡</span>'; $('oLogoDel').hidden = !o.logo;
  $('oPublic').hidden = !o.verified; $('oPublic').href = '/asociacion/' + o.id;
}
$('orgForm').onsubmit = async e => {
  e.preventDefault(); $('oErr').textContent = '';
  try {
    me.org = await api('/api/org', {method: 'PUT', body: {name: $('oName').value, city: $('oCity').value, about: $('oAbout').value, web: $('oWeb').value,
      phone: $('oPhone').value, show_phone: $('oShowPhone').checked, whatsapp: $('oWa').checked, telegram: $('oTg').value,
      email: $('oEmail').value, show_email: $('oShowEmail').checked,
      legal_name: $('oLegal').value, cif: $('oCif').value, reg_number: $('oReg').value, zoo_number: $('oZoo').value}});
    paintOrg(); toast('Guardado');
  } catch (err) { $('oErr').textContent = err.message; }
};
$('oLogoIn').onchange = async e => {
  const f = e.target.files[0]; e.target.value = ''; if (!f) return;
  try { const d = await cropPhoto(f, 512); if (!d) return; me.org = await api('/api/org/logo', {method: 'POST', body: {data: d}}); paintOrg(); toast('Logo guardado'); }
  catch (err) { toast(err.message); }
};
$('oLogoDel').onclick = async () => { me.org = await api('/api/org/logo', {method: 'POST', body: {data: ''}}); paintOrg(); };
$('oWa').onchange = () => { if ($('oWa').checked && !$('oPhone').value.trim()) { toast('Primero pon el teléfono de la asociación'); $('oWa').checked = false; } };

// ---------- carrusel «¿Me adoptas?» ----------
const CUTE = ['¿Me adoptas?', '¡Llévame a casa!', 'Busco una familia', '¿Damos un paseo juntos?', 'Te daré mucho amor', '¿Serás mi familia?', 'Quiero conocerte'];
let adoptList = [];
async function loadAdopt() {
  try { adoptList = await api('/api/adopt'); } catch (e) { adoptList = []; }
  paintAdopt('adoptStrip', 'adoptRow'); paintAdopt('dAdopt', 'dAdoptRow'); paintAdopt('hAdopt', 'hAdoptRow');
}
function paintAdopt(box, row) {
  $(box).hidden = !adoptList.length;
  $(row).innerHTML = adoptList.map((a, i) => `<a class="adc" href="${esc(a.url)}">
    ${a.photo ? `<img src="${esc(a.photo)}" alt="" loading="lazy">` : `<span class="nophoto">${spIcon(a.species)}</span>`}
    <span class="bubble">${esc(a.text && a.text.length <= 40 ? a.text : t(CUTE[i % CUTE.length]))}</span>
    <b translate="no">${esc(a.name)}</b><small translate="no">${esc(a.org)}</small></a>`).join('');
}

// ---------- pestañas ----------
document.querySelectorAll('#tabs button').forEach(b => b.onclick = () => showTab(b.dataset.tab));
function showTab(tab) {
  document.querySelectorAll('#tabs button').forEach(b => b.classList.toggle('sel', b.dataset.tab === tab || (tab === 'pet' && b.dataset.tab === 'pets')));
  document.querySelectorAll('[data-pane]').forEach(p => p.hidden = p.dataset.pane !== tab);
  if (tab === 'pets') { history.replaceState(null, '', '/panel#mascotas'); renderPets(); }
  if (tab === 'home') { history.replaceState(null, '', '/panel'); loadHome(); }
  if (tab === 'admin') loadAdmin();
  if (tab === 'inbox') loadInbox();
  if (tab === 'parks') { history.replaceState(null, '', '/panel#pipicanes'); loadParks(); }
  if (tab === 'orgs') { history.replaceState(null, '', '/panel#asociaciones'); loadOrgs(); }
  const sb = document.querySelector(`#tabs button[data-tab="${tab === 'pet' ? 'pets' : tab}"]`);
  if (sb) { const n = $('tabs'); n.scrollLeft = sb.offsetLeft - (n.clientWidth - sb.offsetWidth) / 2; tabsHint(); }
  scrollTo(0, 0);
}
// En el móvil las pestañas no caben: se deslizan de lado. Una flecha y un difuminado avisan de que hay más.
function tabsHint() {
  const n = $('tabs'), more = n.scrollWidth - n.clientWidth - n.scrollLeft > 4;
  n.classList.toggle('more', more); n.classList.toggle('less', n.scrollLeft > 4);
}
$('tabs').addEventListener('scroll', tabsHint, {passive: true}); addEventListener('resize', tabsHint);
$('tabsMore').onclick = () => $('tabs').scrollBy({left: $('tabs').clientWidth * 0.7, behavior: 'smooth'});

// ---------- asociaciones ----------
const legalLine = o => [o.legal_name && esc(o.legal_name), o.cif && 'CIF ' + esc(o.cif)].filter(Boolean).join(' · ');
const orgLogo = o => o.logo ? `<img class="orglogo" src="${esc(o.logo)}" alt="">` : '<span class="orglogo none">🏡</span>';
async function loadOrgs() {
  const list = await api('/api/orgs');
  $('orgList').innerHTML = list.map(o => `<a class="orgcard oc" href="/asociacion/${o.id}">${orgLogo(o)}<div>
    <h3 translate="no">${esc(o.name)}</h3><span class="tag ok">✔ ${esc(t('Verificada'))}</span>
    ${o.city ? `<p class="small">📍 ${esc(o.city)}</p>` : ''}${o.about ? `<p class="about">${esc(o.about.slice(0, 180))}${o.about.length > 180 ? '…' : ''}</p>` : ''}
    ${legalLine(o) ? `<p class="small">🏛️ ${legalLine(o)}</p>` : ''}
    ${[o.phone && '📞 ' + esc(o.phone), o.email && '✉️ ' + esc(o.email), o.web && '🌐 ' + esc(o.web.replace(/^https?:\/\//, ''))].filter(Boolean).map(x => `<p class="small">${x}</p>`).join('')}
    <p class="nadopt">💛 ${o.n_adopt} ${esc(t(o.n_adopt === 1 ? 'animal en adopción' : 'en adopción'))}</p></div></a>`).join('')
    || `<div class="empty"><b>${esc(t('Todavía no hay asociaciones verificadas'))}</b>${esc(t('¿Eres una asociación o protectora? Regístrate como asociación y, cuando la verifiquemos, saldrá aquí con sus animales.'))}</div>`;
  $('orgAdm').hidden = !me.is_admin;
  if (me.is_admin) paintOrgAdm(await api('/api/admin/orgs'));
}
function paintOrgAdm(all) {
  const wait = all.filter(o => !o.verified).length;
  $('oBadge').hidden = !wait; $('oBadge').textContent = wait;
  const dd = (k, v) => v ? `<dt>${esc(t(k))}</dt><dd translate="no">${esc(v)}</dd>` : '';
  $('orgAdmList').innerHTML = all.map(o => `<div class="orgrow${o.verified ? '' : ' wait'}">${orgLogo(o)}<div class="ot">
    <b translate="no">${esc(o.name)}</b> <span class="tag ${o.verified ? 'ok' : 'wait'}">${esc(t(o.verified ? '✔ Verificada' : 'Pendiente de verificar'))}</span>
    <dl>${dd('Nombre oficial', o.legal_name)}${dd('CIF', o.cif)}${dd('Registro de asociaciones', o.reg_number)}${dd('Núcleo zoológico', o.zoo_number)}
    ${dd('Localidad', o.city)}${dd('Lleva la cuenta', `${o.user.name} (@${o.user.username}) · ${o.user.email}`)}${dd('En adopción', String(o.n_adopt))}</dl>
    ${!o.legal_name && !o.cif && !o.reg_number ? `<p class="hint">⚠️ ${esc(t('No ha puesto datos legales. Pídeselos antes de verificarla.'))}</p>` : ''}</div>
    <div class="act"><button class="${o.verified ? 'ghost' : 'ok'} small" data-ov="${o.id}" data-a="${o.verified ? 'unverify' : 'verify'}">${esc(t(o.verified ? 'Quitar verificación' : '✅ Verificar'))}</button>
    ${o.verified ? `<a class="btn ghost small" href="/asociacion/${o.id}">${esc(t('Ver su página'))}</a>` : ''}</div></div>`).join('')
    || `<p class="hint">${esc(t('Todavía no se ha registrado ninguna asociación.'))}</p>`;
}
$('orgAdmList').onclick = async e => {
  const b = e.target.closest('[data-ov]'); if (!b) return;
  try { await api('/api/admin/users/' + b.dataset.ov, {method: 'POST', body: {action: b.dataset.a}});
    toast(b.dataset.a === 'verify' ? 'Asociación verificada' : 'Verificación quitada'); loadOrgs(); } catch (err) { toast(err.message); }
};

// ---------- lista de mascotas ----------
async function loadPets() { pets = await api('/api/pets'); }
const spName = s => t((SP[s] || SP.otro)[0]);
const spIcon = s => (SP[s] || SP.otro)[1];
function renderPets() {
  $('petList').innerHTML = pets.length ? pets.map(p => `<div class="pwrap"><button type="button" class="pcard${p.lost ? ' lostc' : ''}" data-pet="${p.id}">
    ${p.photo ? `<img class="im" src="${esc(p.photo)}" alt="">` : `<span class="im">${spIcon(p.species)}</span>`}
    <span class="tx"><b translate="no">${esc(p.name)}</b><small>${esc(spName(p.species))}${p.breed ? ' · <span translate="no">' + esc(p.breed) + '</span>' : ''}</small>
    ${p.lost ? `<span class="badge">${esc(t('Perdida'))}</span>` : ''}${p.hidden ? `<span class="badge">${esc(t('Oculta por el administrador'))}</span>` : ''}${p.transfer_to ? `<span class="badge">⏳ ${esc(t('Pasándola a'))} <span translate="no">${esc(p.transfer_to.name)}</span></span>` : ''}</span></button>` +
    (p.lost ? `<button type="button" class="found small" data-found="${p.id}">🏠 ${esc(t('¡Ya está en casa!'))}</button>`
            : `<button type="button" class="sos small" data-sos="${p.id}">🚨 ${esc(t('Se ha perdido'))}</button>`) + '</div>').join('')
    : `<div class="empty"><img class="emptyimg" src="/static/vacio-320.webp" srcset="/static/vacio-480.webp 2x" width="220" height="220" alt=""><b>${esc(t('Aún no has apuntado ninguna mascota'))}</b>${esc(t('Pulsa «+ Añadir mascota» y rellena su ficha con una foto.'))}</div>`;
}
$('petList').onclick = e => {
  const s = e.target.closest('[data-sos]'); if (s) return quickLost(Number(s.dataset.sos), true);
  const f = e.target.closest('[data-found]'); if (f) return quickLost(Number(f.dataset.found), false);
  const c = e.target.closest('[data-pet]'); if (c) openPet(Number(c.dataset.pet));
};
// Un toque: «Se ha perdido» sale al momento en la web pública y en el Inicio de todo el mundo; «Ya está en casa» lo quita
function askUnlost() {
  return new Promise(res => {
    const d = $('unlostDlg'); d.showModal();
    const end = v => { d.close(); res(v); };
    $('ulFound').onclick = () => end('found'); $('ulMistake').onclick = () => end('mistake'); $('ulCancel').onclick = () => end('');
    d.oncancel = e => { e.preventDefault(); end(''); };
  });
}
async function quickLost(id, lost) {
  const p = (P && P.id === id) ? P : pets.find(x => x.id === id); if (!p) return;
  let mistake = false;
  if (!lost) { const why = await askUnlost(); if (!why) return; mistake = why === 'mistake'; }
  if (lost && !confirm(t('¿Marcar a {n} como perdida? Saldrá al momento en la web pública y en el Inicio de todo el mundo.').replace('{n}', p.name))) return;
  try {
    const r = await api('/api/pets/' + id, {method: 'PUT', body: {lost, mistake}});
    const i = pets.findIndex(x => x.id === id); if (i >= 0) pets[i] = r;
    if (P && P.id === id) { setPet(r); paintLost(); paintSos(); drawPreview(); }
    renderPets();
    if (lost) {
      toast('Ya sale en la web para todo el mundo. Añade dónde se perdió y comparte el cartel.');
      if (!(P && P.id === id)) openPet(id);
      setTimeout(() => $('lostCard').scrollIntoView({behavior: 'smooth', block: 'start'}), 150);
    } else toast(mistake ? 'Aviso borrado. Ya no sale en ningún sitio.' : '¡Qué bien! Ya no sale como perdida.');
  } catch (err) { toast(err.message); }
}
function paintSos() {
  const b = $('sosBar'); b.hidden = !P; if (!P) return;
  b.classList.toggle('is-lost', !!P.lost);
  b.innerHTML = P.lost
    ? `<span>🚨 <b>${esc(t('Está perdida: sale en la web para todo el mundo'))}</b></span><button type="button" class="found" data-found="${P.id}">🏠 ${esc(t('¡Ya está en casa!'))}</button>`
    : `<span>${esc(t('Si se pierde, pulsa el botón: saldrá al momento en la web y en el Inicio de todos.'))}</span><button type="button" class="sos" data-sos="${P.id}">🚨 ${esc(t('Se ha perdido'))}</button>`;
}
$('sosBar').onclick = e => {
  const s = e.target.closest('[data-sos]'); if (s) return quickLost(Number(s.dataset.sos), true);
  const f = e.target.closest('[data-found]'); if (f) return quickLost(Number(f.dataset.found), false);
};
$('addPet').onclick = () => openPet(0);
$('backPets').onclick = () => showTab('pets');

// ---------- ficha ----------
const FIELDS = {name: 'pName', species: 'pSpecies', breed: 'pBreed', sex: 'pSex', size: 'pSize', age: 'pAge', chip: 'pChip',
  color: 'pColor', notes: 'pNotes', health: 'pHealth', contact2_name: 'pC2Name', contact2_phone: 'pC2Phone'};
let foreign = false;  // ficha de otra persona abierta por el administrador
function openPet(id, other) {
  P = other || pets.find(p => p.id === id) || null; foreign = !!other;
  newPhoto = undefined;
  for (const [k, el] of Object.entries(FIELDS)) $(el).value = P ? (P[k] || '') : (k === 'species' ? 'perro' : '');
  document.querySelector(`[name=pContact][value=${P && P.contact === 'lost' ? 'lost' : 'never'}]`).checked = true;
  $('pChipOk').checked = !!(P && P.chip_ok); $('pChipSearch').checked = !!(P && P.chip_search); paintChip();
  $('pPublic').checked = !!(P && P.public);
  $('pC2Ok').checked = !!(P && P.contact2_ok); paintC2();
  const orgOwner = foreign ? !!(P && P.owner_kind === 'org') : !!isOrg();
  $('adoptBox').hidden = !orgOwner; $('pAdopt').checked = !!(P && P.adopt); $('pAdoptText').value = P ? (P.adopt_text || '') : '';
  $('adoptHint').textContent = t(!foreign && isOrg() && !me.org.verified
    ? 'Tu asociación todavía no está verificada: tus animales en adopción se publicarán cuando el administrador la verifique.'
    : 'Sale en «Adopción», en el carrusel «¿Me adoptas?» y en la página de tu asociación, con tus datos de contacto públicos.');
  $('petTitle').textContent = P ? P.name + (foreign ? ` (${t('de')} ${P.owner})` : '') : t('Nueva mascota');
  $('pDelete').hidden = !P; $('petSide').hidden = !P; $('pErr').textContent = ''; paintSos();
  $('pSave').textContent = P ? 'Guardar' : 'Guardar y seguir';
  paintPhoto(P && P.photo); paintXfer();
  if (P) {
    $('cHead').value = P.sex === 'hembra' ? 'SE BUSCA · PERDIDA' : 'SE BUSCA · PERDIDO';
    const ok = P.contact === 'lost' && !!(ownerPhone() || P.contact2_phone);
    document.querySelector(`[name=cMode][value=${ok ? 'phone' : 'qr'}]`).checked = true;
    paintLost(); paintQr(); drawPreview(); history.replaceState(null, '', '/panel#m' + P.id);
  }
  showTab('pet');
}
function paintPhoto(src) {
  $('pPhoto').innerHTML = src ? `<img src="${esc(src)}" alt="">` : `<span>${spIcon($('pSpecies').value)}</span>`;
  $('pPhotoDel').hidden = !src; $('pPhotoLbl').textContent = t(src ? 'Cambiar foto' : 'Subir foto');
}
$('pSpecies').onchange = () => { if (!(newPhoto || (newPhoto === undefined && P && P.photo))) paintPhoto(''); };
// Encuadrar la foto al subirla: se mueve arrastrando y se acerca con la barra, la rueda o el
// pellizco. Sale cuadrada (900 px) y en JPEG. Devuelve null si se cancela.
function loadFile(file) {
  return new Promise((ok, ko) => {
    const img = new Image(), url = URL.createObjectURL(file);
    img.onload = () => {
      const k = Math.min(1, 2000 / Math.max(img.width, img.height)), c = document.createElement('canvas');
      c.width = Math.round(img.width * k); c.height = Math.round(img.height * k);
      const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height); g.drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url); ok(c);
    };
    img.onerror = () => { URL.revokeObjectURL(url); ko(new Error(t('No se puede leer esa imagen'))); };
    img.src = url;
  });
}
async function cropPhoto(file, OUT = 900) {
  const src = await loadFile(file), cv = $('cropCv'), W = cv.width, H = cv.height, range = $('cropZoom');
  const base = Math.max(W / src.width, H / src.height);
  let z = 1, ox, oy;
  { const dw = src.width * base, dh = src.height * base; ox = (W - dw) / 2; oy = dh > H ? -(dh - H) * 0.18 : (H - dh) / 2; }
  const draw = () => {
    const s = base * z, dw = src.width * s, dh = src.height * s;
    ox = Math.min(0, Math.max(W - dw, ox)); oy = Math.min(0, Math.max(H - dh, oy));
    const g = cv.getContext('2d'); g.clearRect(0, 0, W, H); g.drawImage(src, ox, oy, dw, dh);
  };
  const zoomAt = (nz, px = W / 2, py = H / 2) => {
    nz = Math.min(5, Math.max(1, nz)); const s0 = base * z, s1 = base * nz;
    ox = px - (px - ox) * s1 / s0; oy = py - (py - oy) * s1 / s0; z = nz; range.value = z; draw();
  };
  const pts = new Map(); let last = null, pinch = 0;
  const pos = e => { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) * W / r.width, (e.clientY - r.top) * H / r.height]; };
  cv.onpointerdown = e => { cv.setPointerCapture(e.pointerId); pts.set(e.pointerId, pos(e)); last = pos(e); };
  cv.onpointermove = e => {
    if (!pts.has(e.pointerId)) return;
    pts.set(e.pointerId, pos(e));
    if (pts.size === 2) {
      const [a, b] = [...pts.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]);
      if (pinch) zoomAt(z * d / pinch, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2);
      pinch = d; return;
    }
    const p = pos(e); ox += p[0] - last[0]; oy += p[1] - last[1]; last = p; draw();
  };
  cv.onpointerup = cv.onpointercancel = e => { pts.delete(e.pointerId); pinch = 0; last = pts.size ? [...pts.values()][0] : null; };
  cv.onwheel = e => { e.preventDefault(); const p = pos(e); zoomAt(z * (e.deltaY < 0 ? 1.08 : 1 / 1.08), p[0], p[1]); };
  range.value = 1; range.oninput = () => zoomAt(+range.value);
  draw(); $('cropDlg').showModal();
  const ok = await new Promise(res => {
    $('cropOk').onclick = () => res(true); $('cropNo').onclick = () => res(false);
    $('cropDlg').oncancel = e => { e.preventDefault(); res(false); };
  });
  $('cropDlg').close();
  if (!ok) return null;
  const o = document.createElement('canvas'); o.width = o.height = OUT;
  const k = OUT / W, s = base * z, g = o.getContext('2d');
  g.fillStyle = '#fff'; g.fillRect(0, 0, OUT, OUT); g.drawImage(src, ox * k, oy * k, src.width * s * k, src.height * s * k);
  return o.toDataURL('image/jpeg', 0.88);
}
$('pPhotoIn').onchange = async e => {
  const f = e.target.files[0]; e.target.value = ''; if (!f) return;
  try { const d = await cropPhoto(f); if (!d) return; newPhoto = d; paintPhoto(newPhoto); if (P) await savePhoto(); } catch (err) { toast(err.message); }
};
$('pPhotoDel').onclick = async () => { newPhoto = ''; paintPhoto(''); if (P) await savePhoto(); };
async function savePhoto() {
  try { setPet(await api(`/api/pets/${P.id}/photo`, {method: 'POST', body: {data: newPhoto}})); newPhoto = undefined; toast('Foto guardada'); drawPreview(); }
  catch (err) { toast(err.message); }
}
function setPet(p) {
  if (foreign) p = {...p, owner: P.owner, owner_phone: P.owner_phone, owner_kind: P.owner_kind};
  P = p; const i = pets.findIndex(x => x.id === p.id); if (i >= 0) pets[i] = p; else if (!foreign) pets.push(p);
}
const ownerPhone = () => foreign ? P.owner_phone : me.phone;
function paintChip() { $('chipBox').hidden = !$('pChip').value.trim(); }
function paintC2() { $('c2okRow').hidden = !$('pC2Phone').value.trim(); }
$('pC2Phone').oninput = paintC2;
$('pChip').oninput = paintChip;
$('petForm').onsubmit = async e => {
  e.preventDefault();
  const body = Object.fromEntries(Object.entries(FIELDS).map(([k, el]) => [k, $(el).value]));
  body.contact = document.querySelector('[name=pContact]:checked').value;
  body.public = $('pPublic').checked;
  body.chip_ok = $('pChipOk').checked; body.chip_search = $('pChipSearch').checked; body.contact2_ok = $('pC2Ok').checked;
  if (!$('adoptBox').hidden) { body.adopt = $('pAdopt').checked; body.adopt_text = $('pAdoptText').value; }
  try {
    const isNew = !P;
    setPet(await api(isNew ? '/api/pets' : '/api/pets/' + P.id, {method: isNew ? 'POST' : 'PUT', body}));
    if (isNew && newPhoto) await savePhoto();
    toast(isNew ? 'Ficha creada. Ya puedes sacar su QR y su cartel.' : 'Guardado');
    if ('adopt' in body) loadAdopt();
    openPet(P.id);
  } catch (err) { $('pErr').textContent = err.message; }
};
$('pDelete').onclick = async () => {
  if (!confirm(t('¿Borrar la ficha de') + ' ' + P.name + '? ' + t('Se borran sus datos y su foto, y su QR deja de funcionar.'))) return;
  await api('/api/pets/' + P.id, {method: 'DELETE'});
  pets = pets.filter(p => p.id !== P.id); P = null; toast('Ficha borrada'); showTab(foreign ? 'admin' : 'pets');
};

// ---------- perdida / encontrada ----------
// Mapa para marcar dónde se perdió (Leaflet + OpenStreetMap; el buscador usa Nominatim, gratis y sin clave)
let lmap = null, lpin = null, lpos = null;
const pinIcon = () => L.divIcon({className: 'pin', html: '<span></span>', iconSize: [34, 34], iconAnchor: [17, 34]});
function setPin(lat, lng, fly) {
  lpos = [Math.round(lat * 1000) / 1000, Math.round(lng * 1000) / 1000];
  if (lpin) lpin.setLatLng(lpos); else lpin = L.marker(lpos, {icon: pinIcon()}).addTo(lmap);
  if (fly) lmap.setView(lpos, 15);
  $('lClear').hidden = false;
}
// En un ordenador sin GPS la ubicación sale por internet y puede fallar muchos km: avisar para que lo corrija
function roughWarn(p) {
  const acc = p.coords.accuracy || 0;
  if (acc > 2000) toast(`${t('Ubicación aproximada (unos')} ${Math.round(acc / 1000)} km). ${t('Si no es ahí, busca el sitio o toca el mapa en el punto correcto.')}`);
}
async function geocode(q) {
  const r = await fetch('https://nominatim.openstreetmap.org/search?format=json&limit=1&accept-language=' + LANG + '&q=' + encodeURIComponent(q));
  const d = await r.json(); return d[0] ? [Number(d[0].lat), Number(d[0].lon)] : null;
}
function paintMap() {
  if (!window.L) return;
  if (!lmap) {
    lmap = L.map('lMap', {scrollWheelZoom: false});
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'}).addTo(lmap);
    lmap.on('click', e => setPin(e.latlng.lat, e.latlng.lng));
  }
  if (lpin) { lpin.remove(); lpin = null; }
  lpos = null; $('lClear').hidden = true;
  if (P.lost_lat != null) { setPin(P.lost_lat, P.lost_lng); lmap.setView(lpos, 15); }
  else {
    lmap.setView([40.2, -3.7], 5);  // España
    const z = P.lost_zone || me.zone;
    if (z) geocode(z).then(ll => { if (ll && !lpos) lmap.setView(ll, 13); }).catch(() => {});
  }
  setTimeout(() => lmap.invalidateSize(), 50);
}
$('lFind').onclick = async () => {
  const q = $('lSearch').value.trim(); if (!q) return;
  try { const ll = await geocode(q); if (ll) { lmap.setView(ll, 15); toast('Ahora toca el sitio exacto en el mapa'); } else toast('No encuentro ese sitio'); }
  catch (e) { toast('No se puede buscar ahora. Mueve el mapa con el dedo.'); }
};
$('lSearch').onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); $('lFind').onclick(); } };
$('lHere').onclick = () => {
  if (!navigator.geolocation) return toast('Este navegador no puede dar la ubicación');
  navigator.geolocation.getCurrentPosition(p => { setPin(p.coords.latitude, p.coords.longitude, true); roughWarn(p); },
    () => toast('No he podido saber dónde estás. Toca el mapa a mano.'), {enableHighAccuracy: true, timeout: 10000, maximumAge: 0});
};
$('lClear').onclick = () => { if (lpin) { lpin.remove(); lpin = null; } lpos = null; $('lClear').hidden = true; };
function paintLost() {
  $('lZone').value = P.lost_zone || ''; $('lNote').value = P.lost_note || ''; $('lReward').value = P.reward || '';
  $('lostCard').classList.toggle('is-lost', P.lost);
  $('lostBtn').textContent = t(P.lost ? 'Guardar cambios del aviso' : 'Marcar como perdida');
  $('foundBtn').hidden = !P.lost;
  $('lostState').textContent = P.lost
    ? t('Está marcada como perdida desde el') + ' ' + new Date(P.lost_at * 1000).toLocaleDateString(LANG === 'en' ? 'en-GB' : 'es-ES') + '. ' + t('Sale en la lista pública de mascotas perdidas.')
    : t('Si se pierde, márcala aquí: saldrá en la lista pública de mascotas perdidas y en su ficha se verá el aviso.');
  paintMap(); paintShare(); paintSos();
}
// ---------- compartir el aviso (Facebook, WhatsApp, Instagram…) ----------
function shareUrl() { return petUrl() + (LANG === 'en' ? '?lang=en' : ''); }
function shareText() {
  const sp = SP[P.species] || SP.otro, cap = v => v ? v[0].toUpperCase() + v.slice(1) : '';
  const bits = [t(sp[0]), (P.breed || '').trim(), P.sex ? t(cap(P.sex)) : '', (P.age || '').trim()].filter(Boolean).join(' · ');
  const name = (P.name || '').trim(), L = [];
  if (P.adopt) {
    L.push(`🏡 ${t('¿ME ADOPTAS?')} ${t('Soy')} ${name}`, `${sp[1]} ${bits}`);
    if ((P.adopt_text || '').trim()) L.push(`💛 ${P.adopt_text.trim()}`);
    if (isOrg()) L.push(`📍 ${t('Estoy en')} ${me.org.name}${me.org.city ? ' (' + me.org.city + ')' : ''}`);
    L.push(t('Conóceme y habla con mi asociación aquí:'), shareUrl(), '', t('¡Comparte para que encuentre una familia! 💛'));
  } else {
    L.push(`🚨 ${t('SE BUSCA')} · ${name.toUpperCase()}`, `${sp[1]} ${bits}`);
    if ((P.color || '').trim()) L.push(`🎨 ${P.color.trim()}`);
    if ((P.lost_zone || '').trim()) L.push(`📍 ${t('Se perdió en')}: ${P.lost_zone.trim()}`);
    if (P.lost_at) L.push(`📅 ${t('Desde el')} ${new Date(P.lost_at * 1000).toLocaleDateString(LANG === 'en' ? 'en-GB' : 'es-ES')}`);
    if ((P.lost_note || '').trim()) L.push(`📣 ${P.lost_note.trim()}`);
    if ((P.reward || '').trim()) L.push(`🎁 ${t('Recompensa')}: ${P.reward.trim()}`);
    L.push('', t('Si lo ves, entra aquí para avisar a su familia (no hace falta registrarse):'), shareUrl(), '', t('¡Por favor, comparte! Cada vez que se comparte está más cerca de casa 🙏'));
  }
  return L.join('\n');
}
function paintShare() {
  const on = !!P && !P.hidden && (P.lost || P.adopt);
  $('shareCard').hidden = !on; if (!on) return;
  $('shTitle').textContent = t(P.adopt ? 'Compartir para que encuentre familia' : 'Compartir el aviso');
  $('shText').value = shareText();
  updShareLinks();
}
function updShareLinks() {
  const txt = $('shText').value, url = shareUrl(), u = encodeURIComponent(url);
  const title = P.adopt ? `${t('¿Me adoptas?')} ${t('Soy')} ${P.name}` : `${t('SE BUSCA')}: ${P.name}`;
  $('shFb').href = 'https://www.facebook.com/sharer/sharer.php?u=' + u;
  $('shWa').href = 'https://wa.me/?text=' + encodeURIComponent(txt);
  $('shTg').href = 'https://t.me/share/url?url=' + u + '&text=' + encodeURIComponent(txt.replace(url, '').trim());
  $('shX').href = 'https://twitter.com/intent/tweet?url=' + u + '&text=' + encodeURIComponent(title);
  $('shMail').href = 'mailto:?subject=' + encodeURIComponent(title) + '&body=' + encodeURIComponent(txt);
}
async function copyText(v, ok) {
  if (AND && AND.copy) { AND.copy(v); return; }
  try { await navigator.clipboard.writeText(v); toast(ok); }
  catch (e) { const a = $('shText'); a.focus(); a.select(); try { document.execCommand('copy'); toast(ok); } catch (e2) { toast('Selecciona el texto y cópialo'); } }
}
$('shText').oninput = updShareLinks;
$('shCopyText').onclick = () => copyText($('shText').value, 'Texto copiado. Pégalo en tu post.');
$('shCopyLink').onclick = () => copyText(shareUrl(), 'Enlace copiado');
// Facebook no deja poner el texto: lo copiamos antes de abrirlo para pegarlo en el post
$('shFb').onclick = () => { copyText($('shText').value, 'Texto copiado: pégalo en el post de Facebook'); };
const instaPoster = () => poster(null, 'insta');
async function socialImage(size, app) {
  const cv = await poster(null, size);
  const b = await new Promise(ok => cv.toBlob(ok, 'image/jpeg', 0.92));
  await copyText($('shText').value, '');
  await download(b, fileName('jpg'));
  toast(`${t('Imagen descargada y texto copiado. Abre')} ${app}, ${t('sube la imagen y pega el texto.')}`);
}
$('shInsta').onclick = () => socialImage('insta', 'Instagram');
$('shTikTok').onclick = () => socialImage('story', 'TikTok');
$('shNative').hidden = !(window.MascotasPanelAndroid || (navigator.canShare && navigator.canShare({files: [new File([''], 'a.jpg', {type: 'image/jpeg'})]})));
$('shNative').onclick = async () => {
  const cv = await instaPoster(), b = await new Promise(ok => cv.toBlob(ok, 'image/jpeg', 0.92)), name = fileName('jpg'), text = $('shText').value;
  if (AND && AND.shareFile) return AND.shareFile(await toB64(b), name, 'image/jpeg', text);
  copyText(text, 'Texto copiado: pégalo si la app no lo pone sola');
  navigator.share({files: [new File([b], name, {type: 'image/jpeg'})], text}).catch(() => {});
};

$('lostBtn').onclick = async () => {
  try {
    const was = P.lost;
    setPet(await api('/api/pets/' + P.id, {method: 'PUT', body: {lost: true, lost_zone: $('lZone').value, lost_note: $('lNote').value, reward: $('lReward').value,
      lost_lat: lpos ? lpos[0] : null, lost_lng: lpos ? lpos[1] : null}}));
    paintLost(); drawPreview(); toast(was ? 'Guardado' : 'Marcada como perdida. Descarga el cartel y compártelo.');
  } catch (err) { toast(err.message); }
};
$('foundBtn').onclick = () => quickLost(P.id, false);

// ---------- QR ----------
const petUrl = () => P.url || location.origin + '/m/' + P.code;
function paintQr() {
  $('qrImg').src = `/qr/${P.code}.png?t=${Date.now()}`;
  $('qrUrl').textContent = $('qrUrl').href = petUrl();
  $('qrPng').href = `/qr/${P.code}.png`; $('qrPng').download = `qr-${P.name}.png`;
  $('qrSvg').href = `/qr/${P.code}.svg`; $('qrSvg').download = `qr-${P.name}.svg`;
}
$('copyUrl').onclick = async () => { if (AND) return AND.copy(petUrl()); try { await navigator.clipboard.writeText(petUrl()); toast('Enlace copiado'); } catch (e) { toast(petUrl()); } };

// ---------- cartel «Se busca» ----------
function buildHeadings() {
  $('cHead').innerHTML = Poster.HEADINGS.map(h => `<option value="${esc(h)}">${esc(t(h))}</option>`).join('');
}
const loadImg = src => new Promise((ok, ko) => { const i = new Image(); i.onload = () => ok(i); i.onerror = ko; i.src = src; });
async function poster(scale, size) {
  const qr = await loadImg(`/qr/${P.code}.png`);
  const qc = document.createElement('canvas'); qc.width = qr.naturalWidth; qc.height = qr.naturalHeight; qc.getContext('2d').drawImage(qr, 0, 0);
  const f = {photo: P.photo, name: P.name, species: P.species, breed: P.breed, sex: P.sex, age: P.age, color: P.color,
    reward: P.lost ? P.reward : '', phone: ownerPhone() || P.contact2_phone, owner: ownerPhone() ? (foreign ? P.owner : me.name) : P.contact2_name,
    phone2: ownerPhone() ? P.contact2_phone : '', name2: P.contact2_name};
  return Poster.drawPoster(f, qc, {size: size || $('cSize').value, heading: size === 'insta' && P.adopt ? '¿ME ADOPTAS?' : $('cHead').value, note: P.lost ? P.lost_note : (size === 'insta' && P.adopt ? P.adopt_text : ''), adopt: size === 'insta' && P.adopt,
    strips: $('cStrips').checked, showPhone: P.contact === 'lost' && document.querySelector('[name=cMode]:checked').value === 'phone'});
}
let drawT;
function drawPreview() {
  clearTimeout(drawT);
  drawT = setTimeout(async () => {
    if (!P) return;
    $('cStripsRow').hidden = $('cSize').value !== 'a4';
    const cv = await poster(); const pv = $('cPrev');
    pv.width = cv.width / 2; pv.height = cv.height / 2;
    pv.getContext('2d').drawImage(cv, 0, 0, pv.width, pv.height);
  }, 120);
}
['cHead', 'cSize', 'cStrips'].forEach(id => $(id).onchange = drawPreview);
// Elegir en el propio cartel si sale el teléfono: hace falta el consentimiento (se guarda en la ficha)
document.querySelectorAll('[name=cMode]').forEach(r => r.onchange = async () => {
  const qr = () => { document.querySelector('[name=cMode][value=qr]').checked = true; drawPreview(); };
  if (r.value === 'qr' || !r.checked) return drawPreview();
  if (!(ownerPhone() || P.contact2_phone)) { toast('Primero pon tu teléfono en Mi cuenta'); return qr(); }
  if (P.contact !== 'lost') {
    if (!confirm(t('Para poner tu teléfono en el cartel necesito tu consentimiento. También se verá en la ficha del QR, solo mientras esté perdida. ¿Das tu consentimiento?'))) return qr();
    try { setPet(await api('/api/pets/' + P.id, {method: 'PUT', body: {contact: 'lost'}}));
      document.querySelector('[name=pContact][value=lost]').checked = true; toast('Guardado'); }
    catch (err) { toast(err.message); return qr(); }
  }
  drawPreview();
});
const fileName = ext => `${t('se-busca')}-${(P.name || 'mascota').toLowerCase().replace(/[^a-z0-9áéíóúñü]+/gi, '-')}.${ext}`;
const AND = window.MascotasPanelAndroid;  // dentro de la app de Android
const toB64 = blob => new Promise(ok => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(',')[1]); r.readAsDataURL(blob); });
async function download(blob, name) {
  if (AND && AND.saveFile) return AND.saveFile(await toB64(blob), name, blob.type || 'application/octet-stream');
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name;
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}
$('cPdf').onclick = async () => {
  const cv = await poster();
  const jpg = await new Promise(r => cv.toBlob(r, 'image/jpeg', 0.92));
  const pdf = await PDF.makePdfPages([{jpg, w: cv.width, h: cv.height}], 'Se busca ' + P.name);
  download(pdf, fileName('pdf'));
};
$('cPng').onclick = async () => { const cv = await poster(); cv.toBlob(b => download(b, fileName('png')), 'image/png'); };

// ---------- avisos ----------
function paintBadge(n) { $('nBadge').textContent = n; $('nBadge').hidden = !n; }
async function loadInbox() {
  const list = await api('/api/messages');
  $('inboxList').innerHTML = list.length ? list.map(m => {
    const c = m.contact || '', tel = c.replace(/[^\d+]/g, '');
    const isPhone = /^\+?\d{6,}$/.test(tel), isMail = /@/.test(c);
    const wa = tel.replace(/\D/g, '').replace(/^(?=[6789]\d{8}$)/, '34');
    return `<article class="msg ${m.read ? '' : 'new'}"><h3><span translate="no">${esc(m.pet)}</span></h3><time>${new Date(m.created * 1000).toLocaleString(LANG === 'en' ? 'en-GB' : 'es-ES', {dateStyle: 'short', timeStyle: 'short'})}</time>
      ${m.text ? `<p translate="no">${esc(m.text)}</p>` : ''}${c ? `<p>${esc(t('Contacto:'))} <b translate="no">${esc(c)}</b></p>` : ''}
      <div class="row">${isPhone ? `<a class="btn small" href="tel:${esc(tel)}">📞 ${esc(t('Llamar'))}</a><a class="btn ghost small" href="https://wa.me/${esc(wa)}" target="_blank" rel="noopener">💬 WhatsApp</a>` : ''}
      ${isMail ? `<a class="btn small" href="mailto:${esc(c)}">✉️ ${esc(t('Contestar'))}</a>` : ''}
      ${m.lat != null ? `<a class="btn ghost small" href="https://www.google.com/maps/search/?api=1&query=${m.lat},${m.lng}" target="_blank" rel="noopener">📍 ${esc(t('Ver dónde estaba'))}</a>` : ''}
      <button class="ghost small" data-del="${m.id}">${esc(t('Borrar'))}</button></div></article>`;
  }).join('') : `<div class="empty"><b>${esc(t('No tienes avisos'))}</b>${esc(t('Ojalá no los necesites.'))}</div>`;
  if (list.some(m => !m.read)) { await api('/api/messages/read', {method: 'POST'}); paintBadge(0); }
}
$('inboxList').onclick = async e => {
  const b = e.target.closest('[data-del]'); if (!b) return;
  await api('/api/messages/' + b.dataset.del, {method: 'DELETE'}); loadInbox();
};

// ---------- mi cuenta ----------
$('meForm').onsubmit = async e => {
  e.preventDefault(); $('mErr').textContent = '';
  try {
    me = await api('/api/profile', {method: 'PUT', body: {name: $('mName').value, username: $('mUser').value, email: $('mEmail').value, phone: $('mPhone').value, zone: $('mZone').value}});
    paintMe(); toast('Guardado');
  } catch (err) { $('mErr').textContent = err.message; }
};
$('pwForm').onsubmit = async e => {
  e.preventDefault(); $('pwErr').textContent = '';
  try { await api('/api/password', {method: 'POST', body: {old: $('pwOld').value, new: $('pwNew').value}}); $('pwForm').reset(); toast('Contraseña cambiada'); }
  catch (err) { $('pwErr').textContent = err.message; }
};
$('newCode').onclick = async () => {
  const pw = prompt(t('Escribe tu contraseña para generar un código nuevo:'));
  if (!pw) return;
  try { await showCode((await api('/api/recovery/new', {method: 'POST', body: {password: pw}})).recovery, me.username); }
  catch (err) { toast(err.message); }
};
$('delAcc').onclick = async () => {
  const pw = prompt(t('Se borrará tu cuenta, todas tus mascotas y sus fotos, para siempre. Escribe tu contraseña para confirmarlo:'));
  if (!pw) return;
  try { await api('/api/account/delete', {method: 'POST', body: {password: pw}}); alert(t('Listo: tu cuenta y todos tus datos se han borrado.')); location.href = '/'; }
  catch (err) { toast(err.message); }
};

// ---------- administración ----------
let adminPets = [];
const fmtDate = s => s ? new Date(s * 1000).toLocaleDateString(LANG === 'en' ? 'en-GB' : 'es-ES') : '';
async function loadAdmin() {
  const [s, users, all] = await Promise.all([api('/api/admin/settings'), api('/api/admin/users'), api('/api/admin/pets')]);
  adminPets = all;
  const parks = adminParks = await api('/api/admin/parks');
  paintReview(parks, users);
  $('parksTbl').innerHTML = `<tr><th></th><th>${t('Nombre')}</th><th>${t('Apuntado por')}</th><th>${t('Estado')}</th><th></th></tr>` +
    parks.map(k => `<tr><td>${k.photo ? `<img src="${esc(k.photo)}" alt="">` : '🌳'}</td>
      <td><button type="button" class="linkbtn" data-view="${k.id}">${esc(k.name)}</button></td>
      <td translate="no">${k.osm ? 'OpenStreetMap' : esc(k.author || '—')}</td><td>${k.pending ? `<span class="tag wait">${esc(t('Por revisar'))}</span>` : k.hidden ? t('Oculto') : t('Visible')}</td>
      <td class="act">${k.pending ? `<button class="ok small" data-k="${k.id}" data-a="approve">✅ ${t('Aprobar')}</button>` : ''}<button class="ghost small" data-edk="${k.id}">✏️ ${t('Editar')}</button><button class="ghost small" data-k="${k.id}" data-a="${k.hidden ? 'show' : 'hide'}">${t(k.hidden ? 'Mostrar' : 'Ocultar')}</button>
      <button class="danger small" data-k="${k.id}" data-a="delete">${t('Borrar')}</button></td></tr>`).join('') ||
      `<tr><td colspan="5">${t('Todavía no hay ningún pipicán.')}</td></tr>`;
  $('sReg').checked = s.allow_register; $('sPublic').value = s.public_url || '';
  $('sTgToken').value = ''; $('sTgToken').placeholder = s.tg_token_set ? s.tg_token_hint + ' ' + t('(guardado)') : '123456789:ABC…';
  $('sTgChat').value = s.tg_chat || ''; $('sTgOff').hidden = !s.tg_token_set; $('sTgDaily').checked = s.tg_daily;
  $('sTgLink').hidden = true;
  $('sTgState').textContent = !s.tg_token_set ? '' : s.tg_chat ? t('✅ Conectado') : t('Falta conectar tu Telegram');
  if (s.tg_token_set && !s.tg_chat) tgLink();
  $('sLegalName').value = s.legal_name || ''; $('sLegalPlace').value = s.legal_place || ''; $('sLegalEmail').value = s.legal_email || '';
  $('legalWarn').hidden = !!(s.legal_name && s.legal_email);
  loadDash().catch(() => {});
  $('usersTbl').innerHTML = `<tr><th>${t('Nombre')}</th><th>${t('Usuario')}</th><th>${t('Correo')}</th><th>${t('Teléfono')}</th><th>${t('Zona')}</th><th>${t('Mascotas')}</th><th>${t('Alta')}</th><th></th></tr>` +
    users.map(u => `<tr><td translate="no">${u.kind === 'org' && u.org ? `🏡 <b>${esc(u.org.name)}</b> ${u.org.verified ? '✔' : `<span class="tag wait">${esc(t('Sin verificar'))}</span>`}<br>` : ''}${esc(u.name)}${u.is_admin ? ' ⭐' : ''}${u.status !== 'approved' ? ' 🚫' : ''}</td><td translate="no">${esc(u.username)}</td><td translate="no">${esc(u.email)}</td><td translate="no">${esc(u.phone)}</td>
      <td translate="no">${esc(u.zone)}</td><td>${u.pets}</td><td>${fmtDate(u.created)}</td><td class="act">${u.id === me.id ? '' :
      `${u.kind === 'org' && u.org ? `<button class="${u.org.verified ? 'ghost' : ''} small" data-u="${u.id}" data-a="${u.org.verified ? 'unverify' : 'verify'}">${t(u.org.verified ? 'Quitar verificación' : 'Verificar')}</button>` : ''}
       <button class="ghost small" data-u="${u.id}" data-a="${u.status === 'approved' ? 'disable' : 'approve'}">${t(u.status === 'approved' ? 'Bloquear' : 'Desbloquear')}</button>
       <button class="ghost small" data-u="${u.id}" data-a="${u.is_admin ? 'unadmin' : 'admin'}">${t(u.is_admin ? 'Quitar admin' : 'Hacer admin')}</button>
       <button class="ghost small" data-u="${u.id}" data-a="password">${t('Contraseña nueva')}</button>
       <button class="danger small" data-u="${u.id}" data-a="delete">${t('Borrar')}</button>`}</td></tr>`).join('');
  $('petsTbl').innerHTML = `<tr><th></th><th>${t('Nombre')}</th><th>${t('Animal')}</th><th>${t('Dueño/a')}</th><th>${t('Estado')}</th><th></th></tr>` +
    all.map(p => `<tr><td>${p.photo ? `<img src="${esc(p.photo)}" alt="">` : spIcon(p.species)}</td><td translate="no"><a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.name)}</a></td>
      <td>${esc(spName(p.species))}</td><td translate="no">${esc(p.owner)}</td><td>${p.hidden ? t('Oculta') : p.lost ? t('Perdida') : t('En casa')}</td>
      <td class="act"><button class="ghost small" data-p="${p.id}" data-a="edit">${t('Editar')}</button>
      <button class="ghost small" data-p="${p.id}" data-a="${p.hidden ? 'show' : 'hide'}">${t(p.hidden ? 'Mostrar' : 'Ocultar')}</button>
      <button class="danger small" data-p="${p.id}" data-a="delete">${t('Borrar')}</button></td></tr>`).join('');
}
$('usersTbl').onclick = async e => {
  const b = e.target.closest('[data-u]'); if (!b) return;
  if (b.dataset.a === 'delete' && !confirm(t('¿Borrar esta cuenta con todas sus mascotas?'))) return;
  const body = {action: b.dataset.a};
  if (b.dataset.a === 'password') { body.password = prompt(t('Contraseña nueva para esta persona (mínimo 8 caracteres). Díselo tú en persona o por teléfono:')); if (!body.password) return; }
  try { await api('/api/admin/users/' + b.dataset.u, {method: 'POST', body}); loadAdmin(); loadAdopt(); if (body.password) toast('Contraseña cambiada'); } catch (err) { toast(err.message); }
};
$('petsTbl').onclick = async e => {
  const b = e.target.closest('[data-p]'); if (!b) return;
  if (b.dataset.a === 'edit') return openPet(+b.dataset.p, adminPets.find(p => p.id === +b.dataset.p));
  if (b.dataset.a === 'delete' && !confirm(t('¿Borrar esta ficha?'))) return;
  try { await api('/api/admin/pets/' + b.dataset.p, {method: 'POST', body: {action: b.dataset.a}}); loadAdmin(); await loadPets(); } catch (err) { toast(err.message); }
};
$('admForm').onsubmit = async e => {
  e.preventDefault(); $('sErr').textContent = '';
  try { await api('/api/admin/settings', {method: 'PUT', body: {allow_register: $('sReg').checked, public_url: $('sPublic').value,
    tg_token: $('sTgToken').value, tg_chat: $('sTgChat').value, tg_daily: $('sTgDaily').checked, legal_name: $('sLegalName').value, legal_place: $('sLegalPlace').value,
    legal_email: $('sLegalEmail').value}}); toast('Guardado'); await loadPets(); loadAdmin(); }
  catch (err) { $('sErr').textContent = err.message; }
};

// ---------- versiones y novedades ----------
// iPhone / iPad (los iPad nuevos dicen que son un Mac con pantalla táctil): la APK no sirve
const IOS = /iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
const md = s => esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/`(.+?)`/g, '<code>$1</code>');
const newer = (a, b) => { const x = a.split('.').map(Number), y = b.split('.').map(Number); for (let i = 0; i < 3; i++) { if ((x[i] || 0) !== (y[i] || 0)) return (x[i] || 0) > (y[i] || 0); } return false; };
function paintVersions() {
  $('vChip').textContent = 'v' + info.version;
  const av = (() => { try { return AND && AND.version ? AND.version() : ''; } catch (e) { return ''; } })();
  $('verLine').innerHTML = `<b translate="no">Web ${esc(info.version)}</b>` + (av ? ` · <b translate="no">App ${esc(av)}</b>`
    : IOS ? `<br><small>${t('La app es solo para Android. En iPhone o iPad, guarda esta web en la pantalla de inicio: botón Compartir → «Añadir a pantalla de inicio».')}</small>`
    : ` · <a href="https://github.com/iaonlineapps/mascotaspanel/raw/main/android/dist/MascotasPanel.apk" target="_blank" rel="noopener">${t('Descargar la app (solo Android)')}</a>`);
  $('accApp').hidden = !!av;  // dentro de la app ya no hace falta
  $('accReload').hidden = !AND; $('accReload').onclick = () => location.reload();  // en la app no hay botón de recargar
  $('accApp').onclick = e => { if (IOS) { e.preventDefault(); toast('La app es solo para Android. En iPhone o iPad, guarda esta web en la pantalla de inicio: botón Compartir → «Añadir a pantalla de inicio».'); } };
  $('appNewsBtn').hidden = !(AND && AND.news); $('appCheckBtn').hidden = !(AND && AND.checkUpdate);
  $('pFoot').innerHTML = `<span translate="no">MascotasPanel</span> ${esc(info.version)} · <a href="#" id="footNews">${t('Novedades')}</a> · <a href="/privacidad${LANG === 'en' ? '?lang=en' : ''}">${t('Privacidad')}</a> · <a href="https://github.com/iaonlineapps/mascotaspanel" target="_blank" rel="noopener">GitHub</a>` +
    `<span class="madeby">💛 ${t('Proyecto sin ánimo de lucro, gratis y sin anuncios')} · 🤖 ${t('App creada con ayuda de inteligencia artificial (IA)')} · © 2026 <span translate="no">IA Online Apps</span> · ${t('Uso personal no comercial')}</span>`;
  $('footNews').onclick = e => { e.preventDefault(); showNews(); };
}
async function showNews(since) {
  const d = await api('/api/novedades?lang=' + LANG);
  const list = since ? d.novedades.filter(n => newer(n.version, since)) : d.novedades;
  if (!list.length) return;
  $('newsTitle').textContent = since ? t('MascotasPanel se ha actualizado a la') + ' ' + d.version : t('Novedades de MascotasPanel');
  $('newsBody').innerHTML = list.map(n => `<h3>${t('Versión')} ${esc(n.version)}${n.version === d.version ? ` <span class="tag">${t('la tuya')}</span>` : ''}</h3>
    <ul>${n.items.map(i => `<li>${md(i)}</li>`).join('')}</ul>`).join('');
  $('news').showModal();
}
function newsIfUpdated() {
  const k = 'mascotaspanel-visto'; let seen = null;
  try { seen = localStorage.getItem(k); localStorage.setItem(k, info.version); } catch (e) {}
  if (seen && seen !== info.version && newer(info.version, seen)) showNews(seen).catch(() => {});
}
$('newsBtn').onclick = () => showNews();
$('vChip').onclick = () => showNews();
$('newsClose').onclick = () => $('news').close();

// ---------- idioma ----------
document.querySelectorAll('[data-lang]').forEach(b => {
  b.classList.toggle('on', b.dataset.lang === LANG);
  b.onclick = () => { if (AND && AND.setLang) try { AND.setLang(b.dataset.lang); } catch (e) {} setLang(b.dataset.lang); };
});
if (AND && AND.setLang) try { AND.setLang(LANG); } catch (e) {}
$('appNewsBtn').onclick = () => AND.news();
$('appCheckBtn').onclick = () => AND.checkUpdate();
// Compartir el cartel (en la app con WhatsApp, Telegram…; en el móvil con el menú de compartir)
$('cShare').hidden = !(AND || (navigator.canShare && navigator.canShare({files: [new File([''], 'a.png', {type: 'image/png'})]})));
$('cShare').onclick = async () => {
  const cv = await poster(), b = await new Promise(ok => cv.toBlob(ok, 'image/png')), name = fileName('png');
  const text = `${$('cHead').value}: ${P.name} · ${petUrl()}`;
  if (AND && AND.shareFile) return AND.shareFile(await toB64(b), name, 'image/png', text);
  navigator.share({files: [new File([b], name, {type: 'image/png'})], text}).catch(() => {});
};

$('iGo').onclick = async () => {
  const q = $('iPlace').value.trim(); if (!q) return toast('Escribe una ciudad o un barrio');
  $('iGo').disabled = true; $('iMsg').textContent = t('Buscando en OpenStreetMap…');
  try {
    const ll = await geocode(q); if (!ll) throw new Error(t('No encuentro ese sitio'));
    const r = await api('/api/admin/parks/import', {method: 'POST', body: {lat: ll[0], lng: ll[1], km: +$('iKm').value}});
    $('iMsg').textContent = `${t('Encontrados')}: ${r.found} · ${t('nuevos')}: ${r.added}`; loadAdmin();
  } catch (err) { $('iMsg').textContent = err.message; }
  $('iGo').disabled = false;
};
// Comprobar un pipicán antes de aprobarlo: foto, mapa, quién lo apuntó y enlaces a Google Maps y Street View
let adminParks = [], pdmap = null, pdpin = null;
function parkView(id) {
  const k = adminParks.find(x => x.id === id); if (!k) return;
  const ll = `${k.lat},${k.lng}`;
  $('pdName').textContent = k.name;
  $('pdBody').innerHTML = (k.photo ? `<img class="pdphoto" src="${esc(k.photo)}" alt="">` : `<p class="hint">${t('No tiene foto.')}</p>`)
    + `<dl class="pdinfo"><dt>${t('Estado')}</dt><dd>${k.pending ? `<span class="tag wait">${esc(t('Por revisar'))}</span>` : k.hidden ? t('Oculto') : t('Visible')}</dd>`
    + `<dt>${t('Apuntado por')}</dt><dd translate="no">${k.osm ? 'OpenStreetMap' : esc(k.author || '—')}</dd>`
    + `<dt>${t('Fecha')}</dt><dd>${fmtDate(k.created)}</dd>`
    + (k.notes ? `<dt>${t('Cómo es')}</dt><dd>${esc(k.notes)}</dd>` : '')
    + `<dt>${t('Coordenadas')}</dt><dd translate="no">${ll}</dd></dl>`;
  $('pdLinks').innerHTML = `<a class="btn small" href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${ll}" target="_blank" rel="noopener">🚶 Street View</a>`
    + `<a class="btn ghost small" href="https://www.google.com/maps/search/?api=1&query=${ll}" target="_blank" rel="noopener">🗺️ Google Maps</a>`
    + `<a class="btn ghost small" href="https://www.google.com/maps/@${ll},120m/data=!3m1!1e3" target="_blank" rel="noopener">🛰️ ${t('Satélite')}</a>`
    + `<a class="btn ghost small" href="https://www.openstreetmap.org/?mlat=${k.lat}&mlon=${k.lng}#map=18/${k.lat}/${k.lng}" target="_blank" rel="noopener">OpenStreetMap</a>`;
  $('pdActs').innerHTML = (k.pending ? `<button type="button" class="ok" data-k="${k.id}" data-a="approve">✅ ${t('Aprobar')}</button>` : '')
    + `<button type="button" class="ghost" data-edk="${k.id}">✏️ ${t('Editar')}</button>`
    + `<button type="button" class="danger" data-k="${k.id}" data-a="delete">${t('Borrar')}</button>`
    + `<button type="button" class="ghost" id="pdClose">${t('Cerrar')}</button>`;
  $('parkDlg').showModal();
  if (window.L) {
    if (!pdmap) { pdmap = L.map('pdMap', {scrollWheelZoom: false});
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'}).addTo(pdmap); }
    pdmap.setView([k.lat, k.lng], 17);
    if (pdpin) pdpin.setLatLng([k.lat, k.lng]); else pdpin = L.marker([k.lat, k.lng], {icon: L.divIcon({className: 'pin park', html: '<span></span>', iconSize: [34, 34], iconAnchor: [17, 34]})}).addTo(pdmap);
    setTimeout(() => pdmap.invalidateSize(), 60);
  }
}
$('parkDlg').onclick = async e => {
  if (e.target.id === 'pdClose') return $('parkDlg').close();
  const ed = e.target.closest('[data-edk]'); if (ed) { $('parkDlg').close(); showTab('parks'); return kEdit(+ed.dataset.edk); }
  const b = e.target.closest('[data-k]'); if (!b) return;
  if (b.dataset.a === 'delete' && !confirm(t('¿Borrar este pipicán?'))) return;
  try { await api('/api/admin/parks/' + b.dataset.k, {method: 'POST', body: {action: b.dataset.a}}); $('parkDlg').close();
    toast(b.dataset.a === 'approve' ? 'Aprobado: ya sale en el mapa' : 'Borrado'); if ($('dReview').closest('[data-pane]').hidden) loadReview(); else loadAdmin(); } catch (err) { toast(err.message); }
};
$('parksTbl').onclick = async e => {
  const v = e.target.closest('[data-view]'); if (v) return parkView(+v.dataset.view);
  const ed = e.target.closest('[data-edk]'); if (ed) { showTab('parks'); return kEdit(+ed.dataset.edk); }
  const b = e.target.closest('[data-k]'); if (!b) return;
  if (b.dataset.a === 'delete' && !confirm(t('¿Borrar este pipicán?'))) return;
  try { await api('/api/admin/parks/' + b.dataset.k, {method: 'POST', body: {action: b.dataset.a}}); loadAdmin(); } catch (err) { toast(err.message); }
};

$('sTgTest').onclick = async () => {
  $('sErr').textContent = '';
  try {
    await api('/api/admin/settings', {method: 'PUT', body: {tg_token: $('sTgToken').value, tg_chat: $('sTgChat').value}});
    await api('/api/admin/telegram/test', {method: 'POST'}); toast('Mensaje enviado. Mira tu Telegram'); loadAdmin();
  } catch (err) { $('sErr').textContent = err.message; }
};
async function tgLink() {
  try { const r = await api('/api/admin/telegram/link', {method: 'POST'}); $('sTgLink').href = r.url; $('sTgLink').hidden = false;
    $('sTgState').textContent = '@' + r.bot; } catch (err) { $('sTgState').textContent = err.message; }
}
$('sTgSave').onclick = async () => {
  $('sErr').textContent = '';
  if (!$('sTgToken').value.trim()) return toast('Pega primero el token que te da @BotFather');
  try { await api('/api/admin/settings', {method: 'PUT', body: {tg_token: $('sTgToken').value}}); toast('Token guardado'); await loadAdmin(); tgLink(); }
  catch (err) { $('sErr').textContent = err.message; }
};
$('sTgLink').onclick = () => {  // cuando vuelve de Telegram, mira si ya está conectado
  let n = 0; const iv = setInterval(async () => {
    const s = await api('/api/admin/settings').catch(() => null);
    if (s && s.tg_chat) { clearInterval(iv); toast('¡Telegram conectado!'); loadAdmin(); } else if (++n > 40) clearInterval(iv);
  }, 3000);
};
$('sTgDaily').onchange = () => api('/api/admin/settings', {method: 'PUT', body: {tg_daily: $('sTgDaily').checked}}).then(() => toast('Guardado')).catch(err => toast(err.message));
$('sTgOff').onclick = async () => { await api('/api/admin/settings', {method: 'PUT', body: {tg_clear: true}}); toast('Avisos quitados'); loadAdmin(); };

// Panel de control del administrador: totales, altas del periodo, gráfico, últimas fichas y actividad
const ago = s => { const m = Math.round((Date.now() / 1000 - s) / 60);
  if (m < 1) return t('ahora'); if (m < 60) return `${t('hace')} ${m} min`; const h = Math.round(m / 60);
  if (h < 24) return `${t('hace')} ${h} h`; const d = Math.round(h / 24); return d === 1 ? t('ayer') : `${t('hace')} ${d} ${t('días')}`; };
let dRange = 30, dData = null;

// ---------- pasar una ficha a otra cuenta ----------
function paintXfer() {
  $('xferBox').hidden = !P; if (!P) return;
  $('xferBox').open = !!P.transfer_to; $('xErr').textContent = ''; $('xTo').value = '';
  $('xHint').textContent = t(me.is_admin
    ? 'Se pasa todo tal cual: la foto, el QR (la placa sigue valiendo), el cartel y sus avisos. Como eres administrador, se pasa al momento.'
    : 'Se pasa todo tal cual: la foto, el QR (la placa sigue valiendo), el cartel y sus avisos. La otra cuenta tiene que aceptarlo.');
  const w = P.transfer_to;
  $('xWait').hidden = !w; $('xTo').parentNode.hidden = !!w;
  if (w) $('xState').innerHTML = `⏳ ${esc(t('Esperando a que la acepte'))} <b translate="no">${esc(w.name)}</b> (@<span translate="no">${esc(w.username)}</span>).`;
}
$('xSend').onclick = async () => {
  const to = $('xTo').value.trim(); $('xErr').textContent = '';
  if (!to) return $('xErr').textContent = t('Escribe el usuario o el correo de la otra cuenta');
  if (me.is_admin && !confirm(t('¿Pasar esta ficha ahora a esa cuenta? Dejará de estar en la tuya.'))) return;
  try {
    const r = await api(`/api/pets/${P.id}/transfer`, {method: 'POST', body: {to}});
    if (r.moved) { await loadPets(); toast(`${t('Ficha pasada a')} ${r.to}`); return foreign ? showTab('admin') : showTab('pets'); }
    Object.assign(P, r); const i = pets.findIndex(x => x.id === r.id); if (i >= 0) pets[i] = r; P = r; paintXfer();
    toast(t('Listo. Cuando la acepte, pasará a su cuenta.'));
  } catch (err) { $('xErr').textContent = err.message; }
};
$('xTo').onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); $('xSend').click(); } };
$('xCancel').onclick = async () => {
  try { const r = await api(`/api/pets/${P.id}/transfer`, {method: 'POST', body: {cancel: true}}); const i = pets.findIndex(x => x.id === r.id); if (i >= 0) pets[i] = r; P = r; paintXfer(); }
  catch (err) { toast(err.message); }
};
let transfers = [];
function paintTransfers() {
  const html = transfers.map(x => `<div class="trcard">${x.photo ? `<img src="${esc(x.photo)}" alt="">` : `<span class="lim">${spIcon(x.species)}</span>`}
    <span class="trtx">🎁 <b translate="no">${esc(x.from)}</b> ${esc(t('quiere pasarte la ficha de'))} <b translate="no">${esc(x.name)}</b>.<small>${esc(t('Se queda con su foto, su QR y sus avisos.'))}</small></span>
    <span class="row"><button type="button" class="ok" data-tr="${x.pet}" data-yes="1">${esc(t('Aceptar'))}</button><button type="button" class="ghost" data-tr="${x.pet}">${esc(t('No, gracias'))}</button></span></div>`).join('');
  $('trHome').innerHTML = html; $('trPets').innerHTML = html;
}
document.querySelectorAll('.trlist').forEach(el => el.onclick = async e => {
  const b = e.target.closest('[data-tr]'); if (!b) return;
  try {
    const r = await api('/api/transfers/' + b.dataset.tr, {method: 'POST', body: {accept: !!b.dataset.yes}});
    transfers = r.transfers; paintTransfers();
    if (b.dataset.yes) { await loadPets(); renderPets(); toast(t('¡Ya es tuya! La tienes en «Mis mascotas».')); if (!$('hKpis').closest('[data-pane]').hidden) loadHome(); }
  } catch (err) { toast(err.message); }
});

// ---------- lo que espera a que el administrador lo apruebe (pipicanes y asociaciones) ----------
function paintReview(parks, users) {
  const kp = parks.filter(k => k.pending), og = users.filter(u => u.kind === 'org' && u.org && !u.org.verified && u.status === 'approved');
  const rows = kp.map(k => `<div class="rrow">${k.photo ? `<img src="${esc(k.photo)}" alt="">` : '<span class="lim">🌳</span>'}
      <span class="rtx"><button type="button" class="linkbtn" data-view="${k.id}">🌳 ${esc(k.name)}</button><small>${esc(t('Pipicán'))} · <span translate="no">${esc(k.author || '—')}</span> · ${ago(k.created)}</small>${k.dupe_of ? `<small class="dupwarn">⚠️ ${esc(t('Posible duplicado de'))} «<span translate="no">${esc(k.dupe_of.name)}</span>»</small>` : ''}</span>
      <span class="row"><button type="button" class="ok small" data-rk="${k.id}">✅ ${esc(t('Aprobar'))}</button><button type="button" class="ghost small" data-view="${k.id}">👀 ${esc(t('Ver'))}</button></span></div>`)
    .concat(og.map(u => `<div class="rrow">${u.org.logo ? `<img src="${esc(u.org.logo)}" alt="">` : '<span class="lim">🏡</span>'}
      <span class="rtx"><b translate="no">🏡 ${esc(u.org.name)}</b><small>${esc(t('Asociación'))} · <span translate="no">${esc(u.name)} · ${esc(u.email)}${u.org.city ? ' · ' + esc(u.org.city) : ''}</span> · ${ago(u.created)}</small></span>
      <span class="row"><button type="button" class="ok small" data-ru="${u.id}">✔ ${esc(t('Verificar'))}</button>${u.org.web ? `<a class="btn ghost small" href="${esc(u.org.web)}" target="_blank" rel="noopener">🌐 Web</a>` : ''}</span></div>`));
  document.querySelectorAll('.review').forEach(box => {
    box.hidden = !rows.length;
    box.querySelector('[data-rn]').textContent = rows.length;
    box.querySelector('[data-rl]').innerHTML = rows.join('');
  });
}
async function loadReview() {
  if (!me.is_admin) return;
  try { const [parks, users] = await Promise.all([api('/api/admin/parks'), api('/api/admin/users')]); adminParks = parks; paintReview(parks, users); } catch (e) { /* nada */ }
}
document.querySelectorAll('.review').forEach(box => box.onclick = async e => {
  const v = e.target.closest('[data-view]'); if (v) return parkView(+v.dataset.view);
  const k = e.target.closest('[data-rk]'), u = e.target.closest('[data-ru]'); if (!k && !u) return;
  try {
    if (k) { await api('/api/admin/parks/' + k.dataset.rk, {method: 'POST', body: {action: 'approve'}}); toast('Aprobado: ya sale en el mapa'); }
    else { await api('/api/admin/users/' + u.dataset.ru, {method: 'POST', body: {action: 'verify'}}); toast('Asociación verificada'); }
    if (!$('dReview').closest('[data-pane]').hidden) loadAdmin(); else loadReview();
  } catch (err) { toast(err.message); }
});

// ---------- inicio de cada persona: lo que se está buscando ----------
let wanted = [], hSp = '';
async function loadHome() {
  $('hHello').textContent = `${t('Hola')}, ${me.name}`;
  $('hSub').textContent = t(me.is_admin ? 'Tu Inicio con tu cuenta: tus mascotas y tus avisos. Los datos de toda la web están en «Administración».'
    : 'Esto es lo que pasa ahora en MascotasPanel.');
  try { wanted = await api('/api/lost'); } catch (e) { wanted = []; }
  const mine = pets.filter(p => p.lost).length, unread = Number($('nBadge').hidden ? 0 : $('nBadge').textContent) || 0;
  const kpi = (k, color, label, big, line, go) => `<button type="button" class="kpi" data-go="${go}"><div><span class="kl">${esc(t(label))}</span><b>${big}</b><span class="ks">${line}</span></div><span class="ki" style="background:${color}">${svgIcon(k)}</span></button>`;
  $('hKpis').innerHTML =
    kpi('lost', '#dc2626', 'Se buscan ahora', wanted.length, esc(t('perros, gatos y más')), 'wanted')
    + kpi('pets', 'var(--or)', 'Mis mascotas', pets.length, mine ? `<span class="down">${mine} ${esc(t(mine === 1 ? 'perdida' : 'perdidas'))}</span>` : esc(t('ver y cambiar sus fichas')), 'pets')
    + kpi('mail', '#2563eb', 'Avisos sin leer', unread, esc(t(unread ? 'alguien te ha escrito' : 'todo leído')), 'inbox')
    + kpi('adopt', '#d97706', 'En adopción', adoptList.length, esc(t('buscan una familia')), 'adopt');
  paintWanted(); loadReview(); loadRecent();
}
// Últimos registros: solo el nombre y el animal (sin foto, dueño, zona ni enlace) y el total por especie
async function loadRecent() {
  let r; try { r = await api('/api/registered'); } catch (e) { return; }
  $('hRecent').hidden = !r.total;
  $('hCounts').innerHTML = `<span><b>${r.total}</b> ${esc(t('en total'))}</span><span>🐶 ${esc(t('Perros'))}: <b>${r.dogs}</b></span>` +
    `<span>🐱 ${esc(t('Gatos'))}: <b>${r.cats}</b></span><span>🐾 ${esc(t('Otros'))}: <b>${r.others}</b></span>`;
  const items = r.recent.map(x => `<span class="tk">${spIcon(x.species)} ${esc(t('Se ha registrado'))} <b translate="no">${esc(x.name)}</b></span>`).join('');
  // se repite una vez para que la cinta dé la vuelta sin saltos (la copia no la leen los lectores de pantalla)
  $('hTicker').innerHTML = items + `<span aria-hidden="true" class="tkcopy">${items}</span>`;
  $('hTicker').style.animationDuration = Math.max(20, r.recent.length * 4) + 's';
}
function paintWanted() {
  document.querySelectorAll('#hSp [data-s]').forEach(b => b.classList.toggle('on', b.dataset.s === hSp));
  const list = wanted.filter(w => !hSp || (hSp === 'otro' ? !['perro', 'gato'].includes(w.species) : w.species === hSp));
  $('hWanted').innerHTML = list.length ? list.map(w => `<a class="wcard${w.mine ? ' mine' : ''}" href="${esc(w.url)}">
    ${w.photo ? `<img src="${esc(w.photo)}" alt="" loading="lazy">` : `<span class="nophoto">${spIcon(w.species)}</span>`}
    <span class="wtag">🚨 ${esc(t('Se busca'))}</span>
    <span class="wtx"><b translate="no">${esc(w.name)}</b><small>${esc(spName(w.species))}${w.breed ? ' · <span translate="no">' + esc(w.breed) + '</span>' : ''}</small>
    ${w.zone ? `<small>📍 <span translate="no">${esc(w.zone)}</span></small>` : ''}<small>${w.at ? ago(w.at) : ''}${w.reward ? ' · 🎁 ' + esc(w.reward) : ''}</small>
    ${w.mine ? `<span class="tag">${esc(t('Es tuya'))}</span>` : `<small class="wsh">📣 ${esc(t('Ábrela para avisar o compartirla'))}</small>`}</span></a>`).join('')
    : `<div class="empty"><b>${esc(t('Ahora mismo no se busca ninguna'))}</b>${esc(t('¡Buena señal! Cuando alguien pierda a su mascota, saldrá aquí.'))}</div>`;
}
$('hSp').onclick = e => { const b = e.target.closest('[data-s]'); if (b) { hSp = b.dataset.s; paintWanted(); } };
$('hKpis').onclick = e => {
  const b = e.target.closest('[data-go]'); if (!b) return;
  const g = b.dataset.go;
  if (g === 'wanted') return document.querySelector('.wanted').scrollIntoView({behavior: 'smooth', block: 'start'});
  if (g === 'adopt') return adoptList.length ? $('hAdopt').scrollIntoView({behavior: 'smooth', block: 'start'}) : open('/adopta', '_blank');
  showTab(g);
};
const ICONS = {
  pets: '<path d="M12 21c-3 0-6-1.6-6-4.3C6 14 9 11 12 11s6 3 6 5.7c0 2.7-3 4.3-6 4.3z"/><circle cx="5" cy="9" r="2"/><circle cx="19" cy="9" r="2"/><circle cx="9" cy="5" r="2"/><circle cx="15" cy="5" r="2"/>',
  users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.6-3.6 3.3-6 6.5-6s5.9 2.4 6.5 6"/><circle cx="17" cy="9" r="2.5"/><path d="M16 14.2c2.8-.4 5 1.6 5.5 4.8"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
  lost: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l5 5"/>',
  adopt: '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/><path d="M12 18s-3.5-2.1-3.5-4.2A1.8 1.8 0 0 1 12 13a1.8 1.8 0 0 1 3.5.8C15.5 15.9 12 18 12 18z"/>',
  parks: '<path d="M12 3c3.5 0 6 2.6 6 5.6 0 3-2.6 5.4-6 5.4s-6-2.4-6-5.4C6 5.6 8.5 3 12 3z"/><path d="M12 14v7M8 21h8"/>'};
const svgIcon = k => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[k]}</svg>`;
const s2color = () => ['azul', 'morado', 'turquesa'].includes(Tema.get().color) ? '#ea580c' : (document.documentElement.dataset.theme === 'dark' || (!document.documentElement.dataset.theme && matchMedia('(prefers-color-scheme: dark)').matches) ? '#3b82f6' : '#2563eb');
function delta(p) {
  if (p.before == null) return '';
  if (!p.before) return p.now ? `<span class="up">↑ ${p.now}</span> ${t('nuevas')}` : `<span class="flat">${t('sin cambios')}</span>`;
  const pc = Math.round((p.now - p.before) / p.before * 100);
  return `<span class="${pc > 0 ? 'up' : pc < 0 ? 'down' : 'flat'}">${pc > 0 ? '↑' : pc < 0 ? '↓' : '='} ${Math.abs(pc)}%</span> ${t('vs periodo anterior')}`;
}
const rangeName = () => ({7: t('últimos 7 días'), 30: t('últimos 30 días'), 90: t('últimos 3 meses'), 365: t('último año'), 0: t('desde el principio')})[dRange];
async function loadDash() {
  const d = dData = await api('/api/admin/dashboard?dias=' + dRange), T = d.totals, P = d.period;
  $('dHello').textContent = `${t('Hola')}, ${me.name}`;
  $('dSub').textContent = `${t('Resumen de MascotasPanel')} · ${rangeName()}`;
  document.querySelectorAll('#dRange [data-d]').forEach(b => b.classList.toggle('on', +b.dataset.d === dRange));
  const kpi = (k, color, label, big, line) => `<div class="kpi"><div><span class="kl">${esc(t(label))}</span><b>${big}</b><span class="ks">${line}</span></div><span class="ki" style="background:${color}">${svgIcon(k)}</span></div>`;
  $('dKpis').innerHTML =
    kpi('pets', 'var(--or)', 'Fichas en total', T.pets, `+${P.pets.now} ${t('en el periodo')}` + (P.pets.before != null ? ' · ' + delta(P.pets) : ''))
    + kpi('users', '#2563eb', 'Personas registradas', T.users, `+${P.users.now} ${t('en el periodo')}` + (P.users.before != null ? ' · ' + delta(P.users) : ''))
    + kpi('lost', '#dc2626', 'Perdidas ahora', T.lost, `${P.lost.now} ${t('perdidas en el periodo')} · ${P.messages.now} ${t('avisos')}`)
    + kpi('parks', '#16a34a', 'Pipicanes', T.parks, `+${P.parks.now} ${t('en el periodo')}` + (T.parks_pending ? ` · <span class="down">${T.parks_pending} ${t('por revisar')}</span>` : ''))
    + kpi('adopt', '#d97706', 'En adopción', T.adopt, `${T.orgs} ${t('asociaciones')}` + (T.orgs_pending ? ` · <span class="down">${T.orgs_pending} ${t('sin verificar')}</span>` : ''));
  $('dChTitle').textContent = `${t('Fichas nuevas')} (${rangeName()})`;
  $('dChBig').textContent = P.pets.now;
  $('dChSub').textContent = `${P.users.now} ${t('personas nuevas')} · ${T.public} ${t('en el registro público')} · ${T.chips} ${t('con microchip')}`;
  drawChart();
  $('dLatest').innerHTML = d.latest.map(p => `<div class="lrow">${p.photo ? `<img src="${esc(p.photo)}" alt="">` : `<span class="lim">${spIcon(p.species)}</span>`}
    <span><b translate="no">${esc(p.name)}</b><small>${esc(spName(p.species))} · <span translate="no">${esc(p.owner)}</span></small></span>
    <span class="lr">${p.lost ? `<span class="badge">${esc(t('Perdida'))}</span>` : ''}<small>${ago(p.created)}</small></span></div>`).join('')
    || `<p class="hint">${t('Todavía no hay ninguna ficha.')}</p>`;
  const maxS = Math.max(1, ...d.species.map(x => x.n));
  $('dSpecies').innerHTML = d.species.map(x => `<div class="hb"><span>${spIcon(x.species)} ${esc(spName(x.species))}</span><span class="hbt"><i style="width:${x.n / maxS * 100}%"></i></span><b>${x.n}</b></div>`).join('')
    || `<p class="hint">${t('Todavía no hay ninguna ficha.')}</p>`;
  const ico = {user: '👤', pet: '🐾', lost: '🔎', park: '🌳', found: '✉️', org: '🏡'};
  const say = e => e.kind === 'user' ? `${t('Se ha registrado')} <b translate="no">${esc(e.name)}</b> <small translate="no">@${esc(e.user)}</small>`
    : e.kind === 'pet' ? `${t('Nueva ficha:')} <b translate="no">${esc(e.name)}</b> (${esc(spName(e.species).toLowerCase())}) ${t('de')} <span translate="no">${esc(e.owner)}</span>`
    : e.kind === 'lost' ? `<b translate="no">${esc(e.name)}</b> ${t('está marcada como perdida')}`
    : e.kind === 'park' ? `${t('Nuevo pipicán:')} <b>${esc(e.name)}</b>`
    : e.kind === 'org' ? `${t('Nueva asociación:')} <b translate="no">${esc(e.name)}</b>`
    : `${t('Alguien ha avisado a la familia de')} <b translate="no">${esc(e.name)}</b>`;
  $('dFeed').innerHTML = d.events.slice(0, 14).map(e => `<li><span class="ic">${ico[e.kind]}</span><span>${say(e)}</span><time>${ago(e.t)}</time></li>`).join('')
    || `<li>${t('Todavía no ha pasado nada.')}</li>`;
}
function bucketName(k) {
  const loc = LANG === 'en' ? 'en-GB' : 'es-ES';
  if (dData.step === 'day') return new Date(k + 'T12:00').toLocaleDateString(loc, {day: 'numeric', month: 'short'});
  if (dData.step === 'week') return t('semana') + ' ' + k.split('-W')[1];
  return new Date(k + '-15T12:00').toLocaleDateString(loc, {month: 'short', year: 'numeric'});
}
function drawChart() {
  const box = $('dChart'), S = dData.series, W = Math.max(280, box.clientWidth), H = 240, pl = 34, pr = 10, pt = 12, pb = 26;
  const max = Math.max(1, ...S.map(x => Math.max(x.pets, x.users)));
  const nice = max <= 4 ? 4 : Math.ceil(max / 4) * 4, n = S.length;
  const X = i => pl + (n === 1 ? (W - pl - pr) / 2 : i * (W - pl - pr) / (n - 1)), Y = v => pt + (H - pt - pb) * (1 - v / nice);
  const path = k => S.map((x, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)},${Y(x[k]).toFixed(1)}`).join('');
  const c2 = s2color();
  const grid = [0, 1, 2, 3, 4].map(g => { const v = nice * g / 4, y = Y(v).toFixed(1);
    return `<line x1="${pl}" x2="${W - pr}" y1="${y}" y2="${y}" class="gl"/><text x="${pl - 6}" y="${+y + 4}" text-anchor="end" class="ax">${v}</text>`; }).join('');
  const labs = [0, Math.floor((n - 1) / 2), n - 1].filter((v, i, a) => a.indexOf(v) === i)
    .map((i, k, a) => `<text x="${X(i)}" y="${H - 6}" text-anchor="${k === 0 && a.length > 1 ? 'start' : k === a.length - 1 && a.length > 1 ? 'end' : 'middle'}" class="ax">${esc(bucketName(S[i].key))}</text>`).join('');
  box.innerHTML = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(t('Fichas nuevas'))}">
    <defs><linearGradient id="gPets" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--or)" stop-opacity=".32"/><stop offset="1" stop-color="var(--or)" stop-opacity="0"/></linearGradient></defs>
    ${grid}<path d="${path('pets')}L${X(n - 1)},${Y(0)}L${X(0)},${Y(0)}Z" fill="url(#gPets)"/>
    <path d="${path('users')}" fill="none" stroke="${c2}" stroke-width="2" stroke-linejoin="round"/>
    <path d="${path('pets')}" fill="none" stroke="var(--or)" stroke-width="2" stroke-linejoin="round"/>
    ${labs}<line id="dX" class="xh" y1="${pt}" y2="${H - pb}" x1="-9" x2="-9"/>
    <circle id="dP1" r="4.5" fill="var(--or)" stroke="var(--card)" stroke-width="2" cx="-9" cy="-9"/><circle id="dP2" r="4.5" fill="${c2}" stroke="var(--card)" stroke-width="2" cx="-9" cy="-9"/>
    <rect x="${pl}" y="0" width="${W - pl - pr}" height="${H}" fill="transparent" id="dHit"/></svg><div class="tip" id="dTip" hidden></div>`;
  const hit = $('dHit'), tip = $('dTip');
  const show = ev => {
    const r = hit.getBoundingClientRect(), x = (ev.touches ? ev.touches[0].clientX : ev.clientX) - r.left;
    const i = Math.max(0, Math.min(n - 1, Math.round(x / ((W - pl - pr) / Math.max(1, n - 1))))), p = S[i];
    $('dX').setAttribute('x1', X(i)); $('dX').setAttribute('x2', X(i));
    $('dP1').setAttribute('cx', X(i)); $('dP1').setAttribute('cy', Y(p.pets)); $('dP2').setAttribute('cx', X(i)); $('dP2').setAttribute('cy', Y(p.users));
    tip.hidden = false;
    tip.innerHTML = `<b>${esc(bucketName(p.key))}</b><span><i style="background:var(--or)"></i>${esc(t('Mascotas'))} <b>${p.pets}</b></span><span><i style="background:${c2}"></i>${esc(t('Personas'))} <b>${p.users}</b></span>`;
    const tx = X(i) + 12 + tip.offsetWidth > W ? X(i) - tip.offsetWidth - 12 : X(i) + 12; tip.style.left = tx + 'px'; tip.style.top = '8px';
  };
  hit.onmousemove = show; hit.ontouchstart = hit.ontouchmove = show;
  hit.onmouseleave = () => { tip.hidden = true; $('dX').setAttribute('x1', -9); $('dX').setAttribute('x2', -9); $('dP1').setAttribute('cx', -9); $('dP2').setAttribute('cx', -9); };
  document.querySelector('.dchart .legend i:last-of-type') && (document.querySelectorAll('.dchart .legend i')[1].style.background = c2);
}
$('dRange').onclick = e => { const b = e.target.closest('[data-d]'); if (!b) return; dRange = +b.dataset.d; loadDash().catch(err => toast(err.message)); };
addEventListener('resize', () => { if (dData && !$('dChart').closest('[hidden]')) drawChart(); });

// ---------- busca tu pipicán ----------
// Lee el GPS que guarda el móvil dentro de la foto (EXIF). Después la foto se redibuja en un canvas,
// que la sube sin esos datos.
function exifGps(buf) {
  const v = new DataView(buf);
  if (v.getUint16(0) !== 0xFFD8) return null;
  let o = 2;
  while (o + 4 < v.byteLength) {
    const mk = v.getUint16(o), len = v.getUint16(o + 2);
    if (mk === 0xFFE1 && v.getUint32(o + 4) === 0x45786966) {
      const t0 = o + 10, le = v.getUint16(t0) === 0x4949;
      const u16 = p => v.getUint16(t0 + p, le), u32 = p => v.getUint32(t0 + p, le);
      const ifd = (p, tag) => { const n = u16(p); for (let i = 0; i < n; i++) { const e = p + 2 + i * 12; if (u16(e) === tag) return e; } return 0; };
      const g = ifd(u32(4), 0x8825); if (!g) return null;
      const gp = u32(g + 8);
      const rat = e => { const p = u32(e + 8), r = []; for (let i = 0; i < 3; i++) r.push(u32(p + i * 8) / (u32(p + i * 8 + 4) || 1)); return r[0] + r[1] / 60 + r[2] / 3600; };
      const ref = e => String.fromCharCode(v.getUint8(t0 + e + 8));
      const la = ifd(gp, 2), laR = ifd(gp, 1), lo = ifd(gp, 4), loR = ifd(gp, 3);
      if (!la || !lo) return null;
      let lat = rat(la), lng = rat(lo);
      if (laR && ref(laR) === 'S') lat = -lat; if (loR && ref(loR) === 'W') lng = -lng;
      return (lat || lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180 ? [lat, lng] : null;
    }
    if ((mk & 0xFF00) !== 0xFF00) break;
    o += 2 + len;
  }
  return null;
}
function shrinkPhoto(file, max) {
  return new Promise((ok, ko) => {
    const img = new Image(), url = URL.createObjectURL(file);
    img.onload = () => {
      const k = Math.min(1, max / Math.max(img.naturalWidth, img.naturalHeight));
      const c = document.createElement('canvas'); c.width = Math.round(img.naturalWidth * k); c.height = Math.round(img.naturalHeight * k);
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height); URL.revokeObjectURL(url);
      ok(c.toDataURL('image/jpeg', 0.85));
    };
    img.onerror = () => { URL.revokeObjectURL(url); ko(new Error(t('No se puede abrir esa imagen'))); };
    img.src = url;
  });
}
let kmap = null, kpin = null, kpos = null, kphoto = '';
let kRough = false, kFromLink = false, kChecked = false, kDistinct = false;  // kChecked: ya ha dicho «Sí, es aquí»
  // kFromLink: el sitio lo ha dado un enlace de Google Maps, y eso manda sobre el GPS
  // el punto viene de una ubicación aproximada (ordenador sin GPS): avisar antes de guardar
function kSetPin(lat, lng, fly, rough) {
  kpos = [Math.round(lat * 1e5) / 1e5, Math.round(lng * 1e5) / 1e5]; kRough = !!rough; kAskReset();
  if (kpin) kpin.setLatLng(kpos);
  else {
    kpin = L.marker(kpos, {draggable: true, autoPan: true, icon: L.divIcon({className: 'pin park', html: '<span></span>', iconSize: [34, 34], iconAnchor: [17, 34]})}).addTo(kmap);
    kpin.on('dragend', () => { const ll = kpin.getLatLng(); kSetPin(ll.lat, ll.lng); });
  }
  if (fly) kmap.setView(kpos, 17);
  $('kWhere').textContent = t(kRough ? '⚠️ Ubicación aproximada: busca tu pueblo arriba, arrastra el punto o toca el sitio exacto en el mapa.'
    : 'Marcado. Si no es el sitio exacto, arrastra el punto o toca otra vez en el mapa.');
  $('kWhere').classList.toggle('warn', kRough);
}
// Ya hay uno igual (a menos de 50 m o con el mismo nombre): se enseña y no se crea otro, salvo que diga que es distinto
let kDupMark = null;
function kShowDupes(list) {
  $('kErr').innerHTML = `<div class="dupes"><b>⚠️ ${esc(t('Ese pipicán ya está apuntado'))}</b>` + list.map(k =>
    `<div class="srow">🌳 <span><b>${esc(k.name)}</b><small>${k.dist} m${k.pending ? ' · ⏳ ' + esc(t('Pendiente de aprobar')) : ''}</small></span>` +
    `<button type="button" class="ghost small" data-dview="${k.lat},${k.lng}">👀 ${esc(t('Ver'))}</button></div>`).join('') +
    `<p class="hint">${esc(t('No hace falta apuntarlo otra vez. Si de verdad es otro pipicán distinto, pulsa el botón y lo revisará el administrador.'))}</p>` +
    `<button type="button" class="ghost small" id="kDistinctBtn">${esc(t('Es otro pipicán distinto'))}</button></div>`;
  const k = list[0]; kDupMark && kDupMark.remove();
  kDupMark = L.circleMarker([k.lat, k.lng], {radius: 12, color: '#dc2626', weight: 3, fillOpacity: .15}).addTo(kmap);
  kmap.fitBounds([[k.lat, k.lng], kpos], {padding: [50, 50], maxZoom: 18});
  $('kErr').scrollIntoView({behavior: 'smooth', block: 'center'});
}
$('kErr').onclick = e => {
  const v = e.target.closest('[data-dview]');
  if (v) { const [a, b] = v.dataset.dview.split(',').map(Number); kmap.setView([a, b], 18); $('kMap').scrollIntoView({behavior: 'smooth', block: 'center'}); return; }
  if (e.target.id === 'kDistinctBtn') { kDistinct = true; $('kErr').textContent = ''; kDupMark && kDupMark.remove(); $('kForm').requestSubmit(); }
};
// «Añadir pipicán aquí» desde un mapa: abre el formulario con el sitio ya puesto y busca su dirección
function kAddHere(lat, lng) {
  kReset(); kPaintMap();
  setTimeout(() => { kSetPin(lat, lng, true); kNear(lat, lng); $('kForm').scrollIntoView({behavior: 'smooth', block: 'start'}); }, 120);
}
function kAskReset() {
  kChecked = false; kDistinct = false; $('kWhere').classList.remove('ask');
  $('kSave').textContent = t(kEditId ? 'Guardar cambios' : 'Guardar pipicán');
}
function kPaintMap() {
  if (!window.L) return;
  if (!kmap) {
    kmap = L.map('kMap', {scrollWheelZoom: false});
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'}).addTo(kmap);
    kmap.on('click', e => kSetPin(e.latlng.lat, e.latlng.lng));
    kmap.setView([40.2, -3.7], 5);
    if (me.zone) geocode(me.zone).then(ll => { if (ll && !kpos) kmap.setView(ll, 13); }).catch(() => {});
  }
  setTimeout(() => kmap.invalidateSize(), 50);
}
function kReset() {
  kEditId = null; $('kTitle').textContent = t('Apuntar un pipicán'); $('kSave').textContent = t('Guardar pipicán');
  $('kCancel').hidden = $('kDel').hidden = true;
  $('kForm').reset(); kphoto = ''; $('kPhoto').innerHTML = '<span>🌳</span>'; $('kErr').textContent = '';
  kFromLink = false; kAskReset(); kSugg(''); if (kpin) { kpin.remove(); kpin = null; } kpos = null; $('kWhere').textContent = t('Toca el mapa en el sitio exacto del pipicán.');
}
// Mapa con todos los pipicanes aprobados (los de todo el mundo) y, en gris, los míos que esperan revisión
let kall = null, kallLayer = null, kallMe = null;
const kAddPop = (lat, lng, here) => `<div class="pop">${here ? `<b>📍 ${esc(t('Estás aquí'))}</b><small>${esc(t('¿Estás en un pipicán que no sale en el mapa?'))}</small>` : ''}` +
  `<button type="button" class="small" data-addhere="${lat.toFixed(5)},${lng.toFixed(5)}">➕ ${esc(t('Añadir pipicán aquí'))}</button></div>`;
function kAllPaint(all, mine) {
  if (!window.L || !$('kAllMap')) return;
  if (!kall) {
    kall = L.map('kAllMap', {scrollWheelZoom: false});
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'}).addTo(kall);
    $('kAllMap').addEventListener('click', e => {
      const b = e.target.closest('[data-edk]'); if (b) return kEdit(+b.dataset.edk);
      const a = e.target.closest('[data-addhere]'); if (a) { kall.closePopup(); const [x, y] = a.dataset.addhere.split(',').map(Number); kAddHere(x, y); }
    });
    // tocar el mapa en un sitio vacío: ofrecer apuntar ahí un pipicán
    kall.on('click', e => L.popup().setLatLng(e.latlng).setContent(kAddPop(e.latlng.lat, e.latlng.lng)).openOn(kall));
  }
  if (kallLayer) kallLayer.remove();
  kallLayer = L.layerGroup().addTo(kall);
  const waiting = mine.filter(k => k.pending), pts = [];
  const add = (k, wait) => {
    const canEdit = me.is_admin || mine.some(x => x.id === k.id);
    L.marker([k.lat, k.lng], {icon: L.divIcon({className: 'pin park' + (wait ? ' wait' : ''), html: '<span></span>', iconSize: [34, 34], iconAnchor: [17, 34], popupAnchor: [0, -30]})})
      .addTo(kallLayer).bindPopup(`<div class="pop">${k.photo ? `<img src="${esc(k.photo)}" alt="">` : ''}<b>${esc(k.name)}</b>${wait ? `<small>⏳ ${esc(t('Pendiente de aprobar'))}</small>` : ''}${k.notes ? `<small>${esc(k.notes)}</small>` : ''}` +
        `<a href="https://www.google.com/maps/dir/?api=1&destination=${k.lat},${k.lng}" target="_blank" rel="noopener">🧭 ${esc(t('Cómo llegar'))} →</a>` +
        (canEdit ? `<button type="button" class="small ghost" data-edk="${k.id}">✏️ ${esc(t('Editar'))}</button>` : '') + '</div>');
    pts.push([k.lat, k.lng]);
  };
  all.forEach(k => add(k, false)); waiting.forEach(k => add(k, true));
  $('kAllN').textContent = all.length ? '(' + all.length + ')' : '';
  setTimeout(() => {
    kall.invalidateSize();
    if (!pts.length) kall.setView([40.2, -3.7], 5);
    else if (pts.length === 1) kall.setView(pts[0], 15); else kall.fitBounds(pts, {padding: [30, 30], maxZoom: 15});
  }, 60);
}
$('kNew').onclick = () => { kReset(); $('kForm').scrollIntoView({behavior: 'smooth', block: 'start'}); };
$('kAllMe').onclick = () => {
  if (!navigator.geolocation || !kall) return toast('Este navegador no puede dar la ubicación');
  navigator.geolocation.getCurrentPosition(p => {
    const ll = [p.coords.latitude, p.coords.longitude], rough = (p.coords.accuracy || 0) > 2000;
    kall.setView(ll, rough ? 11 : 17); roughWarn(p);
    if (kallMe) kallMe.remove();
    kallMe = L.circleMarker(ll, {radius: 9, color: '#2563eb', fillColor: '#2563eb', fillOpacity: .9}).addTo(kall);
    if (!rough) kallMe.bindPopup(kAddPop(ll[0], ll[1], true)).openPopup();
  },
    () => toast('No he podido saber dónde estás. Toca el mapa a mano.'), {enableHighAccuracy: true, timeout: 10000, maximumAge: 0});
};
async function loadParks() {
  kPaintMap();
  const [mine, all] = await Promise.all([api('/api/parks/mine'), api('/api/parks').catch(() => [])]);
  kAllPaint(all, mine);
  $('kList').innerHTML = mine.map(k => `<div class="pcard park">
    ${k.photo ? `<img class="im" src="${esc(k.photo)}" alt="">` : '<span class="im">🌳</span>'}
    <span class="tx"><b>${esc(k.name)}</b>${k.pending ? `<span class="tag wait">⏳ ${esc(t('Pendiente de aprobar: de momento solo lo ves tú'))}</span>` : ''}<small>${esc(k.notes)}</small>
    <span class="row"><button type="button" class="small" data-edk="${k.id}">✏️ ${t('Editar')}</button>
    <a class="btn ghost small" href="https://www.google.com/maps/dir/?api=1&destination=${k.lat},${k.lng}" target="_blank" rel="noopener">🧭 ${t('Cómo llegar')}</a>
    <button type="button" class="danger small" data-delk="${k.id}">${t('Borrar')}</button></span></span></div>`).join('')
    || `<p class="hint">${t('Todavía no has apuntado ninguno.')}</p>`;
}
let kEditId = null;
async function kEdit(id) {
  let k; try { k = await api('/api/parks/' + id); } catch (err) { return toast(err.message); }
  kReset(); kEditId = k.id; kPaintMap();
  $('kName').value = k.name; $('kNotes').value = k.notes || '';
  if (k.photo) $('kPhoto').innerHTML = `<img src="${esc(k.photo)}" alt="">`;
  $('kTitle').textContent = t('Editar pipicán'); $('kSave').textContent = t('Guardar cambios');
  $('kCancel').hidden = $('kDel').hidden = false;
  setTimeout(() => kSetPin(k.lat, k.lng, true), 80);
  $('kForm').scrollIntoView({behavior: 'smooth', block: 'start'});
}
$('kCancel').onclick = () => kReset();
$('kDel').onclick = async () => {
  if (!kEditId || !confirm(t('¿Borrar este pipicán?'))) return;
  try { await api('/api/parks/' + kEditId, {method: 'DELETE'}); toast('Borrado'); kReset(); loadParks(); } catch (err) { toast(err.message); }
};
$('kList').onclick = async e => {
  const ed = e.target.closest('[data-edk]'); if (ed) return kEdit(+ed.dataset.edk);
  const b = e.target.closest('[data-delk]'); if (!b || !confirm(t('¿Borrar este pipicán?'))) return;
  try { await api('/api/parks/' + b.dataset.delk, {method: 'DELETE'}); toast('Borrado'); loadParks(); } catch (err) { toast(err.message); }
};
$('kPhotoIn').onchange = async e => {
  const f = e.target.files[0]; e.target.value = ''; if (!f) return;
  try {
    const gps = exifGps(await f.slice(0, 256 * 1024).arrayBuffer());
    kphoto = await shrinkPhoto(f, 1280);
    $('kPhoto').innerHTML = `<img src="${kphoto}" alt="">`;
    if (gps && kFromLink) toast('Mantengo el sitio del enlace de Google Maps');
    else if (gps) { kSetPin(gps[0], gps[1], true); toast('He puesto el sitio con la ubicación de la foto'); kNear(gps[0], gps[1]); }
  } catch (err) { toast(err.message || 'No se puede abrir esa imagen'); }
};
// Sugerencias bajo el mapa: pipicanes cercanos de OpenStreetMap, los ya apuntados y los resultados de buscar
function kSugg(html) { $('kSugg').innerHTML = html; $('kSugg').hidden = !html; }
let kOpts = [];
function kOpt(o) { kOpts.push(o); return kOpts.length - 1; }
function kFill(o) {
  if (o.name && !$('kName').value.trim()) $('kName').value = o.name;
  if (o.notes && !$('kNotes').value.trim()) $('kNotes').value = o.notes;
}
async function kNear(lat, lng) {
  let r; try { r = await api('/api/geo/near', {method: 'POST', body: {lat, lng, lang: LANG}}); } catch (e) { return; }
  kOpts = []; const rows = [];
  (r.known || []).forEach(k => rows.push(`<div class="srow warn">⚠️ <span>${esc(t('Ya está apuntado en la web'))}: <b>${esc(k.name)}</b> (${k.dist} m)</span></div>`));
  (r.osm || []).forEach(k => {
    const i = kOpt(k);
    rows.push(`<div class="srow">🌳 <span>${esc(t('En OpenStreetMap hay un pipicán cerca'))}: <b>${esc(k.name || t('Pipicán sin nombre'))}</b> (${k.dist} m)</span><button type="button" class="small" data-kopt="${i}">${t('Usar este')}</button></div>`);
  });
  if (r.address) rows.push(`<div class="srow">📍 <span>${esc(r.address)}</span></div>`);
  kSugg(rows.join(''));
  // si no hay un pipicán conocido, se propone un nombre con la calle o el barrio
  const best = (r.osm || []).find(k => k.name && k.dist <= 60);
  if (best) kFill({name: best.name, notes: best.notes});
  else if (r.address && !$('kName').value.trim()) $('kName').value = (t('Pipicán') + ' ' + r.address.split(', ').slice(0, 2).join(', ')).slice(0, 60);
}
$('kSugg').onclick = e => {
  const b = e.target.closest('[data-kopt]'); if (!b) return;
  const o = kOpts[+b.dataset.kopt]; if (!o) return;
  kSetPin(o.lat, o.lng, true); kFromLink = false;
  if (o.name) $('kName').value = o.name; if (o.notes && !$('kNotes').value.trim()) $('kNotes').value = o.notes;
  if (o.search && !o.dog) toast('Ahora toca el sitio exacto en el mapa'); else toast('Comprueba el punto en el mapa');
  if (o.search) kNear(o.lat, o.lng);
};
$('kFind').onclick = async () => {
  const q = $('kSearch').value.trim(); if (!q) return;
  let res;
  try { res = await api('/api/geo/search', {method: 'POST', body: {q, lang: LANG}}); }
  catch (err) {
    try { const ll = await geocode(q); if (ll) { kmap.setView(ll, 16); return toast('Ahora toca el sitio exacto en el mapa'); } } catch (e) {}
    return toast(err.message || 'No se puede buscar ahora. Mueve el mapa con el dedo.');
  }
  if (!res.length) { kSugg(''); return toast('No encuentro ese sitio'); }
  kOpts = [];
  kSugg(`<p class="hint">${esc(t('Elige el que buscas:'))}</p>` + res.map(o => {
    const i = kOpt({...o, search: true});
    return `<button type="button" class="srow pick" data-kopt="${i}">${o.known ? '✅' : o.dog ? '🌳' : '📍'} <span><b>${esc(o.name || o.label)}</b>${o.name && o.label ? `<small>${esc(o.label)}</small>` : ''}${o.known ? `<small>${esc(t('Ya está en la web'))}</small>` : ''}</span></button>`;
  }).join(''));
  const first = res[0]; kmap.setView([first.lat, first.lng], first.dog ? 17 : 15);
};
$('kLinkGo').onclick = async () => {
  const url = $('kLink').value.trim(); if (!url) return;
  $('kErr').textContent = '';
  try {
    const r = await api('/api/maps-link', {method: 'POST', body: {url}});
    kSetPin(r.lat, r.lng, true); kFromLink = true; if (r.name && !$('kName').value.trim()) $('kName').value = r.name;
    $('kWhere').textContent = t('Sitio marcado con el enlace de Google Maps: comprueba el punto. Si no es el sitio exacto, arrastra el punto.');
    toast('Sitio marcado con el enlace de Google Maps'); kNear(r.lat, r.lng);
  } catch (err) {
    $('kErr').textContent = '⚠️ ' + t(err.message).replace(/\.?\s*$/, '. ') + t('El sitio no ha cambiado: márcalo en el mapa antes de guardar.');
    toast(err.message);
  }
};
$('kLink').onpaste = () => setTimeout(() => $('kLinkGo').onclick(), 50);
$('kLink').onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); $('kLinkGo').onclick(); } };
$('kSearch').onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); $('kFind').onclick(); } };
$('kHere').onclick = () => {
  if (!navigator.geolocation) return toast('Este navegador no puede dar la ubicación');
  if (kFromLink && !confirm(t('Ya has marcado el sitio con el enlace de Google Maps, que es más exacto. ¿Lo cambio por tu ubicación de ahora?'))) return;
  navigator.geolocation.getCurrentPosition(p => {
    kSetPin(p.coords.latitude, p.coords.longitude, true, (p.coords.accuracy || 0) > 2000); kFromLink = false; roughWarn(p);
    if ((p.coords.accuracy || 0) <= 2000) kNear(p.coords.latitude, p.coords.longitude);
  },
    () => toast('No he podido saber dónde estás. Toca el mapa a mano.'), {enableHighAccuracy: true, timeout: 10000, maximumAge: 0});
};
$('kForm').onsubmit = async e => {
  e.preventDefault(); $('kErr').textContent = '';
  if (!kpos) { $('kErr').textContent = t('Marca en el mapa dónde está el pipicán'); return; }
  if (!kChecked) {
    // antes de guardar: el mapa se acerca al punto y pregunta «¿Es aquí?»; el segundo toque guarda
    kChecked = true; kmap.setView(kpos, 18); $('kMap').scrollIntoView({behavior: 'smooth', block: 'center'});
    $('kWhere').textContent = t('¿Es aquí? Mira bien el punto verde. Si es correcto, pulsa «Sí, es aquí: guardar». Si no, arrástralo hasta el pipicán.');
    $('kWhere').classList.add('ask'); $('kSave').textContent = t('✅ Sí, es aquí: guardar');
    return;
  }
  if (!kDistinct) {
    let dupes = [];
    try { dupes = await api('/api/parks/check', {method: 'POST', body: {lat: kpos[0], lng: kpos[1], name: $('kName').value, skip: kEditId || 0}}); } catch (e) {}
    if (dupes.length) return kShowDupes(dupes);
  }
  if (kRough && !confirm(t('El sitio viene de una ubicación aproximada (este aparato no tiene GPS) y puede estar a muchos kilómetros. ¿Lo guardo así? Pulsa «Cancelar» para corregirlo en el mapa.'))) return;
  $('kSave').disabled = true;
  try {
    const body = {name: $('kName').value, notes: $('kNotes').value, lat: kpos[0], lng: kpos[1], data: kphoto, distinct: kDistinct};
    const r = await api(kEditId ? '/api/parks/' + kEditId : '/api/parks', {method: kEditId ? 'PUT' : 'POST', body});
    toast(r.pending ? '¡Gracias! Saldrá en el mapa cuando el administrador lo revise' : (kEditId ? 'Guardado' : '¡Gracias! Pipicán apuntado'));
    kReset(); loadParks();
  } catch (err) { $('kErr').textContent = err.message; }
  $('kSave').disabled = false;
};

// Administración: atajos a la gestión (personas, fichas, pipicanes, ajustes), que está debajo del resumen
document.querySelector('.admnav').onclick = e => {
  const a = e.target.closest('[data-jump]'); if (!a) return;
  e.preventDefault(); const el = $(a.dataset.jump); if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'});
};
// ---------- apariencia: claro / oscuro, color y fondo con patitas (se guarda en este dispositivo) ----------
const COLOR_NAMES = {naranja: 'Naranja', azul: 'Azul', verde: 'Verde', morado: 'Morado', rosa: 'Rosa', turquesa: 'Turquesa', rojo: 'Rojo', marron: 'Marrón'};
$('themeColors').innerHTML = Object.entries(Tema.COLORS).map(([k, c]) =>
  `<button type="button" class="sw" data-color="${k}" style="--c:${c}" title="${COLOR_NAMES[k]}" aria-label="${COLOR_NAMES[k]}"></button>`).join('');
function paintTheme() {
  const s = Tema.get();
  document.querySelectorAll('#themeMode [data-mode]').forEach(b => b.classList.toggle('on', b.dataset.mode === s.mode));
  document.querySelectorAll('#themeColors [data-color]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.color === s.color)));
  $('themePaws').checked = s.paws;
}
$('themeMode').onclick = e => { const b = e.target.closest('[data-mode]'); if (b) { Tema.set({mode: b.dataset.mode}); paintTheme(); } };
$('themeColors').onclick = e => { const b = e.target.closest('[data-color]'); if (b) { Tema.set({color: b.dataset.color}); paintTheme(); } };
$('themePaws').onchange = () => { Tema.set({paws: $('themePaws').checked}); paintTheme(); };
paintTheme();

(async () => { info = await api('/api/me'); start(); })().catch(err => { document.body.textContent = t('No se puede conectar con el servidor') + ': ' + err.message; });
})();

