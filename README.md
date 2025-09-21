# Miaubot

Herramienta para organizar y reportar archivos multimedia. Procesa nombres de archivo, extrae metadatos, genera reportes y puede subir contenidos a la nube mediante Rclone.

## Características

- Detección y parseo de series y películas a partir del nombre de archivo
- Soporte para episodios múltiples (por ejemplo: S02E02-E03 y 028-029)
- Extracción de metadatos técnicos con MediaInfo
- Generación de reportes y envío opcional a Telegram
- Subida a almacenamiento en la nube usando Rclone
- Integración opcional con FileBot

## Ejemplo de uso

```bash
uv run main.py -i /ruta/a/Series --upload --rc-config ./rclone.conf --rc-args="--fast-list" --rc-remote myRemote --dry-run
```

### Comando detallado

```bash
miaubot -i \
"/storage/data/media/shows/Anime Ongoing/2025/summer/Captivated, by You (2025) (2025) [tvdbid-455605]/Season 01/Captivated, by You (2025) (2025) - S01E05 - 005 - [1080p CR WEB-DL] [8bit] [8.2 Mbps] [AVC] [AAC 2.0] [ja] [es-419, en] - Erai-raws.mkv" \
--remote-base gdrive:Anime \
--rc-config /home/example/.config/rclone/rclone.conf \
--rc-upload-to gdrive:Anime \
--rc-args="--drive-upload-cutoff=1000T --drive-chunk-size=256M"
```

Descripción breve de las opciones:

- `-i`: ruta de entrada; procesa el archivo indicado en modo archivo único.
- `--remote-base`: base remota para construir la ruta remota (alias:ruta en Rclone).
- `--rc-config`: archivo de configuración de Rclone a utilizar.
- `--rc-upload-to`: remoto de destino para la subida.
- `--rc-args`: argumentos adicionales pasados a Rclone durante la subida.

---

## Requisitos

Antes de ejecutar el proyecto, asegúrate de tener los siguientes requisitos instalados o configurados:

- **[Python 3.12 o superior](https://www.python.org/)**: El script es compatible con Python 3.12 o versiones más recientes.
- **Una clave válida de [TMDb API](https://www.themoviedb.org/settings/api)**: Necesaria para obtener los pósters de series y películas.

### Herramientas opcionales

Las siguientes herramientas son opcionales, pero mejoran la funcionalidad del proyecto:

- **[FileBot](https://www.filebot.net/)**: Útil para automatizar el renombrado y la organización de archivos multimedia en un formato estructurado.
- **[Rclone](https://rclone.org/)**: Útil para subir tus archivos multimedia a servicios de almacenamiento en la nube.

---

## Formato de salida (FileBot)

La salida final (ruta y nombre de archivo) la determina el preset de FileBot. A continuación se describe el patrón de salida según los scripts incluidos en `scripts/filebot/`.

### Series (`tv-shows.local.groovy`)

Estructura de carpetas y nombre de archivo:

```plaintext
/storage/data/media/shows/{categoría}/{año-o-temporada-opcional/}{Serie (Año)} [tvdbid-{tvdbid}]/Season {SS}/
{Serie (Año)} - S{SS}E{EE[-E..]}{ - AAA[-BBB]} - [Resolución Origen]{ [HDR] } [Bits] [Mbps] [VideoCodec] [AudioCodec Canales] [Audios] [Subs]{ - Grupo}.ext
```

Notas sobre los componentes relevantes del nombre:

- `E{EE[-E..]}`: maneja multi-episodio (por ejemplo, `E02-E03`).
- `AAA[-BBB]`: números absolutos de episodio si están disponibles (por ejemplo, `028-029`).
- `Resolución Origen`: combinación de `vf` y el origen detectado (p. ej., `1080p CR WEB-DL`).
- `VideoCodec`: normalizado (x264 → AVC, x265 → HEVC).
- `Audios` y `Subs`: idiomas detectados, separados por comas.
- `Grupo`: grupo de release cuando puede inferirse del nombre original.

### Películas (`movies.local.groovy`)

Estructura de carpetas y nombre de archivo:

```plaintext
/storage/data/media/movies/{New Releases|Movies}/
{Título} ({Año}) [tmdbid-{id}]/{Título} ({Año}) [tmdbid-{id}] - [Resolución Origen]{ [HDR] } [Bits] [Mbps] [VideoCodec] [AudioCodec Canales] [Audios] [Subs]{ - Grupo}.ext
```


## Plataformas soportadas

El script detecta automáticamente las siguientes plataformas basándose en el nombre del archivo:

- **Servicios de streaming**: CR, AMZN, NF, ATVP, MAX, VIX, DSNP, AO
- **Medios físicos**: BD (Blu-ray), DVD

Si no se detecta una plataforma, el script asignará un valor predeterminado de `PLATFORM`.

---

## Resolución de problemas

Si encuentras errores o problemas con el script, asegúrate de verificar:

1. Que los nombres de archivo sigan el formato especificado.
2. Que tengas configuradas las herramientas opcionales si deseas utilizar sus funciones avanzadas.
3. Que los parámetros de entrada sean correctos.

---

## Contribuciones

Si deseas contribuir, puedes enviar problemas (issues) o solicitudes de incorporación de cambios (pull requests) para mejorar este proyecto. Se agradecen las contribuciones que añadan soporte para más plataformas o mejoren las integraciones con la nube.

---

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo [LICENSE](./LICENSE) para más detalles.

## Sistema de build

### Compilación cruzada

El sistema soporta builds para múltiples arquitecturas usando Docker Buildx con emulación QEMU:

#### Arquitecturas soportadas

- `linux-amd64` (x86_64) - Nativo
- `linux-arm64` (aarch64) - Cross-compilation

#### Comandos de build

```bash
# Build para la arquitectura actual (AMD64)
make build
make build-linux-amd64

# Build para ARM64 (usando emulación)
make build-linux-arm64

# Build para todas las arquitecturas
./build.sh build
```