#!/usr/bin/env bash
# Instala o actualiza MascotasPanel.
# Uso: ./install.sh   (desde la carpeta donde descargaste MascotasPanel)
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker no está instalado. Instálalo con: curl -fsSL https://get.docker.com | sh" >&2
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  sed -i "s/^PUID=.*/PUID=$(id -u)/; s/^PGID=.*/PGID=$(id -g)/" .env
  # DATA_DIR=/ruta ./install.sh  → guarda los datos en esa carpeta (por ejemplo un disco externo)
  if [ -n "${DATA_DIR:-}" ]; then sed -i "s#^DATA_DIR=.*#DATA_DIR=${DATA_DIR}#" .env; fi
  echo "Creado el archivo .env con la configuración por defecto (puedes cambiarla luego con: nano .env)"
fi
unset DATA_DIR; set -a; . ./.env; set +a
DATA_DIR="${DATA_DIR:-./data}"

PARENT=$(dirname "$DATA_DIR")
if [ ! -d "$PARENT" ]; then
  echo "ERROR: la carpeta $PARENT no existe. ¿Está montado el disco? Revisa DATA_DIR en .env" >&2
  exit 1
fi

sudo mkdir -p "$DATA_DIR"/{config,fotos}
sudo chown -R "${PUID:-1000}:${PGID:-1000}" "$DATA_DIR"

docker compose up -d --build
docker image prune -f >/dev/null 2>&1 || true

IP=$(hostname -I | awk '{print $1}')
echo
echo "MascotasPanel funcionando en:  http://${IP}:${PORT:-8093}/panel"
echo "Datos guardados en:      ${DATA_DIR}"
