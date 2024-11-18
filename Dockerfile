# Imagen base para Python y UV
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS runtime

# Instalar rclone, MediaInfo y dependencias necesarias
RUN apk add --no-cache \
    rclone \
    mediainfo \
    boost-filesystem \
    boost-regex \
    boost-system \
    curl \
    bash \
    shadow  # Necesario para usermod y manejo de usuarios

# Crear directorio para la aplicación
WORKDIR /app

# Copiar el proyecto al contenedor
COPY . /app

# Sincronizar el entorno con UV
RUN uv sync --frozen

# Configurar el PATH para incluir el entorno virtual creado por UV
ENV PATH="/app/.venv/bin:$PATH"

# Variables para usuario y grupo dinámico
ENV UID=1000
ENV GID=1000

# Crear usuario y grupo dinámicamente y ajustar permisos
RUN set -eux; \
    addgroup -g "${GID}" appgroup || true; \
    adduser -u "${UID}" -G appgroup -h /app -s /bin/bash -D appuser || true; \
    chown -R "${UID}:${GID}" /app

# Cambiar al usuario creado
USER appuser

# Usar ENTRYPOINT para manejar correctamente los argumentos
ENTRYPOINT ["uv", "run", "main.py"]
