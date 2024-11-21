# Miaubot

Este proyecto (semi) automatiza el renombrado y la organización de archivos multimedia, genera reportes de subida y sube archivos a servicios de almacenamiento en la nube utilizando Rclone.

## Ejemplo de uso

```bash
uv run main.py -i /ruta/a/Series --upload --rc-config ./rclone.conf --rc-args="--fast-list" --rc-remote myRemote --dry-run
```

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

## Requisitos de formato de archivo

Para que el script funcione correctamente, los nombres de los archivos de entrada deben seguir un formato específico. A continuación se muestran ejemplos de formatos de entrada y salida.

### Ejemplos de entrada
Asegúrate de que los nombres de archivo incluyan información básica como título, resolución, plataforma y (para series) datos de temporada/episodio:

```plaintext
attack.on.titan.s01e01.1080p.cr.mkv
Attack.on.Titan.S01E02.1080p.dvd.mkv
YOUR.NAME.2016.1080p.bd.mkv
```

### Estructura de salida
El script organizará y renombrará los archivos en el siguiente formato:

```plaintext
Attack on Titan (2013)/
├── Season 01/
│   ├── Attack on Titan (2013) - S01E01 - [1080p] [CR] [tmdbid=12345].mkv
│   ├── Attack on Titan (2013) - S01E02 - [1080p] [DVD] [tmdbid=12345].mkv
Your Name (2016) - [1080p] [BD] [tmdbid=12345].mkv
```

---

## Preset de FileBot

Utiliza el siguiente preset en FileBot para asegurarte de que tus archivos sean renombrados correctamente:

```groovy
{
  // Convierte el nombre original a mayúsculas y busca la plataforma
  def platform = fn.toUpperCase().match(/(?:CR|AMZN|NF|ATVP|MAX|VIX|DSNP|AO|BD|DVD)/) ?: "PLATFORM";

  // Usa el TMDb ID si está disponible
  def tmdbId = any{"$tmdbid"}{"$id"};

  // Extrae la resolución o utiliza un valor predeterminado
  def resolution = vf ?: "1080p";

  if (episode != null) {
    // Series: Organiza en temporadas y renombra
    return "${ny}/Season ${episode.season.pad(2)}/${ny} - S${episode.season.pad(2)}E${episode.episode.pad(2)} - [${resolution}] [${platform}] [tmdbid=${tmdbId}]${'.'+ext}";
  } else if (movie != null) {
    // Películas: Renombra en un formato estructurado
    return "${ny} - [${resolution}] [${platform}] [tmdbid=${tmdbId}]${'.'+ext}";
  } else {
    return fn; // Mantén el nombre original si no se reconoce
  }
}
```

---

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