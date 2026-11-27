"""Bot de Telegram del administrador: avisos (con foto), botones para aprobar desde el móvil y resumen diario.

No hace falta abrir puertos ni tener la web en Internet: el servidor pregunta a Telegram cada poco
(getUpdates) si el administrador ha pulsado algún botón o escrito un comando.
"""
import json, secrets, threading, time, urllib.error, urllib.request
from pathlib import Path

from . import db

API = "https://api.telegram.org/bot{tok}/{method}"
ACTIONS = {}    # "park_ok" -> función(id) -> texto del resultado; las pone main.py
COMMANDS = {}   # "/estado" -> función() -> texto
SUMMARY = None  # función() -> texto del resumen diario
SUMMARY_HOUR = 21


def creds():
    return db.get_setting("tg_token"), db.get_setting("tg_chat")


def call(method, data=None, files=None, tok=None, timeout=15):
    """Llama a la API de Telegram. files: {"photo": Path}. Devuelve el «result» o lanza una excepción."""
    tok = tok or db.get_setting("tg_token")
    url = API.format(tok=tok, method=method)
    if files:
        b = "----mascotas" + secrets.token_hex(8)
        body = bytearray()
        for k, v in (data or {}).items():
            v = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        for k, p in files.items():
            ctype = "image/png" if str(p).endswith(".png") else "image/webp" if str(p).endswith(".webp") else "image/jpeg"
            body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{Path(p).name}"\r\nContent-Type: {ctype}\r\n\r\n'.encode()
            body += Path(p).read_bytes() + b"\r\n"
        body += f"--{b}--\r\n".encode()
        req = urllib.request.Request(url, data=bytes(body), headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    else:
        req = urllib.request.Request(url, data=json.dumps(data or {}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.loads(r.read())
    if not out.get("ok"):
        raise RuntimeError(out.get("description", "error"))
    return out.get("result")


def explain(e):
    if isinstance(e, urllib.error.HTTPError):
        return ("Telegram dice que el token no vale" if e.code == 401 else
                "Telegram no encuentra ese chat: escribe primero al bot y revisa el número" if e.code in (400, 403) else
                f"Telegram ha respondido con un error ({e.code})")
    return "No se puede conectar con Telegram desde el servidor"


def keyboard(buttons):
    """buttons: [[("✅ Aprobar", "park_ok:12"), …], …] -> teclado de botones debajo del mensaje."""
    return {"inline_keyboard": [[{"text": t, "callback_data": d} if not d.startswith("http") else {"text": t, "url": d}
                                 for t, d in row] for row in buttons]}


def send(msg, photo=None, buttons=None, chat=None):
    """Manda un aviso. photo: ruta de una foto del servidor (se sube, así no hace falta que la web sea pública)."""
    tok, chat0 = creds()
    chat = chat or chat0
    if not tok or not chat:
        return False, "Primero guarda el token del bot y el chat"
    try:
        extra = {"reply_markup": keyboard(buttons)} if buttons else {}
        if photo and Path(photo).is_file():
            try:
                call("sendPhoto", {"chat_id": chat, "caption": msg[:1024], **extra}, files={"photo": photo}, timeout=30)
                return True, ""
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    raise
                # si la foto no le gusta a Telegram (formato raro), manda solo el texto
        call("sendMessage", {"chat_id": chat, "text": msg, "disable_web_page_preview": True, **extra})
        return True, ""
    except Exception as e:  # noqa: BLE001
        return False, explain(e)


def notify(msg, wait=False, photo=None, buttons=None, delay=0):
    """Aviso al administrador sin frenar la petición. photo puede ser una función (se mira al mandar)."""
    tok, chat = creds()
    if not tok or not chat:
        return False, "Primero guarda el token del bot y el chat"

    def go():
        if delay:
            time.sleep(delay)
        p = photo() if callable(photo) else photo
        return send(msg, p, buttons)
    if wait:
        return go()
    threading.Thread(target=go, daemon=True).start()
    return True, ""


def link_url():
    """Enlace t.me/<bot>?start=<código> para conectar el chat del administrador con un toque."""
    me = call("getMe")
    code = secrets.token_urlsafe(12)
    db.set_setting("tg_link", f"{code}|{time.time() + 1800:.0f}")
    return f"https://t.me/{me['username']}?start={code}", me["username"]


# --- escuchar a Telegram -------------------------------------------------------
_offset = 0


def _handle(u):
    tok, chat = creds()
    if "callback_query" in u:
        cq = u["callback_query"]
        m = cq.get("message") or {}
        cid = str((m.get("chat") or {}).get("id", ""))
        if not chat or cid != str(chat):
            call("answerCallbackQuery", {"callback_query_id": cq["id"], "text": "No tienes permiso"})
            return
        name, _, arg = str(cq.get("data", "")).partition(":")
        fn = ACTIONS.get(name)
        try:
            res = fn(int(arg)) if fn else "Acción desconocida"
        except Exception as e:  # noqa: BLE001
            res = f"No se ha podido: {e}"
        call("answerCallbackQuery", {"callback_query_id": cq["id"], "text": res[:190]})
        # quita los botones y apunta lo que se ha hecho
        key = "caption" if "caption" in m else "text"
        old = m.get(key, "")
        try:
            call("editMessageCaption" if key == "caption" else "editMessageText",
                 {"chat_id": cid, "message_id": m["message_id"], key: f"{old}\n\n➡️ {res}"[:1024 if key == "caption" else 4096]})
        except Exception:  # noqa: BLE001
            pass
        return
    m = u.get("message") or {}
    cid = str((m.get("chat") or {}).get("id", ""))
    txt = (m.get("text") or "").strip()
    if not cid or not txt:
        return
    cmd, _, arg = txt.partition(" ")
    cmd = cmd.split("@")[0].lower()
    if cmd == "/start" and arg:
        saved = db.get_setting("tg_link") or ""
        code, _, until = saved.partition("|")
        if code and secrets.compare_digest(arg.strip(), code) and float(until or 0) > time.time():
            db.set_setting("tg_chat", cid)
            db.set_setting("tg_link", "")
            call("sendMessage", {"chat_id": cid, "text": "✅ ¡Conectado! Aquí te avisaré de todo lo que pase en MascotasPanel.\n\n"
                                 "Escribe /ayuda para ver lo que puedo hacer."})
            return
    if not chat or cid != str(chat):
        call("sendMessage", {"chat_id": cid, "text": "🐾 Este bot es privado: solo avisa al administrador de su MascotasPanel."})
        return
    fn = COMMANDS.get(cmd) or COMMANDS.get("/ayuda")
    if fn:
        out = fn()
        if isinstance(out, list):  # varios mensajes, con botones
            for o in out:
                send(*o)
        else:
            call("sendMessage", {"chat_id": cid, "text": out, "disable_web_page_preview": True})


def _maybe_summary():
    if not SUMMARY or db.get_setting("tg_daily") == "0":
        return
    now = time.localtime()
    today = time.strftime("%Y-%m-%d", now)
    if now.tm_hour >= SUMMARY_HOUR and db.get_setting("tg_daily_last") != today:
        db.set_setting("tg_daily_last", today)
        send(SUMMARY())


def _loop():
    global _offset
    last_tok = None
    while True:
        tok, chat = creds()
        if not tok:
            time.sleep(20)
            continue
        try:
            if tok != last_tok:
                call("deleteWebhook", {"drop_pending_updates": False})
                last_tok = tok
            if chat:
                _maybe_summary()
            ups = call("getUpdates", {"offset": _offset, "timeout": 30, "allowed_updates": ["message", "callback_query"]}, timeout=45)
            for u in ups or []:
                _offset = u["update_id"] + 1
                try:
                    _handle(u)
                except Exception:  # noqa: BLE001
                    pass
        except urllib.error.HTTPError as e:
            time.sleep(300 if e.code == 401 else 30)  # 401: token malo; 409: otro programa usa el mismo bot
        except Exception:  # noqa: BLE001
            time.sleep(30)


_started = False


def start():
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_loop, daemon=True, name="telegram").start()
