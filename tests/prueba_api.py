"""Prueba rápida de la API: python3 tests/prueba_api.py (con el servidor en http://127.0.0.1:8093)."""
import base64, http.cookiejar, json, sys, urllib.request, urllib.error

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8093"
PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 100).decode()


def client():
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def call(method, path, body=None, ok=True):
        req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", "X-MascotasPanel": "1"})
        try:
            r = op.open(req); code, raw = r.status, r.read()
        except urllib.error.HTTPError as e:
            code, raw = e.code, e.read()
        if ok and code >= 400:
            raise AssertionError(f"{method} {path} -> {code} {raw[:200]}")
        try:
            return code, json.loads(raw)
        except ValueError:
            return code, raw.decode("utf-8", "replace")
    return call


a = client()
_, r = a("POST", "/api/register", {"username": "alex", "email": "alex@example.com", "name": "Alex", "phone": "600123456",
                                    "zone": "Valencia", "password": "contrasena1", "accept": True, "age_ok": True})
code_a = r["recovery"]; assert len(code_a) == 14
a("POST", "/api/login", {"login": "alex", "password": "contrasena1"})
_, me = a("GET", "/api/me"); assert me["user"]["is_admin"]
_, p = a("POST", "/api/pets", {"name": "Toby", "species": "perro", "breed": "Mestizo", "color": "Marrón"})
a("POST", f"/api/pets/{p['id']}/photo", {"data": PNG})
_, p = a("PUT", f"/api/pets/{p['id']}", {"lost": True, "lost_zone": "Benimaclet", "reward": "100 €"})
assert p["lost"] and p["lost_at"]
_, home = a("GET", "/?ver=perdidas"); assert "Toby" in home and "600123456" not in home, "el teléfono no debe salir en la lista"
assert p["contact"] == "never", "el teléfono está oculto por defecto"
_, ficha = a("GET", "/m/" + p["code"]); assert "600123456" not in ficha and "Valencia" not in ficha and 'id="found"' in ficha
_, home = a("GET", "/"); assert "Valencia" not in home, "la zona de la persona no sale en el registro"
# con su consentimiento, el teléfono sale solo mientras está perdida
a("PUT", f"/api/pets/{p['id']}", {"contact": "lost"})
_, ficha = a("GET", "/m/" + p["code"]); assert "tel:600123456" in ficha and "alex@example.com" not in ficha
c, _ = a("PUT", f"/api/pets/{p['id']}", {"contact2_name": "Marta", "contact2_phone": "611222333"}, ok=False); assert c == 400, "hace falta el permiso de la otra persona"
a("PUT", f"/api/pets/{p['id']}", {"contact2_name": "Marta", "contact2_phone": "611222333", "contact2_ok": True})
_, ficha = a("GET", "/m/" + p["code"]); assert "tel:611222333" in ficha and "Marta" in ficha
c, _ = a("GET", f"/qr/{p['code']}.png", ok=False); assert c == 200
# quien la encuentra avisa sin ver el teléfono
z = client()
z("POST", f"/api/found/{p['code']}", {"text": "La tengo yo", "contact": "699000111"})
_, msgs = a("GET", "/api/messages"); assert msgs and msgs[0]["text"] == "La tengo yo"
# 1.0.16: «Lo he visto aquí» (sin cuenta) y la última posición del localizador (la pone el dueño)
z("POST", f"/api/seen/{p['code']}", {"lat": 39.4812345, "lng": -0.3567891, "note": "Iba hacia el río"})
c, _ = z("POST", f"/api/seen/{p['code']}", {"note": "sin sitio"}, ok=False); assert c == 400, "hace falta el sitio"
_, seen = z("GET", f"/api/seen/{p['code']}"); assert seen[0]["note"] == "Iba hacia el río" and seen[0]["lat"] == 39.4812
_, own = a("GET", f"/api/pets/{p['id']}/seen"); assert len(own) == 1
_, msgs = a("GET", "/api/messages"); assert msgs[0]["text"].startswith("📍") and msgs[0]["lat"]
_, p = a("PUT", f"/api/pets/{p['id']}", {"tracker_kind": "apple", "tracker_lat": 39.48, "tracker_lng": -0.35, "tracker_at": 1})
assert p["tracker_kind"] == "apple" and p["tracker_lat"] == 39.48
_, ficha = z("GET", "/m/" + p["code"]); assert 'id="seenBtn"' in ficha and "Iba hacia el río" in ficha and 'id="trkOpen"' not in ficha
_, ficha = a("GET", "/m/" + p["code"]); assert 'id="trkOpen"' in ficha, "el dueño ve el botón de su localizador"
a("DELETE", f"/api/pets/{p['id']}/seen/{own[0]['id']}")
_, own = a("GET", f"/api/pets/{p['id']}/seen"); assert not own
z("POST", f"/api/seen/{p['code']}", {"lat": 39.48, "lng": -0.35})
a("PUT", f"/api/pets/{p['id']}", {"lost": False})
_, ficha = a("GET", "/m/" + p["code"]); assert "tel:" not in ficha and "Marta" not in ficha and 'id="seenBtn"' not in ficha
_, own = a("GET", f"/api/pets/{p['id']}/seen"); assert not own, "al volver a casa se borran los avistamientos"
c, _ = z("POST", f"/api/seen/{p['code']}", {"lat": 39.48, "lng": -0.35}, ok=False); assert c == 404
_, home = a("GET", "/?ver=perdidas"); assert "Toby" not in home
anon = client()
_, home = anon("GET", "/"); assert "Toby" not in home and "mascotas registradas" in home, "en el registro los demás solo ven el total"
_, home = a("GET", "/"); assert f"/panel#m{p['id']}" in home, "el dueño la ve como suya y la puede abrir"
c, _ = a("PUT", f"/api/pets/{p['id']}", {"chip": "941 000 024 680 135"}, ok=False); assert c == 400, "el chip necesita consentimiento"
a("PUT", f"/api/pets/{p['id']}", {"chip": "941 000 024 680 135", "chip_ok": True})
_, home = anon("GET", "/?nombre=941000024680135"); assert p["code"] not in home, "sin permiso no se busca por chip"
a("PUT", f"/api/pets/{p['id']}", {"chip": "941 000 024 680 135", "chip_ok": True, "chip_search": True})
_, home = anon("GET", "/?nombre=941000024680135"); assert p["code"] in home, "buscando el chip exacto lleva a la ficha"
_, ficha = a("GET", "/m/" + p["code"]); assert "941" not in ficha, "el chip no se enseña nunca"
a("PUT", f"/api/pets/{p['id']}", {"public": False})
_, home = anon("GET", "/"); assert "Toby" not in home, "si no quiere salir en el registro, no sale"
c, csv_ = a("GET", "/api/admin/export.csv"); assert "Toby" in csv_ and "941" in csv_

# otra persona no puede tocar la mascota
b = client()
c, _ = b("POST", "/api/register", {"username": "alex", "email": "otra@example.com", "name": "Ana", "phone": "611222333", "password": "contrasena2", "accept": True, "age_ok": True}, ok=False)
assert c == 409
c, _ = b("POST", "/api/register", {"username": "ana", "email": "ana@example.com", "name": "Ana", "phone": "611222333", "password": "contrasena2"}, ok=False)
assert c == 400, "sin consentimiento no se registra"
b("POST", "/api/register", {"username": "ana", "email": "ana@example.com", "name": "Ana", "password": "contrasena2", "accept": True, "age_ok": True})
b("POST", "/api/login", {"login": "ana@example.com", "password": "contrasena2"})
c, _ = b("GET", f"/api/pets/{p['id']}", ok=False); assert c == 404
c, _ = b("GET", "/api/admin/users", ok=False); assert c == 403

# recuperar la cuenta solo con el código
c, _ = b("POST", "/api/recover", {"code": "AAAA-BBBB-CCCC", "password": "nueva12345"}, ok=False); assert c == 400
_, r = b("POST", "/api/recover", {"code": code_a.lower(), "password": "nueva12345"})
assert r["username"] == "alex" and r["recovery"] != code_a
c, _ = b("POST", "/api/recover", {"code": code_a, "password": "otra123456"}, ok=False); assert c == 400, "el código viejo ya no vale"
c, _ = a("GET", "/api/me"); assert _["user"] is None, "al recuperar se cierran las sesiones"
a("POST", "/api/login", {"login": "alex@example.com", "password": "nueva12345"})

# pipicanes: cualquiera con cuenta los apunta; el mapa es público y no dice quién los puso
c, _ = b("POST", "/api/parks", {"name": "Pipicán del río"}, ok=False); assert c == 400, "sin sitio no vale"
_, k = b("POST", "/api/parks", {"name": "Pipicán del río", "lat": 39.47, "lng": -0.37, "notes": "Vallado"})
_, ll = b("POST", "/api/maps-link", {"url": "https://www.google.com/maps/place/Pipic%C3%A1n+del+Turia/@39.4766,-0.3632,17z/data=!3d39.47712!4d-0.36254"})
assert ll["lat"] == 39.47712 and ll["lng"] == -0.36254 and ll["name"] == "Pipicán del Turia"
c, _ = b("POST", "/api/maps-link", {"url": "https://evil.example.com/@1.0,2.0"}, ok=False); assert c == 400
anon = client()
_, ks = anon("GET", "/api/parks"); assert not ks, "sin aprobar no sale en el mapa"
_, mine = b("GET", "/api/parks/mine"); assert mine[0]["pending"] and mine[0]["can_edit"]
_, k2 = b("PUT", f"/api/parks/{k['id']}", {"name": "Pipicán del río Turia", "notes": "Vallado y con fuente"}); assert k2["name"] == "Pipicán del río Turia"
c, _ = anon("PUT", f"/api/parks/{k['id']}", {"name": "x"}, ok=False); assert c == 401
_, ka = a("GET", "/api/admin/parks"); assert ka[0]["pending"]
a("POST", f"/api/admin/parks/{k['id']}", {"action": "approve"})
a("PUT", f"/api/parks/{k['id']}", {"name": "Pipicán del río"})  # el administrador también puede cambiarlo y no vuelve a revisión
_, ks = anon("GET", "/api/parks"); assert ks[0]["name"] == "Pipicán del río" and "author" not in ks[0] and "user_id" not in ks[0]
_, html = anon("GET", "/pipicanes"); assert "Pipicán del río" in html and "Ana" not in html
c, _ = anon("POST", "/api/parks", {"name": "x", "lat": 1, "lng": 1}, ok=False); assert c == 401
_, ka = a("GET", "/api/admin/parks"); assert ka[0]["author"] == "Ana"
# panel de control y Telegram: solo el administrador
c, _ = b("GET", "/api/admin/dashboard", ok=False); assert c == 403
_, dash = a("GET", "/api/admin/dashboard"); assert dash["totals"]["parks"] == 1 and len(dash["series"]) == 30 and dash["events"] and dash["period"]["pets"]["now"] >= 1
c, _ = a("PUT", "/api/admin/settings", {"tg_token": "no-vale"}, ok=False); assert c == 400
_, st = a("PUT", "/api/admin/settings", {"tg_token": "123456789:" + "A" * 35, "tg_chat": "123456789"})
assert st["tg_token_set"] and "AAAAAAAAAA" not in json.dumps(st), "el token no se devuelve entero"
a("PUT", "/api/admin/settings", {"tg_clear": True})

# edad mínima y aviso legal
c, _ = anon("POST", "/api/register", {"username": "peque", "email": "p@example.com", "name": "Peque", "password": "contrasena9", "accept": True}, ok=False)
assert c == 400, "sin confirmar 14 años no se registra"
a("PUT", "/api/admin/settings", {"legal_name": "Responsable Prueba", "legal_email": "priv@example.com"})
_, html = anon("GET", "/privacidad"); assert "Responsable Prueba" in html and "14 años" in html
_, html = anon("GET", "/aviso-legal"); assert "Responsable Prueba" in html
# asociaciones y adopción
c, _ = b("POST", "/api/pets", {"name": "Kira", "species": "perro", "adopt": True}, ok=False); assert c == 400, "una persona no pone animales en adopción"
o = client()
o("POST", "/api/register", {"username": "protectora", "email": "prote@example.com", "name": "Lucía", "password": "contrasena3",
                            "accept": True, "age_ok": True, "kind": "org", "org_name": "Huellas Valencia", "zone": "Valencia",
                            "org_legal": "Asociación Protectora Huellas", "org_cif": "g-12345678"})
o("POST", "/api/login", {"login": "protectora", "password": "contrasena3"})
_, m = o("GET", "/api/me"); assert m["user"]["kind"] == "org" and not m["user"]["org"]["verified"]
o("PUT", "/api/org", {"phone": "600999888", "show_phone": False, "whatsapp": True, "telegram": "@huellas_vlc"})
_, kp = o("POST", "/api/pets", {"name": "Kira", "species": "perro", "adopt": True, "adopt_text": "¿Me adoptas?"})
_, ad = anon("GET", "/api/adopt"); assert ad == [], "sin verificar no se publica"
assert m["user"]["org"]["cif"] == "G12345678" and m["user"]["org"]["legal_name"] == "Asociación Protectora Huellas"
c, _ = o("PUT", "/api/org", {"cif": "12345"}, ok=False); assert c == 400, "CIF mal escrito"
o("PUT", "/api/org", {"reg_number": "CV-01-012345-V", "zoo_number": "NZ-46-001"})
_, ol = anon("GET", "/api/orgs"); assert ol == [], "sin verificar no sale en Asociaciones"
_, ao = a("GET", "/api/admin/orgs"); assert ao[0]["reg_number"] == "CV-01-012345-V" and not ao[0]["verified"]
c, _ = b("GET", "/api/admin/orgs", ok=False); assert c == 403
a("POST", f"/api/admin/users/{m['user']['id']}", {"action": "verify"})
_, ad = anon("GET", "/api/adopt"); assert ad and ad[0]["name"] == "Kira" and ad[0]["org"] == "Huellas Valencia"
_, html = anon("GET", "/m/" + kp["code"]); assert "Huellas Valencia" in html and "t.me/huellas_vlc" in html and "wa.me/34600999888" in html and "tel:" not in html
_, html = anon("GET", "/adopta"); assert "Kira" in html
_, html = anon("GET", f"/asociacion/{m['user']['id']}"); assert "Kira" in html and "G12345678" in html and "NZ-46-001" in html
_, ol = anon("GET", "/api/orgs"); assert ol[0]["name"] == "Huellas Valencia" and ol[0]["n_adopt"] == 1 and ol[0]["cif"] == "G12345678"
assert ol[0]["phone"] == "", "el teléfono oculto no sale"
_, html = anon("GET", "/asociaciones"); assert "Huellas Valencia" in html and "CIF G12345678" in html
_, html = anon("GET", "/"); assert "Kira" in html and "Me adoptas" in html
anon("POST", f"/api/found/{kp['code']}", {"text": "Me gustaría conocer a Kira", "contact": "x@example.com"})
_, msgs = o("GET", "/api/messages"); assert msgs[0]["text"].startswith("Me gustaría")
_, dash = a("GET", "/api/admin/dashboard"); assert dash["totals"]["adopt"] == 1 and dash["totals"]["orgs"] == 1

# pasar una ficha a otra cuenta: la otra cuenta acepta; el administrador la pasa directamente
c, _ = o("POST", f"/api/pets/{kp['id']}/transfer", {"to": "nadie"}, ok=False); assert c == 404
_, kx = o("POST", f"/api/pets/{kp['id']}/transfer", {"to": "@ANA"}); assert kx["transfer_to"]["username"] == "ana"
c, _ = anon("POST", f"/api/transfers/{kp['id']}", {"accept": True}, ok=False); assert c == 401
_, mb = b("GET", "/api/me"); assert mb["transfers"][0]["name"] == "Kira"
b("POST", f"/api/transfers/{kp['id']}", {"accept": False})
_, mo = o("GET", "/api/pets"); assert not mo[0].get("transfer_to")
o("POST", f"/api/pets/{kp['id']}/transfer", {"to": "ana@example.com"})
b("POST", f"/api/transfers/{kp['id']}", {"accept": True})
_, pb = b("GET", "/api/pets"); assert any(x["code"] == kp["code"] for x in pb), "mismo QR"
_, mb = b("GET", "/api/messages"); assert any(x["text"].startswith("Me gustaría") for x in mb), "los avisos van con la ficha"
_, mo = o("GET", "/api/pets"); assert mo == []
c, _ = o("POST", f"/api/pets/{kp['id']}/transfer", {"to": "protectora"}, ok=False); assert c == 404
_, r = a("POST", f"/api/pets/{kp['id']}/transfer", {"to": "protectora"}); assert r["moved"]
_, mo = o("GET", "/api/pets"); assert mo[0]["name"] == "Kira"

# borrar la cuenta lo borra todo
_, ana = b("GET", "/api/me")
b("POST", "/api/pets", {"name": "Luna", "species": "gato"})
b("POST", "/api/account/delete", {"password": "contrasena2"})
_, pets = a("GET", "/api/admin/pets"); assert sorted(x["name"] for x in pets) == ["Kira", "Toby"]
_, ka = a("GET", "/api/admin/parks"); assert ka and not ka[0]["author"], "el pipicán se queda, pero ya sin su nombre"
# protección CSRF
req = urllib.request.Request(BASE + "/api/logout", method="POST")
try:
    urllib.request.urlopen(req); raise AssertionError("sin cabecera debería fallar")
except urllib.error.HTTPError as e:
    assert e.code == 403
# pipicanes repetidos: el mismo sitio no se apunta dos veces, salvo que diga que es distinto (y lo revisa el admin)
a("POST", "/api/parks", {"name": "Pipicán de prueba A", "lat": 39.5, "lng": -0.4})
_, dup = a("POST", "/api/parks/check", {"lat": 39.50001, "lng": -0.40001, "name": "Otro"}); assert dup and dup[0]["dist"] < 50
c, _ = a("POST", "/api/parks", {"name": "Otro", "lat": 39.50001, "lng": -0.40001}, ok=False); assert c == 409, "no deja duplicar"
_, k2 = a("POST", "/api/parks", {"name": "Otro", "lat": 39.50001, "lng": -0.40001, "distinct": True}); assert k2["pending"], "el distinto lo revisa el admin"
_, ks = a("GET", "/api/admin/parks"); assert any(k["id"] == k2["id"] and k["dupe_of"] for k in ks)
print("Todo bien ✔")
