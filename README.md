# MascotasPanel

<p align="center"><img src="docs/logo.png" width="120" alt="Logo de MascotasPanel"></p>

**Registro libre de mascotas, en tu propio servidor.** Cada persona se apunta y guarda las fichas de
sus mascotas con foto. Cada mascota tiene su **placa con QR** para el collar y, si se pierde, un
**cartel «Se busca»** listo para imprimir en un minuto. Ligera (unos 50 MB de RAM) y pensada para
Raspberry Pi. En español y en inglés.

| Web | App (solo Android) |
|---|---|
| **1.0.15** ([novedades](app/NOVEDADES.md)) | **1.1** ([descargar la APK, solo Android](https://github.com/iaonlineapps/mascotaspanel/raw/main/android/dist/MascotasPanel.apk)) |

> 📱 **La app es solo para Android** (móviles y tablets Android). En iPhone o iPad no se puede instalar: usa la web y añádela a la pantalla de inicio (Compartir → «Añadir a pantalla de inicio»).

![Ficha de una mascota con su cartel «Se busca» y su QR](docs/capturas/ficha.png)

## Qué incluye

- **Registro con lo mínimo:** solo tu nombre (sin apellidos ni DNI), usuario, correo y, si quieres, un
  teléfono y una zona aproximada. Casilla de consentimiento (RGPD).
- **Pantalla de Inicio** al entrar: los **perros y gatos que se están buscando** (con foto, zona y desde cuándo),
  tus mascotas, tus avisos sin leer y los animales en adopción. El administrador entra directo a su **panel de control**.
- **Fichas de mascotas:** foto (la encuadras al subirla), animal (perro, gato, conejo, hurón, pájaro, loro,
  roedores, reptiles, peces, caballos, cerdos, cabras…), raza, color y señas, sexo, tamaño, edad,
  microchip, cómo es, salud y una **segunda persona de contacto** opcional.
- **Registro público** de todas las mascotas (foto, nombre y raza) y **lista de perdidas con mapa**.
- **Placa con QR:** al escanearla se abre su ficha. Quien la encuentra te manda un **aviso** (con su
  teléfono y dónde está, si quiere) y te llega a la pestaña **«Avisos»**, sin ver tus datos.
- **¿Se ha perdido?** Márcala como perdida, señala en el mapa dónde se perdió (aproximado, unos 100 m) y
  sale en la lista pública, con botón para abrirlo en Google Maps.
- **Cartel «Se busca»** con «SE BUSCA · PERDIDO/PERDIDA» arriba, en **PDF A4** (con tiras recortables) o
  en imagen para redes, con foto, datos, recompensa y QR.
- **Compartir el aviso** en Facebook, WhatsApp, Telegram, X o por correo, con el **anuncio ya escrito** y un botón
  «Copiar texto». El enlace se ve con su foto. Para **Instagram** (4:5) y **TikTok** (vertical), una imagen con su foto y el QR.
  Cualquiera puede compartirlo desde la ficha pública.
- **Pasar una ficha a otra cuenta** sin volver a escribir nada: se va con su foto, su QR y sus avisos.
- **Recuperar la cuenta** con un **código de recuperación** (cópialo o mándatelo por WhatsApp, Telegram o
  correo). Con él recuperas el usuario y pones una contraseña nueva, aunque hayas olvidado los dos.
- **Tus datos son tuyos:** descárgalos o bórralo todo (cuenta, mascotas y fotos) con un botón.
- **Asociaciones y animales en adopción:** las asociaciones y protectoras se registran como tales, ponen su
  logo y cómo contactar, y publican sus animales en adopción con un mensaje («¿Me adoptas?»). Salen en la
  sección **«Adopción»** y en un carrusel en el inicio. El administrador verifica cada asociación antes.
- **Pipicanes («Busca tu pipicán»):** un mapa público que hace la gente entre todos. Apuntas un pipicán
  con una foto y la ubicación sale sola de la foto (o pegando el enlace de Google Maps, con «Estoy aquí», o
  tocando el mapa). Los nuevos salen cuando el administrador los aprueba, y quien lo apuntó puede editarlo.
  El administrador puede importar los que ya están en OpenStreetMap. Cada uno tiene
  su botón **«Cómo llegar»** con Google Maps. No sale quién lo ha apuntado y a las fotos se les quita la
  ubicación y los datos de la cámara.
- **Administrador:** la primera cuenta que se crea. Tiene su propia pestaña con un **panel de control**
  y su propio **bot de Telegram** (avisos con foto y botones para aprobar). Mira abajo qué puede hacer y qué no.
- **App solo para Android** (móviles y tablets Android; en iPhone o iPad se usa la web y se puede guardar en la pantalla de inicio): una APK firmada que abre tu servidor, avisa cuando hay versión nueva y te deja
  elegir el servidor. Se descarga [aquí](https://github.com/iaonlineapps/mascotaspanel/raw/main/android/dist/MascotasPanel.apk).
- **Apariencia:** claro u oscuro, 8 colores y fondo con patitas y huesos. **Español de España e inglés.**
- Se ve bien en **móvil, tablet y ordenador**. Menú de cuenta con ajustes y cambio rápido de usuario.

| Lista pública de mascotas perdidas | Lo que ve quien escanea el QR |
|---|---|
| ![Inicio](docs/capturas/inicio.png) | <img src="docs/capturas/qr-movil.png" width="300" alt="Ficha del QR en el móvil"> |

| Animales en adopción | Pipicanes |
|---|---|
| ![Adopción](docs/capturas/adopcion.png) | ![Mapa de pipicanes](docs/capturas/pipicanes.png) |

| Panel de control del administrador | Ficha de un animal en adopción (móvil) |
|---|---|
| ![Panel de control](docs/capturas/panel-admin.png) | <img src="docs/capturas/adopcion-movil.png" width="300" alt="Ficha en adopción"> |

### Más capturas

*Las capturas usan datos inventados.*

| Inicio de cada persona: los que se buscan | Inicio en la app de Android |
|---|---|
| ![Inicio de la persona](docs/capturas/inicio-usuario.png) | <img src="docs/capturas/app-inicio.png" width="300" alt="Inicio en la app"> |

| Mis mascotas | Menú de la cuenta |
|---|---|
| ![Mis mascotas](docs/capturas/mis-mascotas.png) | ![Menú de la cuenta](docs/capturas/menu-cuenta.png) |

| Ficha de una mascota | Cartel «Se busca» |
|---|---|
| ![Editar ficha](docs/capturas/ficha-editar.png) | ![Cartel](docs/capturas/cartel.png) |

| Avisos | Mi cuenta |
|---|---|
| ![Avisos](docs/capturas/avisos.png) | ![Mi cuenta](docs/capturas/mi-cuenta.png) |

| Tablet | Panel del administrador en el móvil | Ficha perdida en el móvil |
|---|---|---|
| <img src="docs/capturas/tablet-inicio.png" width="300" alt="Inicio en tablet"> | <img src="docs/capturas/panel-movil.png" width="260" alt="Panel en el móvil"> | <img src="docs/capturas/ficha-perdida-movil.png" width="260" alt="Ficha perdida"> |

| Compartir desde la ficha pública (también TikTok e Instagram) | Imagen para TikTok |
|---|---|
| <img src="docs/capturas/compartir-publica.png" width="300" alt="Compartir"> | <img src="docs/capturas/cartel-tiktok.jpg" width="270" alt="Imagen para TikTok"> |

| Pasar una ficha a otra cuenta y compartir el aviso |
|---|
| ![Pasar ficha](docs/capturas/pasar-ficha.png) |

| Política de privacidad |
|---|
| ![Privacidad](docs/capturas/privacidad.png) |

## Administrador y cuentas normales

**La primera persona que se registra es la administradora.** Las demás cuentas son normales. Los ajustes
del administrador están **aparte**, en la pestaña **«Administración»**, que solo ve él. Los ajustes de
**«Mi cuenta»** son los mismos para todos y solo cambian tu propia cuenta.

| Qué | Cuenta normal | Administrador |
|---|---|---|
| Sus mascotas: fichas, fotos, placa QR, cartel «Se busca», marcar como perdida | ✔ | ✔ |
| Avisos de quien encuentra **sus** mascotas | ✔ | ✔ |
| Apuntar pipicanes y borrar los suyos | ✔ | ✔ |
| Si es una **asociación**: su perfil (logo, contacto) y poner animales en adopción, cuando esté verificada | ✔ | ✔ |
| Mi cuenta: nombre, correo, teléfono, contraseña, apariencia, idioma, descargar o borrar sus datos | ✔ | ✔ |
| **Panel de control:** total de fichas, cuentas, perdidas y pipicanes, gráfica de altas, últimas fichas y actividad («se ha registrado Hans…») | ✖ | ✔ |
| Ver, editar, ocultar o borrar **cualquier** ficha | ✖ | ✔ |
| Ver todas las cuentas, bloquearlas o borrarlas, ponerles una contraseña nueva, hacerlas administradoras | ✖ | ✔ |
| Ocultar o borrar cualquier pipicán, ver quién lo apuntó e importar los de OpenStreetMap | ✖ | ✔ |
| **Verificar asociaciones** (hasta entonces no publican animales en adopción) | ✖ | ✔ |
| **Aprobar pipicanes** (hasta entonces no salen en el mapa) tras verlos en su ficha con foto, mapa y Street View; editar o borrar cualquiera | Solo los suyos | ✔ |
| Descargar el registro completo (Excel/CSV) | ✖ | ✔ |
| Ajustes del servidor: dirección pública, registro abierto o cerrado, avisos por Telegram, **responsable de los datos** (sale en la privacidad y el aviso legal) | ✖ | ✔ |

### Bot de Telegram (opcional)

Tu propio bot te avisa de todo con fotos (altas, mascotas perdidas y encontradas, asociaciones con su logo,
pipicanes), te deja **aprobar pipicanes y verificar asociaciones con un botón** y te manda un **resumen cada
noche**. Se crea con @BotFather y se conecta con un toque desde **Administración**.

**Guía paso a paso, con capturas y un prompt para pedírselo a una IA: [docs/BOT-TELEGRAM.md](docs/BOT-TELEGRAM.md)**

<p align="center"><img src="docs/capturas/bot-telegram.png" width="300" alt="Avisos del bot en Telegram (datos inventados)"></p>

### Compartir el aviso

| Anuncio ya escrito y botones para compartir | Imagen para Instagram |
|---|---|
| ![Compartir el aviso](docs/capturas/compartir.png) | ![Cartel 4:5 para Instagram](docs/capturas/cartel-instagram.jpg) |

## App para Android (solo Android)

> La app es **solo para Android**. En iPhone o iPad usa la web: en Safari, botón Compartir → «Añadir a pantalla de inicio».

Descarga la APK desde [aquí](https://github.com/iaonlineapps/mascotaspanel/raw/main/android/dist/MascotasPanel.apk) en el
móvil e instálala (Android te pedirá permiso para instalar apps de fuera de la tienda). La primera vez
escribe la dirección de tu servidor (por ejemplo `http://192.168.1.x:8093` o
`https://mascotas.tudominio.com`). Puedes cambiarla en el menú de la app. Al abrirla te avisa si hay
una versión nueva y te enseña sus novedades. Usa la cámara para las fotos y la ubicación para el mapa
solo cuando tú lo pides.

## Instalar (Raspberry Pi o cualquier Linux con Docker)

Necesitas Docker con el plugin Compose (`curl -fsSL https://get.docker.com | sh`).

```bash
git clone https://github.com/iaonlineapps/mascotaspanel.git ~/mascotaspanel
cd ~/mascotaspanel
./install.sh
```

Se abre en `http://IP-DE-TU-PI:8093/` (el panel en `/panel`). **La primera persona que se registra es
la administradora.** Los ajustes están en `.env` (`nano .env` y otra vez `./install.sh`):
carpeta de datos, puerto, registro abierto o cerrado, y tu nombre y correo para el aviso de privacidad.

Para guardar los datos en un disco externo desde el principio:
`DATA_DIR=/mnt/disco/mascotaspanel ./install.sh`

### Actualizar

```bash
curl -fsSL https://raw.githubusercontent.com/iaonlineapps/mascotaspanel/main/update.sh | bash
```

No toca tus datos. Para desinstalar: `bash ~/mascotaspanel/uninstall.sh` (pregunta antes de borrar).

### Publicarla en Internet

Con Pangolin, Nginx Proxy Manager, Caddy o Cloudflare Tunnel: crea un recurso HTTP que apunte a la IP
de la Raspberry (por ejemplo `192.168.1.x`) y al puerto `8093`, **sin la autenticación del proxy** (la
web es pública y el panel ya tiene su usuario y contraseña). Luego pon la dirección
(`https://mascotas.tudominio.com`) en **Administración → Dirección pública**: es la que llevan los QR.

## Privacidad

**Los datos de las personas están ocultos por defecto.** Nadie que no sea el administrador ve tu nombre,
tu correo, tu teléfono, tu zona ni el número de microchip de tu mascota.

| Dato | Quién lo ve |
|---|---|
| Foto, nombre, raza y señas de la mascota | Todo el mundo, en el registro público (puedes quitarla) y en su ficha del QR |
| Tu nombre, correo y zona | Solo tú y el administrador |
| Tu teléfono y el de la segunda persona | Nadie, **salvo que des tu consentimiento** en la ficha. Entonces se ven en su ficha y en el cartel «Se busca» **solo mientras esté perdida** |
| Número de microchip | Solo se guarda **si das tu consentimiento**. No se enseña nunca. Si lo permites, quien tenga el número completo (un veterinario, por ejemplo) puede encontrar la ficha |
| Dónde se perdió | Todo el mundo mientras esté perdida, redondeado a unos 100 m |
| Avisos de quien la encuentra | Solo tú. Se borran solos a los 90 días |
| Pipicanes | Todo el mundo ve el sitio, la foto y la nota. **Quién lo apuntó** solo lo ve el administrador |
| Segunda persona de contacto | Solo se puede poner si **esa persona te ha dado permiso** (casilla obligatoria) |
| Asociaciones | Su nombre, logo y lo que cuenten de sí mismas es público. Teléfono, WhatsApp, Telegram y correo, **solo lo que ellas marquen** |

Sin teléfono a la vista, quien encuentra a la mascota escanea el QR y te manda un aviso desde un
formulario. Sin cookies de terceros, sin analítica y sin publicidad: solo una cookie técnica para la
sesión. Lo único de fuera son las imágenes del mapa (OpenStreetMap). Todo se guarda en tu servidor
(SQLite y una carpeta de fotos).

---

## ¿Es legal? (RGPD y LOPDGDD)

MascotasPanel está pensado para cumplir el RGPD (Reglamento UE 2016/679) y la Ley Orgánica 3/2018 (LOPDGDD).
Esto **no es asesoramiento jurídico**: si lo usas para mucha gente o para una asociación, consúltalo con alguien
que sepa de protección de datos.

- **Quien instala el servidor es el responsable de los datos.** Como la web es pública y cualquiera puede
  registrarse, no cuenta como «uso doméstico»: hay que cumplir la ley. Pon tu nombre y un correo en
  **Administración → Responsable de los datos**; salen en la política de privacidad y en el aviso legal.
- **Datos mínimos:** solo el nombre (sin apellidos ni DNI) y un correo. Lo demás es opcional y cada dato
  opcional tiene su propia casilla de consentimiento.
- **El microchip** está unido al dueño en los registros oficiales, así que se trata como dato personal: solo
  se guarda con consentimiento y no se enseña nunca.
- **Edad mínima: 14 años** (art. 7 LOPDGDD). Al registrarse se confirma con una casilla.
- **Información y derechos:** al registrarse se enseña la información básica (responsable, finalidad, base
  legal, derechos). Cada persona puede **descargar** sus datos (portabilidad) y **borrarlo todo** (supresión)
  desde «Mi cuenta», y reclamar ante la [AEPD](https://www.aepd.es).
- **Datos de otras personas** (segunda persona de contacto): solo con su permiso.
- **Fotos:** se les quita la ubicación y los datos de la cámara. Las normas piden no subir fotos en las que se
  reconozca a personas.
- **Animales en adopción:** solo asociaciones verificadas. **No se permite vender animales.**
- **Sin cookies de terceros ni analítica**, así que no hace falta banner de cookies.

## English

**A free pet registry on your own server.** People sign up and keep profiles of their pets with a photo.
Each pet gets a **QR tag** for its collar and, if it gets lost, a printable **"Missing" poster**. The
public home page lists all registered pets and the lost ones on a map. Account recovery works with a
one-time **recovery code**. Spanish (Spain) and English, phone/tablet/desktop, light and dark mode.

**Privacy: people's details are hidden by default.** Nobody but the administrator sees an owner's name,
email, phone, area or the pet's microchip number. Finders scan the QR and send the owner a notice through
a form. The owner's phone (and an optional second contact) is shown on the pet's page and on the
"Missing" poster **only if the owner gives explicit consent, and only while the pet is lost**. The
microchip number is stored only with consent and is never displayed.

**Dog parks ("Find your dog park"):** a public map that everyone builds together. Add a dog park with a
photo and its location is read from the photo (or use "I'm here", or tap the map). Each one has a
**"Directions"** button for Google Maps. It never shows who added it, and location and camera data are
removed from the photos.

**Administrator vs normal accounts:** the first account created is the administrator. Its settings live
**apart**, in the **"Administration"** tab that only it can see; "My account" settings are the same for
everyone and only affect your own account.

| What | Normal account | Administrator |
|---|---|---|
| Own pets: profiles, photos, QR tag, "Missing" poster, mark as lost | ✔ | ✔ |
| Notices from people who find **their** pets | ✔ | ✔ |
| Add dog parks and delete their own | ✔ | ✔ |
| My account: name, email, phone, password, appearance, language, download or delete their data | ✔ | ✔ |
| **Dashboard:** total profiles, accounts, lost pets and dog parks, sign-up chart, latest profiles and activity | ✖ | ✔ |
| See, edit, hide or delete **any** profile | ✖ | ✔ |
| **Verify associations** (until then they cannot publish animals for adoption) | ✖ | ✔ |
| See all accounts, block or delete them, reset passwords, make them administrators | ✖ | ✔ |
| Hide or delete any dog park and see who added it | ✖ | ✔ |
| Export the full registry (CSV) | ✖ | ✔ |
| Server settings: public address, open or closed sign-ups, Telegram notifications | ✖ | ✔ |

**Associations and adoption:** associations and shelters sign up as such, add their logo and the contact
details they choose to show, and publish animals up for adoption with a message ("Will you adopt me?"). They
appear in the **"Adoption"** section and in a carousel on the home page. The administrator verifies each
association first. Dog parks can also be added by pasting a Google Maps link, and the administrator can import
the ones already on OpenStreetMap.

**Is it legal? (GDPR):** whoever installs the server is the data controller and enters their name and email in
Administration (shown in the privacy policy and legal notice). Minimum data, one consent box per optional item,
minimum age 14, the microchip treated as personal data, data download and deletion from "My account", and no
third-party cookies. This is not legal advice.

**Share the notice:** when a pet is lost (or up for adoption) the owner gets the post already written, with a
"Copy text" button and buttons for Facebook, WhatsApp, Telegram, X and email; the link shows its photo. For
Instagram there is a 4:5 image with the photo and the QR. New dog parks wait for the administrator's approval,
and whoever added one can edit it.

**Telegram bot (optional):** notices with photos, buttons to approve dog parks and verify associations, and a
nightly summary. Create it with **@BotFather** and connect it with one tap from **Administration**. Step-by-step
guide with screenshots and an AI prompt: [docs/BOT-TELEGRAM.md](docs/BOT-TELEGRAM.md#telegram-bot-for-mascotaspanel).

**Android app (Android only; on iPhone or iPad use the website and add it to the home screen):** download the signed APK from
[here](https://github.com/iaonlineapps/mascotaspanel/raw/main/android/dist/MascotasPanel.apk), install it and enter your
server's address. It warns you about new versions and lets you change the server.

Install: `git clone https://github.com/iaonlineapps/mascotaspanel.git && cd mascotaspanel && ./install.sh`,
then open `http://YOUR-PI-IP:8093/`. The first person to sign up becomes the administrator.

## Licencia / License

Gratis para uso personal y no comercial: [PolyForm Noncommercial 1.0.0](LICENSE.md). No se puede vender.
Free for personal, non-commercial use. It may not be sold.

Hecho por [IA Online Apps](https://github.com/iaonlineapps) con ayuda de inteligencia artificial (Claude).
Los QR se generan con [segno](https://github.com/heuer/segno) (BSD).
Los mapas usan [Leaflet](https://leafletjs.com) (BSD-2) y las imágenes y datos de pipicanes importados de [OpenStreetMap](https://www.openstreetmap.org/copyright) (ODbL).
