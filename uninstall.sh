#!/usr/bin/env bash
# Desinstala MascotasPanel: para y borra el contenedor y la imagen de Docker y, si quieres, los
# datos (personas, mascotas y fotos) y la carpeta del programa.
# Antes de borrar nada pregunta, y ofrece hacer una copia de seguridad de los datos.
#
# Uso:  bash /mnt/datos/apps/mascotas-panel/uninstall.sh
set -uo pipefail

APP="MascotasPanel"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
CONTAINER="mascotaspanel"
IMAGES="mascotaspanel:latest ghcr.io/iaonlineapps/mascotaspanel"
BACKUP="mascotaspanel"
DATA_DIR="/mnt/datos/mascotas-panel"
# si hay .env con DATA_DIR (versión pública), manda ese
if [ -f "$APP_DIR/.env" ]; then
  d=$(grep -E '^DATA_DIR=' "$APP_DIR/.env" | tail -1 | cut -d= -f2- | tr -d '"'"'"' ')
  [ -n "${d:-}" ] && DATA_DIR="$d"
fi
case "$DATA_DIR" in /*) ;; *) DATA_DIR="$APP_DIR/${DATA_DIR#./}" ;; esac
STAMP=$(date +%Y%m%d-%H%M)

ask() {  # ask "pregunta" -> 0 si contesta s/si
  local r; read -r -p "$1 [s/N] " r || return 1
  [[ "$r" =~ ^([sS]|[sS][iíIÍ])$ ]]
}

echo "=============================================="
echo "  Desinstalar $APP"
echo "=============================================="
echo "  Programa: $APP_DIR"
echo "  Datos:    $DATA_DIR"
echo
read -r -p "Para seguir escribe DESINSTALAR (en mayúsculas): " ok
[ "$ok" = "DESINSTALAR" ] || { echo "Cancelado. No se ha tocado nada."; exit 0; }

# 1. copia de seguridad
if [ -d "$DATA_DIR" ] && [ -n "$(ls -A "$DATA_DIR" 2>/dev/null)" ]; then
  SIZE=$(sudo du -sh "$DATA_DIR" 2>/dev/null | cut -f1)
  # la copia va junto a los datos (mismo disco); si están dentro del programa, a tu carpeta personal
  case "$DATA_DIR" in "$APP_DIR"/*) BKDIR="$HOME" ;; *) BKDIR="$(dirname "$DATA_DIR")" ;; esac
  if ask "¿Hago una copia de seguridad de los datos antes (ocupan ${SIZE:-?}; recomendado)?"; then
    BK="$BKDIR/${BACKUP:-qrpanel}-copia-$STAMP.tar.gz"
    echo "  Haciendo la copia en $BK (puede tardar si hay muchos datos)…"
    if sudo tar -czf "$BK" -C "$(dirname "$DATA_DIR")" "$(basename "$DATA_DIR")"; then
      sudo chown "$(id -u):$(id -g)" "$BK"
      echo "  Copia guardada en: $BK"
    else
      echo "  No se pudo hacer la copia. Paro aquí para no perder nada."; exit 1
    fi
  fi
fi

# 2. contenedor e imagen
echo "Parando y borrando el contenedor…"
if [ -f "$APP_DIR/docker-compose.yaml" ] || [ -f "$APP_DIR/docker-compose.yml" ]; then
  (cd "$APP_DIR" && docker compose down --remove-orphans) >/dev/null 2>&1 || true
fi
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
echo "Borrando la imagen de Docker…"
for img in $IMAGES; do
  docker images --format '{{.Repository}}:{{.Tag}}' | grep -E "^${img%%:*}(:|$)" | xargs -r docker rmi -f >/dev/null 2>&1 || true
done
docker image prune -f >/dev/null 2>&1 || true
echo "  Hecho: $APP ya no está funcionando."

# 3. datos
if [ -d "$DATA_DIR" ]; then
  echo
  echo "Los datos ($DATA_DIR) tienen las personas registradas, sus mascotas y sus fotos."
  if ask "¿Borrar también los datos? Esto NO se puede deshacer."; then
    read -r -p "Escribe BORRAR para confirmarlo: " ok2
    if [ "$ok2" = "BORRAR" ]; then sudo rm -rf "$DATA_DIR" && echo "  Datos borrados."
    else echo "  No se han borrado los datos."; fi
  else
    # si los datos están dentro de la carpeta del programa, se sacan antes de borrarla
    case "$DATA_DIR" in "$APP_DIR"/*)
      KEEP="$HOME/${BACKUP:-qrpanel}-datos-$STAMP"
      sudo mv "$DATA_DIR" "$KEEP" && sudo chown -R "$(id -u):$(id -g)" "$KEEP" && DATA_DIR="$KEEP"
      echo "  He sacado los datos a: $KEEP (para usarlos otra vez, pon esa carpeta en DATA_DIR del .env)" ;;
    *) echo "  Los datos se quedan en: $DATA_DIR (si vuelves a instalar, se usan otra vez)." ;;
    esac
  fi
fi

# 4. carpeta del programa
echo
if ask "¿Borrar también la carpeta del programa ($APP_DIR)?"; then
  cd / && sudo rm -rf "$APP_DIR" && echo "  Carpeta del programa borrada."
fi

echo
echo "$APP desinstalado."
echo "Si usabas un proxy (Pangolin, Nginx Proxy Manager, Cloudflare Tunnel), quita también allí"
echo "el recurso de $APP. La app de Android se quita como cualquier otra, desde el móvil."
