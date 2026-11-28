"""MascotasPanel: registro libre de mascotas, con ficha, QR y cartel «Se busca»."""
import base64, io, re, secrets, time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

import segno
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import bot, db, page
from .config import ALLOW_REGISTER, CONTACT_EMAIL, MAX_PETS, OWNER_NAME, PHOTOS, PUBLIC_URL
from .version import VERSION

STATIC = Path(__file__).parent / "static"
COOKIE = "mascotaspanel_sesion"


@asynccontextmanager
async def lifespan(_app):
    db.init()
    import os
    if os.environ.get("MASCOTAS_NO_BOT") != "1":
        bot.start()  # escucha los botones y comandos del bot de Telegram (si hay token)
    yield


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")

USER_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")
CODE_RE = re.compile(r"^[a-z0-9]{6,16}$")
SPECIES = tuple(page.SPECIES)
# Mapas: las teselas vienen de OpenStreetMap y el buscador de sitios de Nominatim (gratis, sin clave)
CSP = ("default-src 'self'; img-src 'self' data: blob: https://tile.openstreetmap.org; "
       "connect-src 'self' https://nominatim.openstreetmap.org; style-src 'self' 'unsafe-inline'; script-src 'self'; "
       "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'self'")


@app.middleware("http")
async def security(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.method not in ("GET", "HEAD"):
        # cabecera propia: un formulario de otra web no puede enviarla (protección CSRF)
        if request.headers.get("x-mascotaspanel") != "1":
            return JSONResponse({"detail": "Petición no permitida"}, status_code=403)
    r = await call_next(request)
    p = request.url.path
    if (request.method == "GET" and (p in ("/", "/pipicanes", "/adopta", "/asociaciones", "/privacidad", "/aviso-legal") or p.startswith(("/asociacion/", "/m/")))
            and request.cookies.get(COOKIE) and db.session_user(request.cookies.get(COOKIE, ""))):
        # Con la sesión abierta, las páginas públicas no dicen «Entrar» (parecía que se había cerrado la sesión)
        body = b"".join([c async for c in r.body_iterator]).decode()
        body = (body.replace('<a class="btn" href="/panel">Entrar</a>', '<a class="btn" href="/panel">🏠 Mi panel</a>')
                    .replace('<a class="btn" href="/panel">Sign in</a>', '<a class="btn" href="/panel">🏠 My panel</a>'))
        h = {k: v for k, v in r.headers.items() if k.lower() not in ("content-length",)}
        r = HTMLResponse(body, status_code=r.status_code, headers=h)
    r.headers.setdefault("X-Content-Type-Options", "nosniff")
    r.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    r.headers.setdefault("Content-Security-Policy", CSP)
    r.headers.setdefault("Permissions-Policy", "interest-cohort=(), browsing-topics=()")
    return r


# --- utilidades ------------------------------------------------------------
def err(code, msg):
    raise HTTPException(code, msg)


def text(v, n) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(v or "")).strip()[:n]


def clean_phone(v) -> str:
    p = text(v, 30)
    if p and not re.match(r"^\+?[\d\s().-]{6,20}$", p):
        err(400, "Ese teléfono no parece válido. Escríbelo así: +34 600 123 456")
    return p


def clean_email(v) -> str:
    e = text(v, 120).lower()
    if not EMAIL_RE.match(e):
        err(400, "Ese correo no parece válido")
    return e


def user_or_401(request: Request):
    u = db.session_user(request.cookies.get(COOKIE, ""))
    if not u:
        err(401, "Tienes que entrar")
    return u


def admin_or_403(request: Request):
    u = user_or_401(request)
    if not u["is_admin"]:
        err(403, "Solo para el administrador")
    return u


def own_pet(u, pet_id: int):
    p = db.q1("SELECT * FROM pets WHERE id=?", pet_id)
    if not p or (p["user_id"] != u["id"] and not u["is_admin"]):
        err(404, "Mascota no encontrada")
    return p


def base_url(request: Request) -> str:
    pub = db.get_setting("public_url") or PUBLIC_URL
    if pub:
        return pub
    return f"{request.url.scheme}://{request.headers.get('host', request.url.netloc)}"


def legal() -> dict:
    """Quién es el responsable de los datos (RGPD). Lo rellena el administrador; si no, sale lo del .env."""
    return {"legal_name": db.get_setting("legal_name") or OWNER_NAME, "legal_email": db.get_setting("legal_email") or CONTACT_EMAIL,
            "legal_place": db.get_setting("legal_place")}


def registration_open() -> bool:
    v = db.get_setting("allow_register")
    return ALLOW_REGISTER if v == "" else v == "1"


def clean_public_url(raw) -> str:
    u = str(raw or "").strip().rstrip("/")
    if not u:
        return ""
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u
    parts = urlsplit(u)
    if not parts.hostname or parts.path not in ("", "/") or parts.query or " " in u:
        err(400, "Escribe solo la dirección, por ejemplo https://mascotas.midominio.com")
    return f"{parts.scheme.lower()}://{parts.netloc.lower()}"


CONSENT_V = "2026-11"  # versión del texto de privacidad que se acepta al registrarse


def org_json(o, public=False):
    """Perfil de una asociación. En público solo sale el contacto que la asociación ha elegido enseñar."""
    if not o:
        return None
    d = {"id": o["user_id"], "name": o["name"], "city": o["city"], "about": o["about"], "web": o["web"],
         "logo": f"/f/{o['logo']}" if o["logo"] else "", "verified": bool(o["verified"]), "telegram": o["telegram"],
         "legal_name": o["legal_name"] or "", "cif": o["cif"] or "", "reg_number": o["reg_number"] or "", "zoo_number": o["zoo_number"] or ""}
    if public:
        d |= {"phone": o["phone"] if o["show_phone"] else "", "whatsapp": _wa_num(o["phone"]) if o["whatsapp"] and o["phone"] else "",
              "email": o["email"] if o["show_email"] else ""}
    else:
        d |= {"phone": o["phone"], "show_phone": bool(o["show_phone"]), "whatsapp": bool(o["whatsapp"]),
              "email": o["email"], "show_email": bool(o["show_email"])}
    return d


def clean_cif(v):
    """CIF o NIF de la asociación: letra + 7 cifras + control (las asociaciones suelen empezar por G). Vacío vale."""
    c = re.sub(r"[\s.-]", "", str(v or "")).upper()[:12]
    if c and not re.fullmatch(r"[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]", c):
        err(400, "El CIF es una letra y 8 caracteres, como G12345678")
    return c


def _wa_num(p):
    d = re.sub(r"\D", "", p or "")
    return "34" + d if len(d) == 9 and d[0] in "6789" else d


def get_org(user_id):
    return db.q1("SELECT * FROM orgs WHERE user_id=?", user_id)


def user_json(u):
    d = {"id": u["id"], "username": u["username"], "email": u["email"], "name": u["name"], "phone": u["phone"], "zone": u["zone"],
         "is_admin": bool(u["is_admin"]), "kind": u["kind"] or "person",
         "avatar": f"/f/{u['avatar']}" if "avatar" in u.keys() and u["avatar"] else ""}
    if d["kind"] == "org":
        d["org"] = org_json(get_org(u["id"]))
    return d


def pet_json(p, base=""):
    d = {k: p[k] for k in ("id", "code", "name", "species", "breed", "color", "sex", "age", "size", "chip",
                           "notes", "health", "contact", "contact2_name", "contact2_phone", "lost_at", "lost_zone", "lost_note", "reward", "lost_lat", "lost_lng",
                           "tracker_lat", "tracker_lng", "tracker_at", "tracker_kind", "created", "updated")}
    d |= {"chip_ok": bool(p["chip_ok"]), "chip_search": bool(p["chip_search"]), "contact2_ok": bool(p["contact2_ok"]),
          "adopt": bool(p["adopt"]), "adopt_text": p["adopt_text"]}
    d |= {"lost": bool(p["lost"]), "hidden": bool(p["hidden"]), "public": bool(p["public"]),
          "photo": f"/f/{p['photo']}" if p["photo"] else ""}
    to = p["transfer_to"] if "transfer_to" in p.keys() else 0
    if to:
        t = db.q1("SELECT name, username FROM users WHERE id=?", to)
        d["transfer_to"] = {"name": t["name"], "username": t["username"]} if t else None
    if base:
        d["url"] = f"{base}/m/{p['code']}"
    return d


# --- límite de intentos ------------------------------------------------------
_fails: dict = {}


def _client(request: Request) -> str:
    return request.client.host if request.client else "?"


def check_rate(request: Request):
    f = _fails.get(_client(request))
    if f and f[0] >= 8 and f[1] > time.time():
        err(429, "Demasiados intentos. Espera unos minutos.")


def note_fail(request: Request):
    ip = _client(request)
    n, until = _fails.get(ip, (0, 0))
    if until < time.time():
        n = 0
    _fails[ip] = (n + 1, time.time() + 600)


def set_cookie(r, name, value, request):
    r.set_cookie(name, value, max_age=30 * 86400, httponly=True, samesite="lax",
                 secure=request.url.scheme == "https")


def find_user(login):
    """Busca por usuario o por correo."""
    v = text(login, 120)
    return db.q1("SELECT * FROM users WHERE username=? OR email=?", v, v.lower()) if v else None


def clean_username(v) -> str:
    n = text(v, 32)
    if not USER_RE.match(n):
        err(400, "El usuario debe tener de 3 a 32 letras, números, puntos, guiones o _")
    return n


# --- cuenta ----------------------------------------------------------------
@app.get("/api/me")
def me(request: Request):
    u = db.session_user(request.cookies.get(COOKIE, ""))
    no_users = db.q1("SELECT COUNT(*) n FROM users")["n"] == 0
    info = {"version": VERSION, "allow_register": registration_open() or no_users, "first_user": no_users, "legal": legal(),
            "max_pets": MAX_PETS, "base": base_url(request)}
    if u:
        info["unread"] = db.q1("SELECT COUNT(*) n FROM messages WHERE user_id=? AND read=0", u["id"])["n"]
        info["transfers"] = _transfers_for(u)
    return info | {"user": user_json(u) if u else None}


@app.post("/api/login")
async def login(request: Request):
    check_rate(request)
    d = await request.json()
    u = find_user(d.get("login"))
    if not u or not db.check_pw(str(d.get("password") or ""), u["pw_hash"]):
        note_fail(request)
        err(401, "Usuario o contraseña incorrectos")
    if u["status"] != "approved":
        err(403, "Esta cuenta está bloqueada. Habla con el administrador")
    _fails.pop(_client(request), None)
    cur_tok = request.cookies.get(COOKIE, "")
    cur = db.session_user(cur_tok)
    keep = [cur_tok] if cur and cur["id"] != u["id"] else []
    if cur and cur["id"] == u["id"]:
        db.run("DELETE FROM sessions WHERE token=?", cur_tok)
    r = JSONResponse({"ok": True})
    set_cookie(r, COOKIE, db.new_session(u["id"]), request)
    _save_accounts(r, request, keep + _accounts(request), u["id"])
    return r


class LogoutReq(BaseModel):
    all: bool = False


@app.post("/api/logout")
def logout(request: Request, b: LogoutReq | None = None):
    db.run("DELETE FROM sessions WHERE token=?", request.cookies.get(COOKIE, ""))
    r = JSONResponse({"ok": True})
    r.delete_cookie(COOKIE)
    if b and b.all:
        for t in _accounts(request):
            db.run("DELETE FROM sessions WHERE token=?", t)
        r.delete_cookie(ACCOUNTS)
    return r


# --- cambio rápido de usuario ------------------------------------------------
# Las cuentas abiertas en este dispositivo se recuerdan (cada una con su sesión, en una
# cookie que el JavaScript no puede leer) y se puede pasar de una a otra sin contraseña.
ACCOUNTS = "mp_accounts"
MAX_ACCOUNTS = 6


def _accounts(request: Request) -> list[str]:
    return [t for t in request.cookies.get(ACCOUNTS, "").split(".") if t][:MAX_ACCOUNTS * 2]


def _clean_accounts(toks, current_uid):
    out, seen = [], {current_uid}
    for t in dict.fromkeys(toks):
        u = db.session_user(t)
        if not u:
            continue
        if u["id"] in seen or len(out) >= MAX_ACCOUNTS:
            db.run("DELETE FROM sessions WHERE token=?", t)
            continue
        seen.add(u["id"])
        out.append((t, u))
    return out


def _save_accounts(r, request: Request, toks, current_uid):
    good = [t for t, _ in _clean_accounts(toks, current_uid)]
    if good:
        set_cookie(r, ACCOUNTS, ".".join(good), request)
    elif request.cookies.get(ACCOUNTS):
        r.delete_cookie(ACCOUNTS)


@app.get("/api/accounts")
def accounts_list(request: Request):
    cur = db.session_user(request.cookies.get(COOKIE, ""))
    toks = _accounts(request)
    found = _clean_accounts(toks, cur["id"] if cur else None)
    r = JSONResponse({"current": cur["username"] if cur else None,
                      "accounts": [{"username": u["username"], "name": u["name"]} for _, u in found]})
    if [t for t, _ in found] != toks:
        _save_accounts(r, request, toks, cur["id"] if cur else None)
    return r


class AccountReq(BaseModel):
    username: str


@app.post("/api/accounts/switch")
def accounts_switch(b: AccountReq, request: Request):
    cur_tok = request.cookies.get(COOKIE, "")
    cur = db.session_user(cur_tok)
    found = _clean_accounts(_accounts(request), cur["id"] if cur else None)
    target = next((t for t, u in found if u["username"].lower() == b.username.lower()), None)
    if not target:
        err(400, "Esa cuenta ya no tiene la sesión abierta aquí. Entra con su contraseña")
    rest = ([cur_tok] if cur else []) + [t for t, _ in found if t != target]
    r = JSONResponse({"ok": True})
    set_cookie(r, COOKIE, target, request)
    _save_accounts(r, request, rest, db.session_user(target)["id"])
    return r


@app.post("/api/accounts/forget")
def accounts_forget(b: AccountReq, request: Request):
    cur = db.session_user(request.cookies.get(COOKIE, ""))
    rest = []
    for t, u in _clean_accounts(_accounts(request), cur["id"] if cur else None):
        if u["username"].lower() == b.username.lower():
            db.run("DELETE FROM sessions WHERE token=?", t)
        else:
            rest.append(t)
    r = JSONResponse({"ok": True})
    _save_accounts(r, request, rest, cur["id"] if cur else None)
    return r


@app.post("/api/register")
async def register(request: Request):
    check_rate(request)
    first = db.q1("SELECT COUNT(*) n FROM users")["n"] == 0
    if not registration_open() and not first:
        err(403, "El registro está cerrado")
    d = await request.json()
    name, pw = text(d.get("name"), 40), str(d.get("password") or "")
    username = clean_username(d.get("username"))
    email = clean_email(d.get("email"))
    phone = clean_phone(d.get("phone"))
    if len(name) < 2:
        err(400, "Escribe tu nombre (sin apellidos)")
    if len(pw) < 8:
        err(400, "La contraseña debe tener al menos 8 caracteres")
    if not d.get("age_ok"):
        err(400, "Para registrarte tienes que tener 14 años o más")
    if not d.get("accept"):
        err(400, "Tienes que aceptar la política de privacidad")
    kind = "org" if d.get("kind") == "org" else "person"
    org_name = text(d.get("org_name"), 80)
    if kind == "org" and len(org_name) < 3:
        err(400, "Escribe el nombre de la asociación o protectora")
    org_cif = clean_cif(d.get("org_cif")) if kind == "org" else ""
    if db.q1("SELECT 1 FROM users WHERE username=?", username):
        note_fail(request)
        err(409, "Ese usuario ya existe. Elige otro")
    if db.q1("SELECT 1 FROM users WHERE email=?", email):
        note_fail(request)
        err(409, "Ya hay una cuenta con ese correo")
    now, code = time.time(), db.new_recovery()
    cur = db.run("INSERT INTO users(username,email,name,phone,zone,pw_hash,recovery_hash,is_admin,status,consent,created,kind,age_ok,consent_v) "
                 "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", username, email, name, phone, text(d.get("zone"), 80), db.hash_pw(pw),
                 db.hash_recovery(code), int(first), "approved", now, now, kind, now, CONSENT_V)
    if kind == "org":
        legal = {"legal_name": text(d.get("org_legal"), 120), "cif": org_cif, "reg_number": text(d.get("org_reg"), 60),
                 "zoo_number": text(d.get("org_zoo"), 60)}
        db.run("INSERT INTO orgs(user_id,name,city,email,verified,created,legal_name,cif,reg_number,zoo_number) VALUES(?,?,?,?,?,?,?,?,?,?)",
               cur.lastrowid, org_name, text(d.get("zone"), 80), email, int(first), now, *legal.values())
        notify(f"🏡 Nueva asociación registrada: {org_name}\n👤 {name} (@{username}) · ✉️ {email}"
               + (f"\n🏛️ {legal['legal_name']}" if legal["legal_name"] else "") + (f" · CIF {org_cif}" if org_cif else "")
               + (f"\n📋 Registro: {legal['reg_number']}" if legal["reg_number"] else "")
               + (f"\n🏠 Núcleo zoológico: {legal['zoo_number']}" if legal["zoo_number"] else "")
               + (f"\n📍 {text(d.get('zone'), 80)}" if d.get("zone") else "")
               + "\nCompruébala y verifícala para que pueda publicar animales en adopción." + notify_url("/panel"),
               buttons=[[("✅ Verificar asociación", f"org_ok:{cur.lastrowid}")]])
    elif not first:
        notify(f"👤 Nueva persona registrada: {name} (@{username})" + (f" · 📍 {text(d.get('zone'), 80)}" if d.get("zone") else ""))
    return {"ok": True, "recovery": code}


@app.post("/api/recover")
async def recover(request: Request):
    """¿Olvidaste el usuario o la contraseña? Con el correo (o usuario) y el código de recuperación
    se pone una contraseña nueva. Devuelve el usuario y un código nuevo (el viejo deja de valer)."""
    check_rate(request)
    d = await request.json()
    code = db.norm_recovery(d.get("code"))
    u = db.q1("SELECT * FROM users WHERE recovery_hash=?", db.hash_recovery(code)) if len(code) == 12 else None
    login = text(d.get("login"), 120)
    if u and login and login.lower() not in (u["username"].lower(), u["email"].lower()):
        u = None
    if not u:
        note_fail(request)
        err(400, "El código de recuperación no es correcto")
    pw = str(d.get("password") or "")
    if len(pw) < 8:
        err(400, "La contraseña nueva debe tener al menos 8 caracteres")
    new = db.new_recovery()
    db.run("UPDATE users SET pw_hash=?, recovery_hash=? WHERE id=?", db.hash_pw(pw), db.hash_recovery(new), u["id"])
    db.run("DELETE FROM sessions WHERE user_id=?", u["id"])
    _fails.pop(_client(request), None)
    return {"ok": True, "username": u["username"], "recovery": new}


@app.post("/api/recovery/new")
async def recovery_new(request: Request):
    """Genera otro código de recuperación (pide la contraseña)."""
    u = user_or_401(request)
    d = await request.json()
    if not db.check_pw(str(d.get("password") or ""), u["pw_hash"]):
        err(400, "La contraseña no es correcta")
    new = db.new_recovery()
    db.run("UPDATE users SET recovery_hash=? WHERE id=?", db.hash_recovery(new), u["id"])
    return {"recovery": new}


@app.put("/api/profile")
async def profile(request: Request):
    u = user_or_401(request)
    d = await request.json()
    f = {}
    if "name" in d:
        f["name"] = text(d["name"], 40)
        if len(f["name"]) < 2:
            err(400, "Escribe tu nombre (sin apellidos)")
    if "phone" in d:
        f["phone"] = clean_phone(d["phone"])
    if "zone" in d:
        f["zone"] = text(d["zone"], 80)
    if "username" in d:
        f["username"] = clean_username(d["username"])
        if db.q1("SELECT 1 FROM users WHERE username=? AND id<>?", f["username"], u["id"]):
            err(409, "Ese usuario ya existe. Elige otro")
    if "email" in d:
        f["email"] = clean_email(d["email"])
        if db.q1("SELECT 1 FROM users WHERE email=? AND id<>?", f["email"], u["id"]):
            err(409, "Ya hay una cuenta con ese correo")
    if f:
        db.run(f"UPDATE users SET {', '.join(k + '=?' for k in f)} WHERE id=?", *f.values(), u["id"])
    return user_json(db.q1("SELECT * FROM users WHERE id=?", u["id"]))


@app.post("/api/password")
async def change_password(request: Request):
    u = user_or_401(request)
    d = await request.json()
    if not db.check_pw(str(d.get("old") or ""), u["pw_hash"]):
        err(400, "La contraseña actual no es correcta")
    new = str(d.get("new") or "")
    if len(new) < 8:
        err(400, "La contraseña nueva debe tener al menos 8 caracteres")
    db.run("UPDATE users SET pw_hash=? WHERE id=?", db.hash_pw(new), u["id"])
    db.run("DELETE FROM sessions WHERE user_id=? AND token<>?", u["id"], request.cookies.get(COOKIE, ""))
    return {"ok": True}


def _delete_pet(p):
    if p["photo"]:
        (PHOTOS / p["photo"]).unlink(missing_ok=True)
    db.run("DELETE FROM messages WHERE pet_id=?", p["id"])
    db.run("DELETE FROM pets WHERE id=?", p["id"])


def _delete_user_data(user_id: int):
    for p in db.q("SELECT * FROM pets WHERE user_id=?", user_id):
        _delete_pet(p)
    db.run("DELETE FROM sessions WHERE user_id=?", user_id)
    db.run("DELETE FROM messages WHERE user_id=?", user_id)
    db.run("UPDATE parks SET user_id=0 WHERE user_id=?", user_id)  # el pipicán sigue en el mapa, sin saber quién lo puso
    o = get_org(user_id)
    if o and o["logo"]:
        (PHOTOS / o["logo"]).unlink(missing_ok=True)
    db.run("DELETE FROM orgs WHERE user_id=?", user_id)
    av = db.q1("SELECT avatar FROM users WHERE id=?", user_id)
    if av and av["avatar"]:
        (PHOTOS / av["avatar"]).unlink(missing_ok=True)
    db.run("DELETE FROM users WHERE id=?", user_id)


@app.post("/api/account/delete")
async def delete_account(request: Request):
    """Derecho de supresión (RGPD): borra la cuenta, sus mascotas y sus fotos."""
    u = user_or_401(request)
    d = await request.json()
    if not db.check_pw(str(d.get("password") or ""), u["pw_hash"]):
        err(400, "La contraseña no es correcta")
    if u["is_admin"] and db.q1("SELECT COUNT(*) n FROM users WHERE is_admin=1")["n"] == 1 \
            and db.q1("SELECT COUNT(*) n FROM users")["n"] > 1:
        err(400, "Eres el único administrador: nombra antes a otro")
    _delete_user_data(u["id"])
    r = JSONResponse({"ok": True})
    r.delete_cookie(COOKIE)
    return r


@app.get("/api/export")
def export(request: Request):
    """Descarga de todos tus datos (derecho de portabilidad del RGPD)."""
    u = user_or_401(request)
    pets = [pet_json(p, base_url(request)) for p in db.q("SELECT * FROM pets WHERE user_id=? ORDER BY id", u["id"])]
    data = {"usuario": u["username"], "nombre": u["name"], "correo": u["email"], "telefono": u["phone"], "zona": u["zone"],
            "cuenta_creada": u["created"], "consentimiento": u["consent"], "mascotas": pets,
            "pipicanes": [park_json(r) for r in db.q("SELECT * FROM parks WHERE user_id=?", u["id"])],
            "asociacion": org_json(get_org(u["id"])), "mayor_de_14_confirmado": u["age_ok"], "version_privacidad_aceptada": u["consent_v"],
            "app": f"MascotasPanel {VERSION}"}
    return JSONResponse(data, headers={"Content-Disposition": 'attachment; filename="mascotaspanel-mis-datos.json"'})


# --- mascotas --------------------------------------------------------------
@app.get("/api/pets")
def list_pets(request: Request):
    u = user_or_401(request)
    b = base_url(request)
    return [pet_json(p, b) for p in db.q("SELECT * FROM pets WHERE user_id=? ORDER BY id", u["id"])]


def pet_fields(d) -> dict:
    f = {}
    for k, n in (("name", 40), ("breed", 60), ("color", 120), ("age", 30),
                 ("notes", 600), ("health", 400), ("lost_zone", 120), ("lost_note", 300), ("reward", 60)):
        if k in d:
            f[k] = text(d[k], n)
    if "species" in d:
        f["species"] = d["species"] if d["species"] in SPECIES else "otro"
    if "sex" in d:
        f["sex"] = d["sex"] if d["sex"] in ("macho", "hembra") else ""
    if "size" in d:
        f["size"] = d["size"] if d["size"] in ("pequeno", "mediano", "grande") else ""
    if "contact2_name" in d:
        f["contact2_name"] = text(d["contact2_name"], 40)
    if "contact2_phone" in d:
        f["contact2_phone"] = clean_phone(d["contact2_phone"])
        # son datos de otra persona: hace falta que ella esté de acuerdo
        if f["contact2_phone"] and not d.get("contact2_ok"):
            err(400, "Para poner el teléfono de otra persona tienes que marcar que te ha dado permiso")
        f["contact2_ok"] = time.time() if f["contact2_phone"] else None
    if "adopt_text" in d:
        f["adopt_text"] = text(d["adopt_text"], 300)
    if "adopt" in d:
        f["adopt"] = int(bool(d["adopt"]))
    if "chip" in d:
        # el microchip identifica al animal en el registro oficial: solo se guarda con consentimiento expreso
        f["chip"] = re.sub(r"[^\dA-Za-z -]", "", text(d["chip"], 30))
        if f["chip"] and not d.get("chip_ok"):
            err(400, "Para guardar el número de microchip tienes que marcar que das tu consentimiento")
        f["chip_ok"] = time.time() if f["chip"] else None
        f["chip_search"] = int(bool(f["chip"] and d.get("chip_search")))
    if "contact" in d:
        # el teléfono está oculto salvo que el dueño dé su consentimiento («lost»: se ve solo mientras esté perdida)
        f["contact"] = "lost" if d["contact"] in ("lost", "always") else "never"
    if "lost" in d:
        f["lost"] = int(bool(d["lost"]))
    if "public" in d:
        f["public"] = int(bool(d["public"]))
    if "lost_lat" in d or "lost_lng" in d:
        # dónde se perdió, redondeado a 3 decimales (unos 100 m): suficiente para buscar, sin dar una casa exacta
        try:
            lat, lng = float(d.get("lost_lat")), float(d.get("lost_lng"))
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                raise ValueError
            f["lost_lat"], f["lost_lng"] = round(lat, 3), round(lng, 3)
        except (TypeError, ValueError):
            f["lost_lat"] = f["lost_lng"] = None
    if "tracker_kind" in d:
        f["tracker_kind"] = d["tracker_kind"] if d["tracker_kind"] in ("google", "apple") else ""
    if "tracker_lat" in d or "tracker_lng" in d:
        # última posición del localizador de Google: la pone el dueño a mano (Google no deja leerla desde otra app)
        try:
            lat, lng = float(d.get("tracker_lat")), float(d.get("tracker_lng"))
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                raise ValueError
            f["tracker_lat"], f["tracker_lng"] = round(lat, 4), round(lng, 4)
            try:
                at = float(d.get("tracker_at"))
            except (TypeError, ValueError):
                at = time.time()
            f["tracker_at"] = min(at, time.time())
        except (TypeError, ValueError):
            f["tracker_lat"] = f["tracker_lng"] = f["tracker_at"] = None
    return f


def check_adopt(u, f):
    """Solo las asociaciones pueden poner animales en adopción (y se ven cuando el administrador las verifica).
    Vender animales no está permitido."""
    if f.get("adopt") and (u["kind"] or "person") != "org":
        err(400, "Solo las asociaciones y protectoras pueden poner animales en adopción")


@app.post("/api/pets")
async def create_pet(request: Request):
    u = user_or_401(request)
    if db.q1("SELECT COUNT(*) n FROM pets WHERE user_id=?", u["id"])["n"] >= MAX_PETS:
        err(400, f"Puedes tener como mucho {MAX_PETS} mascotas")
    d = await request.json()
    f = pet_fields(d)
    check_adopt(u, f)
    if not f.get("name"):
        err(400, "Escribe el nombre de tu mascota")
    now = time.time()
    f.setdefault("public", 0)  # en el registro público solo si el dueño lo marca
    f |= {"user_id": u["id"], "code": db.new_code(), "created": now, "updated": now}
    if f.get("lost"):
        f["lost_at"] = now
    cur = db.run(f"INSERT INTO pets({','.join(f)}) VALUES({','.join('?' * len(f))})", *f.values())
    pid = cur.lastrowid
    sp = _sp(f.get("species"))
    notify(f"{sp[2]} Nueva mascota: {f['name']} ({sp[0].lower()}{', ' + f['breed'] if f.get('breed') else ''}), de {u['name']}"
           + ("\n🏡 En adopción" if f.get("adopt") else "") + notify_url(f"/m/{f['code']}"),
           photo=lambda: _photo((db.q1("SELECT photo FROM pets WHERE id=?", pid) or {"photo": ""})["photo"]), delay=20)
    return pet_json(db.q1("SELECT * FROM pets WHERE id=?", cur.lastrowid), base_url(request))


@app.get("/api/pets/{pet_id}")
def get_pet(pet_id: int, request: Request):
    return pet_json(own_pet(user_or_401(request), pet_id), base_url(request))


@app.put("/api/pets/{pet_id}")
async def update_pet(pet_id: int, request: Request):
    u = user_or_401(request)
    p = own_pet(u, pet_id)
    d = await request.json()
    f = pet_fields(d)
    owner = db.q1("SELECT * FROM users WHERE id=?", p["user_id"])
    check_adopt(owner, f)
    if f.get("adopt") and not p["adopt"]:
        notify(f"🏡 {p['name']} está en adopción ({_sp(p['species'])[0].lower()})" + notify_url(f"/m/{p['code']}"), photo=_photo(p["photo"]))
    if "name" in f and not f["name"]:
        err(400, "Escribe el nombre de tu mascota")
    if f.get("lost") and not p["lost"]:
        f["lost_at"] = time.time()
        zone = f.get("lost_zone") or p["lost_zone"]
        sp = _sp(p["species"])
        notify(f"🚨🚨 PERDIDO: {p['name'].upper()}\n{sp[2]} {sp[0]}{' · ' + p['breed'] if p['breed'] else ''}{' · ' + p['color'] if p['color'] else ''}"
               + (f"\n📍 Se perdió en {zone}" if zone else "") + (f"\n📣 {f.get('lost_note')}" if f.get("lost_note") else "")
               + f"\n👤 Familia: {owner['name']}" + notify_url(f"/m/{p['code']}"), photo=_photo(p["photo"]))
    mistake = bool(d.get("mistake"))  # «Me he equivocado»: se quita el aviso y sus datos, como si no hubiera pasado
    if "lost" in f and not f["lost"] and p["lost"]:
        if mistake:
            notify(f"↩️ Aviso de {p['name']} retirado: se marcó como perdido por error.")
        else:
            notify(f"🏠🎉 {p['name']} ya está en casa. ¡Encontrado!", photo=_photo(p["photo"]))
    if "lost" in f and not f["lost"] and mistake:
        f["lost_zone"] = f["lost_note"] = f["reward"] = ""
    if "lost" in f and not f["lost"]:
        f["lost_at"] = f["lost_lat"] = f["lost_lng"] = None
        f["tracker_lat"] = f["tracker_lng"] = f["tracker_at"] = None
        db.run("DELETE FROM sightings WHERE pet_id=?", pet_id)  # ya está en casa: los avistamientos dejan de servir
    f["updated"] = time.time()
    db.run(f"UPDATE pets SET {', '.join(k + '=?' for k in f)} WHERE id=?", *f.values(), pet_id)
    return pet_json(db.q1("SELECT * FROM pets WHERE id=?", pet_id), base_url(request))


# --- pasar una ficha a otra cuenta (con su foto, su QR y sus avisos) ---------
def _transfers_for(u):
    return [{"pet": r["id"], "name": r["name"], "species": r["species"], "photo": f"/f/{r['photo']}" if r["photo"] else "",
             "from": r["owner"]} for r in db.q("SELECT p.*, u.name owner FROM pets p JOIN users u ON u.id=p.user_id "
                                                "WHERE p.transfer_to=? ORDER BY p.id", u["id"])]


def _move_pet(p, to_id):
    db.run("UPDATE pets SET user_id=?, transfer_to=0, updated=? WHERE id=?", to_id, time.time(), p["id"])
    db.run("UPDATE messages SET user_id=? WHERE pet_id=?", to_id, p["id"])


@app.post("/api/pets/{pet_id}/transfer")
async def transfer_pet(pet_id: int, request: Request):
    """El dueño ofrece la ficha a otra cuenta (que tiene que aceptar). El administrador la pasa directamente."""
    u = user_or_401(request)
    p = own_pet(u, pet_id)
    d = await request.json()
    if d.get("cancel"):
        db.run("UPDATE pets SET transfer_to=0 WHERE id=?", p["id"])
        return pet_json(db.q1("SELECT * FROM pets WHERE id=?", p["id"]), base_url(request))
    who = text(d.get("to", ""), 120).lstrip("@").lower()
    if not who:
        err(400, "Escribe el usuario o el correo de la otra cuenta")
    t = db.q1("SELECT * FROM users WHERE (lower(username)=? OR lower(email)=?) AND status='approved'", who, who)
    if not t:
        err(404, "No hay ninguna cuenta con ese usuario o correo")
    if t["id"] == p["user_id"]:
        err(400, "Esa ficha ya es de esa cuenta")
    if u["is_admin"]:
        _move_pet(p, t["id"])
        return {"moved": True, "to": t["name"]}
    db.run("UPDATE pets SET transfer_to=? WHERE id=?", t["id"], p["id"])
    return pet_json(db.q1("SELECT * FROM pets WHERE id=?", p["id"]), base_url(request))


@app.post("/api/transfers/{pet_id}")
async def answer_transfer(pet_id: int, request: Request):
    u = user_or_401(request)
    p = db.q1("SELECT * FROM pets WHERE id=? AND transfer_to=?", pet_id, u["id"])
    if not p:
        err(404, "Ya no está pendiente")
    if (await request.json()).get("accept"):
        _move_pet(p, u["id"])
    else:
        db.run("UPDATE pets SET transfer_to=0 WHERE id=?", p["id"])
    return {"ok": True, "transfers": _transfers_for(u)}


@app.delete("/api/pets/{pet_id}")
def delete_pet(pet_id: int, request: Request):
    _delete_pet(own_pet(user_or_401(request), pet_id))
    return {"ok": True}


MAGIC = {b"\xff\xd8\xff": "jpg", b"\x89PNG\r\n\x1a\n": "png"}


def read_image(d) -> tuple:
    data = str(d.get("data") or "")
    if not data:
        return b"", ""
    try:
        raw = base64.b64decode(data.split(",", 1)[-1], validate=True)
    except ValueError:
        err(400, "Imagen no válida")
    if len(raw) > 2_500_000:
        err(400, "La imagen es demasiado grande")
    ext = next((e for m, e in MAGIC.items() if raw.startswith(m)), None)
    if not ext:
        ext = "webp" if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP" else None
    if not ext:
        err(400, "La imagen debe ser JPG, PNG o WebP")
    return raw, ext


@app.post("/api/pets/{pet_id}/photo")
async def set_photo(pet_id: int, request: Request):
    p = own_pet(user_or_401(request), pet_id)
    raw, ext = read_image(await request.json())
    if p["photo"]:
        (PHOTOS / p["photo"]).unlink(missing_ok=True)
    name = ""
    if raw:
        name = f"{pet_id}-{secrets.token_hex(6)}.{ext}"
        (PHOTOS / name).write_bytes(strip_meta(raw, ext))
    db.run("UPDATE pets SET photo=?, updated=? WHERE id=?", name, time.time(), pet_id)
    return pet_json(db.q1("SELECT * FROM pets WHERE id=?", pet_id), base_url(request))


def strip_meta(raw: bytes, ext: str) -> bytes:
    """Quita los metadatos de un JPG (EXIF con el GPS, el modelo del móvil…): solo se guarda la imagen."""
    if ext != "jpg":
        return raw
    out, i = bytearray(raw[:2]), 2
    try:
        while i + 4 <= len(raw) and raw[i] == 0xFF:
            m = raw[i + 1]
            if m == 0xDA:  # empieza la imagen
                out += raw[i:]
                return bytes(out)
            n = int.from_bytes(raw[i + 2:i + 4], "big")
            if not (m == 0xE1 or m == 0xED or m == 0xFE):  # fuera APP1 (EXIF/XMP), APP13 y comentarios
                out += raw[i:i + 2 + n]
            i += 2 + n
    except Exception:
        pass
    return raw


# --- avisos al administrador por Telegram (opcional) --------------------------
def notify(msg: str, wait=False, photo=None, buttons=None, delay=0):
    """Manda un aviso al Telegram del administrador si lo ha configurado. No frena la petición."""
    return bot.notify(msg, wait=wait, photo=photo, buttons=buttons, delay=delay)


def _photo(fn):
    return (PHOTOS / fn) if fn else None


def _sp(k):
    return page.SPECIES.get(k or "otro", page.SPECIES["otro"])


def notify_url(path=""):
    b = db.get_setting("public_url") or PUBLIC_URL
    return f"\n{b.rstrip('/')}{path}" if b else ""


# --- «Busca tu pipicán» -------------------------------------------------------
def park_json(r, me=None):
    d = {"id": r["id"], "name": r["name"], "notes": r["notes"], "lat": r["lat"], "lng": r["lng"],
         "photo": f"/f/{r['photo']}" if r["photo"] else "", "created": r["created"]}
    if me is not None:
        d["mine"] = r["user_id"] == me["id"]
        d["pending"] = bool(r["pending"])
        d["can_edit"] = d["mine"] or bool(me["is_admin"])
        if me["is_admin"]:
            dup = r["dupe_of"] if "dupe_of" in r.keys() else 0
            o = db.q1("SELECT name FROM parks WHERE id=?", dup) if dup else None
            d |= {"dupe_of": {"id": dup, "name": o["name"]} if o else None}
            d |= {"hidden": bool(r["hidden"]), "author": r["author"] if "author" in r.keys() else "",
                  "osm": bool(r["osm_id"]) if "osm_id" in r.keys() else False}
    return d


@app.get("/api/parks")
def parks_list(request: Request):
    """Todos los pipicanes visibles (es público: son sitios de la calle, sin datos de quién los apuntó)."""
    me_ = db.session_user(request.cookies.get(COOKIE, ""))
    return [park_json(r, me_) for r in db.q("SELECT * FROM parks WHERE hidden=0 AND pending=0 ORDER BY id DESC LIMIT 2000")]


@app.get("/api/parks/mine")
def parks_mine(request: Request):
    """Los pipicanes que he apuntado yo (también los que esperan a que el administrador los revise)."""
    u = user_or_401(request)
    return [park_json(r, u) for r in db.q("SELECT * FROM parks WHERE user_id=? ORDER BY id DESC", u["id"])]


@app.get("/api/parks/{park_id}")
def park_get(park_id: int, request: Request):
    u = user_or_401(request)
    r = db.q1("SELECT * FROM parks WHERE id=?", park_id)
    if not r or (r["user_id"] != u["id"] and not u["is_admin"]):
        err(404, "Solo puede cambiarlo quien lo apuntó o el administrador")
    return park_json(r, u)


def _park_dupes(lat, lng, name, skip=0):
    """Pipicanes que ya están apuntados en el mismo sitio (a menos de 50 m) o con el mismo nombre cerca (2 km)."""
    d = 2000 / 111000
    out = []
    for r in db.q("SELECT id,name,lat,lng,pending,photo FROM parks WHERE hidden=0 AND id<>? AND lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?",
                  skip, lat - d, lat + d, lng - d * 1.4, lng + d * 1.4):
        dist = _dist_m(lat, lng, r["lat"], r["lng"])
        same = name and r["name"].strip().lower() == name.strip().lower() and dist <= 2000
        if dist <= 50 or same:
            out.append({"id": r["id"], "name": r["name"], "lat": r["lat"], "lng": r["lng"], "dist": dist,
                        "pending": bool(r["pending"]), "photo": f"/f/{r['photo']}" if r["photo"] else ""})
    return sorted(out, key=lambda x: x["dist"])


@app.post("/api/parks/check")
async def park_check(request: Request):
    """Antes de guardar: ¿ya hay uno igual? (mismo sitio o mismo nombre)."""
    user_or_401(request)
    d = await request.json()
    try:
        lat, lng = float(d.get("lat")), float(d.get("lng"))
    except (TypeError, ValueError):
        err(400, "Marca en el mapa dónde está el pipicán")
    return _park_dupes(lat, lng, text(d.get("name"), 60), int(d.get("skip") or 0))


def _park_notice(r, what="Nuevo pipicán para revisar"):
    notify(f"🌳 {what}: {r['name']}" + (f"\n📝 {r['notes']}" if r["notes"] else "")
           + f"\n🗺️ Mapa: https://www.google.com/maps/search/?api=1&query={r['lat']},{r['lng']}"
           + f"\n🚶 Street View: https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={r['lat']},{r['lng']}"
           + "\nMira que de verdad existe y apruébalo para que salga en el mapa.",
           photo=_photo(r["photo"]), buttons=[[("✅ Aprobar", f"park_ok:{r['id']}"), ("🗑️ Borrar", f"park_del:{r['id']}")]])


@app.post("/api/parks")
async def park_add(request: Request):
    u = user_or_401(request)
    if db.q1("SELECT COUNT(*) n FROM parks WHERE user_id=? AND created>?", u["id"], time.time() - 86400)["n"] >= 20:
        err(429, "Has apuntado muchos pipicanes hoy. Prueba mañana")
    d = await request.json()
    name = text(d.get("name"), 60)
    try:
        lat, lng = float(d.get("lat")), float(d.get("lng"))
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValueError
    except (TypeError, ValueError):
        err(400, "Marca en el mapa dónde está el pipicán")
    if not name:
        err(400, "Ponle un nombre (por ejemplo, el parque o la calle)")
    dupes = _park_dupes(lat, lng, name)
    if dupes and not d.get("distinct"):
        err(409, "Ese pipicán ya está apuntado")
    raw, ext = read_image(d)
    now = time.time()
    # si dice que es otro distinto, lo revisa siempre el administrador (también si lo apunta él, para que lo vea)
    pending = 1 if dupes or not u["is_admin"] else 0
    cur = db.run("INSERT INTO parks(user_id,name,notes,lat,lng,created,pending,dupe_of) VALUES(?,?,?,?,?,?,?,?)",
                 u["id"], name, text(d.get("notes"), 300), round(lat, 5), round(lng, 5), now, pending, dupes[0]["id"] if dupes else 0)
    if raw:
        fn = f"pipican-{cur.lastrowid}-{secrets.token_hex(6)}.{ext}"
        (PHOTOS / fn).write_bytes(strip_meta(raw, ext))
        db.run("UPDATE parks SET photo=? WHERE id=?", fn, cur.lastrowid)
    r = db.q1("SELECT * FROM parks WHERE id=?", cur.lastrowid)
    if r["pending"]:
        _park_notice(r, f"⚠️ Posible duplicado de «{dupes[0]['name']}» ({dupes[0]['dist']} m)" if dupes else "Nuevo pipicán para revisar")
    return park_json(r, u)


@app.put("/api/parks/{park_id}")
async def park_edit(park_id: int, request: Request):
    """Cambiar un pipicán: quien lo apuntó o el administrador. Corregirlo no lo quita del mapa."""
    u = user_or_401(request)
    r = db.q1("SELECT * FROM parks WHERE id=?", park_id)
    if not r or (r["user_id"] != u["id"] and not u["is_admin"]):
        err(404, "Solo puede cambiarlo quien lo apuntó o el administrador")
    d = await request.json()
    name = text(d.get("name"), 60) if "name" in d else r["name"]
    if not name:
        err(400, "Ponle un nombre (por ejemplo, el parque o la calle)")
    lat, lng = r["lat"], r["lng"]
    if d.get("lat") is not None:
        try:
            lat, lng = round(float(d["lat"]), 5), round(float(d["lng"]), 5)
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                raise ValueError
        except (TypeError, ValueError):
            err(400, "Marca en el mapa dónde está el pipicán")
    notes = text(d.get("notes"), 300) if "notes" in d else r["notes"]
    photo = r["photo"]
    if d.get("data") or d.get("photo_del"):
        raw, ext = read_image(d) if d.get("data") else (None, "")
        if photo:
            (PHOTOS / photo).unlink(missing_ok=True)
        photo = ""
        if raw:
            photo = f"pipican-{park_id}-{secrets.token_hex(6)}.{ext}"
            (PHOTOS / photo).write_bytes(strip_meta(raw, ext))
    # el administrador lo deja aprobado; quien lo apuntó puede corregirlo sin que desaparezca del mapa (sigue como estaba)
    pending = 0 if u["is_admin"] else (r["pending"] if r["user_id"] == u["id"] else 1)
    db.run("UPDATE parks SET name=?, notes=?, lat=?, lng=?, photo=?, pending=? WHERE id=?", name, notes, lat, lng, photo, pending, park_id)
    r = db.q1("SELECT * FROM parks WHERE id=?", park_id)
    if pending:
        _park_notice(r, "Pipicán cambiado, para revisar")
    return park_json(r, u)


_MAPS_HOSTS = ("maps.app.goo.gl", "goo.gl", "maps.google.com", "www.google.com", "google.com", "www.google.es", "google.es", "maps.google.es")


def _coords_from(u: str):
    """Saca latitud, longitud y nombre de un enlace de Google Maps (los largos llevan @lat,lng o !3d…!4d…)."""
    from urllib.parse import unquote
    u = unquote(unquote(u))  # dos veces: la página de consentimiento de Google lo lleva codificado dentro de «continue=»
    for rx in (r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)",  # el punto exacto del sitio
               r"[?&](?:q|query|ll|destination|daddr|center|sll)=(-?\d+\.\d+)\s*,\s*\+?(-?\d+\.\d+)",
               r"/(?:search|place|dir)/(?:[^/@]*/)?\+?(-?\d{1,2}\.\d{3,})\s*,\s*\+?(-?\d{1,3}\.\d{3,})",
               r"@(-?\d+\.\d+),(-?\d+\.\d+)",  # el centro del mapa (casi siempre el sitio)
               r"\[null,null,(-?\d{1,2}\.\d{4,}),(-?\d{1,3}\.\d{4,})\]",  # dentro de la página de Google Maps
               r"/(-?\d{1,2}\.\d{4,}),\s*\+?(-?\d{1,3}\.\d{4,})"):
        m = re.search(rx, u)
        if m:
            lat, lng = float(m.group(1)), float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                name = re.search(r"/place/([^/@]+)", u)
                return {"lat": round(lat, 5), "lng": round(lng, 5), "name": name.group(1).replace("+", " ")[:60] if name else ""}
    return None


@app.post("/api/maps-link")
async def maps_link(request: Request):
    """Pegar un enlace de Google Maps para marcar el sitio. Los cortos (maps.app.goo.gl) se siguen desde el servidor."""
    user_or_401(request)
    u = text((await request.json()).get("url"), 2000)
    m = re.search(r"https?://\S+", u)
    if not m:
        err(400, "Pega un enlace de Google Maps")
    u = m.group(0)
    host = (urlsplit(u).hostname or "").lower()
    if host not in _MAPS_HOSTS:
        err(400, "Ese enlace no es de Google Maps")
    found = _coords_from(u)
    if not found and (host in ("maps.app.goo.gl", "goo.gl") or "/maps" in u):
        import urllib.request as _u
        try:
            # como un navegador normal, y con el consentimiento de cookies ya dado (si no, Google manda a otra página)
            req = _u.Request(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                                         "Accept-Language": "es-ES,es;q=0.9", "Cookie": "CONSENT=YES+cb; SOCS=CAESEwgDEgk0ODE3Nzk3MjQaAmVzIAEaBgiA_LyaBg"})
            with _u.urlopen(req, timeout=8) as r:
                final = r.geturl()
                found = _coords_from(final) or _coords_from(r.read(300_000).decode("utf-8", "ignore"))
        except Exception:
            err(400, "No he podido abrir ese enlace. Prueba con el enlace largo o marca el sitio en el mapa")
    if not found:
        err(400, "Ese enlace no trae la ubicación. Abre el sitio en Google Maps, pulsa Compartir y copia el enlace")
    return found


_UA = {"User-Agent": "MascotasPanel/1.0 (registro de mascotas sin animo de lucro)"}


def _get_json(url: str, data: bytes | None = None, timeout: int = 12):
    import json as _j, urllib.request as _u
    return _j.loads(_u.urlopen(_u.Request(url, data=data, headers=_UA), timeout=timeout).read())


def _dist_m(a_lat, a_lng, b_lat, b_lng) -> int:
    import math
    x = math.radians(b_lng - a_lng) * math.cos(math.radians((a_lat + b_lat) / 2))
    return int(math.hypot(x, math.radians(b_lat - a_lat)) * 6371000)


def _addr(a: dict) -> str:
    """Calle, barrio y pueblo a partir de la dirección de OpenStreetMap."""
    street = a.get("road") or a.get("pedestrian") or a.get("footway") or a.get("square") or ""
    hood = a.get("suburb") or a.get("neighbourhood") or a.get("quarter") or ""
    town = a.get("city") or a.get("town") or a.get("village") or a.get("municipality") or ""
    return ", ".join(dict.fromkeys(x for x in (street, hood, town) if x))


def _osm_dog_parks(lat, lng, radius):
    ql = (f'[out:json][timeout:15];(node["leisure"="dog_park"](around:{radius},{lat},{lng});'
          f'way["leisure"="dog_park"](around:{radius},{lat},{lng});relation["leisure"="dog_park"](around:{radius},{lat},{lng}););out center 20;')
    import urllib.parse as _p
    out = []
    for e in _get_json("https://overpass-api.de/api/interpreter", _p.urlencode({"data": ql}).encode(), 20).get("elements", []):
        c = e.get("center") or e
        if "lat" not in c:
            continue
        tags = e.get("tags") or {}
        notes = " · ".join(x for x in ("Vallado" if tags.get("barrier") == "fence" or tags.get("fence") == "yes" else "",
                                        "Con fuente" if tags.get("drinking_water") == "yes" else "") if x)
        out.append({"name": text(tags.get("name"), 60), "lat": round(c["lat"], 5), "lng": round(c["lon"], 5),
                    "notes": notes, "dist": _dist_m(lat, lng, c["lat"], c["lon"])})
    return sorted(out, key=lambda x: x["dist"])


def _known_parks(lat, lng, radius):
    d = radius / 111000
    rows = db.q("SELECT id,name,lat,lng FROM parks WHERE hidden=0 AND pending=0 AND lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?",
                lat - d, lat + d, lng - d * 1.4, lng + d * 1.4)
    out = [{"id": r["id"], "name": r["name"], "lat": r["lat"], "lng": r["lng"], "dist": _dist_m(lat, lng, r["lat"], r["lng"])} for r in rows]
    return sorted((x for x in out if x["dist"] <= radius), key=lambda x: x["dist"])


@app.post("/api/geo/near")
async def geo_near(request: Request):
    """«Estoy aquí»: la dirección del sitio y los pipicanes que ya hay muy cerca (en OpenStreetMap y en la web)."""
    user_or_401(request)
    d = await request.json()
    try:
        lat, lng = float(d.get("lat")), float(d.get("lng"))
    except (TypeError, ValueError):
        err(400, "Elige primero el sitio")
    lang = "en" if d.get("lang") == "en" else "es"
    out = {"address": "", "town": "", "osm": [], "known": _known_parks(lat, lng, 150)}
    try:
        j = _get_json(f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=18&addressdetails=1&accept-language={lang}&lat={lat}&lon={lng}")
        a = j.get("address") or {}
        out["address"] = _addr(a)
        out["town"] = a.get("city") or a.get("town") or a.get("village") or a.get("municipality") or ""
    except Exception:
        pass
    try:
        out["osm"] = _osm_dog_parks(lat, lng, 150)[:5]
    except Exception:
        pass
    return out


@app.post("/api/geo/search")
async def geo_search(request: Request):
    """Buscar un pipicán por su nombre o por la dirección: primero los de la web, luego OpenStreetMap."""
    user_or_401(request)
    d = await request.json()
    q = text(d.get("q"), 120).strip()
    if len(q) < 3:
        err(400, "Escribe al menos 3 letras")
    lang = "en" if d.get("lang") == "en" else "es"
    import urllib.parse as _p
    out = []
    for r in db.q("SELECT id,name,notes,lat,lng FROM parks WHERE hidden=0 AND pending=0 AND (name LIKE ? OR notes LIKE ?) LIMIT 5", f"%{q}%", f"%{q}%"):
        out.append({"name": r["name"], "label": r["notes"] or "", "lat": r["lat"], "lng": r["lng"], "dog": True, "known": r["id"]})
    try:
        for x in _get_json("https://nominatim.openstreetmap.org/search?format=jsonv2&limit=6&addressdetails=1&countrycodes=es"
                           f"&accept-language={lang}&q=" + _p.quote(q)):
            dog = x.get("type") == "dog_park"
            a = x.get("address") or {}
            out.append({"name": text(x.get("name") or "", 60), "label": _addr(a) or text(x.get("display_name"), 120),
                        "lat": round(float(x["lat"]), 5), "lng": round(float(x["lon"]), 5), "dog": dog, "known": 0})
    except Exception:
        if not out:
            err(502, "No se puede buscar ahora. Mueve el mapa con el dedo.")
    out.sort(key=lambda x: (not x["known"], not x["dog"]))
    return out[:8]


def _delete_park(r):
    if r["photo"]:
        (PHOTOS / r["photo"]).unlink(missing_ok=True)
    db.run("DELETE FROM parks WHERE id=?", r["id"])


@app.delete("/api/parks/{park_id}")
def park_delete(park_id: int, request: Request):
    u = user_or_401(request)
    r = db.q1("SELECT * FROM parks WHERE id=?", park_id)
    if not r or (r["user_id"] != u["id"] and not u["is_admin"]):
        err(404, "Pipicán no encontrado")
    _delete_park(r)
    return {"ok": True}


@app.get("/api/admin/parks")
def admin_parks(request: Request):
    me_ = admin_or_403(request)
    return [park_json(r, me_) for r in db.q("SELECT k.*, u.name author FROM parks k LEFT JOIN users u ON u.id=k.user_id ORDER BY k.id DESC")]


@app.post("/api/admin/parks/import")
async def admin_parks_import(request: Request):
    """Trae los pipicanes que ya están en OpenStreetMap (leisure=dog_park) alrededor de un sitio. Gratis, sin clave."""
    admin_or_403(request)
    d = await request.json()
    try:
        lat, lng = float(d.get("lat")), float(d.get("lng"))
        km = min(30, max(1, int(d.get("km") or 10)))
    except (TypeError, ValueError):
        err(400, "Elige primero el sitio")
    import json as _j, urllib.request as _u, urllib.parse as _p
    ql = (f'[out:json][timeout:25];(node["leisure"="dog_park"](around:{km * 1000},{lat},{lng});'
          f'way["leisure"="dog_park"](around:{km * 1000},{lat},{lng});relation["leisure"="dog_park"](around:{km * 1000},{lat},{lng}););out center 300;')
    try:
        req = _u.Request("https://overpass-api.de/api/interpreter", data=_p.urlencode({"data": ql}).encode(),
                         headers={"User-Agent": "MascotasPanel (registro de mascotas)"})
        els = _j.loads(_u.urlopen(req, timeout=40).read()).get("elements", [])
    except Exception:
        err(502, "No se puede conectar con OpenStreetMap ahora. Prueba dentro de un rato")
    added, now = 0, time.time()
    for e in els:
        c = e.get("center") or e
        if "lat" not in c:
            continue
        oid = f'{e["type"]}/{e["id"]}'
        if db.q1("SELECT 1 FROM parks WHERE osm_id=?", oid):
            continue
        tags = e.get("tags") or {}
        name = text(tags.get("name") or "Pipicán", 60)
        notes = " · ".join(x for x in ((("Vallado" if tags.get("barrier") == "fence" else "") or ("Vallado" if tags.get("fence") == "yes" else "")),
                                        "Con fuente" if tags.get("drinking_water") == "yes" else "", text(tags.get("description"), 200)) if x)
        db.run("INSERT INTO parks(user_id,name,notes,lat,lng,created,osm_id) VALUES(0,?,?,?,?,?,?)",
               name, notes, round(c["lat"], 5), round(c["lon"], 5), now, oid)
        added += 1
    return {"found": len(els), "added": added}


@app.post("/api/admin/parks/{park_id}")
async def admin_park(park_id: int, request: Request):
    admin_or_403(request)
    r = db.q1("SELECT * FROM parks WHERE id=?", park_id) or err(404, "Pipicán no encontrado")
    action = (await request.json()).get("action")
    if action in ("hide", "show"):
        db.run("UPDATE parks SET hidden=? WHERE id=?", int(action == "hide"), park_id)
    elif action == "approve":
        db.run("UPDATE parks SET pending=0 WHERE id=?", park_id)
    elif action == "delete":
        _delete_park(r)
    else:
        err(400, "Acción desconocida")
    return {"ok": True}


# --- asociaciones y adopciones ----------------------------------------------
@app.put("/api/org")
async def org_update(request: Request):
    u = user_or_401(request)
    if (u["kind"] or "person") != "org":
        err(403, "Solo para asociaciones")
    d = await request.json()
    f = {}
    for k, n in (("name", 80), ("city", 80), ("about", 800), ("telegram", 40), ("legal_name", 120), ("reg_number", 60), ("zoo_number", 60)):
        if k in d:
            f[k] = text(d[k], n)
    if "cif" in d:
        f["cif"] = clean_cif(d["cif"])
    if "name" in f and len(f["name"]) < 3:
        err(400, "Escribe el nombre de la asociación o protectora")
    if "telegram" in f and f["telegram"]:
        tg = f["telegram"].lstrip("@").replace("https://t.me/", "")
        if not re.fullmatch(r"[A-Za-z0-9_]{4,40}", tg):
            err(400, "El usuario de Telegram es como @protectora_valencia")
        f["telegram"] = tg
    if "web" in d:
        w = text(d["web"], 200)
        if w and not re.match(r"^https?://", w, re.I):
            w = "https://" + w
        if w and (not urlsplit(w).hostname or " " in w):
            err(400, "Esa web no parece válida")
        f["web"] = w
    if "phone" in d:
        f["phone"] = clean_phone(d["phone"])
    if "email" in d:
        f["email"] = clean_email(d["email"]) if text(d["email"], 120) else ""
    for k in ("show_phone", "whatsapp", "show_email"):
        if k in d:
            f[k] = int(bool(d[k]))
    if f:
        db.run(f"UPDATE orgs SET {', '.join(k + '=?' for k in f)} WHERE user_id=?", *f.values(), u["id"])
    return org_json(get_org(u["id"]))


@app.post("/api/me/avatar")
async def me_avatar(request: Request):
    """Foto de perfil (opcional). Vacía = quitarla y volver a la huella."""
    u = user_or_401(request)
    raw, ext = read_image(await request.json())
    if u["avatar"]:
        (PHOTOS / u["avatar"]).unlink(missing_ok=True)
    name = ""
    if raw:
        name = f"avatar-{u['id']}-{secrets.token_hex(6)}.{ext}"
        (PHOTOS / name).write_bytes(strip_meta(raw, ext))
    db.run("UPDATE users SET avatar=? WHERE id=?", name, u["id"])
    return user_json(db.q1("SELECT * FROM users WHERE id=?", u["id"]))


@app.post("/api/org/logo")
async def org_logo(request: Request):
    u = user_or_401(request)
    o = get_org(u["id"]) or err(403, "Solo para asociaciones")
    raw, ext = read_image(await request.json())
    if o["logo"]:
        (PHOTOS / o["logo"]).unlink(missing_ok=True)
    name = ""
    if raw:
        name = f"org-{u['id']}-{secrets.token_hex(6)}.{ext}"
        (PHOTOS / name).write_bytes(strip_meta(raw, ext))
    db.run("UPDATE orgs SET logo=? WHERE user_id=?", name, u["id"])
    if name:
        notify(f"🏡 {o['name']} ha puesto su logo" + ("" if o["verified"] else "\n⏳ Todavía no está verificada."), photo=_photo(name),
               buttons=None if o["verified"] else [[("✅ Verificar asociación", f"org_ok:{u['id']}")]])
    return org_json(get_org(u["id"]))


ADOPT_SQL = ("FROM pets p JOIN users u ON u.id=p.user_id JOIN orgs o ON o.user_id=p.user_id "
             "WHERE p.adopt=1 AND p.hidden=0 AND u.status='approved' AND o.verified=1")


ORGS_SQL = ("SELECT o.*, (SELECT COUNT(*) FROM pets p WHERE p.user_id=o.user_id AND p.adopt=1 AND p.hidden=0) n_adopt "
            "FROM orgs o JOIN users u ON u.id=o.user_id WHERE o.verified=1 AND u.status='approved' ORDER BY o.name COLLATE NOCASE")


def public_orgs():
    """Asociaciones verificadas, con sus datos públicos y legales y cuántos animales tienen en adopción."""
    return [org_json(o, public=True) | {"n_adopt": o["n_adopt"]} for o in db.q(ORGS_SQL)]


@app.get("/api/orgs")
def orgs_list():
    return public_orgs()


@app.get("/api/admin/orgs")
def admin_orgs(request: Request):
    """Todas las asociaciones (también las que esperan verificación), con la persona que lleva la cuenta."""
    admin_or_403(request)
    return [org_json(o) | {"user": {"name": o["uname"], "username": o["username"], "email": o["uemail"], "status": o["status"]},
                           "created": o["created"], "n_adopt": o["n_adopt"]}
            for o in db.q("SELECT o.*, u.name uname, u.username, u.email uemail, u.status, "
                          "(SELECT COUNT(*) FROM pets p WHERE p.user_id=o.user_id AND p.adopt=1) n_adopt "
                          "FROM orgs o JOIN users u ON u.id=o.user_id ORDER BY o.verified, o.created DESC")]


def adopt_rows(limit=200, especie="", org_id=0):
    where, args = "", []
    if especie in SPECIES:
        where += " AND p.species=?"; args.append(especie)
    if org_id:
        where += " AND p.user_id=?"; args.append(org_id)
    return db.q(f"SELECT p.*, o.name org_name, o.logo org_logo, o.city org_city {ADOPT_SQL}{where} "
                f"ORDER BY p.updated DESC LIMIT {int(limit)}", *args)


@app.get("/api/lost")
def lost_list(request: Request):
    """Inicio de cada persona: los perros, gatos… que se están buscando ahora (lo mismo que se ve en la web pública)."""
    u = user_or_401(request)
    b = base_url(request)
    rows = db.q("SELECT p.* FROM pets p JOIN users u ON u.id=p.user_id WHERE p.lost=1 AND p.hidden=0 "
                "AND u.status='approved' ORDER BY p.lost_at DESC LIMIT 60")
    return [{"id": r["id"] if r["user_id"] == u["id"] else 0, "name": r["name"], "species": r["species"], "breed": r["breed"],
             "photo": f"/f/{r['photo']}" if r["photo"] else "", "zone": r["lost_zone"] or "", "note": r["lost_note"] or "",
             "reward": r["reward"] or "", "at": r["lost_at"] or 0, "url": f"{b}/m/{r['code']}", "mine": r["user_id"] == u["id"]}
            for r in rows]


@app.get("/api/registered")
def registered(request: Request):
    """Inicio: cuántas mascotas hay apuntadas y los últimos nombres (sin foto, sin dueño, sin zona y sin enlace)."""
    user_or_401(request)
    base = "FROM pets p JOIN users u ON u.id=p.user_id WHERE p.hidden=0 AND u.status='approved'"
    c = db.q1(f"SELECT COUNT(*) n, SUM(p.species='perro') dogs, SUM(p.species='gato') cats {base}")
    recent = [{"name": r["name"], "species": r["species"]} for r in db.q(f"SELECT p.name, p.species {base} ORDER BY p.created DESC LIMIT 20")]
    n, dogs, cats = c["n"] or 0, c["dogs"] or 0, c["cats"] or 0
    return {"total": n, "dogs": dogs, "cats": cats, "others": n - dogs - cats, "recent": recent}


@app.get("/api/adopt")
def adopt_list(request: Request):
    """Animales en adopción (público): para el carrusel «¿Me adoptas?»."""
    b = base_url(request)
    return [{"code": r["code"], "name": r["name"], "species": r["species"], "breed": r["breed"], "sex": r["sex"], "age": r["age"],
             "text": r["adopt_text"], "photo": f"/f/{r['photo']}" if r["photo"] else "", "url": f"{b}/m/{r['code']}",
             "org": r["org_name"], "org_id": r["user_id"]} for r in adopt_rows(40)]


# --- avisos de «la he encontrado» -------------------------------------------
_found_ip: dict = {}


@app.post("/api/found/{code}")
async def found(code: str, request: Request):
    """Quien escanea el QR manda un aviso a la familia sin ver su teléfono ni su correo."""
    p = db.q1("SELECT * FROM pets WHERE code=? AND hidden=0", code) if CODE_RE.match(code) else None
    if not p:
        err(404, "Mascota no encontrada")
    ip, now = _client(request), time.time()
    recent = [t for t in _found_ip.get(ip, []) if t > now - 3600]
    if len(recent) >= 5:
        err(429, "Has mandado muchos avisos. Espera un rato.")
    d = await request.json()
    msg, contact = text(d.get("text"), 600), text(d.get("contact"), 120)
    if len(msg) < 3 and not contact:
        err(400, "Escribe un mensaje o cómo pueden contactarte")
    lat = lng = None
    try:
        lat, lng = round(float(d["lat"]), 5), round(float(d["lng"]), 5)
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            lat = lng = None
    except (KeyError, TypeError, ValueError):
        pass
    _found_ip[ip] = recent + [now]
    db.run("INSERT INTO messages(pet_id,user_id,created,text,contact,lat,lng) VALUES(?,?,?,?,?,?,?)",
           p["id"], p["user_id"], now, msg, contact, lat, lng)
    notify(f"💌 Alguien quiere conocer a {p['name']} (en adopción)" if p["adopt"] else
           f"✉️ {'🚨 ' if p['lost'] else ''}Alguien ha mandado un aviso a la familia de {p['name']} desde su QR"
           + (" (está perdido: ¡puede que lo hayan encontrado!)" if p["lost"] else ""), photo=_photo(p["photo"]) if p["lost"] else None)
    return {"ok": True}


# --- «📍 Lo he visto aquí»: avistamientos de una mascota perdida -------------
_seen_ip: dict = {}
MAX_SIGHTINGS = 60


def sighting_json(r):
    return {"id": r["id"], "at": r["seen_at"], "lat": r["lat"], "lng": r["lng"], "note": r["note"] or ""}


def sightings_of(pet_id):
    return db.q("SELECT * FROM sightings WHERE pet_id=? ORDER BY seen_at DESC LIMIT ?", pet_id, MAX_SIGHTINGS)


@app.post("/api/seen/{code}")
async def seen(code: str, request: Request):
    """Cualquiera (sin cuenta) marca en el mapa dónde y cuándo ha visto a una mascota perdida."""
    p = db.q1("SELECT * FROM pets WHERE code=? AND hidden=0 AND lost=1", code) if CODE_RE.match(code) else None
    if not p:
        err(404, "Esta mascota ya no está marcada como perdida")
    ip, now = _client(request), time.time()
    recent = [t for t in _seen_ip.get(ip, []) if t > now - 3600]
    if len(recent) >= 6:
        err(429, "Has apuntado muchos avistamientos. Espera un rato.")
    d = await request.json()
    try:
        lat, lng = float(d["lat"]), float(d["lng"])
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        err(400, "Marca en el mapa dónde lo has visto")
    try:
        at = float(d.get("at") or now)
    except (TypeError, ValueError):
        at = now
    at = min(at, now)
    if at < (p["lost_at"] or now) - 86400:
        err(400, "Esa hora es de antes de que se perdiera")
    note = text(d.get("note"), 200)
    _seen_ip[ip] = recent + [now]
    cur = db.run("INSERT INTO sightings(pet_id,created,seen_at,lat,lng,note) VALUES(?,?,?,?,?,?)",
                 p["id"], now, at, round(lat, 4), round(lng, 4), note)
    db.run("DELETE FROM sightings WHERE pet_id=? AND id NOT IN (SELECT id FROM sightings WHERE pet_id=? ORDER BY seen_at DESC LIMIT ?)",
           p["id"], p["id"], MAX_SIGHTINGS)
    # le llega también a la familia como aviso, con el sitio, para que lo vea en «Avisos»
    db.run("INSERT INTO messages(pet_id,user_id,created,text,contact,lat,lng) VALUES(?,?,?,?,?,?,?)",
           p["id"], p["user_id"], now, "📍 " + ("Lo han visto aquí" + (f": {note}" if note else "")), "", round(lat, 5), round(lng, 5))
    notify(f"📍 Alguien ha visto a {p['name']} (perdido) y lo ha marcado en el mapa" + (f"\n💬 {note}" if note else "")
           + f"\n🗺️ https://www.google.com/maps/search/?api=1&query={round(lat, 5)},{round(lng, 5)}" + notify_url(f"/m/{p['code']}"))
    return sighting_json(db.q1("SELECT * FROM sightings WHERE id=?", cur.lastrowid))


@app.get("/api/seen/{code}")
def seen_list(code: str):
    p = db.q1("SELECT id FROM pets WHERE code=? AND hidden=0 AND lost=1", code) if CODE_RE.match(code) else None
    return [sighting_json(r) for r in sightings_of(p["id"])] if p else []


@app.get("/api/pets/{pet_id}/seen")
def pet_seen(pet_id: int, request: Request):
    p = own_pet(user_or_401(request), pet_id)
    return [sighting_json(r) for r in sightings_of(p["id"])]


@app.delete("/api/pets/{pet_id}/seen/{sid}")
def pet_seen_delete(pet_id: int, sid: int, request: Request):
    """El dueño quita un avistamiento que no le sirve (una broma, otro perro…)."""
    p = own_pet(user_or_401(request), pet_id)
    db.run("DELETE FROM sightings WHERE id=? AND pet_id=?", sid, p["id"])
    return {"ok": True}


@app.get("/api/messages")
def messages(request: Request):
    u = user_or_401(request)
    return [{"id": r["id"], "pet": r["name"], "pet_id": r["pet_id"], "created": r["created"], "text": r["text"],
             "contact": r["contact"], "lat": r["lat"], "lng": r["lng"], "read": bool(r["read"])}
            for r in db.q("SELECT m.*, p.name FROM messages m JOIN pets p ON p.id=m.pet_id WHERE m.user_id=? "
                          "ORDER BY m.created DESC LIMIT 200", u["id"])]


@app.post("/api/messages/read")
def messages_read(request: Request):
    u = user_or_401(request)
    db.run("UPDATE messages SET read=1 WHERE user_id=?", u["id"])
    return {"ok": True}


@app.delete("/api/messages/{msg_id}")
def message_delete(msg_id: int, request: Request):
    u = user_or_401(request)
    db.run("DELETE FROM messages WHERE id=? AND user_id=?", msg_id, u["id"])
    return {"ok": True}


# --- administración --------------------------------------------------------
@app.get("/api/admin/users")
def admin_users(request: Request):
    admin_or_403(request)
    return [user_json(u) | {"status": u["status"], "created": u["created"], "pets": u["pets"], "age_ok": bool(u["age_ok"])}
            for u in db.q("SELECT u.*, (SELECT COUNT(*) FROM pets p WHERE p.user_id=u.id) pets "
                          "FROM users u ORDER BY u.id DESC")]


@app.post("/api/admin/users/{user_id}")
async def admin_user(user_id: int, request: Request):
    me_ = admin_or_403(request)
    d = await request.json()
    action = d.get("action")
    if user_id == me_["id"] and action in ("disable", "unadmin", "delete"):
        err(400, "No puedes hacerte eso a ti mismo")
    if not db.q1("SELECT 1 FROM users WHERE id=?", user_id):
        err(404, "Usuario no encontrado")
    if action == "approve":
        db.run("UPDATE users SET status='approved' WHERE id=?", user_id)
    elif action == "disable":
        db.run("UPDATE users SET status='disabled' WHERE id=?", user_id)
        db.run("DELETE FROM sessions WHERE user_id=?", user_id)
    elif action in ("verify", "unverify"):
        if not get_org(user_id):
            err(400, "Esta cuenta no es de una asociación")
        db.run("UPDATE orgs SET verified=? WHERE user_id=?", int(action == "verify"), user_id)
    elif action in ("admin", "unadmin"):
        db.run("UPDATE users SET is_admin=? WHERE id=?", int(action == "admin"), user_id)
    elif action == "delete":
        _delete_user_data(user_id)
    elif action == "password":
        pw = str(d.get("password") or "")
        if len(pw) < 8:
            err(400, "La contraseña debe tener al menos 8 caracteres")
        db.run("UPDATE users SET pw_hash=? WHERE id=?", db.hash_pw(pw), user_id)
        db.run("DELETE FROM sessions WHERE user_id=?", user_id)
    else:
        err(400, "Acción desconocida")
    return {"ok": True}


@app.get("/api/admin/pets")
def admin_pets(request: Request):
    admin_or_403(request)
    b = base_url(request)
    return [pet_json(p, b) | {"owner": p["owner"], "owner_phone": p["phone"], "owner_email": p["email"], "owner_kind": p["kind"] or "person"}
            for p in db.q("SELECT p.*, u.name owner, u.phone, u.email, u.kind FROM pets p JOIN users u ON u.id=p.user_id ORDER BY p.id DESC")]


@app.get("/api/admin/export.csv")
def admin_csv(request: Request):
    """El registro completo en una hoja de cálculo (para llevar el control)."""
    import csv
    admin_or_403(request)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Mascota", "Animal", "Raza", "Sexo", "Tamaño", "Edad", "Color", "Microchip", "Perdida",
                "Dueño/a", "Usuario", "Correo", "Teléfono", "Zona", "Alta"])
    for p in db.q("SELECT p.*, u.name owner, u.username, u.email, u.phone, u.zone FROM pets p "
                  "JOIN users u ON u.id=p.user_id ORDER BY u.zone, p.name"):
        w.writerow([p["name"], p["species"], p["breed"], p["sex"], p["size"], p["age"], p["color"], p["chip"],
                    "sí" if p["lost"] else "", p["owner"], p["username"], p["email"], p["phone"], p["zone"],
                    time.strftime("%d/%m/%Y", time.localtime(p["created"]))])
    return Response("\ufeff" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="registro-mascotas.csv"'})


@app.post("/api/admin/pets/{pet_id}")
async def admin_pet(pet_id: int, request: Request):
    admin_or_403(request)
    p = db.q1("SELECT * FROM pets WHERE id=?", pet_id) or err(404, "Mascota no encontrada")
    action = (await request.json()).get("action")
    if action in ("hide", "show"):
        db.run("UPDATE pets SET hidden=? WHERE id=?", int(action == "hide"), pet_id)
    elif action == "delete":
        _delete_pet(p)
    else:
        err(400, "Acción desconocida")
    return {"ok": True}


@app.get("/api/admin/dashboard")
def admin_dashboard(request: Request, dias: int = 30):
    """Panel de control del administrador: totales, altas en el periodo (y el anterior), gráfico,
    últimas fichas, mascotas por animal y lo último que ha pasado."""
    admin_or_403(request)
    now = time.time()
    n = lambda sql, *a: db.q1(sql, *a)["n"] or 0
    pet_t = [r["created"] or 0 for r in db.q("SELECT created FROM pets")]
    usr_t = [r["created"] or 0 for r in db.q("SELECT created FROM users")]
    lost_t = [r["lost_at"] for r in db.q("SELECT lost_at FROM pets WHERE lost_at IS NOT NULL")]
    park_t = [r["created"] or 0 for r in db.q("SELECT created FROM parks")]
    msg_t = [r["created"] or 0 for r in db.q("SELECT created FROM messages")]
    dias = dias if dias in (7, 30, 90, 365) else 0
    first = min(pet_t + usr_t + [now])
    start = now - dias * 86400 if dias else first
    prev = start - (now - start)
    cnt = lambda ts, a, b: sum(1 for x in ts if a <= x < b)
    per = lambda ts: {"now": cnt(ts, start, now + 1), "before": cnt(ts, prev, start) if dias else None}
    # gráfico: por días (hasta 3 meses), por semanas (1 año) o por meses (todo)
    lt = time.localtime
    if dias and dias <= 90:
        step, keyf = "day", lambda x: time.strftime("%Y-%m-%d", lt(x))
        keys = [time.strftime("%Y-%m-%d", lt(now - i * 86400)) for i in range(dias - 1, -1, -1)]
    elif dias == 365:
        step, keyf = "week", lambda x: time.strftime("%G-W%V", lt(x))
        keys = list(dict.fromkeys(time.strftime("%G-W%V", lt(now - i * 86400)) for i in range(364, -1, -1)))
    else:
        step, keyf = "month", lambda x: time.strftime("%Y-%m", lt(x))
        keys, t0 = [], first
        while True:
            k = time.strftime("%Y-%m", lt(t0))
            if k not in keys:
                keys.append(k)
            if k == time.strftime("%Y-%m", lt(now)):
                break
            t0 += 27 * 86400
    series = {k: {"key": k, "pets": 0, "users": 0} for k in keys}
    for ts, name in ((pet_t, "pets"), (usr_t, "users")):
        for x in ts:
            if x >= start and keyf(x) in series:
                series[keyf(x)][name] += 1
    latest = [{"id": r["id"], "name": r["name"], "species": r["species"], "owner": r["owner"], "created": r["created"],
               "lost": bool(r["lost"]), "photo": f"/f/{r['photo']}" if r["photo"] else ""}
              for r in db.q("SELECT p.*, u.name owner FROM pets p JOIN users u ON u.id=p.user_id ORDER BY p.created DESC LIMIT 6")]
    species = [{"species": r["species"], "n": r["n"]} for r in db.q("SELECT species, COUNT(*) n FROM pets GROUP BY species ORDER BY n DESC")]
    ev = []
    for r in db.q("SELECT name, username, created FROM users WHERE created IS NOT NULL ORDER BY created DESC LIMIT 15"):
        ev.append({"t": r["created"], "kind": "user", "name": r["name"], "user": r["username"]})
    for r in db.q("SELECT p.name, p.species, p.created, u.name owner FROM pets p JOIN users u ON u.id=p.user_id ORDER BY p.created DESC LIMIT 15"):
        ev.append({"t": r["created"], "kind": "pet", "name": r["name"], "species": r["species"], "owner": r["owner"]})
    for r in db.q("SELECT name, lost_at FROM pets WHERE lost=1 ORDER BY lost_at DESC LIMIT 15"):
        ev.append({"t": r["lost_at"], "kind": "lost", "name": r["name"]})
    for r in db.q("SELECT name, created FROM parks ORDER BY created DESC LIMIT 15"):
        ev.append({"t": r["created"], "kind": "park", "name": r["name"]})
    for r in db.q("SELECT name, created FROM orgs ORDER BY created DESC LIMIT 15"):
        ev.append({"t": r["created"], "kind": "org", "name": r["name"]})
    for r in db.q("SELECT m.created, p.name FROM messages m JOIN pets p ON p.id=m.pet_id ORDER BY m.created DESC LIMIT 15"):
        ev.append({"t": r["created"], "kind": "found", "name": r["name"]})
    ev.sort(key=lambda e: e["t"] or 0, reverse=True)
    return {"dias": dias, "step": step,
            "totals": {"pets": len(pet_t), "users": len(usr_t), "lost": n("SELECT COUNT(*) n FROM pets WHERE lost=1"),
                       "parks": len(park_t), "public": n("SELECT COUNT(*) n FROM pets WHERE public=1 AND hidden=0"),
                       "chips": n("SELECT COUNT(*) n FROM pets WHERE chip<>''"), "unread": n("SELECT COUNT(*) n FROM messages WHERE read=0"),
                       "adopt": n("SELECT COUNT(*) n " + ADOPT_SQL), "orgs": n("SELECT COUNT(*) n FROM orgs"),
                       "orgs_pending": n("SELECT COUNT(*) n FROM orgs WHERE verified=0"),
                       "parks_pending": n("SELECT COUNT(*) n FROM parks WHERE pending=1")},
            "period": {"pets": per(pet_t), "users": per(usr_t), "lost": per(lost_t), "parks": per(park_t), "messages": per(msg_t)},
            "series": list(series.values()), "latest": latest, "species": species, "events": ev[:25]}


@app.get("/api/admin/settings")
def admin_settings(request: Request):
    admin_or_403(request)
    tok = db.get_setting("tg_token")
    return {"public_url": db.get_setting("public_url") or PUBLIC_URL, "allow_register": registration_open(),
            # el token no se devuelve entero: es una contraseña del bot
            "tg_token_set": bool(tok), "tg_token_hint": (tok[:6] + "…") if tok else "", "tg_chat": db.get_setting("tg_chat"),
            "tg_daily": db.get_setting("tg_daily") != "0"} | legal()


@app.put("/api/admin/settings")
async def admin_settings_put(request: Request):
    admin_or_403(request)
    d = await request.json()
    if "public_url" in d:
        db.set_setting("public_url", clean_public_url(d["public_url"]))
    if "allow_register" in d:
        db.set_setting("allow_register", "1" if d["allow_register"] else "0")
    if d.get("tg_token") is not None and str(d["tg_token"]).strip() != "":
        tok = text(d["tg_token"], 100)
        if not re.fullmatch(r"\d{5,15}:[A-Za-z0-9_-]{20,60}", tok):
            err(400, "Ese token de Telegram no parece válido. Es como 123456789:ABC… y te lo da @BotFather")
        db.set_setting("tg_token", tok)
    if "legal_name" in d:
        db.set_setting("legal_name", text(d["legal_name"], 120))
    if "legal_place" in d:
        db.set_setting("legal_place", text(d["legal_place"], 120))
    if "legal_email" in d:
        db.set_setting("legal_email", clean_email(d["legal_email"]) if text(d["legal_email"], 120) else "")
    if "tg_daily" in d:
        db.set_setting("tg_daily", "1" if d["tg_daily"] else "0")
    if d.get("tg_clear"):
        db.set_setting("tg_token", ""); db.set_setting("tg_chat", "")
    if "tg_chat" in d:
        chat = text(d["tg_chat"], 40)
        if chat and not re.fullmatch(r"-?\d{3,20}|@[A-Za-z0-9_]{4,40}", chat):
            err(400, "El chat de Telegram es un número (por ejemplo 123456789) o @nombre_del_canal")
        db.set_setting("tg_chat", chat)
    return admin_settings(request)


@app.post("/api/admin/telegram/link")
def admin_tg_link(request: Request):
    """Enlace para conectar el chat del administrador: lo abre en el móvil, pulsa «Iniciar» y listo."""
    admin_or_403(request)
    if not db.get_setting("tg_token"):
        err(400, "Primero guarda el token del bot")
    try:
        url, name = bot.link_url()
    except Exception as e:  # noqa: BLE001
        err(400, bot.explain(e))
    return {"url": url, "bot": name}


# --- lo que hace el bot de Telegram al pulsar sus botones o escribirle comandos ---
def _tg_org_ok(uid):
    o = get_org(uid)
    if not o:
        return "Esa asociación ya no existe"
    db.run("UPDATE orgs SET verified=1 WHERE user_id=?", uid)
    return f"Asociación {o['name']} verificada ✅"


def _tg_park_ok(pid):
    r = db.q1("SELECT * FROM parks WHERE id=?", pid)
    if not r:
        return "Ese pipicán ya no existe"
    db.run("UPDATE parks SET pending=0 WHERE id=?", pid)
    return f"Pipicán {r['name']} aprobado ✅ Ya sale en el mapa"


def _tg_park_del(pid):
    r = db.q1("SELECT * FROM parks WHERE id=?", pid)
    if not r:
        return "Ese pipicán ya no existe"
    _delete_park(r)
    return f"Pipicán {r['name']} borrado 🗑️"


def _counts(since=0):
    n = lambda sql, *a: db.q1(sql, *a)["n"] or 0
    return {"users": n("SELECT COUNT(*) n FROM users WHERE created>=?", since),
            "orgs": n("SELECT COUNT(*) n FROM orgs WHERE created>=?", since),
            "pets": n("SELECT COUNT(*) n FROM pets WHERE created>=?", since),
            "lost": n("SELECT COUNT(*) n FROM pets WHERE lost=1 AND lost_at>=?", since),
            "parks": n("SELECT COUNT(*) n FROM parks WHERE created>=?", since),
            "msgs": n("SELECT COUNT(*) n FROM messages WHERE created>=?", since)}


def _tg_status():
    c, n = _counts(), lambda sql: db.q1(sql)["n"] or 0
    return (f"📊 MascotasPanel {VERSION}\n\n👤 Personas: {c['users']}\n🏡 Asociaciones: {c['orgs']} ({n('SELECT COUNT(*) n FROM orgs WHERE verified=0')} sin verificar)"
            f"\n🐾 Mascotas: {c['pets']}\n🚨 Perdidas ahora: {n('SELECT COUNT(*) n FROM pets WHERE lost=1')}"
            f"\n💛 En adopción: {n('SELECT COUNT(*) n FROM pets WHERE adopt=1')}"
            f"\n🌳 Pipicanes: {n('SELECT COUNT(*) n FROM parks WHERE pending=0')} ({n('SELECT COUNT(*) n FROM parks WHERE pending=1')} por revisar)"
            f"\n✉️ Avisos desde el QR: {c['msgs']}")


def _tg_summary():
    t0 = time.mktime(time.localtime()[:3] + (0, 0, 0, 0, 0, -1))
    c = _counts(t0)
    lost = db.q("SELECT name FROM pets WHERE lost=1 ORDER BY lost_at DESC LIMIT 10")
    return (f"🗓️ Resumen de hoy ({time.strftime('%d/%m/%Y')})\n\n👤 Personas nuevas: {c['users']}\n🏡 Asociaciones nuevas: {c['orgs']}"
            f"\n🐾 Mascotas nuevas: {c['pets']}\n🚨 Perdidas hoy: {c['lost']}\n🌳 Pipicanes nuevos: {c['parks']}\n✉️ Avisos desde el QR: {c['msgs']}"
            + (f"\n\n🚨 Siguen perdidas: {', '.join(r['name'] for r in lost)}" if lost else "\n\n🏠 No hay ninguna mascota perdida.")
            + "\n\n" + _tg_status())


def _tg_pending():
    out = []
    for o in db.q("SELECT o.*, u.name uname, u.username FROM orgs o JOIN users u ON u.id=o.user_id WHERE o.verified=0 LIMIT 10"):
        out.append((f"🏡 Asociación sin verificar: {o['name']}\n👤 {o['uname']} (@{o['username']}) · ✉️ {o['email']}", _photo(o["logo"]),
                    [[("✅ Verificar asociación", f"org_ok:{o['user_id']}")]]))
    for r in db.q("SELECT * FROM parks WHERE pending=1 ORDER BY id LIMIT 10"):
        out.append((f"🌳 Pipicán por revisar: {r['name']}\n🗺️ https://www.google.com/maps/search/?api=1&query={r['lat']},{r['lng']}",
                    _photo(r["photo"]), [[("✅ Aprobar", f"park_ok:{r['id']}"), ("🗑️ Borrar", f"park_del:{r['id']}")]]))
    return out or "✅ No hay nada pendiente de revisar."


def _tg_lost():
    rows = db.q("SELECT * FROM pets WHERE lost=1 ORDER BY lost_at DESC LIMIT 10")
    if not rows:
        return "🏠 Ahora mismo no hay ninguna mascota perdida."
    return [(f"🚨 PERDIDO: {r['name'].upper()}\n{_sp(r['species'])[2]} {_sp(r['species'])[0]}{' · ' + r['breed'] if r['breed'] else ''}"
             + (f"\n📍 {r['lost_zone']}" if r["lost_zone"] else "") + f"\n📅 Desde el {page._date(r['lost_at'], 'es')}"
             + notify_url(f"/m/{r['code']}"), _photo(r["photo"]), None) for r in rows]


bot.ACTIONS.update({"org_ok": _tg_org_ok, "park_ok": _tg_park_ok, "park_del": _tg_park_del})
bot.COMMANDS.update({
    "/estado": _tg_status, "/resumen": _tg_summary, "/pendientes": _tg_pending, "/perdidas": _tg_lost,
    "/ayuda": lambda: ("🐾 Soy el bot de tu MascotasPanel. Te aviso de las altas, las mascotas perdidas, los avisos desde el QR, "
                       "las asociaciones y los pipicanes nuevos (con botones para aprobarlos).\n\n"
                       "/estado · cuántos hay de todo\n/resumen · el resumen de hoy\n/perdidas · las mascotas perdidas ahora\n"
                       "/pendientes · lo que tienes que revisar\n\nCada día a las 21:00 te mando el resumen del día."),
    "/start": lambda: bot.COMMANDS["/ayuda"](),
})
bot.SUMMARY = _tg_summary


@app.post("/api/admin/telegram/test")
def admin_tg_test(request: Request):
    admin_or_403(request)
    ok, msg = notify("✅ MascotasPanel: los avisos por Telegram funcionan.\n\n" + _tg_status(), wait=True)
    if not ok:
        err(400, msg)
    return {"ok": True}


@app.get("/api/novedades")
def novedades(lang: str = "es"):
    out, cur = [], None
    f = Path(__file__).parent / ("NOVEDADES.en.md" if lang == "en" else "NOVEDADES.md")
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            cur = {"version": line[3:].strip(), "items": []}
            out.append(cur)
        elif cur is not None and line.startswith("- "):
            cur["items"].append(line[2:].strip())
        elif cur is not None and line.startswith("  ") and cur["items"]:
            cur["items"][-1] += " " + line.strip()
    return {"version": VERSION, "novedades": out}


# --- QR y fotos --------------------------------------------------------------
@app.get("/qr/{code}.{fmt}")
def qr(code: str, fmt: str, request: Request):
    p = db.q1("SELECT code FROM pets WHERE code=? AND hidden=0", code) if CODE_RE.match(code) else None
    if not p or fmt not in ("svg", "png"):
        err(404, "No encontrado")
    buf = io.BytesIO()
    segno.make(f"{base_url(request)}/m/{p['code']}", error="q").save(
        buf, kind=fmt, scale=16 if fmt == "png" else 10, border=2, dark="#111111", light="#ffffff")
    return Response(buf.getvalue(), media_type="image/svg+xml" if fmt == "svg" else "image/png",
                    headers={"Content-Disposition": f'inline; filename="qr-{p["code"]}.{fmt}"', "Cache-Control": "no-cache"})


@app.get("/f/{name}")
def photo(name: str):
    if not re.match(r"^(pipican-|org-|avatar-)?\d+-[0-9a-f]{12}\.(jpg|png|webp)$", name) or not (PHOTOS / name).is_file():
        err(404, "No encontrado")
    return FileResponse(PHOTOS / name, headers={"Cache-Control": "public, max-age=31536000, immutable"})


# --- páginas públicas --------------------------------------------------------
def req_lang(request: Request) -> str:
    q_ = request.query_params.get("lang", "")
    if q_ in ("es", "en"):
        return q_
    al = (request.headers.get("accept-language") or "es").strip().lower()
    return "es" if not al or al.startswith("es") or al.startswith("*") else "en"


@app.get("/salud")
def health():
    return {"ok": True, "version": VERSION}


@app.get("/robots.txt")
def robots():
    return Response("User-agent: *\nDisallow: /api/\nDisallow: /panel\nDisallow: /m/\nDisallow: /f/\n", media_type="text/plain")


@app.get("/panel", response_class=HTMLResponse)
def panel():
    html_ = (STATIC / "index.html").read_text(encoding="utf-8")
    for f in ("style.css", "theme.js", "i18n.js", "app.js", "poster.js", "pdf.js", "vendor/leaflet/leaflet.js", "vendor/leaflet/leaflet.css"):
        html_ = html_.replace(f"/static/{f}", f"/static/{f}?v={VERSION}")
    return HTMLResponse(html_, headers={"Cache-Control": "no-cache"})


@app.get("/privacidad", response_class=HTMLResponse)
def privacy(request: Request):
    return page.render_privacy(req_lang(request), legal())


@app.get("/aviso-legal", response_class=HTMLResponse)
def legal_notice(request: Request):
    return page.render_legal(req_lang(request), legal(), base_url(request))


@app.get("/adopta", response_class=HTMLResponse)
def adopt_page(request: Request, especie: str = ""):
    rows = adopt_rows(200, especie)
    orgs = db.q("SELECT o.* FROM orgs o JOIN users u ON u.id=o.user_id WHERE o.verified=1 AND u.status='approved' ORDER BY o.name")
    return HTMLResponse(page.render_adopt(rows, orgs, req_lang(request), especie), headers={"Cache-Control": "no-cache"})


@app.get("/asociaciones", response_class=HTMLResponse)
def orgs_page(request: Request):
    return HTMLResponse(page.render_orgs(public_orgs(), req_lang(request)), headers={"Cache-Control": "no-cache"})


@app.get("/asociacion/{org_id}", response_class=HTMLResponse)
def org_page(org_id: int, request: Request):
    lang = req_lang(request)
    o = db.q1("SELECT o.* FROM orgs o JOIN users u ON u.id=o.user_id WHERE o.user_id=? AND o.verified=1 AND u.status='approved'", org_id)
    if not o:
        return HTMLResponse(page.render_404(lang), status_code=404)
    return HTMLResponse(page.render_org(org_json(o, public=True), adopt_rows(200, org_id=org_id), lang),
                        headers={"Cache-Control": "no-cache"})


@app.get("/m/{code}", response_class=HTMLResponse)
def pet_page(code: str, request: Request):
    lang = req_lang(request)
    row = db.q1("SELECT p.*, u.name owner, u.phone, u.email, u.zone FROM pets p JOIN users u ON u.id=p.user_id "
                "WHERE p.code=? AND p.hidden=0 AND u.status='approved'", code) if CODE_RE.match(code) else None
    if not row:
        return HTMLResponse(page.render_404(lang), status_code=404)
    o = get_org(row["user_id"]) if row["adopt"] else None
    if o and o["verified"]:
        return HTMLResponse(page.render_adopt_pet(row, org_json(o, public=True), lang, base_url(request)),
                            headers={"Cache-Control": "no-cache"})
    seen = sightings_of(row["id"]) if row["lost"] else []
    u = db.session_user(request.cookies.get(COOKIE, ""))
    mine = bool(u and u["id"] == row["user_id"])
    return HTMLResponse(page.render_pet(row, lang, base_url(request), seen=seen, mine=mine),
                        headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex"})


@app.get("/pipicanes", response_class=HTMLResponse)
def parks_page(request: Request):
    rows = db.q("SELECT * FROM parks WHERE hidden=0 AND pending=0 ORDER BY id DESC LIMIT 2000")
    return HTMLResponse(page.render_parks(rows, req_lang(request)), headers={"Cache-Control": "no-cache"})


PER_PAGE = 48


@app.get("/", response_class=HTMLResponse)
def home(request: Request, ver: str = "", zona: str = "", especie: str = "", nombre: str = "", pag: int = 1):
    """Inicio público: el registro de todas las mascotas (sin datos de contacto) y las perdidas."""
    lang = req_lang(request)
    view = "perdidas" if ver == "perdidas" else "registro"
    me_ = db.session_user(request.cookies.get(COOKIE, ""))
    where = ["p.hidden=0", "u.status='approved'"]
    args = []
    if view == "perdidas":
        where.append("p.lost=1")
    elif me_ and me_["is_admin"]:
        where.append("1=1")  # el administrador ve todas
    else:
        # privacidad: en el registro cada persona solo ve las suyas (las perdidas están en «Perdidas»); de las demás, solo el total
        where.append(f"p.user_id={int(me_['id']) if me_ else -1}")
    zona, nombre = text(zona, 60), text(nombre, 40)
    if zona:
        where.append("p.lost=1 AND p.lost_zone LIKE ?")
        args.append(f"%{zona}%")
    chip = re.sub(r"\D", "", nombre) if re.fullmatch(r"[\d\s-]{9,}", nombre or "") else ""
    if chip:
        # número de microchip exacto: lleva a su ficha para poder avisar a la familia
        if view != "perdidas":
            where[2] = "1=1"
        where.append("p.chip_search=1 AND REPLACE(REPLACE(p.chip,' ',''),'-','')=?")
        args.append(chip)
    elif nombre:
        where.append("(p.name LIKE ? OR p.breed LIKE ?)")
        args += [f"%{nombre}%", f"%{nombre}%"]
    if especie in SPECIES:
        where.append("p.species=?")
        args.append(especie)
    base_sql = "FROM pets p JOIN users u ON u.id=p.user_id WHERE " + " AND ".join(where)
    found = db.q1("SELECT COUNT(*) n " + base_sql, *args)["n"]
    pag = max(1, min(pag, (found - 1) // PER_PAGE + 1 if found else 1))
    order = "p.lost_at DESC" if view == "perdidas" else "p.lost DESC, p.created DESC"
    rows = db.q(f"SELECT p.*, u.zone {base_sql} ORDER BY {order} LIMIT {PER_PAGE} OFFSET {(pag - 1) * PER_PAGE}", *args)
    counts = db.q1("SELECT COUNT(*) n, SUM(p.lost) lost, SUM(p.species='perro') dogs, SUM(p.species='gato') cats "
                   "FROM pets p JOIN users u ON u.id=p.user_id WHERE p.hidden=0 AND u.status='approved'")
    return HTMLResponse(page.render_home(rows, lang, view, zona, especie, nombre, pag, found, PER_PAGE,
                                         counts["n"] or 0, counts["lost"] or 0, bool(chip), adopt_rows(16), me_id=me_["id"] if me_ else 0,
                                         species=(counts["dogs"] or 0, counts["cats"] or 0), admin=bool(me_ and me_["is_admin"])),
                        headers={"Cache-Control": "private, no-cache" if me_ else "no-cache"})
