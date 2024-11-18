import os
import re
import shlex
import subprocess
import requests
from pymediainfo import MediaInfo
from dotenv import load_dotenv
import argparse

# Cargar variables de entorno desde .env.local o el entorno del contenedor
load_dotenv(dotenv_path=".env.local")

# Variables de entorno configurables
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = int(os.getenv("TG_CHAT_ID"))
TMDB_API_TOKEN = os.getenv("TMDB_API_TOKEN")

# Argumentos del programa
parser = argparse.ArgumentParser(description="Procesa archivos de video en una carpeta.")
parser.add_argument("-i", "--input", required=True, help="Carpeta para analizar los archivos")
parser.add_argument("--upload", action="store_true", help="Subir todos los archivos a la nube")
args = parser.parse_args()

# Directorio de entrada
folder_path = args.input.rstrip("/") + "/"

def search_files(folder_path):
    """Busca archivos .mkv en la carpeta especificada y los ordena alfabéticamente."""
    return sorted([f for f in os.listdir(folder_path) if f.endswith(".mkv")])

def get_data(file_name):
    """Extrae información del nombre del archivo usando una expresión regular."""
    pattern = r'^(.*?)\s*\((\d{4})\)\s*-\s*S(\d{2})E(\d{2})\s*-\s*\d+p\s*\[id=(\d+)\]\.(mkv|mp4|avi)$'
    match = re.match(pattern, file_name)
    return [match.group(1), match.group(2), match.group(3), match.group(4), match.group(5)] if match else []

def season_to_string(season):
    """Convierte un número de temporada en el formato 'Season xx'."""
    season_number = int(season.lstrip('0'))  # Elimina ceros iniciales
    return f"Season {season_number:02d}"

def new_name(filename):
    """Genera un nuevo nombre para el archivo basado en su nombre original."""
    pattern = r'^(.*?)\s*\(\d{4}\)\s*-\s*(.*?)\s*\[\w+=\d+\]\.(mkv|mp4|avi)$'
    match = re.match(pattern, filename)
    if match:
        title, remaining, extension = match.group(1), match.group(2), match.group(3)
        return f"{title} - {remaining}.{extension}"
    return filename

def get_media_info(file_path):
    """Obtiene información de video, audio y subtítulos de un archivo de medios."""
    media_info = MediaInfo.parse(file_path)
    video_info = []
    audio_info = []
    subtitle_info = []

    for track in media_info.tracks:
        if track.track_type == 'Video':
            codec = track.internet_media_type.split('/')[-1]
            quality = f"{track.height}p {codec}"
            if 7000000 <= track.bit_rate <= 8500000:
                quality = f"{track.height}p CR WEB-DL"
            video_info.append(quality)
        elif track.track_type == 'Audio':
            audio_info.append(f"{track.title} ({track.format.replace('E-AC-3', 'E-AC3')} {track.channel_s}.0)")
        elif track.track_type == 'Text':
            subtitle_info.append(f"{track.title} ({track.format.replace('UTF-8', 'SRT')})")

    return video_info, audio_info, subtitle_info

def get_poster(tmdbid, token=TMDB_API_TOKEN):
    """Obtiene la URL del póster desde TMDB API."""
    url = f"https://api.themoviedb.org/3/tv/{tmdbid}?api_key={token}"
    backdrop_path = requests.get(url).json().get('backdrop_path')
    return f"https://image.tmdb.org/t/p/original{backdrop_path}" if backdrop_path else None

def send_photo(chat_id, token, image_url, caption=""):
    """Envía una foto al chat de Telegram."""
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    data = {"chat_id": chat_id, "photo": image_url, "caption": caption, "parse_mode": "HTML"}
    return requests.post(url, data=data).json()

def send_report(chat_id, token, anime_name, year, season, episode, media_info, poster_url):
    """Envía un reporte detallado al chat de Telegram."""
    video_info, audio_info, subtitle_info = media_info
    message = (
        f"#miauporte <b>{anime_name} ({year}) - agregado S{season}E{episode}</b>\n\n"
        f"<b>Calidad:</b> {video_info[0]}\n"
        f"<b>Audio:</b> {', '.join(audio_info)}\n"
        f"<b>Subtítulos:</b> {', '.join(subtitle_info)}\n\n"
        f"<b>Ruta:</b> Anime/{anime_name} ({year})"
    )
    send_photo(chat_id, token, poster_url, message)

def rename_file(file_path):
    """Renombra un archivo según el nuevo formato."""
    new_file_path = os.path.join(os.path.dirname(file_path), new_name(os.path.basename(file_path)))
    os.rename(file_path, new_file_path)
    return new_file_path

def upload_files(folder_path, remote_name, remote_path, include_all=False):
    """Sube archivos a la nube usando rclone."""
    command = (
        f'rclone move "{folder_path}" "{remote_name}:{remote_path}" -P --drive-chunk-size 128M --config transfers/rclone.conf '
        f'--include "**.mkv" --onedrive-chunk-size 100M --onedrive-no-versions'
    ) if include_all else (
        f'rclone copy "{folder_path}" "{remote_name}:{remote_path}" -P --drive-chunk-size 128M --config transfers/rclone.conf'
    )
    subprocess.run(shlex.split(command), check=True)

def main():
    """Punto de entrada del script."""
    files = search_files(folder_path)
    for file in files:
        data = get_data(file)
        if data:
            anime_name, year, season, episode, file_id = data
            season_str = season_to_string(season)
            file_path = os.path.join(folder_path, file)
            media_info = get_media_info(file_path)
            poster_url = get_poster(file_id, TMDB_API_TOKEN)
            new_file_path = rename_file(file_path)
            upload_files(new_file_path, "fc4", f"Anime/{anime_name} ({year})/{season_str}/", include_all=False)
            send_report(TG_CHAT_ID, TG_BOT_TOKEN, anime_name, year, season, episode, media_info, poster_url)
            print(f"Reporte enviado: {anime_name} {season_str}E{episode}")

    if args.upload:
        print("Subiendo todos los archivos a la nube...")
        upload_files(folder_path, "crypt_series", "Animes en emision/", include_all=True)

if __name__ == "__main__":
    main()
