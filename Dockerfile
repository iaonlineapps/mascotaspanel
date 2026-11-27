FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MASCOTASPANEL_DATA=/data
# Versión que se ve en la web; la imagen publicada la recibe de la etiqueta (v1.2.3)
ARG MASCOTASPANEL_VERSION=
ENV MASCOTASPANEL_VERSION=${MASCOTASPANEL_VERSION}
WORKDIR /app
COPY requirements.txt .
# Todas las dependencias son Python puro: funciona igual en PC (amd64),
# Raspberry Pi 4/5 (arm64) y Raspberry Pi 3 de 32 bits (arm/v7) sin compilar nada.
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY entrypoint.sh /entrypoint.sh
# el contenedor corre como usuario normal: el código tiene que ser legible
# aunque se haya copiado con permisos restrictivos (por ejemplo desde Windows)
RUN chmod -R a+rX /app && chmod 755 /entrypoint.sh

EXPOSE 8093
HEALTHCHECK --interval=60s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8093/salud')" || exit 1
ENTRYPOINT ["/entrypoint.sh"]
# Un solo proceso: suficiente para la Pi y lo más seguro con SQLite
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8093", "--proxy-headers", "--forwarded-allow-ips", "*", "--no-access-log"]
