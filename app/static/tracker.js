// Abrir el localizador del dueño: Google (Find Hub) o Apple (AirTag, app Buscar).
// Google y Apple no dejan que otra web lea la posición, así que solo se abre su app o su web oficial.
(() => {
const ua = navigator.userAgent || '';
const IOS = /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
const MAC = /Macintosh/.test(ua) && !IOS;
const ANDROID = /Android/.test(ua), INAPP = /MascotasPanelAndroid/.test(ua);
const GOOGLE_WEB = 'https://www.google.com/android/find', APPLE_WEB = 'https://www.icloud.com/find';
const T = (lang, es, en) => (lang === 'en' ? en : es);
const pick = kind => kind || (IOS || MAC ? 'apple' : 'google');
const go = url => { if (INAPP || IOS) location.href = url; else window.open(url, '_blank', 'noopener'); };
function open(kind) {
  kind = pick(kind);
  if (kind === 'apple') {
    if (IOS) {  // la app Buscar; si no se abre, la web de iCloud
      location.href = 'findmy://';
      setTimeout(() => { if (document.visibilityState === 'visible') location.href = APPLE_WEB; }, 1500);
    } else go(APPLE_WEB);
    return;
  }
  if (ANDROID && !INAPP) {  // Chrome en Android: la app Encontrar (Find Hub); si no está, su web
    location.href = 'intent:#Intent;action=android.intent.action.MAIN;category=android.intent.category.LAUNCHER;'
      + 'package=com.google.android.apps.adm;S.browser_fallback_url=' + encodeURIComponent(GOOGLE_WEB) + ';end';
  } else go(GOOGLE_WEB);
}
function hint(kind, lang) {
  kind = pick(kind);
  if (kind === 'apple') return T(lang,
    'Se abre la app Buscar del iPhone (en un ordenador, icloud.com/find). En «Objetos», toca su AirTag y activa el «Modo perdido» para dejar tu teléfono; con «Compartir» lo ve también tu familia. Los AirTag solo se ven en la app Buscar de un iPhone, iPad o Mac.',
    'The Find My app opens on iPhone (on a computer, icloud.com/find). In «Items», tap its AirTag and turn on «Lost Mode» to leave your phone number; «Share» lets your family see it too. AirTags only show in the Find My app on an iPhone, iPad or Mac.');
  return T(lang,
    'Se abre Encontrar (Find Hub) de Google. Toca su localizador y pulsa «Marcar como perdido» para que quien lo encuentre vea tu mensaje; con «Compartir» lo ve también tu familia.',
    "Google's Find Hub opens. Tap its tracker and press «Mark as lost» so whoever finds it sees your message; «Share» lets your family see it too.");
}
window.Tracker = {open, hint, pick, IOS, ANDROID, INAPP};
})();
