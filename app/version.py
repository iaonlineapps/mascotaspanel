"""Version de MascotasPanel que se ve en la web.

Se toma de la variable MASCOTASPANEL_VERSION (la pone la imagen Docker publicada) o, si no,
del archivo app/VERSION. Al sacar una version nueva, cambia app/VERSION.
"""
import os
from pathlib import Path


def _read() -> str:
    v = os.environ.get("MASCOTASPANEL_VERSION", "").strip().lstrip("vV")
    if v and v[0].isdigit():
        return v
    try:
        return (Path(__file__).parent / "VERSION").read_text().strip() or "?"
    except OSError:
        return "?"


VERSION = _read()
