"""Base de datos SQLite: personas, sesiones, mascotas y ajustes."""
import hashlib, hmac, os, secrets, sqlite3, threading, time
from .config import CONFIG, ADMIN_EMAIL, ADMIN_PASSWORD, SESSION_DAYS

DB_PATH = CONFIG / "mascotaspanel.db"
_local = threading.local()

# Datos mínimos (RGPD): solo nombre (sin apellidos ni DNI), correo, teléfono y una zona aproximada.
SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL COLLATE NOCASE,
  email TEXT UNIQUE NOT NULL COLLATE NOCASE, name TEXT NOT NULL, phone TEXT DEFAULT '', zone TEXT DEFAULT '',
  pw_hash TEXT NOT NULL, recovery_hash TEXT DEFAULT '', is_admin INTEGER DEFAULT 0,
  status TEXT DEFAULT 'approved', consent REAL, created REAL);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER, expires REAL);
CREATE TABLE IF NOT EXISTS pets(
  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, code TEXT UNIQUE NOT NULL,
  name TEXT DEFAULT '', species TEXT DEFAULT 'perro', breed TEXT DEFAULT '', color TEXT DEFAULT '',
  sex TEXT DEFAULT '', age TEXT DEFAULT '', size TEXT DEFAULT '', chip TEXT DEFAULT '',
  notes TEXT DEFAULT '', health TEXT DEFAULT '', photo TEXT DEFAULT '',
  contact TEXT DEFAULT 'never',
  lost INTEGER DEFAULT 0, lost_at REAL, lost_zone TEXT DEFAULT '', lost_note TEXT DEFAULT '',
  reward TEXT DEFAULT '', hidden INTEGER DEFAULT 0, created REAL, updated REAL);
CREATE INDEX IF NOT EXISTS pets_user ON pets(user_id);
CREATE INDEX IF NOT EXISTS pets_lost ON pets(lost, lost_at);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
-- Avisos de quien encuentra una mascota (sin que vea el teléfono del dueño). Se borran a los 90 días.
CREATE TABLE IF NOT EXISTS messages(
  id INTEGER PRIMARY KEY, pet_id INTEGER NOT NULL, user_id INTEGER NOT NULL, created REAL,
  text TEXT DEFAULT '', contact TEXT DEFAULT '', lat REAL, lng REAL, read INTEGER DEFAULT 0);
CREATE INDEX IF NOT EXISTS messages_user ON messages(user_id, created);
-- «📍 Lo he visto aquí»: dónde y cuándo ha visto alguien a una mascota perdida (sin datos de quien lo apunta).
-- Se ven en su ficha mientras está perdida y se borran cuando vuelve a casa.
CREATE TABLE IF NOT EXISTS sightings(
  id INTEGER PRIMARY KEY, pet_id INTEGER NOT NULL, created REAL, seen_at REAL, lat REAL NOT NULL, lng REAL NOT NULL,
  note TEXT DEFAULT '');
CREATE INDEX IF NOT EXISTS sightings_pet ON sightings(pet_id, seen_at);
-- «Busca tu pipicán»: mapa de pipicanes que va apuntando la gente (sitios públicos, no casas)
CREATE TABLE IF NOT EXISTS parks(
  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, name TEXT DEFAULT '', notes TEXT DEFAULT '',
  lat REAL NOT NULL, lng REAL NOT NULL, photo TEXT DEFAULT '', hidden INTEGER DEFAULT 0, created REAL);
CREATE INDEX IF NOT EXISTS parks_pos ON parks(hidden, lat, lng);
-- Asociaciones y protectoras: una cuenta de tipo «asociación» con su perfil público. Sus animales en
-- adopción solo se publican cuando el administrador la ha verificado.
CREATE TABLE IF NOT EXISTS orgs(
  user_id INTEGER PRIMARY KEY, name TEXT DEFAULT '', city TEXT DEFAULT '', about TEXT DEFAULT '', web TEXT DEFAULT '',
  logo TEXT DEFAULT '', phone TEXT DEFAULT '', show_phone INTEGER DEFAULT 0, whatsapp INTEGER DEFAULT 0,
  telegram TEXT DEFAULT '', email TEXT DEFAULT '', show_email INTEGER DEFAULT 0, verified INTEGER DEFAULT 0, created REAL);
"""


def conn():
    c = getattr(_local, "c", None)
    if c is None:
        c = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA foreign_keys=ON")
        _local.c = c
    return c


def q(sql, *args):
    return conn().execute(sql, args).fetchall()


def q1(sql, *args):
    return conn().execute(sql, args).fetchone()


def run(sql, *args):
    return conn().execute(sql, args)


# --- contraseñas -----------------------------------------------------------
ITER = 120_000


def hash_pw(pw: str) -> str:
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, ITER)
    return f"pbkdf2${ITER}${salt.hex()}${h.hex()}"


def check_pw(pw: str, stored: str) -> bool:
    try:
        _, it, salt, h = stored.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), int(it))
        return hmac.compare_digest(calc.hex(), h)
    except Exception:
        return False


# --- sesiones --------------------------------------------------------------
def new_session(user_id: int) -> str:
    tok = secrets.token_urlsafe(32)
    run("INSERT INTO sessions VALUES(?,?,?)", tok, user_id, time.time() + SESSION_DAYS * 86400)
    return tok


def session_user(tok: str):
    if not tok:
        return None
    u = q1("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id "
           "WHERE s.token=? AND s.expires>?", tok, time.time())
    if u and u["status"] == "approved":
        return u
    return None


# --- ajustes ---------------------------------------------------------------
def get_setting(key, default=""):
    r = q1("SELECT value FROM settings WHERE key=?", key)
    return r["value"] if r else default


def set_setting(key, value):
    run("INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        key, value)


def new_recovery() -> str:
    """Código de recuperación (como un PIN largo): 12 letras y números en grupos de 4."""
    abc = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    c = "".join(secrets.choice(abc) for _ in range(12))
    return f"{c[:4]}-{c[4:8]}-{c[8:]}"


def norm_recovery(c: str) -> str:
    return "".join(ch for ch in str(c or "").upper() if ch.isalnum())


def hash_recovery(c: str) -> str:
    """SHA-256 sin sal: el código es aleatorio y largo (60 bits), así se puede buscar la cuenta solo con él."""
    return hashlib.sha256(("recovery:" + norm_recovery(c)).encode()).hexdigest()


def new_code() -> str:
    """Código público de la ficha (no se puede adivinar): 10 letras y números sin confusiones."""
    abc = "abcdefghjkmnpqrstuvwxyz23456789"
    while True:
        c = "".join(secrets.choice(abc) for _ in range(10))
        if not q1("SELECT 1 FROM pets WHERE code=?", c):
            return c


def init():
    conn().executescript(SCHEMA)
    # Columnas añadidas en versiones nuevas (las bases de datos antiguas no las tienen)
    cols = {r["name"] for r in q("PRAGMA table_info(pets)")}
    for c in ("lost_lat", "lost_lng"):
        if c not in cols:
            run(f"ALTER TABLE pets ADD COLUMN {c} REAL")
    if "public" not in cols:  # que salga en el registro público (sin datos de contacto)
        run("ALTER TABLE pets ADD COLUMN public INTEGER DEFAULT 1")
    if "chip_ok" not in cols:  # consentimiento para guardar el microchip (fecha) y si se puede buscar por él
        run("ALTER TABLE pets ADD COLUMN chip_ok REAL")
        run("ALTER TABLE pets ADD COLUMN chip_search INTEGER DEFAULT 0")
    if "contact2_name" not in cols:  # segunda persona de contacto (pareja, hija…), con las mismas reglas que el teléfono
        run("ALTER TABLE pets ADD COLUMN contact2_name TEXT DEFAULT ''")
        run("ALTER TABLE pets ADD COLUMN contact2_phone TEXT DEFAULT ''")
    if "adopt" not in cols:  # animales en adopción de una asociación, con su mensaje («¿Me adoptas?»)
        run("ALTER TABLE pets ADD COLUMN adopt INTEGER DEFAULT 0")
        run("ALTER TABLE pets ADD COLUMN adopt_text TEXT DEFAULT ''")
    if "tracker_lat" not in cols:  # última posición que dio el localizador de Google (Find Hub), la pone el dueño
        run("ALTER TABLE pets ADD COLUMN tracker_lat REAL")
        run("ALTER TABLE pets ADD COLUMN tracker_lng REAL")
        run("ALTER TABLE pets ADD COLUMN tracker_at REAL")
    if "tracker_kind" not in cols:  # qué localizador lleva: «google» (Find Hub), «apple» (AirTag) o nada
        run("ALTER TABLE pets ADD COLUMN tracker_kind TEXT DEFAULT ''")
    if "transfer_to" not in cols:  # pasar la ficha a otra cuenta: esa cuenta tiene que aceptarlo
        run("ALTER TABLE pets ADD COLUMN transfer_to INTEGER DEFAULT 0")
    if "contact2_ok" not in cols:  # la segunda persona ha dado su permiso (fecha)
        run("ALTER TABLE pets ADD COLUMN contact2_ok REAL")
        run("UPDATE pets SET contact2_ok=updated WHERE contact2_phone<>''")
    if get_setting("public_off_1012") != "1":
        # 1.0.12: el registro público pasa a ser opcional y desactivado por defecto. Las fichas ya apuntadas dejan de
        # salir (salvo las perdidas o en adopción); cada dueño puede volver a activarlo en su ficha.
        run("UPDATE pets SET public=0")
        set_setting("public_off_1012", "1")
    pk = {r["name"] for r in q("PRAGMA table_info(parks)")}
    if "dupe_of" not in pk:  # «es otro distinto» a pesar de estar muy cerca de este: que lo mire el administrador
        run("ALTER TABLE parks ADD COLUMN dupe_of INTEGER DEFAULT 0")
    ocols = {r["name"] for r in q("PRAGMA table_info(orgs)")}
    for c in ("legal_name", "cif", "reg_number", "zoo_number"):  # datos legales de la asociación (públicos)
        if c not in ocols:
            run(f"ALTER TABLE orgs ADD COLUMN {c} TEXT DEFAULT ''")
    ucols = {r["name"] for r in q("PRAGMA table_info(users)")}
    if "avatar" not in ucols:  # foto de perfil (opcional)
        run("ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT ''")
    kcols = {r["name"] for r in q("PRAGMA table_info(parks)")}
    if "osm_id" not in kcols:  # pipicanes importados de OpenStreetMap (para no repetirlos)
        run("ALTER TABLE parks ADD COLUMN osm_id TEXT DEFAULT ''")
    if "pending" not in kcols:  # 1 = apuntado por alguien y sin revisar todavía por el administrador
        run("ALTER TABLE parks ADD COLUMN pending INTEGER DEFAULT 0")
    ucols = {r["name"] for r in q("PRAGMA table_info(users)")}
    if "seen_version" not in ucols:  # última versión cuyas novedades ha visto (para enseñarle la ventana al actualizar)
        run("ALTER TABLE users ADD COLUMN seen_version TEXT DEFAULT ''")
    if "kind" not in ucols:  # «person» o «org» (asociación o protectora)
        run("ALTER TABLE users ADD COLUMN kind TEXT DEFAULT 'person'")
    if "age_ok" not in ucols:  # ha confirmado que tiene 14 años o más (LOPDGDD art. 7), con fecha
        run("ALTER TABLE users ADD COLUMN age_ok REAL")
        run("ALTER TABLE users ADD COLUMN consent_v TEXT DEFAULT ''")
    if get_setting("privacy_v2") != "1":
        # 1.0.1: el teléfono pasa a estar oculto salvo consentimiento expreso. Antes «siempre» era lo que venía
        # marcado, así que no cuenta como consentimiento: se oculta y cada dueño lo vuelve a activar si quiere.
        run("UPDATE pets SET contact='never' WHERE contact='always'")
        set_setting("privacy_v2", "1")
    run("DELETE FROM sessions WHERE expires<?", time.time())
    run("DELETE FROM messages WHERE created<?", time.time() - 90 * 86400)
    if ADMIN_EMAIL and ADMIN_PASSWORD and not q1("SELECT 1 FROM users WHERE email=?", ADMIN_EMAIL):
        run("INSERT INTO users(username,email,name,pw_hash,is_admin,status,consent,created) VALUES(?,?,?,?,1,'approved',?,?)",
            "admin", ADMIN_EMAIL, "Admin", hash_pw(ADMIN_PASSWORD), time.time(), time.time())
