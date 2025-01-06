import os
import re
import requests
from pymediainfo import MediaInfo
from config import TG_BOT_TOKEN, TG_CHAT_ID, TMDB_API_TOKEN
import argparse
from typing import Optional, Dict, List
import subprocess

# Argumentos
parser = argparse.ArgumentParser(description="Procesa carpetas y archivos de video.")
parser.add_argument("-i", "--input", required=True, help="Carpeta raíz a analizar")
parser.add_argument("--rc-config", required=False, default="rclone.conf", help="Ruta al archivo de configuración de rclone")
parser.add_argument("--rc-args", required=False, default="", help="Argumentos adicionales para rclone (como string)")
parser.add_argument("--rc-remote", required=True, help="Nombre del remoto configurado en rclone")
parser.add_argument("--dry-run", action="store_true", help="Simula el envío sin realizar llamadas")
parser.add_argument('--rc-upload-to', required=False, action='store_true', help='Nombre del remoto (con su path) configurado en rclone')
parser.add_argument('--rc-upload-all', required=False, action='store_true', help='Subir todos los archivos encontrados')
args = parser.parse_args()

# Directorio de entrada
folder_path = args.input.rstrip("/") + "/"

# Regex para nombrado
FILE_PATTERN: str = r'^(.+?) \((\d{4})\) - S(\d{2})E(\d{2}) - \[(\d{3,4}p)\] \[([^\]]+)\] \[tmdbid=(\d+)\]\.(\w+)$'

def get_file_info(file_name: str) -> Optional[Dict[str, str]]:
    """
    Extrae información del archivo usando una expresión regular.
    
    :param file_name: Nombre del archivo
    :return: Diccionario con la información extraída o None si no coincide
    """
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

def get_media_info(file_path: str) -> Dict[str, str]:
    """
    Obtiene codec, audio y subtítulos del archivo usando pymediainfo.
    
    :param file_path: Ruta completa del archivo
    :return: Diccionario con detalles de video, audio y subtítulos
    """
    media_info = MediaInfo.parse(file_path)
    video_info: List[str] = []
    audio_info: List[str] = []
    subtitle_info: List[str] = []

    for track in media_info.tracks:
        if track.track_type == "Video":
            codec = track.other_format[0] if track.other_format else "Unknown"
            quality = f"{track.height}p {codec}"
            video_info.append(quality)
        elif track.track_type == "Audio":
            channels = (
                "5.1" if track.channel_s == 6 else f"{track.channel_s}.0"
                if track.channel_s else "Stereo"
            )
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

def format_report(
    info: Dict[str, str],
    media_info: Dict[str, str],
    is_movie: bool,
    remote_path: str
) -> str:
    """
    Genera un reporte detallado para consola o Telegram.
    
    :param info: Información del archivo
    :param media_info: Detalles del archivo multimedia
    :param is_movie: True si es película, False si es serie
    :param remote_path: Ruta remota en la nube
    :return: Reporte formateado como texto
    """
    title = info["title"]
    year = info["year"]
    resolution = info["resolution"]
    platform = info["platform"]
    season_episode = f"S{info['season']}E{info['episode']}" if not is_movie else ""

    quality_type = "WEB-DL" if platform.lower() not in ["dvd", "bd"] else ""
    video_details = media_info["video"].split(", ")[0] if media_info["video"] else "Desconocido"
    final_quality = f"{resolution} {platform} {quality_type} ({video_details.split(' ')[1]})".strip()

    return (
        f"#Reporte <b>{title} ({year}) - {season_episode or 'Película'}</b>\n\n"
        f"<b>Calidad:</b> {final_quality}\n"
        f"<b>Audio:</b> {media_info['audio']}\n"
        f"<b>Subtítulos:</b> {media_info['subtitles']}\n\n"
        f"<b>Ruta:</b> <em>{remote_path}</em>\n"
    )

def get_backdrop_url(tmdb_id: str, is_movie: bool) -> Optional[str]:
    """
    Obtiene la URL del backdrop desde TMDB usando el tmdb_id.
    
    :param tmdb_id: ID del TMDB
    :param is_movie: True si es película, False si es serie
    :return: URL del backdrop o None si no se encuentra
    """
    tmdb_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}" if is_movie else f"https://api.themoviedb.org/3/tv/{tmdb_id}"
    tmdb_url += f"?api_key={TMDB_API_TOKEN}"

    response = requests.get(tmdb_url)
    if response.status_code == 200:
        data = response.json()
        backdrop_path = data.get("backdrop_path")
        if backdrop_path:
            return f"https://image.tmdb.org/t/p/original{backdrop_path}"
    return None

def send_report(
    chat_id: int, 
    token: str, 
    report: str, 
    is_movie: bool, 
    backdrop_url: Optional[str], 
    dry_run: bool = False
) -> None:
    """
    Envía el reporte a Telegram como una foto con caption o muestra en consola en modo dry-run.
    
    :param chat_id: ID del chat de Telegram
    :param token: Token del bot de Telegram
    :param report: Reporte a enviar
    :param is_movie: True si es película, False si es serie
    :param backdrop_url: URL del backdrop
    :param dry_run: True para simular el envío
    """
    if dry_run:
        print("Simulación de envío:")
        print("Backdrop URL:", backdrop_url)
        print("Reporte:\n", report)
    else:
        if backdrop_url:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                data={
                    "chat_id": chat_id,
                    "caption": report,
                    "parse_mode": "HTML",
                },
                files={"photo": requests.get(backdrop_url).content}
            )
        else:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat_id, "text": report, "parse_mode": "HTML"},
            )

def process_directory(directory: str, dry_run: bool = False) -> None:
    """
    Procesa una carpeta y sus subcarpetas para analizar archivos multimedia.

    :param directory: Ruta de la carpeta a procesar
    :param dry_run: True para simular las operaciones sin ejecutarlas
    """
    files_to_upload = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".mkv", ".mp4", ".avi")):
                file_path = os.path.join(root, file)
                info = get_file_info(file)
                if not info:
                    print(f"Archivo no válido: {file}")
                    continue

                is_movie = not info["season"]  # Es película si no hay temporada
                media_info = get_media_info(file_path)

                # Construir ruta remota
                relative_path = os.path.relpath(root, directory)
                remote_path = construct_remote_path(directory, relative_path)

                if args.rc_upload_to:
                    success = upload_files(
                        local_path=root,
                        remote_path=args.rc_upload_to,
                        config_path=args.rc_config,
                        extra_args=args.rc_args,
                        dry_run=dry_run
                    )
                    if not success:
                        print(f"Error al subir el archivo: {file}")
                        continue

                report = format_report(info, media_info, is_movie, remote_path)

                # Obtener URL del backdrop
                backdrop_url = get_backdrop_url(info["tmdb_id"], is_movie)

                # Enviar reporte a Telegram
                send_report(TG_CHAT_ID, TG_BOT_TOKEN, report, is_movie, backdrop_url, dry_run)

                # Agregar archivo a la lista de archivos a subir si se especifica subir todos
                if args.rc_upload_all:
                    files_to_upload.append(file_path)

    # Si se especifica subir todos los archivos, se suben al finalizar el procesamiento de la carpeta
    if args.rc_upload_all and files_to_upload:
        extra_args_with_filter = f"{args.rc_args} --include {' '.join(files_to_upload)}"
        upload_files(
            local_path=directory,
            remote_path=args.rc_upload_to,
            config_path=args.rc_config,
            extra_args=extra_args_with_filter,
            dry_run=dry_run
        )

def construct_remote_path(base_path: str, relative_path: str) -> str:
    """
    Construye la ruta remota basada en la carpeta de entrada.

    :param base_path: Ruta base local
    :param relative_path: Ruta relativa desde la base
    :return: Ruta remota en formato adecuado
    """
    base_name = os.path.basename(base_path.rstrip("/"))
    return os.path.join(base_name, relative_path).replace("\\", "/")

def upload_files(
    local_path: str, 
    remote_path: str,
    config_path: str, 
    extra_args: str, 
    dry_run: bool
) -> bool:
    """
    Sube archivos a la nube usando rclone.

    :param local_path: Ruta local de los archivos
    :param remote_name: Nombre del remoto configurado en rclone
    :param remote_path: Ruta remota donde subir los archivos
    :param config_path: Ruta al archivo de configuración de rclone
    :param extra_args: Argumentos adicionales para rclone
    :param dry_run: True para simular la subida sin ejecutarla
    :return: True si la subida fue exitosa, False en caso contrario
    """
    extra_args_list = extra_args.split() if extra_args else []

    command = [
        "rclone", "copy", local_path, f"{remote_path}",
        "-P", "--config", config_path
    ] + extra_args_list

    if dry_run:
        print("Simulación de subida con el comando:")
        print(" ".join(command))
        return True
    else:
        try:
            result = subprocess.run(command, check=True)
            if result.returncode == 0:
                print(f"Subida completada: {local_path} -> {remote_path}")
                return True
            else:
                print(f"Error al subir archivos: Código de retorno {result.returncode}")
                return False
        except subprocess.CalledProcessError as e:
            print(f"Error al subir archivos: {e}")
            return False

def main() -> None:
    """
    Punto de entrada principal. Procesa la carpeta o archivo especificado en los argumentos.
    """
    if not os.path.exists(folder_path):
        print(f"La carpeta {folder_path} no existe.")
        return

    process_directory(folder_path, dry_run=args.dry_run)

if __name__ == "__main__":
    main()