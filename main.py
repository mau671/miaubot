import os
import re
import requests
from pymediainfo import MediaInfo
from config import TG_BOT_TOKEN, TG_CHAT_ID, TMDB_API_TOKEN
import argparse
from typing import Optional, Dict, List
import subprocess

# Arguments
parser = argparse.ArgumentParser(description="Process folders and video files.")
parser.add_argument("-i", "--input", required=True, help="Root folder to analyze")
parser.add_argument(
    "--rc-config",
    required=False,
    default="rclone.conf",
    help="Path to the rclone configuration file",
)
parser.add_argument(
    "--rc-args",
    required=False,
    default="",
    help="Additional arguments for rclone (as string)",
)
parser.add_argument(
    "--rc-remote", required=True, help="Name of the remote configured in rclone"
)
parser.add_argument(
    "--dry-run", action="store_true", help="Simulate the upload without making calls"
)
parser.add_argument(
    "--rc-upload-to",
    required=False,
    action="store_true",
    help="Name of the remote (with its path) configured in rclone",
)
parser.add_argument(
    "--rc-upload-all",
    required=False,
    action="store_true",
    help="Upload all found files",
)
args = parser.parse_args()

# Input directory
folder_path = args.input.rstrip("/") + "/"

# Regex for naming
FILE_PATTERN: str = r"^(.+?) \((\d{4})\) - S(\d{2})E(\d{2}) - \[(\d{3,4}p)\] \[([^\]]+)\] \[tmdbid=(\d+)\]\.(\w+)$"


def get_file_info(file_name: str) -> Optional[Dict[str, str]]:
    """
    Extracts information from the file using a regular expression.

    :param file_name: File name
    :return: Dictionary with the extracted information or None if it does not match
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
    Gets codec, audio, and subtitles from the file using pymediainfo.

    :param file_path: Full path of the file
    :return: Dictionary with video, audio, and subtitle details
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
                "5.1"
                if track.channel_s == 6
                else f"{track.channel_s}.0"
                if track.channel_s
                else "Stereo"
            )
            audio_format = (
                track.other_format[0].split()[0] if track.other_format else "Unknown"
            )
            audio_language = (
                track.other_language[0] if track.other_language else "Unknown"
            )
            audio_info.append(f"{audio_language} ({audio_format} {channels})")
        elif track.track_type == "Text":
            subtitle_format = (
                track.other_format[0].upper() if track.other_format else "SRT"
            )
            if subtitle_format == "UTF-8":
                subtitle_format = "SRT"
            subtitle_language = (
                track.other_language[0] if track.other_language else "Unknown"
            )
            subtitle_info.append(f"{subtitle_language} ({subtitle_format})")

    return {
        "video": ", ".join(video_info),
        "audio": ", ".join(audio_info),
        "subtitles": ", ".join(subtitle_info),
    }


def format_report(
    info: Dict[str, str], media_info: Dict[str, str], is_movie: bool, remote_path: str
) -> str:
    """
    Generates a detailed report for console or Telegram.

    :param info: File information
    :param media_info: Multimedia file details
    :param is_movie: True if it is a movie, False if it is a series
    :param remote_path: Remote path in the cloud
    :return: Formatted report as text
    """
    title = info["title"]
    year = info["year"]
    resolution = info["resolution"]
    platform = info["platform"]
    season_episode = f"S{info['season']}E{info['episode']}" if not is_movie else ""

    quality_type = "WEB-DL" if platform.lower() not in ["dvd", "bd"] else platform
    video_details = (
        media_info["video"].split(", ")[0] if media_info["video"] else "Unknown"
    )
    final_quality = f"{resolution} {platform} {quality_type} ({video_details.split(' ')[1]})".strip()

    return (
        f"#Report <b>{title} ({year}) - {season_episode or 'Movie'}</b>\n\n"
        f"<b>Quality:</b> {final_quality}\n"
        f"<b>Audio:</b> {media_info['audio']}\n"
        f"<b>Subtitles:</b> {media_info['subtitles']}\n\n"
        f"<b>Path:</b> <em>{remote_path}</em>\n"
    )


def get_backdrop_url(tmdb_id: str, is_movie: bool) -> Optional[str]:
    """
    Gets the backdrop URL from TMDB using the tmdb_id.

    :param tmdb_id: TMDB ID
    :param is_movie: True if it is a movie, False if it is a series
    :return: Backdrop URL or None if not found
    """
    tmdb_url = (
        f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        if is_movie
        else f"https://api.themoviedb.org/3/tv/{tmdb_id}"
    )
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
    dry_run: bool = False,
) -> None:
    """
    Sends the report to Telegram as a photo with caption or displays it in the console in dry-run mode.

    :param chat_id: Telegram chat ID
    :param token: Telegram bot token
    :param report: Report to send
    :param is_movie: True if it is a movie, False if it is a series
    :param backdrop_url: Backdrop URL
    :param dry_run: True to simulate the send
    """
    if dry_run:
        print("Send simulation:")
        print("Backdrop URL:", backdrop_url)
        print("Report:\n", report)
    else:
        if backdrop_url:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                data={
                    "chat_id": chat_id,
                    "caption": report,
                    "parse_mode": "HTML",
                },
                files={"photo": requests.get(backdrop_url).content},
            )
        else:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat_id, "text": report, "parse_mode": "HTML"},
            )


def process_directory(directory: str, dry_run: bool = False) -> None:
    """
    Processes a folder and its subfolders to analyze multimedia files.

    :param directory: Path of the folder to process
    :param dry_run: True to simulate the operations without executing them
    """
    files_to_upload = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".mkv", ".mp4", ".avi")):
                file_path = os.path.join(root, file)
                info = get_file_info(file)
                if not info:
                    print(f"Invalid file: {file}")
                    continue

                is_movie = not info["season"]  # It is a movie if there is no season
                media_info = get_media_info(file_path)

                # Build remote path
                relative_path = os.path.relpath(root, directory)
                remote_path = construct_remote_path(directory, relative_path)

                if args.rc_upload_to:
                    success = upload_files(
                        local_path=root,
                        remote_path=args.rc_upload_to,
                        config_path=args.rc_config,
                        extra_args=args.rc_args,
                        dry_run=dry_run,
                    )
                    if not success:
                        print(f"Error uploading file: {file}")
                        continue

                report = format_report(info, media_info, is_movie, remote_path)

                # Get backdrop URL
                backdrop_url = get_backdrop_url(info["tmdb_id"], is_movie)

                # Send report to Telegram
                send_report(
                    TG_CHAT_ID, TG_BOT_TOKEN, report, is_movie, backdrop_url, dry_run
                )

                # Add file to the list of files to upload if upload all is specified
                if args.rc_upload_all:
                    files_to_upload.append(file_path)

    # If upload all files is specified, upload them after processing the folder
    if args.rc_upload_all and files_to_upload:
        extra_args_with_filter = f"{args.rc_args} --include {' '.join(files_to_upload)}"
        upload_files(
            local_path=directory,
            remote_path=args.rc_upload_to,
            config_path=args.rc_config,
            extra_args=extra_args_with_filter,
            dry_run=dry_run,
        )


def construct_remote_path(base_path: str, relative_path: str) -> str:
    """
    Constructs the remote path based on the input folder.

    :param base_path: Local base path
    :param relative_path: Relative path from the base
    :return: Remote path in the appropriate format
    """
    base_name = os.path.basename(base_path.rstrip("/"))
    return os.path.join(base_name, relative_path).replace("\\", "/")


def upload_files(
    local_path: str, remote_path: str, config_path: str, extra_args: str, dry_run: bool
) -> bool:
    """
    Uploads files to the cloud using rclone.

    :param local_path: Local path of the files
    :param remote_name: Name of the remote configured in rclone
    :param remote_path: Remote path where to upload the files
    :param config_path: Path to the rclone configuration file
    :param extra_args: Additional arguments for rclone
    :param dry_run: True to simulate the upload without executing it
    :return: True if the upload was successful, False otherwise
    """
    extra_args_list = extra_args.split() if extra_args else []

    command = [
        "rclone",
        "copy",
        local_path,
        f"{remote_path}",
        "-P",
        "--config",
        config_path,
    ] + extra_args_list

    if dry_run:
        print("Upload simulation with the command:")
        print(" ".join(command))
        return True
    else:
        try:
            result = subprocess.run(command, check=True)
            if result.returncode == 0:
                print(f"Upload completed: {local_path} -> {remote_path}")
                return True
            else:
                print(f"Error uploading files: Return code {result.returncode}")
                return False
        except subprocess.CalledProcessError as e:
            print(f"Error uploading files: {e}")
            return False


def main() -> None:
    """
    Main entry point. Processes the folder or file specified in the arguments.
    """
    if not os.path.exists(folder_path):
        print(f"The folder {folder_path} does not exist.")
        return

    process_directory(folder_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
