import os
import re
import requests
from pymediainfo import MediaInfo
from dotenv import load_dotenv
import argparse
from collections import defaultdict
import subprocess

# Cargar variables de entorno
load_dotenv(dotenv_path=".env.local")

# Variables de entorno
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = int(os.getenv("TG_CHAT_ID"))
TMDB_API_TOKEN = os.getenv("TMDB_API_TOKEN")

# Argumentos
parser = argparse.ArgumentParser(description="Procesa carpetas y archivos de video.")
parser.add_argument("-i", "--input", required=True, help="Carpeta raíz a analizar")
parser.add_argument("--upload", action="store_true", help="Subir archivos a la nube")
parser.add_argument("--rc-config", required=False, default="rclone.conf", help="Ruta al archivo de configuración de rclone")
parser.add_argument("--rc-args", required=False, default="", help="Argumentos adicionales para rclone (como string)")
parser.add_argument("--rc-remote", required=True, help="Nombre del remoto configurado en rclone")
parser.add_argument("--dry-run", action="store_true", help="Simula el envío sin realizar llamadas")
args = parser.parse_args()

# Directorio de entrada
folder_path = args.input.rstrip("/") + "/"

# Regex para nombrado
FILE_PATTERN = r'^(.+?) \((\d{4})\) - S(\d{2})E(\d{2}) - \[(\d{3,4}p)\] \[([^\]]+)\] \[tmdbid=(\d+)\]\.(\w+)$'

def get_file_info(file_name):
    """Extrae información del archivo usando una expresión regular."""
    match = re.match(FILE_PATTERN, file_name)
    if not match:
        return None
    return {
        "title": match.group(1),
        "year": match.group(2),
        "season": match.group(3),
        "episode": match.group(4),
        "resolution": match.group(5),
        "platform": match.group(6),
        "tmdb_id": match.group(7),
        "extension": match.group(8),
    }

def get_media_info(file_path):
    """Obtiene codec, audio, y subtítulos del archivo usando pymediainfo."""
    media_info = MediaInfo.parse(file_path)
    video_info = []
    audio_info = []
    subtitle_info = []

    for track in media_info.tracks:
        if track.track_type == "Video":
            codec = track.other_format[0] if track.other_format else "Unknown"
            quality = f"{track.height}p {codec}"
            video_info.append(quality)
        elif track.track_type == "Audio":
            if track.channel_s:
                channels = "5.1" if track.channel_s == "6" else f"{track.channel_s}.0"
            else:
                channels = "Stereo"
            audio_format = track.other_format[0].split()[0] if track.other_format else "Unknown"
            audio_language = track.other_language[0] if track.other_language else "Unknown"
            audio_info.append(f"{audio_language} ({audio_format} {channels})")
        elif track.track_type == "Text":
            subtitle_format = track.other_format[0].upper() if track.other_format else "SRT"
            if subtitle_format == "UTF-8":
                subtitle_format = "SRT"
            subtitle_language = track.other_language[0] if track.other_language else "Unknown"
            subtitle_info.append(f"{subtitle_language} ({subtitle_format})")

    return {
        "video": ", ".join(video_info),
        "audio": ", ".join(audio_info),
        "subtitles": ", ".join(subtitle_info),
    }

def format_report(info, media_info, is_movie, remote_path):
    """Genera un reporte detallado para consola o Telegram."""
    title = info["title"]
    year = info["year"]
    resolution = info["resolution"]
    platform = info["platform"]
    season_episode = f"S{info['season']}E{info['episode']}" if not is_movie else ""

    # Ajustar calidad
    quality_type = "WEB-DL" if platform.lower() not in ["dvd", "bd"] else ""
    video_details = media_info["video"].split(", ")[0]  # Solo el primer video track (por ejemplo, "1080p AVC")
    final_quality = f"{resolution} {platform} {quality_type} ({video_details.split(' ')[1]})".strip()

    return (
        f"#miauporte <b>{title} ({year}) - agregado {season_episode or 'Película'}</b>\n\n"
        f"<b>Calidad:</b> {final_quality}\n"
        f"<b>Audio:</b> {media_info['audio']}\n"
        f"<b>Subtítulos:</b> {media_info['subtitles']}\n\n"
        f"<b>Ruta:</b> <em>{remote_path}</em>\n"
    )

def get_backdrop_url(tmdb_id, is_movie):
    """Obtiene la URL del backdrop desde TMDB usando el tmdb_id."""
    tmdb_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}" if is_movie else f"https://api.themoviedb.org/3/tv/{tmdb_id}"
    
    tmdb_url += f"?api_key={TMDB_API_TOKEN}"

    response = requests.get(tmdb_url)
    if response.status_code == 200:
        data = response.json()
        backdrop_path = data.get("backdrop_path")
        if backdrop_path:
            return f"https://image.tmdb.org/t/p/original{backdrop_path}"
    return None

def send_report(chat_id, token, report, is_movie, backdrop_url, dry_run=False):
    """Envía el reporte a Telegram como una foto con caption o muestra en consola en modo dry-run."""
    if dry_run:
        print("Simulación de envío:")
        print("Backdrop URL:", backdrop_url)
        print("Reporte:\n", report)
    else:
        if backdrop_url:
            print("Enviando reporte a Telegram...")
            requests.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                data={
                    "chat_id": chat_id,
                    "caption": report,
                    "parse_mode": "HTML",
                },
                files={
                    "photo": requests.get(backdrop_url).content
                }
            )
        else:
            print("No se encontró un backdrop. Enviando solo texto.")
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat_id, "text": report, "parse_mode": "HTML"},
            )

def process_directory(directory, dry_run=False):
    """Procesa una carpeta y sus subcarpetas."""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith((".mkv", ".mp4", ".avi")):
                file_path = os.path.join(root, file)
                info = get_file_info(file)
                if not info:
                    print(f"Archivo no válido: {file}")
                    continue

                is_movie = not info["season"]
                media_info = get_media_info(file_path)

                # Construir ruta remota
                relative_path = os.path.relpath(root, directory)
                remote_path = construct_remote_path(directory, relative_path)

                if args.upload:
                    upload_files(
                        local_path=root,
                        remote_name=args.rc_remote,
                        remote_path=remote_path,
                        config_path=args.rc_config,
                        extra_args=args.rc_args,
                        dry_run=dry_run
                    )
                report = format_report(info, media_info, is_movie, remote_path)

                # Obtener backdrop URL
                backdrop_url = get_backdrop_url(info["tmdb_id"], is_movie)

                # Enviar reporte
                send_report(TG_CHAT_ID, TG_BOT_TOKEN, report, is_movie, backdrop_url, dry_run)

def construct_remote_path(base_path, relative_path):
    """Construye la ruta remota basada en la carpeta de entrada."""
    base_name = os.path.basename(base_path.rstrip("/"))
    return os.path.join(base_name, relative_path).replace("\\", "/")

def upload_files(local_path, remote_name, remote_path, config_path, extra_args, dry_run):
    """Sube archivos a la nube usando rclone."""
    # Convertir extra_args (string) en una lista de argumentos
    extra_args_list = extra_args.split() if extra_args else []
    
    command = [
        "rclone", "copy", local_path, f"{remote_name}:{remote_path}",
        "-P", "--config", config_path
    ] + extra_args_list

    if dry_run:
        print("Simulación de subida con el comando:")
        print(" ".join(command))
    else:
        try:
            subprocess.run(command, check=True)
            print(f"Subida completada: {local_path} -> {remote_name}:{remote_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error al subir archivos: {e}")

def main():
    """Procesa carpetas o archivos desde la ruta raíz."""
    if not os.path.exists(folder_path):
        print(f"La carpeta {folder_path} no existe.")
        return

    process_directory(folder_path, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
