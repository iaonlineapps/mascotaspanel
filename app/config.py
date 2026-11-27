"""Configuracion leida de variables de entorno (ver .env.example)."""
import os
from pathlib import Path


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


DATA = Path(os.environ.get("MASCOTASPANEL_DATA", "./data")).resolve()
CONFIG = DATA / "config"
PHOTOS = DATA / "fotos"
for p in (CONFIG, PHOTOS):
    p.mkdir(parents=True, exist_ok=True)

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "").strip().lower()
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
ALLOW_REGISTER = os.environ.get("ALLOW_REGISTER", "1") == "1"
MAX_PETS = max(1, _int("MAX_PETS", 20))           # mascotas por persona
SESSION_DAYS = 30
# Datos del responsable para el aviso de privacidad (RGPD)
OWNER_NAME = os.environ.get("OWNER_NAME", "").strip()
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "").strip()
# Dirección pública (por ejemplo https://mascotas.midominio.com). También en Administración.
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").strip().rstrip("/")
