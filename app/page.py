"""Páginas públicas que pinta el servidor: inicio (mascotas perdidas), ficha del QR y privacidad."""
import json, re, time
from html import escape
from urllib.parse import quote

from .config import CONTACT_EMAIL, OWNER_NAME
from .version import VERSION

SPECIES = {"perro": ("Perro", "Dog", "🐶"), "gato": ("Gato", "Cat", "🐱"), "conejo": ("Conejo", "Rabbit", "🐰"),
           "huron": ("Hurón", "Ferret", "🦦"), "pajaro": ("Pájaro", "Bird", "🐦"), "loro": ("Loro", "Parrot", "🦜"),
           "gallina": ("Gallina", "Hen", "🐔"), "hamster": ("Hámster", "Hamster", "🐹"), "cobaya": ("Cobaya", "Guinea pig", "🐹"),
           "raton": ("Ratón o rata", "Mouse or rat", "🐭"), "erizo": ("Erizo", "Hedgehog", "🦔"), "tortuga": ("Tortuga", "Tortoise", "🐢"),
           "reptil": ("Reptil", "Reptile", "🦎"), "pez": ("Pez", "Fish", "🐟"), "caballo": ("Caballo", "Horse", "🐴"),
           "burro": ("Burro", "Donkey", "🐴"), "cerdo": ("Cerdo", "Pig", "🐷"), "cabra": ("Cabra u oveja", "Goat or sheep", "🐐"),
           "otro": ("Otro", "Other", "🐾")}
SEX = {"macho": ("Macho", "Male"), "hembra": ("Hembra", "Female")}
SIZE = {"pequeno": ("Pequeño", "Small"), "mediano": ("Mediano", "Medium"), "grande": ("Grande", "Large")}

EN = {
    "Asociaciones": "Associations", "Verificada": "Verified", "Nombre oficial": "Official name", "Datos legales": "Legal details",
    "Registro de asociaciones": "Associations register no.", "Núcleo zoológico": "Animal facility (núcleo zoológico) no.",
    "en adopción": "up for adoption", "animal en adopción": "animal up for adoption",
    "Todavía no hay asociaciones verificadas": "There are no verified associations yet",
    "¿Eres una asociación o protectora? Regístrate como asociación y, cuando la verifiquemos, saldrá aquí con sus animales.":
        "Are you an association or shelter? Sign up as an association and, once we verify it, it will appear here with its animals.",
    "Asociaciones y protectoras verificadas: quiénes son, dónde están, cómo contactar y sus animales en adopción.":
        "Verified associations and shelters: who they are, where they are, how to contact them and their animals up for adoption.",
    "Todas están verificadas por el administrador. Toca una para ver sus datos y sus animales en adopción.":
        "All of them are verified by the administrator. Tap one to see its details and its animals up for adoption.",
    "Añadir pipicán aquí": "Add a dog park here",
    "¿Estás en un pipicán que no sale en el mapa?": "Are you at a dog park that isn't on the map?",
    "Uso personal no comercial": "Personal, non-commercial use",
    "Proyecto sin ánimo de lucro, gratis y sin anuncios": "Non-profit project, free and ad-free",
    "App creada con ayuda de inteligencia artificial (IA)": "App made with the help of artificial intelligence (AI)",
    "Inicio": "Home",
    "mascotas registradas": "registered pets", "perros": "dogs", "gatos": "cats", "perdidas ahora": "lost right now",
    "Administrador: aquí ves todas las mascotas registradas.": "Admin: you can see every registered pet here.",
    "Por privacidad, aquí solo ves las tuyas. De las demás solo sale el total. Las perdidas las ve todo el mundo en «Perdidas», y las que buscan casa en «Adopción».": "For privacy, you only see your own here. For the rest, only the total is shown. Lost pets are visible to everyone in «Lost», and those looking for a home in «Adoption».",
    "Todavía no has apuntado ninguna mascota": "You haven't added any pets yet",
    "Entra en tu panel y apunta a la tuya con una foto.": "Go to your panel and add yours with a photo.",
    "Entra para ver tus mascotas": "Sign in to see your pets",
    "Por privacidad, las fichas solo las ve su familia. Las perdidas salen en «Perdidas» para todo el mundo.": "For privacy, profiles are only visible to their family. Lost pets show in «Lost» for everyone.",
    "Tuya: abrir y editar": "Yours: open and edit",
    "Registro general: solo salen las mascotas perdidas y las que su familia ha querido enseñar (foto, nombre y raza, sin ningún dato de los dueños). Las demás no las ve nadie más. Las tuyas llevan «✏️ Tuya» y se abren en tu panel.": "General registry: only lost pets and the ones their family chose to show (photo, name and breed, with no owner details). Nobody else sees the rest. Yours are marked «✏️ Yours» and open in your panel.",
    "📱 App (solo Android)": "📱 App (Android only)",
    "Descargar la app para Android. No sirve para iPhone ni iPad: allí usa esta web.": "Download the Android app. It does not work on iPhone or iPad: use this website there.",
    "Mascotas perdidas": "Lost pets",
    "Registro libre de mascotas": "Free pet registry",
    "Apunta a tus mascotas con su foto, saca su placa con QR y, si se pierde, imprime un cartel «Se busca» en un minuto.":
        "Register your pets with a photo, get a QR tag for them and, if one gets lost, print a \"Missing\" poster in a minute.",
    "Entrar o registrarme": "Sign in or sign up", "Entrar": "Sign in",
    "Gratis y sin anuncios. Solo pedimos tu nombre y un correo, y no se enseñan a nadie.": "Free and ad-free. We only ask for your name and an email, and they are never shown to anyone.",
    "Buscar por zona": "Search by area", "Zona donde se perdió": "Area where it got lost", "Ej.: Valencia, Benimaclet…": "E.g.: Valencia, Benimaclet…",
    "Todas": "All", "Buscar": "Search", "Animal": "Animal",
    "No hay ninguna mascota perdida": "There are no lost pets", "con esa búsqueda": "for that search",
    "¡Buena señal! Si has perdido la tuya, entra y márcala como perdida para que salga aquí.":
        "Good news! If you have lost yours, sign in and mark it as lost so it shows here.",
    "Perdido desde": "Missing since", "Zona": "Area", "Ver ficha": "See profile",
    "mascotas registradas": "registered pets", "Privacidad": "Privacy", "Hecho con": "Made with",
    "¿Has visto a alguna? Toca su foto para avisar a su familia.": "Have you seen one? Tap its photo to tell its family.",
    "¡Me he perdido! Ayúdame a volver a casa": "I'm lost! Help me get back home",
    "Hola, soy": "Hi, I'm", "Si me has encontrado, por favor avisa a mi familia. ¡Gracias!": "If you have found me, please tell my family. Thank you!",
    "Llamar a": "Call", "su familia": "my family", "Mandar un WhatsApp": "Send a WhatsApp", "Enviar dónde estoy": "Send where I am",
    "Raza": "Breed", "Color / señas": "Colour / markings", "Sexo": "Sex", "Edad": "Age", "Tamaño": "Size",
    "Pipicanes": "Dog parks", "Busca tu pipicán": "Find a dog park", "Cómo llegar": "Directions",
    "Todavía no hay ningún pipicán apuntado.": "No dog parks have been added yet.",
    "Entra y apunta el de tu barrio: con una foto y su sitio en el mapa.": "Sign in and add the one in your area: with a photo and its place on the map.",
    "Ver los que tengo cerca": "Show the ones near me", "Tu ubicación es aproximada (unos {km} km): este aparato no tiene GPS y la calcula por internet. Si no es tu zona, escribe tu pueblo o barrio arriba.": "Your location is approximate (about {km} km): this device has no GPS and works it out from the internet. If it is not your area, type your town or neighbourhood above.",
    "No he podido saber dónde estás. Escribe tu pueblo o barrio arriba.": "I could not find where you are. Type your town or neighbourhood above.", "No encuentro ese sitio": "I cannot find that place",
    "Ir a mi zona": "Go to my area", "Escribe tu pueblo o barrio (ej.: Puçol)": "Type your town or neighbourhood (e.g. Puçol)", "Pueblo o barrio": "Town or neighbourhood", "Buscar": "Search", "Apuntar un pipicán": "Add a dog park",
    "Mapa de pipicanes que va apuntando la gente, con foto y cómo llegar.": "Map of dog parks added by people, with photos and directions.",
    "Los pipicanes que va apuntando la gente, con su foto y cómo llegar. ¿Falta el tuyo? Apúntalo en un momento.":
        "Dog parks added by people, with a photo and directions. Is yours missing? Add it in a moment.",
    "Microchip": "Microchip", "otra persona de su familia": "another family member", "Vive en": "Lives in", "Se perdió en": "Lost in", "Salud": "Health", "Cómo es": "What I'm like",
    "Recompensa": "Reward", "Ficha hecha con": "Profile made with", "Más información": "More info",
    "Esta mascota está en casa. Su familia ha elegido no enseñar su contacto mientras no esté perdida.":
        "This pet is at home. Its family has chosen not to show their contact while it is not lost.",
    "¡Hola! He encontrado a": "Hi! I've found",
    "Mapa de mascotas perdidas": "Map of lost pets", "Avisar a su familia": "Tell its family",
    "Tu mensaje le llega a su familia. Ellos no te enseñan su teléfono, pero tú puedes dejar el tuyo para que te llamen.":
        "Your message reaches its family. They don't show you their phone, but you can leave yours so they can call you.",
    "Mensaje": "Message", "Lo he visto / lo tengo yo. Estoy en…": "I've seen it / I have it. I'm at…",
    "Tu teléfono o correo": "Your phone or email", "para que te contesten": "so they can reply",
    "Mandar también dónde estoy ahora": "Also send where I am now", "Enviar aviso": "Send notice",
    "Prefiero mandar un mensaje": "I'd rather send a message", "Registro": "Registry", "Perdidas": "Lost", "Perdida": "Lost",
    "Todavía no hay mascotas en el registro": "There are no pets in the registry yet",
    "Entra, apunta a la tuya con una foto y será la primera.": "Sign in, add yours with a photo and it will be the first.",
    "Todas las mascotas apuntadas, sin ningún dato de sus dueños: solo su foto, nombre y raza.":
        "All registered pets, with no details about their owners: only photo, name and breed.",
    "Registrar a mi mascota": "Register my pet", "Nombre, raza o nº de chip": "Name, breed or chip number", "Nombre o raza": "Name or breed", "Ej.: Rocky, mestizo…": "E.g.: Rocky, mixed breed…",
    "resultados": "results", "Anteriores": "Previous", "Siguientes": "Next", "Los puntos son aproximados: la zona donde se perdió cada una.":
        "The points are approximate: the area where each one got lost.",
    "Se perdió por esta zona": "Lost around this area", "Abrir en Google Maps": "Open in Google Maps", "gracias a su QR.": "thanks to its QR.",
}


EN.update({
    "Cambiar": "Edit", "Solo quien lo apuntó o el administrador": "Only whoever added it or the administrator",
    "Los pipicanes nuevos salen en el mapa cuando el administrador comprueba que existen.": "New dog parks show on the map once the administrator checks they exist.",
    "Tu mensaje y tu contacto solo le llegan a su destinatario y se borran a los 90 días.": "Your message and contact only reach the recipient and are deleted after 90 days.",
    "Compártelo para ayudar": "Share it to help", "Correo": "Email", "Copiar enlace": "Copy link", "Más…": "More…", "Copiar texto": "Copy text",
    "Instagram y TikTok no dejan poner enlaces: se descarga una imagen con su foto y el QR, y se copia el texto para que lo pegues.": "Instagram and TikTok do not allow links: an image with its photo and QR is downloaded, and the text is copied so you can paste it.",
    "SE BUSCA": "MISSING", "¿ME ADOPTAS?": "WILL YOU ADOPT ME?", "Soy": "I'm", "Estoy en": "I'm at", "Desde el": "Since",
    "Conóceme y habla con mi asociación aquí:": "Meet me and talk to my association here:",
    "Si lo ves, entra aquí para avisar a su familia (no hace falta registrarse):": "If you see it, tap here to tell its family (no sign-up needed):",
    "¿Le has visto? Entra para avisar a su familia.": "Have you seen it? Tap to tell its family.",
    "En adopción": "Up for adoption", "Adopción": "Adoption", "¿Me adoptas?": "Will you adopt me?",
    "Busco una familia": "I'm looking for a family", "Quiero conocerte": "I want to meet you",
    "Animales que buscan familia, de asociaciones y protectoras verificadas. Toca uno para conocerle y hablar con su asociación.":
        "Animals looking for a family, from verified associations and shelters. Tap one to meet it and talk to its association.",
    "Ver todos": "See all", "Ahora mismo no hay animales en adopción": "There are no animals up for adoption right now",
    "¿Eres una asociación o protectora? Regístrate como asociación y, cuando la verifiquemos, podrás publicar tus animales.":
        "Are you an association or shelter? Sign up as an association and, once we verify it, you can publish your animals.",
    "Asociaciones y protectoras": "Associations and shelters", "Está en": "Is at", "Su asociación": "Its association",
    "Llamar": "Call", "Escribir por WhatsApp": "Message on WhatsApp", "Escribir por Telegram": "Message on Telegram",
    "Mandar un correo": "Send an email", "Su web": "Website", "Ver la asociación": "See the association",
    "Escribir a la asociación": "Write to the association",
    "Tu mensaje le llega a la asociación por la app. Deja tu teléfono o tu correo para que te contesten.":
        "Your message reaches the association through the app. Leave your phone or email so they can reply.",
    "Hola, me gustaría conocer a": "Hi, I'd like to meet", "Enviar mensaje": "Send message",
    "Tu teléfono o tu correo": "Your phone or email", "Sus animales en adopción": "Its animals up for adoption",
    "Adoptar es para siempre. Piénsalo con calma y habla con la asociación: te contarán cómo es y qué necesita.":
        "Adopting is forever. Think it over and talk to the association: they will tell you what it is like and what it needs.",
    "Aviso legal": "Legal notice", "Algunos pipicanes vienen de OpenStreetMap": "Some dog parks come from OpenStreetMap", "Animales en adopción": "Animals up for adoption",
    "¡Hola! Me ha encantado": "Hi! I loved", "y me gustaría adoptarle.": "and I'd like to adopt them.",
})
CUTE = ["¿Me adoptas?", "¡Llévame a casa!", "Busco una familia", "¿Damos un paseo juntos?", "Te daré mucho amor",
        "¿Serás mi familia?", "Quiero conocerte"]
CUTE_EN = ["Will you adopt me?", "Take me home!", "I'm looking for a family", "Shall we go for a walk?", "I'll give you lots of love",
           "Will you be my family?", "I want to meet you"]


def cute(i, lang):
    return (CUTE_EN if lang == "en" else CUTE)[i % len(CUTE)]


def _cover(img, title, text_html, alt=""):
    """Cabecera con ilustración 16:9 (el hueco de la izquierda es para el texto)."""
    return (f'<section class="cover"><img src="/static/{img}-1280.webp" srcset="/static/{img}-768.webp 768w, '
            f'/static/{img}-1280.webp 1280w, /static/{img}-1920.webp 1920w" sizes="(min-width:1400px) 1400px, 100vw" '
            f'alt="{esc(alt)}" width="1280" height="714" fetchpriority="high"><div class="covertxt"><h1>{title}</h1>{text_html}</div></section>')


def _carousel(rows, lang, more=True):
    """Tira de animales en adopción con mensajes bonitos («¿Me adoptas?»)."""
    if not rows:
        return ""
    q = "?lang=en" if lang == "en" else ""
    items = "".join(
        f'<a class="adc" href="/m/{esc(r["code"])}{q}">'
        + (f'<img src="/f/{esc(r["photo"])}" alt="" loading="lazy">' if r["photo"] else f'<span class="nophoto">{SPECIES.get(r["species"], SPECIES["otro"])[2]}</span>')
        + f'<span class="bubble">{esc(r["adopt_text"][:60]) if r["adopt_text"] and len(r["adopt_text"]) <= 40 else cute(i, lang)}</span>'
        + f'<b translate="no">{esc(r["name"])}</b><small>{esc(r["org_name"])}</small></a>' for i, r in enumerate(rows))
    link = f'<a href="/adopta{q}">{L(lang, "Ver todos")} →</a>' if more else ""
    return (f'<section class="adopt"><div class="adhead"><h2>🏡 {L(lang, "En adopción")} · <span>{L(lang, "¿Me adoptas?")}</span></h2>{link}</div>'
            f'<div class="adrow">{items}</div></section>')


def _tabs(lang, on, total=None, total_lost=None, parks=None, url=None):
    q = "?lang=en" if lang == "en" else ""
    a = lambda k, href, label, n=None: f'<a href="{href}" class="{"on" if on == k else ""}">{label}{f" <small>{n}</small>" if n is not None else ""}</a>'
    return ('<nav class="vtabs">' + a("registro", url(ver="", pag=1) if url else f"/{q}", f'🐾 {L(lang, "Registro")}', total)
            + a("perdidas", url(ver="perdidas", pag=1) if url else f'/?ver=perdidas{"&lang=en" if lang == "en" else ""}', f'🔎 {L(lang, "Perdidas")}', total_lost)
            + a("adopta", f"/adopta{q}", f'🏡 {L(lang, "Adopción")}')
            + a("asociaciones", f"/asociaciones{q}", f'🤝 {L(lang, "Asociaciones")}')
            + a("pipicanes", f"/pipicanes{q}", f'🌳 {L(lang, "Pipicanes")}', parks) + "</nav>")


def L(lang, s):
    return EN.get(s, s) if lang == "en" else s


def esc(v) -> str:
    return escape(str(v or "").strip())


def _tel(p: str) -> str:
    return re.sub(r"[^0-9+]", "", p or "")[:20]


def _wa(p: str) -> str:
    d = re.sub(r"[^0-9]", "", p or "")
    if len(d) == 9 and d[0] in "6789":   # número español sin prefijo
        d = "34" + d
    return d


def _date(t, lang):
    if not t:
        return ""
    return time.strftime("%d/%m/%Y", time.localtime(t))


def _og(og):
    """Vista previa al compartir el enlace (Facebook, WhatsApp, Telegram, X…): título, texto y foto."""
    if not og:
        return ""
    m = [f'<meta property="og:{k}" content="{esc(og[k])}">' for k in ("title", "description", "url", "image") if og.get(k)]
    m.append('<meta property="og:type" content="website"><meta property="og:site_name" content="MascotasPanel">')
    m.append(f'<meta name="twitter:card" content="{"summary_large_image" if og.get("image") else "summary"}">')
    return "\n" + "".join(m)


def _poster(r, lang, adopt=False):
    """Datos para dibujar en el móvil la imagen de Instagram / TikTok (sin teléfono: solo la foto, los datos y el QR)."""
    sp = SPECIES.get(r["species"], SPECIES["otro"])
    if adopt:
        head = "ADOPT ME?" if lang == "en" else "¿ME ADOPTAS?"
    elif lang == "en":
        head = "MISSING"
    else:
        head = "SE BUSCA · PERDIDA" if r["sex"] == "hembra" else "SE BUSCA · PERDIDO"
    return {"code": r["code"], "photo": f"/f/{r['photo']}" if r["photo"] else "", "name": r["name"], "species": r["species"],
            "sp": sp[1] if lang == "en" else sp[0], "breed": r["breed"], "sex": r["sex"], "age": r["age"], "color": r["color"],
            "reward": "" if adopt else r["reward"], "note": r["adopt_text"] if adopt else r["lost_note"], "heading": head, "adopt": adopt}


def _share(lang, url, text, title, poster=None):
    """Botones para compartir el enlace de la ficha. Facebook no deja poner texto, solo el enlace (con su vista previa).
    Instagram y TikTok no dejan poner enlaces: se descarga una imagen con su foto y el QR, y se copia el texto."""
    u, tx, ti = quote(url, safe=""), quote(text + "\n" + url), quote(title)
    pj = esc(json.dumps(poster, ensure_ascii=False)) if poster else ""
    imgs = (f"""<div class="sh sh2"><button class="s ig" type="button" data-img="insta">📸 Instagram</button>
<button class="s tt" type="button" data-img="story">🎵 TikTok</button></div>
<p class="small">{L(lang, 'Instagram y TikTok no dejan poner enlaces: se descarga una imagen con su foto y el QR, y se copia el texto para que lo pegues.')}</p>""" if poster else "")
    return f"""<section class="share" id="share" data-url="{esc(url)}" data-text="{esc(text)}" data-title="{esc(title)}" data-poster="{pj}">
<h2>📣 {L(lang, 'Compártelo para ayudar')}</h2><div class="sh">
<a class="s fb" href="https://www.facebook.com/sharer/sharer.php?u={u}" target="_blank" rel="noopener">Facebook</a>
<a class="s wa" href="https://wa.me/?text={tx}" target="_blank" rel="noopener">WhatsApp</a>
<a class="s tg" href="https://t.me/share/url?url={u}&amp;text={quote(text)}" target="_blank" rel="noopener">Telegram</a>
<a class="s x" href="https://twitter.com/intent/tweet?url={u}&amp;text={ti}" target="_blank" rel="noopener">X</a>
<a class="s mail" href="mailto:?subject={ti}&amp;body={tx}">✉️ {L(lang, 'Correo')}</a>
<button class="s copy" type="button" id="shCopyT">📋 {L(lang, 'Copiar texto')}</button>
<button class="s copy" type="button" id="shCopy">🔗 {L(lang, 'Copiar enlace')}</button>
<button class="s more" type="button" id="shMore" hidden>📤 {L(lang, 'Más…')}</button></div>{imgs}
<p class="fmsg ok" id="shMsg" role="status"></p></section><script src="/static/share.js?v={VERSION}"></script>"""


def _head(title, lang, css="site.css", desc="", leaflet=False, og=None):
    lf = f'<link rel="stylesheet" href="/static/vendor/leaflet/leaflet.css?v={VERSION}">' if leaflet else ""
    # el mismo color, modo claro/oscuro y fondo que cada persona elige en su panel
    theme = f'<script src="/static/theme.js?v={VERSION}"></script>' if css == "site.css" else ""
    return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8">{lf}
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>{f'<meta name="description" content="{esc(desc)}">' if desc else ''}
<meta name="theme-color" content="#ea580c">
<link rel="icon" href="/static/icons/favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/static/icons/apple-touch-icon.png?web=1">
<link rel="stylesheet" href="/static/{css}?v={VERSION}">{theme}<script src="/static/ptr.js?v={VERSION}" defer></script>{_og(og)}</head>"""


LOGO = '<img class="logo" src="/static/icons/logo-64.png" srcset="/static/icons/logo-128.png 2x" width="32" height="32" alt="">'


APK_URL = "https://github.com/iaonlineapps/mascotaspanel/raw/main/android/dist/MascotasPanel.apk"


def _applink(lang):
    """Botón del menú de arriba para bajar la app (solo vale para Android)."""
    return (f'<a class="appdl" href="{APK_URL}" rel="noopener" title="{esc(L(lang, "Descargar la app para Android. No sirve para iPhone ni iPad: allí usa esta web."))}">'
            f'{L(lang, "📱 App (solo Android)")}</a>')


def _langlink(lang, path):
    other = "en" if lang == "es" else "es"
    sep = "&" if "?" in path else "?"
    return f'<a class="lang" href="{esc(path)}{sep}lang={other}" translate="no">{"English" if other == "en" else "Español"}</a>'


def _foot(lang, total=None):
    n = f"{total} {L(lang, 'mascotas registradas')} · " if total is not None else ""
    q = "?lang=en" if lang == "en" else ""
    return (f'<footer class="foot">{n}<a href="/privacidad{q}">{L(lang, "Privacidad")}</a> · <a href="/aviso-legal{q}">{L(lang, "Aviso legal")}</a> · '
            f'{L(lang, "Hecho con")} <span translate="no">MascotasPanel</span> {VERSION}'
            f'<span class="madeby">💛 {L(lang, "Proyecto sin ánimo de lucro, gratis y sin anuncios")} · 🤖 {L(lang, "App creada con ayuda de inteligencia artificial (IA)")} · '
            f'© 2026 <a href="https://github.com/iaonlineapps/mascotaspanel" rel="noopener" translate="no">IA Online Apps</a> · {L(lang, "Uso personal no comercial")}</span></footer>')


def _card(r, lang, link=False, me_id=0):
    """Tarjeta del registro. Solo las perdidas llevan a su ficha (con el contacto); las demás no
    enseñan ni el código del QR ni ningún dato de contacto."""
    sp = SPECIES.get(r["species"], SPECIES["otro"])
    img = (f'<img src="/f/{esc(r["photo"])}" alt="" loading="lazy">' if r["photo"]
           else f'<span class="nophoto">{sp[2]}</span>')
    zone = r["lost_zone"] if r["lost"] else ""  # la zona de la persona no se enseña: solo dónde se perdió
    pick = lambda d_, k: (d_[k][1] if lang == "en" else d_[k][0]) if k in d_ else ""
    bits = " · ".join(x for x in (sp[1] if lang == "en" else sp[0], esc(r["breed"]), pick(SEX, r["sex"])) if x)
    body = (f'{img}<div class="pi"><b translate="no">{esc(r["name"])}</b><span>{bits}</span>'
            + (f'<span>📍 {esc(zone)}</span>' if zone else "")
            + (f'<span class="when">{L(lang, "Perdido desde")} {_date(r["lost_at"], lang)}</span>' if r["lost"] else "")
            + "</div>")
    q = "?lang=en" if lang == "en" else ""
    if me_id and r["user_id"] == me_id:  # las tuyas: se abren en tu panel para cambiarlas
        return (f'<a class="pet is-mine{" is-lost" if r["lost"] else ""}" href="/panel#m{r["id"]}"><span class="tag mine">✏️ {L(lang, "Tuya: abrir y editar")}</span>{body}</a>')
    if r["lost"]:
        return f'<a class="pet is-lost" href="/m/{esc(r["code"])}{q}"><span class="tag">{L(lang, "Perdida")}</span>{body}</a>'
    if link:
        return f'<a class="pet" href="/m/{esc(r["code"])}{q}">{body}</a>'
    return f'<div class="pet">{body}</div>'


def render_home(rows, lang, view, zona, especie, nombre, pag, found, per_page, total, total_lost, by_chip=False, adopt=(), me_id=0, species=(0, 0), admin=False) -> str:
    opts = f'<option value="">{L(lang, "Todas")}</option>' + "".join(
        f'<option value="{k}" {"selected" if k == especie else ""}>{v[2]} {v[1] if lang == "en" else v[0]}</option>'
        for k, v in SPECIES.items())
    lost_view = view == "perdidas"
    cards = "".join(_card(r, lang, by_chip, me_id) for r in rows)
    pins = [{"lat": r["lost_lat"], "lng": r["lost_lng"], "name": r["name"], "code": r["code"],
             "photo": f"/f/{r['photo']}" if r["photo"] else "", "icon": SPECIES.get(r["species"], SPECIES["otro"])[2],
             "when": _date(r["lost_at"], lang)} for r in rows if r["lost"] and r["lost_lat"] is not None] if lost_view else []
    mapblock = ""
    if pins:
        data = json.dumps({"pins": pins, "lang": lang, "see": L(lang, "Ver ficha"), "since": L(lang, "Perdido desde")}).replace("</", "<\\/")
        mapblock = (f'<div class="map" id="lostMap" aria-label="{L(lang, "Mapa de mascotas perdidas")}"></div>'
                    f'<p class="small">{L(lang, "Los puntos son aproximados: la zona donde se perdió cada una.")}</p>'
                    f'<script type="application/json" id="mapData">{data}</script>'
                    f'<script src="/static/vendor/leaflet/leaflet.js?v={VERSION}"></script><script src="/static/maps.js?v={VERSION}"></script>')
    filtered = zona or especie or nombre
    if not cards:
        extra = f" {L(lang, 'con esa búsqueda')}" if filtered else ""
        if lost_view:
            cards = f'<p class="empty"><b>{L(lang, "No hay ninguna mascota perdida")}{extra}.</b><br>{L(lang, "¡Buena señal! Si has perdido la tuya, entra y márcala como perdida para que salga aquí.")}</p>'
        else:
            cards = (f'<p class="empty"><b>{L(lang, "Todavía no has apuntado ninguna mascota")}{extra}.</b><br>{L(lang, "Entra en tu panel y apunta a la tuya con una foto.")}</p>' if me_id
                     else f'<p class="empty"><b>{L(lang, "Entra para ver tus mascotas")}.</b><br>{L(lang, "Por privacidad, las fichas solo las ve su familia. Las perdidas salen en «Perdidas» para todo el mundo.")}</p>')

    def url(**kw):
        params = {"ver": "perdidas" if lost_view else "", "zona": zona, "especie": especie, "nombre": nombre,
                  "lang": "en" if lang == "en" else ""} | kw
        qs = "&".join(f"{k}={quote(str(v))}" for k, v in params.items() if v not in ("", None, 1))
        return "/" + ("?" + qs if qs else "")
    pages = (found - 1) // per_page + 1 if found else 1
    nav = ""
    if pages > 1:
        nav = '<nav class="pager">' + (f'<a class="btn ghost" href="{url(pag=pag - 1)}">← {L(lang, "Anteriores")}</a>' if pag > 1 else "") \
            + f'<span>{pag} / {pages}</span>' + (f'<a class="btn ghost" href="{url(pag=pag + 1)}">{L(lang, "Siguientes")} →</a>' if pag < pages else "") + "</nav>"
    tabs = _tabs(lang, "perdidas" if lost_view else "registro", total, total_lost, url=url)
    stats = (f'<div class="regstats"><span><b>{total}</b> {L(lang, "mascotas registradas")}</span>'
             f'<span>🐶 <b>{species[0]}</b> {L(lang, "perros")}</span><span>🐱 <b>{species[1]}</b> {L(lang, "gatos")}</span>'
             f'<span>🚨 <b>{total_lost}</b> {L(lang, "perdidas ahora")}</span></div>') if not lost_view else ""
    lead = (L(lang, "¿Has visto a alguna? Toca su foto para avisar a su familia.") if lost_view
            else L(lang, "Administrador: aquí ves todas las mascotas registradas.") if admin
            else L(lang, "Por privacidad, aquí solo ves las tuyas. De las demás solo sale el total. Las perdidas las ve todo el mundo en «Perdidas», y las que buscan casa en «Adopción»."))
    hidden = (f'<input type="hidden" name="ver" value="perdidas">' if lost_view else "") + \
             ('<input type="hidden" name="lang" value="en">' if lang == "en" else "")
    path = url(lang="")
    zfield = (f'<label>{L(lang, "Zona donde se perdió")}<input name="zona" value="{esc(zona)}" '
              f'placeholder="{L(lang, "Ej.: Valencia, Benimaclet…")}" maxlength="60"></label>') if lost_view else ""
    return _head(f"MascotasPanel · {L(lang, 'Registro libre de mascotas')}", lang,
                 desc=L(lang, "Apunta a tus mascotas con su foto, saca su placa con QR y, si se pierde, imprime un cartel «Se busca» en un minuto."),
                 leaflet=bool(pins)) + f"""
<body class="home"><header class="bar"><a class="brand" href="/">{LOGO}<span translate="no">Mascotas<b>Panel</b></span></a>
{_applink(lang)}{_langlink(lang, path)}<a class="btn" href="/panel">{L(lang, 'Entrar')}</a></header>
{_cover("portada", L(lang, 'Registro libre de mascotas'), f"""<p>{L(lang, 'Apunta a tus mascotas con su foto, saca su placa con QR y, si se pierde, imprime un cartel «Se busca» en un minuto.')}</p>
<p class="small">{L(lang, 'Gratis y sin anuncios. Solo pedimos tu nombre y un correo, y no se enseñan a nadie.')}</p>
<a class="btn big" href="/panel">{L(lang, 'Registrar a mi mascota')}</a>""")}
<main class="lostlist">{_carousel(adopt, lang) if not lost_view else ""}{tabs}
{stats}<p class="small">{lead}</p>
<form class="filter" method="get" action="/">{hidden}
<label>{L(lang, 'Nombre, raza o nº de chip')}<input name="nombre" value="{esc(nombre)}" placeholder="{L(lang, 'Ej.: Rocky, mestizo…')}" maxlength="40"></label>
{zfield}
<label>{L(lang, 'Animal')}<select name="especie">{opts}</select></label><button class="btn">{L(lang, 'Buscar')}</button></form>
{f'<p class="small">{found} {L(lang, "resultados")}</p>' if filtered else ''}
{mapblock}<div class="grid">{cards}</div>{nav}</main>{_foot(lang, total)}</body></html>"""


def render_parks(rows, lang) -> str:
    """«Busca tu pipicán»: el mapa de pipicanes que va apuntando la gente."""
    q = "?lang=en" if lang == "en" else ""
    pins = [{"id": r["id"], "name": r["name"], "notes": r["notes"], "lat": r["lat"], "lng": r["lng"],
             "photo": f"/f/{r['photo']}" if r["photo"] else ""} for r in rows]
    data = json.dumps({"pins": pins, "go": L(lang, "Cómo llegar"), "edit": L(lang, "Cambiar"), "lang": lang,
                       "add": L(lang, "Añadir pipicán aquí"), "here": L(lang, "¿Estás en un pipicán que no sale en el mapa?"),
                       "rough": L(lang, "Tu ubicación es aproximada (unos {km} km): este aparato no tiene GPS y la calcula por internet. Si no es tu zona, escribe tu pueblo o barrio arriba."),
                       "nogps": L(lang, "No he podido saber dónde estás. Escribe tu pueblo o barrio arriba."),
                       "notfound": L(lang, "No encuentro ese sitio"), "home": L(lang, "Ir a mi zona")}, ensure_ascii=False).replace("</", "<\\/")
    cards = "".join(
        f'<div class="pet park" id="k{r["id"]}">'
        + (f'<img src="/f/{esc(r["photo"])}" alt="" loading="lazy">' if r["photo"] else '<span class="nophoto">🌳</span>')
        + f'<div class="pi"><b>{esc(r["name"])}</b>' + (f'<span>{esc(r["notes"])}</span>' if r["notes"] else "")
        + f'<a class="go" href="https://www.google.com/maps/dir/?api=1&amp;destination={r["lat"]},{r["lng"]}" target="_blank" rel="noopener">🧭 {L(lang, "Cómo llegar")}</a>'
        + f'<a class="edit" href="/panel#k{r["id"]}" title="{L(lang, "Solo quien lo apuntó o el administrador")}">✏️ {L(lang, "Cambiar")}</a>'
        + "</div></div>" for r in rows)
    if not cards:
        cards = f'<p class="empty"><b>{L(lang, "Todavía no hay ningún pipicán apuntado.")}</b><br>{L(lang, "Entra y apunta el de tu barrio: con una foto y su sitio en el mapa.")}</p>'
    tabs = _tabs(lang, "pipicanes", parks=len(rows))
    mapblock = (f'<form class="mapfind" id="pfForm" role="search"><input id="pfQ" maxlength="80" placeholder="{L(lang, "Escribe tu pueblo o barrio (ej.: Puçol)")}" aria-label="{L(lang, "Pueblo o barrio")}">'
                f'<button class="btn" type="submit">🔎 {L(lang, "Buscar")}</button><button class="btn ghost" type="button" id="pfHome" hidden></button></form>'
                f'<p class="fmsg" id="pfMsg" role="status"></p>'
                f'<div class="map big" id="parkMap"></div>'
                f'<div class="row center"><button type="button" class="btn ghost" id="nearMe">📍 {L(lang, "Ver los que tengo cerca")}</button>'
                f'<a class="btn" href="/panel#pipicanes">➕ {L(lang, "Apuntar un pipicán")}</a></div>'
                f'<script type="application/json" id="parkData">{data}</script>'
                f'<script src="/static/vendor/leaflet/leaflet.js?v={VERSION}"></script><script src="/static/maps.js?v={VERSION}"></script>')
    return _head(f"{L(lang, 'Busca tu pipicán')} · MascotasPanel", lang, desc=L(lang, "Mapa de pipicanes que va apuntando la gente, con foto y cómo llegar."), leaflet=True) + f"""
<body class="home"><header class="bar"><a class="brand" href="/{q}">{LOGO}<span translate="no">Mascotas<b>Panel</b></span></a>
{_applink(lang)}{_langlink(lang, "/pipicanes")}<a class="btn" href="/panel">{L(lang, 'Entrar')}</a></header>
{_cover("pipican", "🌳 " + L(lang, 'Busca tu pipicán'), "<p>" + L(lang, 'Los pipicanes que va apuntando la gente, con su foto y cómo llegar. ¿Falta el tuyo? Apúntalo en un momento.') + "</p>")}
<main class="lostlist">{tabs}{mapblock}<div class="grid">{cards}</div>
<p class="small">{L(lang, "Algunos pipicanes vienen de OpenStreetMap")} (© <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap</a>, ODbL).</p></main>{_foot(lang)}</body></html>"""


def share_text(r, lang, org_name=""):
    """Texto de anuncio ya redactado (lo mismo que prepara el panel), sin datos de la familia."""
    sp = SPECIES.get(r["species"], SPECIES["otro"])
    pick = lambda d, k: (d[k][1] if lang == "en" else d[k][0]) if k in d else ""
    bits = " · ".join(x for x in (sp[1] if lang == "en" else sp[0], (r["breed"] or "").strip(), pick(SEX, r["sex"]), (r["age"] or "").strip()) if x)
    name = (r["name"] or "").strip()
    if r["adopt"]:
        t = [f"🏡 {L(lang, '¿ME ADOPTAS?')} {L(lang, 'Soy')} {name}", f"{sp[2]} {bits}"]
        if (r["adopt_text"] or "").strip():
            t.append(f"💛 {r['adopt_text'].strip()}")
        if org_name:
            t.append(f"📍 {L(lang, 'Estoy en')} {org_name}")
        t.append(L(lang, "Conóceme y habla con mi asociación aquí:"))
        return "\n".join(t)
    t = [f"🚨 {L(lang, 'SE BUSCA')} · {name.upper()}", f"{sp[2]} {bits}"]
    if (r["color"] or "").strip():
        t.append(f"🎨 {r['color'].strip()}")
    if r["lost_zone"]:
        t.append(f"📍 {L(lang, 'Se perdió en')}: {r['lost_zone'].strip()}")
    if r["lost_at"]:
        t.append(f"📅 {L(lang, 'Desde el')} {_date(r['lost_at'], lang)}")
    if (r["lost_note"] or "").strip():
        t.append(f"📣 {r['lost_note'].strip()}")
    if (r["reward"] or "").strip():
        t.append(f"🎁 {L(lang, 'Recompensa')}: {r['reward'].strip()}")
    t.append(L(lang, "Si lo ves, entra aquí para avisar a su familia (no hace falta registrarse):"))
    return "\n".join(t)


def render_pet(r, lang, base) -> str:
    e = lambda k: esc(r[k])
    name = e("name") or "🐾"
    sp = SPECIES.get(r["species"], SPECIES["otro"])
    sp_name = sp[1] if lang == "en" else sp[0]
    # Datos de la persona ocultos por defecto: el teléfono, su nombre y su zona solo se ven si el dueño
    # ha dado su consentimiento y la mascota está marcada como perdida. El microchip no se enseña nunca.
    show = r["contact"] in ("lost", "always") and bool(r["lost"]) and bool(r["phone"] or r["contact2_phone"])
    phone = _tel(r["phone"]) if show and r["phone"] else ""
    wa = _wa(r["phone"]) if show and r["phone"] else ""
    phone2 = _tel(r["contact2_phone"]) if show and r["contact2_phone"] else ""
    wa2 = _wa(r["contact2_phone"]) if show and r["contact2_phone"] else ""
    found = quote(f"{L(lang, '¡Hola! He encontrado a')} {r['name'] or ''} {L(lang, 'gracias a su QR.')}")
    photo = (f'<img class="photo" src="/f/{esc(r["photo"])}" alt="{name}">' if r["photo"]
             else f'<div class="photo none">{sp[2]}</div>')
    pick = lambda d, k: (d[k][1] if lang == "en" else d[k][0]) if k in d else ""
    rows = [("Raza", e("breed")), ("Color / señas", e("color")), ("Sexo", pick(SEX, r["sex"])),
            ("Edad", e("age")), ("Tamaño", pick(SIZE, r["size"]))]
    if show:
        rows.append(("Vive en", e("zone")))
    if r["lost"] and r["lost_zone"]:
        rows.append(("Se perdió en", e("lost_zone")))
    info = "".join(f"<dt>{L(lang, k)}</dt><dd>{v}</dd>" for k, v in rows if v)
    blocks = ""
    if r["lost"] and r["lost_note"]:
        blocks += f'<section class="health"><h2>📣</h2><p>{e("lost_note")}</p></section>'
    if r["health"]:
        blocks += f'<section class="health"><h2>⚕️ {L(lang, "Salud")}</h2><p>{e("health")}</p></section>'
    if r["notes"]:
        blocks += f'<section><h2>{L(lang, "Cómo es")}</h2><p>{e("notes")}</p></section>'
    btns = ""
    if phone:
        btns += f'<a class="b call" href="tel:{escape(phone)}">📞 {L(lang, "Llamar a")} {e("owner") or L(lang, "su familia")}</a>'
    if wa:
        btns += f'<a class="b wa" href="https://wa.me/{wa}?text={found}">💬 {L(lang, "Mandar un WhatsApp")}</a>'
    if phone2:
        btns += f'<a class="b call" href="tel:{escape(phone2)}">📞 {L(lang, "Llamar a")} {e("contact2_name") or L(lang, "otra persona de su familia")}</a>'
    if wa2 and not wa:
        btns += f'<a class="b wa" href="https://wa.me/{wa2}?text={found}">💬 {L(lang, "Mandar un WhatsApp")}</a>'
    if wa or wa2:
        btns += f'<button class="b loc" type="button" id="loc" data-wa="{wa or wa2}" data-name="{name}">📍 {L(lang, "Enviar dónde estoy")}</button>'
    # Formulario para avisar a la familia sin ver su teléfono (siempre disponible)
    form = f"""<form class="found" id="found" data-code="{esc(r['code'])}" {'' if not show else 'hidden'}>
<h2>✉️ {L(lang, 'Avisar a su familia')}</h2>
<p>{L(lang, 'Tu mensaje le llega a su familia. Ellos no te enseñan su teléfono, pero tú puedes dejar el tuyo para que te llamen.')}</p>
<label for="fText">{L(lang, 'Mensaje')}</label>
<textarea id="fText" rows="3" maxlength="600" placeholder="{L(lang, 'Lo he visto / lo tengo yo. Estoy en…')}"></textarea>
<label for="fContact">{L(lang, 'Tu teléfono o correo')} <span>({L(lang, 'para que te contesten')})</span></label>
<input id="fContact" maxlength="120" autocomplete="tel">
<label class="chk"><input type="checkbox" id="fLoc" checked> {L(lang, 'Mandar también dónde estoy ahora')}</label>
<button class="b wa" type="submit">✉️ {L(lang, 'Enviar aviso')}</button><p class="fmsg" id="fMsg" role="status"></p>
<p class="small">🔒 {L(lang, "Tu mensaje y tu contacto solo le llegan a su destinatario y se borran a los 90 días.")} <a href="/privacidad{'?lang=en' if lang == 'en' else ''}">{L(lang, 'Privacidad')}</a></p></form>"""
    if show:
        btns += f'<button class="b alt" type="button" id="showFound">✉️ {L(lang, "Prefiero mandar un mensaje")}</button>'
    else:
        btns = ""
    mapblock = ""
    if r["lost"] and r["lost_lat"] is not None:
        ll = f'{r["lost_lat"]},{r["lost_lng"]}'
        mapblock = (f'<section class="where"><h2>📍 {L(lang, "Se perdió por esta zona")}</h2>'
                    f'<div class="map" id="petMap" data-lat="{r["lost_lat"]}" data-lng="{r["lost_lng"]}"></div>'
                    f'<a class="b alt" href="https://www.google.com/maps/search/?api=1&amp;query={ll}" target="_blank" rel="noopener">🗺️ {L(lang, "Abrir en Google Maps")}</a></section>'
                    f'<script src="/static/vendor/leaflet/leaflet.js?v={VERSION}"></script><script src="/static/maps.js?v={VERSION}"></script>')
    lost = f'<div class="lost">{L(lang, "¡Me he perdido! Ayúdame a volver a casa")}</div>' if r["lost"] else ""
    reward = f'<div class="reward">🎁 {L(lang, "Recompensa")}: {e("reward")}</div>' if r["lost"] and r["reward"] else ""
    q = "?lang=en" if lang == "en" else ""
    url = f"{base}/m/{r['code']}{q}"
    img = f"{base}/f/{r['photo']}" if r["photo"] else f"{base}/static/icons/icon-512.png"
    if r["lost"]:
        title = f"🚨 {L(lang, 'SE BUSCA')}: {r['name']} · {sp_name}{' · ' + r['breed'] if r['breed'] else ''}"
        desc = (f"{L(lang, 'Se perdió en')} {r['lost_zone']}. " if r["lost_zone"] else "") + L(lang, "¿Le has visto? Entra para avisar a su familia.")
        share = _share(lang, url, share_text(r, lang), title, _poster(r, lang))
    else:
        title, desc, share = f"{L(lang, 'Hola, soy')} {r['name']}", L(lang, "Ficha hecha con") + " MascotasPanel", ""
    og = {"title": title, "description": desc, "url": url, "image": img}
    return _head(f"{r['name']} · MascotasPanel", lang, "pet.css", leaflet=bool(mapblock), og=og) + f"""<body>
<nav class="pettop"><a href="/{q}">🏠 {L(lang, 'Inicio')}</a><a class="btn" href="/panel">{L(lang, 'Entrar')}</a></nav><main>{lost}{photo}<h1>{L(lang, 'Hola, soy')} <span translate="no">{name}</span></h1><p class="sub">{sp[2]} {sp_name}{" · " + e("breed") if r["breed"] else ""}</p>
<p class="lead">{L(lang, 'Si me has encontrado, por favor avisa a mi familia. ¡Gracias!')}</p>{reward}
<div class="btns">{btns}</div>{form}{share}{mapblock}{f'<dl>{info}</dl>' if info else ""}{blocks}
<p class="foot">{L(lang, 'Ficha hecha con')} <a href="/{q}" translate="no">MascotasPanel</a> · <a href="/privacidad{q}">{L(lang, 'Privacidad')}</a></p></main>
<script src="/static/pet.js?v={VERSION}"></script><script src="/static/found.js?v={VERSION}"></script></body></html>"""


def _org_buttons(o, lang, pet_name=""):
    """Botones de contacto de una asociación: solo los que ella ha elegido enseñar."""
    msg = quote(f"{L(lang, '¡Hola! Me ha encantado')} {pet_name} {L(lang, 'y me gustaría adoptarle.')}" if pet_name else "")
    b = ""
    if o.get("phone"):
        b += f'<a class="b call" href="tel:{escape(_tel(o["phone"]))}">📞 {L(lang, "Llamar")} · {esc(o["phone"])}</a>'
    if o.get("whatsapp"):
        b += f'<a class="b wa" href="https://wa.me/{esc(o["whatsapp"])}{"?text=" + msg if msg else ""}" target="_blank" rel="noopener">💬 {L(lang, "Escribir por WhatsApp")}</a>'
    if o.get("telegram"):
        b += f'<a class="b tg" href="https://t.me/{esc(o["telegram"])}" target="_blank" rel="noopener">✈️ {L(lang, "Escribir por Telegram")}</a>'
    if o.get("email"):
        b += f'<a class="b alt" href="mailto:{esc(o["email"])}{"?body=" + msg if msg else ""}">✉️ {L(lang, "Mandar un correo")}</a>'
    if o.get("web"):
        b += f'<a class="b alt" href="{esc(o["web"])}" target="_blank" rel="noopener nofollow">🌐 {L(lang, "Su web")}</a>'
    return b


def _org_logo(o, cls="orglogo"):
    return (f'<img class="{cls}" src="{esc(o["logo"])}" alt="">' if o.get("logo")
            else f'<span class="{cls} none">🏡</span>')


def _adopt_card(r, lang, i):
    sp = SPECIES.get(r["species"], SPECIES["otro"])
    q = "?lang=en" if lang == "en" else ""
    img = (f'<img src="/f/{esc(r["photo"])}" alt="" loading="lazy">' if r["photo"] else f'<span class="nophoto">{sp[2]}</span>')
    pick = lambda d_, k: (d_[k][1] if lang == "en" else d_[k][0]) if k in d_ else ""
    bits = " · ".join(x for x in (sp[1] if lang == "en" else sp[0], esc(r["breed"]), pick(SEX, r["sex"]), esc(r["age"])) if x)
    return (f'<a class="pet is-adopt" href="/m/{esc(r["code"])}{q}"><span class="tag">💛 {cute(i, lang)}</span>{img}'
            f'<div class="pi"><b translate="no">{esc(r["name"])}</b><span>{bits}</span><span>🏡 {esc(r["org_name"])}'
            f'{" · " + esc(r["org_city"]) if r["org_city"] else ""}</span></div></a>')


def render_adopt(rows, orgs, lang, especie="") -> str:
    """«En adopción»: animales de asociaciones y protectoras verificadas."""
    q = "?lang=en" if lang == "en" else ""
    opts = f'<option value="">{L(lang, "Todas")}</option>' + "".join(
        f'<option value="{k}" {"selected" if k == especie else ""}>{v[2]} {v[1] if lang == "en" else v[0]}</option>' for k, v in SPECIES.items())
    cards = "".join(_adopt_card(r, lang, i) for i, r in enumerate(rows)) or (
        f'<p class="empty"><b>{L(lang, "Ahora mismo no hay animales en adopción")}.</b><br>'
        f'{L(lang, "¿Eres una asociación o protectora? Regístrate como asociación y, cuando la verifiquemos, podrás publicar tus animales.")}</p>')
    org_list = "".join(f'<a class="orgchip" href="/asociacion/{o["user_id"]}{q}">{_org_logo({"logo": f"/f/{o["logo"]}" if o["logo"] else ""}, "orgmini")}'
                       f'<span><b>{esc(o["name"])}</b><small>{esc(o["city"])}</small></span></a>' for o in orgs)
    hidden = '<input type="hidden" name="lang" value="en">' if lang == "en" else ""
    return _head(f"{L(lang, 'Animales en adopción')} · MascotasPanel", lang,
                 desc=L(lang, "Animales que buscan familia, de asociaciones y protectoras verificadas. Toca uno para conocerle y hablar con su asociación.")) + f"""
<body class="home"><header class="bar"><a class="brand" href="/{q}">{LOGO}<span translate="no">Mascotas<b>Panel</b></span></a>
{_applink(lang)}{_langlink(lang, "/adopta")}<a class="btn" href="/panel">{L(lang, 'Entrar')}</a></header>
{_cover("adopcion", "🏡 " + L(lang, "¿Me adoptas?"), f"<p>{L(lang, 'Animales que buscan familia, de asociaciones y protectoras verificadas. Toca uno para conocerle y hablar con su asociación.')}</p><p class='small'>{L(lang, 'Adoptar es para siempre. Piénsalo con calma y habla con la asociación: te contarán cómo es y qué necesita.')}</p>")}
<main class="lostlist">{_tabs(lang, "adopta")}
<form class="filter" method="get" action="/adopta">{hidden}<label>{L(lang, 'Animal')}<select name="especie">{opts}</select></label><button class="btn">{L(lang, 'Buscar')}</button></form>
<div class="grid">{cards}</div>
{f'<h2>{L(lang, "Asociaciones y protectoras")}</h2><div class="orgs">{org_list}</div>' if org_list else ''}
</main>{_foot(lang)}</body></html>"""


def _org_legal(o, lang):
    """Datos legales que la asociación ha apuntado: nombre oficial, CIF y números de registro."""
    rows = [(L(lang, "Nombre oficial"), o.get("legal_name")), ("CIF", o.get("cif")),
            (L(lang, "Registro de asociaciones"), o.get("reg_number")), (L(lang, "Núcleo zoológico"), o.get("zoo_number"))]
    dl = "".join(f"<dt>{k}</dt><dd translate=\"no\">{esc(v)}</dd>" for k, v in rows if v)
    return f'<section class="orglegal"><h2>🏛️ {L(lang, "Datos legales")}</h2><dl>{dl}</dl></section>' if dl else ""


def render_orgs(orgs, lang) -> str:
    """«Asociaciones»: todas las asociaciones y protectoras verificadas, con sus datos y sus animales en adopción."""
    q = "?lang=en" if lang == "en" else ""
    def card(o):
        n = o["n_adopt"]
        about = esc(o["about"][:180] + ("…" if len(o["about"]) > 180 else ""))
        city = f'<p class="small">📍 {esc(o["city"])}</p>' if o["city"] else ""
        legal = " · ".join(x for x in (esc(o["legal_name"]), f'CIF {esc(o["cif"])}' if o["cif"] else "") if x)
        return (f'<article class="orgcard"><a class="oc" href="/asociacion/{o["id"]}{q}">{_org_logo(o)}<div><h2 translate="no">{esc(o["name"])}</h2>'
                f'<span class="tag ok">✔ {L(lang, "Verificada")}</span>'
                f'{city}{f"<p class=about>{about}</p>" if about else ""}{f"<p class=small>🏛️ {legal}</p>" if legal else ""}'
                f'<p class="nadopt">💛 {n} {L(lang, "en adopción") if n != 1 else L(lang, "animal en adopción")}</p></div></a>'
                f'<div class="orgbtns">{_org_buttons(o, lang)}</div></article>')
    cards = "".join(card(o) for o in orgs) or (
        f'<p class="empty"><b>{L(lang, "Todavía no hay asociaciones verificadas")}.</b><br>'
        f'{L(lang, "¿Eres una asociación o protectora? Regístrate como asociación y, cuando la verifiquemos, saldrá aquí con sus animales.")}</p>')
    return _head(f"{L(lang, 'Asociaciones y protectoras')} · MascotasPanel", lang,
                 desc=L(lang, "Asociaciones y protectoras verificadas: quiénes son, dónde están, cómo contactar y sus animales en adopción.")) + f"""
<body class="home"><header class="bar"><a class="brand" href="/{q}">{LOGO}<span translate="no">Mascotas<b>Panel</b></span></a>
{_applink(lang)}{_langlink(lang, "/asociaciones")}<a class="btn" href="/panel">{L(lang, 'Entrar')}</a></header>
<main class="lostlist">{_tabs(lang, "asociaciones")}
<h1>🤝 {L(lang, 'Asociaciones y protectoras')}</h1>
<p class="lead">{L(lang, 'Todas están verificadas por el administrador. Toca una para ver sus datos y sus animales en adopción.')}</p>
<div class="orgcards">{cards}</div>
<p class="small">{L(lang, '¿Eres una asociación o protectora? Regístrate como asociación y, cuando la verifiquemos, saldrá aquí con sus animales.')} <a href="/panel">{L(lang, 'Entrar')}</a></p>
</main>{_foot(lang)}</body></html>"""


def render_org(o, rows, lang) -> str:
    q = "?lang=en" if lang == "en" else ""
    cards = "".join(_adopt_card(r, lang, i) for i, r in enumerate(rows)) or f'<p class="empty">{L(lang, "Ahora mismo no hay animales en adopción")}.</p>'
    return _head(f"{o['name']} · MascotasPanel", lang, desc=o["about"][:150]) + f"""
<body class="home"><header class="bar"><a class="brand" href="/{q}">{LOGO}<span translate="no">Mascotas<b>Panel</b></span></a>
{_applink(lang)}{_langlink(lang, f"/asociacion/{o['id']}")}<a class="btn" href="/panel">{L(lang, 'Entrar')}</a></header>
<main class="lostlist"><section class="orghead">{_org_logo(o)}<div><h1 translate="no">{esc(o["name"])}</h1>
{f'<p class="small">📍 {esc(o["city"])}</p>' if o["city"] else ''}{f'<p class="about">{esc(o["about"])}</p>' if o["about"] else ''}
<div class="orgbtns">{_org_buttons(o, lang)}</div></div></section>{_org_legal(o, lang)}
<h2>{L(lang, 'Sus animales en adopción')}</h2><div class="grid">{cards}</div>
<p><a href="/asociaciones{q}">← {L(lang, 'Asociaciones y protectoras')}</a> · <a href="/adopta{q}">{L(lang, 'Animales en adopción')}</a></p></main>{_foot(lang)}</body></html>"""


def render_adopt_pet(r, o, lang, base="") -> str:
    """Ficha de un animal en adopción: sus datos, su mensaje y cómo hablar con la asociación."""
    e = lambda k: esc(r[k])
    name = e("name") or "🐾"
    sp = SPECIES.get(r["species"], SPECIES["otro"])
    pick = lambda d, k: (d[k][1] if lang == "en" else d[k][0]) if k in d else ""
    photo = (f'<img class="photo" src="/f/{esc(r["photo"])}" alt="{name}">' if r["photo"] else f'<div class="photo none">{sp[2]}</div>')
    rows = [("Raza", e("breed")), ("Color / señas", e("color")), ("Sexo", pick(SEX, r["sex"])), ("Edad", e("age")),
            ("Tamaño", pick(SIZE, r["size"])), ("Está en", esc(o["city"]))]
    info = "".join(f"<dt>{L(lang, k)}</dt><dd>{v}</dd>" for k, v in rows if v)
    blocks = ""
    if r["notes"]:
        blocks += f'<section><h2>{L(lang, "Cómo es")}</h2><p>{e("notes")}</p></section>'
    if r["health"]:
        blocks += f'<section class="health"><h2>⚕️ {L(lang, "Salud")}</h2><p>{e("health")}</p></section>'
    q = "?lang=en" if lang == "en" else ""
    form = f"""<form class="found" id="found" data-code="{esc(r['code'])}" data-adopt="1">
<h2>💌 {L(lang, 'Escribir a la asociación')}</h2>
<p>{L(lang, 'Tu mensaje le llega a la asociación por la app. Deja tu teléfono o tu correo para que te contesten.')}</p>
<label for="fText">{L(lang, 'Mensaje')}</label>
<textarea id="fText" rows="3" maxlength="600">{L(lang, 'Hola, me gustaría conocer a')} {name}.</textarea>
<label for="fContact">{L(lang, 'Tu teléfono o tu correo')}</label>
<input id="fContact" maxlength="120" autocomplete="email" required>
<button class="b wa" type="submit">💌 {L(lang, 'Enviar mensaje')}</button><p class="fmsg" id="fMsg" role="status"></p>
<p class="small">🔒 {L(lang, "Tu mensaje y tu contacto solo le llegan a su destinatario y se borran a los 90 días.")} <a href="/privacidad{'?lang=en' if lang == 'en' else ''}">{L(lang, 'Privacidad')}</a></p></form>"""
    url = f"{base}/m/{r['code']}{q}"
    title = f"🏡 {L(lang, '¿Me adoptas?')} {L(lang, 'Soy')} {r['name']}"
    og = {"title": title, "url": url, "image": f"{base}/f/{r['photo']}" if r["photo"] else f"{base}/static/icons/icon-512.png",
          "description": (r["adopt_text"] or "").strip() or f"{L(lang, 'Busco una familia')} · {o['name']}"}
    share = _share(lang, url, share_text(r, lang, o["name"]), title, _poster(r, lang, adopt=True))
    return _head(f"{r['name']} · {L(lang, 'En adopción')} · MascotasPanel", lang, "pet.css", og=og) + f"""<body>
<nav class="pettop"><a href="/{q}">🏠 {L(lang, 'Inicio')}</a><a class="btn" href="/panel">{L(lang, 'Entrar')}</a></nav><main><div class="adoptbadge">🏡 {L(lang, 'Busco una familia')}</div>{photo}
<h1>{L(lang, 'Hola, soy')} <span translate="no">{name}</span></h1><p class="sub">{sp[2]} {sp[1] if lang == "en" else sp[0]}{" · " + e("breed") if r["breed"] else ""}</p>
<p class="bubble">{e("adopt_text") or L(lang, "¿Me adoptas?")}</p>
{f'<dl>{info}</dl>' if info else ""}{blocks}
<section class="orgbox"><h2>{L(lang, 'Su asociación')}</h2><a class="orgline" href="/asociacion/{o['id']}{q}">{_org_logo(o, "orgmini")}<b translate="no">{esc(o["name"])}</b></a>
<div class="btns">{_org_buttons(o, lang, r["name"])}</div></section>{form}{share}
<p class="small">{L(lang, 'Adoptar es para siempre. Piénsalo con calma y habla con la asociación: te contarán cómo es y qué necesita.')}</p>
<p class="foot"><a href="/adopta{q}">← {L(lang, 'Animales en adopción')}</a> · <a href="/privacidad{q}">{L(lang, 'Privacidad')}</a></p></main>
<script src="/static/found.js?v={VERSION}"></script></body></html>"""


def _who(lg, lang):
    name = esc(lg.get("legal_name")) or ("the person who runs this server" if lang == "en" else "la persona que administra este servidor")
    place = f", {esc(lg['legal_place'])}" if lg.get("legal_place") else ""
    mail = (f' · <a href="mailto:{esc(lg["legal_email"])}">{esc(lg["legal_email"])}</a>') if lg.get("legal_email") else ""
    return f"{name}{place}{mail}"


def render_privacy(lang="es", lg=None) -> str:
    lg = lg or {"legal_name": OWNER_NAME, "legal_email": CONTACT_EMAIL, "legal_place": ""}
    who = _who(lg, lang)
    if lang == "en":
        body = f"""<h1>Privacy policy</h1>
<p class="small">This server runs MascotasPanel, a free, non-commercial pet registry. Below is what is stored, why, who
sees it and your rights, as required by the GDPR (EU Regulation 2016/679) and the Spanish data protection law (LOPDGDD 3/2018).</p>
<h2>Non-profit</h2><p>MascotasPanel is a <b>free, non-profit</b> project, made to help lost pets get home, help shelter animals find a
family and share local dog parks. Nothing is charged, there are no ads and <b>your data is never sold, rented or used for any commercial
purpose</b>.</p>
<h2>Who is responsible for your data</h2><p>{who}. They installed and run this server and decide how it is used.</p>
<h2>What we store, and why</h2><ul>
<li><b>Your account:</b> your first name (no surnames or ID number), username, email and encrypted password. Optional: a phone number and an
approximate area. Used to manage your account and your pets' profiles.</li>
<li><b>Your pets' profiles:</b> photo and the details you write. Used for the QR tag and the "Missing" poster. Only you (and the server admin) can see them, unless you mark the pet as lost or put it up for adoption (associations). For the rest, only the total number is shown.</li>
<li><b>Microchip number:</b> it is linked to you in the official pet registries, so it is treated as personal data. Only stored if you tick
your consent, and never shown.</li>
<li><b>Second contact person:</b> only if you confirm that person has given you permission.</li>
<li><b>If you send a notice</b> to a family from the QR, or write to an association to adopt, without an account: we keep your
message, the contact you leave and, if you tick it, where you are. Only that family or association receives it, the legal basis is your
consent when sending it, and it is deleted after 90 days.</li>
<li><b>Notices</b> that someone sends you from the QR (with their phone or email if they leave it): deleted after 90 days.</li>
<li><b>Dog parks:</b> name, photo and place. Location and camera data are removed from photos. Do not upload photos where people or number plates can be seen.</li>
<li><b>Associations:</b> the association's name and the contact details it chooses to make public, to publish its animals up for adoption.</li>
</ul>
<h2>Legal basis</h2><p>Your <b>consent</b> (GDPR art. 6.1.a), which you give when creating the account and, for each optional item (phone
on the poster, microchip, second contact, public registry), with its own tick box. You can withdraw it at any time from the app,
without it affecting what was done before.</p>
<h2>Who sees it</h2><p>Your details are <b>hidden by default</b>: nobody but the administrator sees your name, email, phone, area or the microchip.
The public only sees what you choose (photo, name and breed of your pets; your phone only with your consent and only while the pet is lost).
The administrator can see all the data to manage the registry and does not give it to anyone.</p>
<h2>Outside services</h2><p>Nothing is sold or shared. The map images come from OpenStreetMap, which sees your IP address like any website.
If the administrator turns on Telegram notifications, they receive short messages through Telegram (for example "New sign-up: Laura"),
with the photo of a pet when it is added or gets lost and the logo of an association. They never include the microchip, the phone or what
someone writes to a family from the QR. If you use the share buttons (Facebook, WhatsApp, X…), that service receives the link you share.</p>
<h2>How long</h2><p>Until you delete your account (it is deleted at once, with your pets and photos). Notices: 90 days.</p>
<h2>Minimum age</h2><p>You must be <b>14 or older</b> to sign up (LOPDGDD art. 7). Younger people need their parents or guardians to do it.</p>
<h2>Which data is required</h2><p>To create an account you need a name, a username, an email and a password. Everything else is optional.
Without the required data the account cannot be created.</p>
<h2>Where it is kept and how it is protected</h2><p>The data is kept on the controller's own server, not on third-party services. The connection
is encrypted (https), passwords are stored encrypted, sign-in attempts are limited and location data is removed from photos. No automated
decisions or profiling are made with your data.</p>
<h2>Transfers outside the EU</h2><p>No data is sent outside the European Union, except the Telegram notices to the administrator if they turn
them on (Telegram may process them outside the EU). Those notices carry minimal data, as explained above.</p>
<h2>Your rights</h2><p>Access, rectification, erasure, objection, restriction and portability. You can do most of it yourself in
<b>My account</b> (edit your details, download your data, delete everything), or by writing to the controller above. If you are not
satisfied, you can complain to the Spanish Data Protection Agency (<a href="https://www.aepd.es" rel="noopener">aepd.es</a>).</p>
<h2>Cookies</h2><p>Only technical cookies to keep you signed in. No analytics, ads or trackers.</p>
<p class="small">Last updated: November 2026.</p>"""
        back = "← Back"
    else:
        body = f"""<h1>Política de privacidad</h1>
<p class="small">Este servidor usa MascotasPanel, un registro de mascotas gratuito y sin ánimo de lucro. Aquí tienes qué se guarda,
para qué, quién lo ve y tus derechos, como piden el RGPD (Reglamento UE 2016/679) y la Ley Orgánica 3/2018 (LOPDGDD).</p>
<h2>Sin ánimo de lucro</h2><p>MascotasPanel es un proyecto <b>gratuito y sin ánimo de lucro</b>, hecho para ayudar a que las mascotas perdidas
vuelvan a casa, a que los animales de las protectoras encuentren familia y a compartir los pipicanes del barrio. No se cobra nada, no hay
publicidad y <b>tus datos no se venden, no se alquilan y no se usan para ningún fin comercial</b>.</p>
<h2>Responsable de tus datos</h2><p>{who}. Es quien ha instalado este servidor, lo gestiona y decide cómo se usa.</p>
<h2>Qué guardamos y para qué</h2><ul>
<li><b>Tu cuenta:</b> tu nombre (sin apellidos ni DNI), usuario, correo y contraseña cifrada. Si quieres: un teléfono y una zona
aproximada. Sirve para gestionar tu cuenta y las fichas de tus mascotas.</li>
<li><b>Las fichas de tus mascotas:</b> foto y los datos que escribas. Sirven para la placa con QR y el cartel «Se busca». Solo las ves tú (y el administrador del servidor), salvo que la marques como perdida o la pongas en adopción (asociaciones). De las demás solo se enseña el número total.</li>
<li><b>Número de microchip:</b> en los registros oficiales está unido a tu nombre, así que se trata como un dato personal. Solo se
guarda si marcas tu consentimiento, y no se enseña nunca.</li>
<li><b>Segunda persona de contacto:</b> solo si confirmas que esa persona te ha dado permiso.</li>
<li><b>Avisos</b> que te mandan desde el QR (con el teléfono o correo de quien lo manda, si lo deja): se borran a los 90 días.</li>
<li><b>Si tú mandas un aviso</b> a una familia desde el QR, o escribes a una asociación para adoptar, sin tener cuenta: guardamos tu mensaje,
el contacto que dejes y, si lo marcas, dónde estás. Solo le llega a esa familia o asociación, la base legal es tu consentimiento al enviarlo y
se borra a los 90 días.</li>
<li><b>Pipicanes:</b> nombre, foto y sitio. A las fotos se les quita la ubicación y los datos de la cámara. No subas fotos en las que se vean personas o matrículas.</li>
<li><b>Asociaciones:</b> el nombre de la asociación y los datos de contacto que ella decida hacer públicos, para dar a conocer sus animales en adopción.</li>
</ul>
<h2>Base legal</h2><p>Tu <b>consentimiento</b> (art. 6.1.a del RGPD), que das al crear la cuenta y, para cada dato opcional (teléfono en
el cartel, microchip, segunda persona, registro público), con su propia casilla. Puedes retirarlo cuando quieras desde la app, sin que
afecte a lo hecho antes.</p>
<h2>Quién lo ve</h2><p>Tus datos están <b>ocultos por defecto</b>: nadie, salvo el administrador, ve tu nombre, tu correo, tu teléfono, tu
zona ni el microchip. En público solo sale lo que tú eliges (foto, nombre y raza de tus mascotas; tu teléfono solo con tu consentimiento
y solo mientras esté perdida). El administrador puede ver todos los datos para gestionar el registro y no se los da a nadie.</p>
<h2>Servicios de fuera</h2><p>No se vende ni se cede nada. Las imágenes del mapa vienen de OpenStreetMap, que ve tu IP como cualquier web.
Si el administrador activa los avisos por Telegram, le llegan mensajes cortos a través de Telegram (por ejemplo «Se ha registrado Laura»),
con la foto de una mascota cuando se apunta o se pierde y el logo de una asociación. Nunca llevan el microchip, el teléfono ni lo que alguien
le escribe a una familia desde el QR. Si usas los botones de compartir (Facebook, WhatsApp, X…), ese servicio recibe el enlace que compartes.</p>
<h2>Cuánto tiempo</h2><p>Hasta que borres tu cuenta (se borra en el momento, con tus mascotas y sus fotos). Los avisos, 90 días.</p>
<h2>Edad mínima</h2><p>Para registrarte tienes que tener <b>14 años o más</b> (art. 7 de la LOPDGDD). Si eres menor, que lo hagan tus padres o tutores.</p>
<h2>Qué datos son obligatorios</h2><p>Para crear la cuenta hacen falta tu nombre, un usuario, tu correo y una contraseña. Todo lo demás es
voluntario. Si no das los obligatorios, no se puede crear la cuenta.</p>
<h2>Dónde están y cómo se protegen</h2><p>Los datos se guardan en el propio servidor del responsable, no en servicios de terceros. La conexión va
cifrada (https), las contraseñas se guardan cifradas, hay un límite de intentos para entrar y a las fotos se les quitan los datos de ubicación.
No se toman decisiones automáticas ni se hacen perfiles con tus datos.</p>
<h2>Transferencias fuera de la UE</h2><p>No se envían datos fuera de la Unión Europea, salvo los avisos de Telegram al administrador si los activa
(Telegram puede tratarlos fuera de la UE). Esos avisos llevan los mínimos datos, como se explica arriba.</p>
<h2>Tus derechos</h2><p>Acceso, rectificación, supresión, oposición, limitación y portabilidad. Casi todo lo puedes hacer tú en <b>Mi cuenta</b>
(cambiar tus datos, descargarlos o borrarlo todo), o escribiendo al responsable de arriba. Si no te atienden bien, puedes reclamar ante la
Agencia Española de Protección de Datos (<a href="https://www.aepd.es" rel="noopener">aepd.es</a>).</p>
<h2>Cookies</h2><p>Solo cookies técnicas para mantener tu sesión. Sin analítica, ni publicidad, ni rastreadores.</p>
<p class="small">Última actualización: noviembre de 2026.</p>"""
        back = "← Volver"
    q = "?lang=en" if lang == "en" else ""
    return _head("Privacidad · MascotasPanel" if lang == "es" else "Privacy · MascotasPanel", lang) + f"""
<body class="home"><header class="bar"><a class="brand" href="/{q}">{LOGO}<span translate="no">Mascotas<b>Panel</b></span></a>{_langlink(lang, "/privacidad")}<a class="btn" href="/panel">{L(lang, 'Entrar')}</a></header>
<main class="doc">{body}<p><a href="/{q}">{back}</a></p></main>{_foot(lang)}</body></html>"""


def render_legal(lang, lg, base) -> str:
    who = _who(lg, lang)
    if lang == "en":
        body = f"""<h1>Legal notice</h1>
<h2>Owner</h2><p>{who}. Website: {esc(base)}</p>
<h2>What this website is</h2><p>A free, <b>non-profit</b> pet registry: QR tags, "Missing" posters, lost pets, dog parks and animals up for
adoption from associations. Nothing is charged, there are no ads and no data is sold or shared. It runs on MascotasPanel (PolyForm Noncommercial licence).</p>
<h2>Rules of use</h2><ul><li>Only upload real pets and photos you are allowed to use. No photos where people can be recognised.</li>
<li>Do not put other people's details without their permission.</li>
<li><b>Selling animals is not allowed.</b> Only verified associations and shelters can publish animals up for adoption.</li>
<li>The administrator can hide or delete anything that breaks these rules, and block accounts.</li></ul>
<h2>Responsibility</h2><p>Each person is responsible for what they publish. The information is shared in good faith to help pets get home or
find a family; the owner of this website cannot guarantee it is always correct or available.</p>
<h2>Intellectual property</h2><p>Photos and texts belong to whoever uploads them, who allows them to be shown on this website until deleted.
The MascotasPanel software is under the PolyForm Noncommercial licence. Maps are from OpenStreetMap (ODbL licence).</p>
<h2>Applicable law</h2><p>This website is governed by Spanish law, in particular Law 34/2002 on information society services (LSSI), the GDPR
and the LOPDGDD.</p>
<h2>Privacy</h2><p>See the <a href="/privacidad?lang=en">privacy policy</a>.</p>"""
        back = "← Back"
    else:
        body = f"""<h1>Aviso legal</h1>
<h2>Titular</h2><p>{who}. Web: {esc(base)}</p>
<h2>Qué es esta web</h2><p>Un registro de mascotas gratuito y <b>sin ánimo de lucro</b>: placas con QR, carteles «Se busca», mascotas perdidas,
pipicanes y animales en adopción de asociaciones. No se cobra nada, no tiene publicidad y no se venden ni se ceden datos. Funciona con MascotasPanel (licencia PolyForm Noncommercial).</p>
<h2>Normas de uso</h2><ul><li>Sube solo mascotas reales y fotos que puedas usar. Nada de fotos en las que se reconozca a personas.</li>
<li>No pongas datos de otras personas sin su permiso.</li>
<li><b>No se permite vender animales.</b> Solo las asociaciones y protectoras verificadas pueden publicar animales en adopción.</li>
<li>El administrador puede ocultar o borrar lo que no cumpla estas normas y bloquear cuentas.</li></ul>
<h2>Responsabilidad</h2><p>Cada persona es responsable de lo que publica. La información se comparte de buena fe para ayudar a que las
mascotas vuelvan a casa o encuentren familia; el titular no puede garantizar que sea siempre exacta ni que la web esté siempre disponible.</p>
<h2>Propiedad intelectual</h2><p>Las fotos y los textos son de quien los sube, que da permiso para enseñarlos en esta web mientras no los borre.
El programa MascotasPanel tiene licencia PolyForm Noncommercial. Los mapas son de OpenStreetMap (licencia ODbL).</p>
<h2>Ley aplicable</h2><p>Esta web se rige por la ley española, en especial la Ley 34/2002 de servicios de la sociedad de la información (LSSI),
el RGPD y la LOPDGDD.</p>
<h2>Privacidad</h2><p>Mira la <a href="/privacidad">política de privacidad</a>.</p>"""
        back = "← Volver"
    q = "?lang=en" if lang == "en" else ""
    return _head(("Legal notice" if lang == "en" else "Aviso legal") + " · MascotasPanel", lang) + f"""
<body class="home"><header class="bar"><a class="brand" href="/{q}">{LOGO}<span translate="no">Mascotas<b>Panel</b></span></a>{_langlink(lang, "/aviso-legal")}<a class="btn" href="/panel">{L(lang, 'Entrar')}</a></header>
<main class="doc">{body}<p><a href="/{q}">{back}</a></p></main>{_foot(lang)}</body></html>"""


def render_404(lang="es") -> str:
    t, p = (("This page does not exist", "The link may be mistyped or the profile may have been deleted.") if lang == "en"
            else ("Esta página no existe", "Puede que el enlace esté mal escrito o que la ficha se haya borrado."))
    return _head(t, lang) + f"""<body class="home"><header class="bar"><a class="brand" href="/">{LOGO}<span translate="no">Mascotas<b>Panel</b></span></a><a class="btn" href="/panel">Entrar</a></header>
<main class="doc"><h1>{t}</h1><p>{p}</p></main></body></html>"""
