import requests
from typing import Dict, Optional
from src.config import TMDB_API_TOKEN


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
        f"#miauporte <b>{title} ({year}) - {season_episode or 'Movie'}</b>\n\n"
        f"<b>Calidad:</b> {final_quality}\n"
        f"<b>Audio:</b> {media_info['audio']}\n"
        f"<b>Subtítulos:</b> {media_info['subtitles']}\n\n"
        f"<b>Ruta:</b> <em>{remote_path.split(":", 1)[-1]}</em>\n"
    )


def get_backdrop_url(tmdb_id: str, is_movie: bool) -> Optional[str]:
    """
    Gets the backdrop URL from TMDB using the tmdb_id.

    :param tmdb_id: TMDB ID
    :param is_movie: True if it is a movie, False if it is a series
    :return: Backdrop URL or None if not found
    """
    try:
        tmdb_url = (
            f"https://api.themoviedb.org/3/movie/{tmdb_id}"
            if is_movie
            else f"https://api.themoviedb.org/3/tv/{tmdb_id}"
        )
        tmdb_url += f"?api_key={TMDB_API_TOKEN}"
        response = requests.get(tmdb_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        backdrop_path = data.get("backdrop_path")
        if backdrop_path:
            return f"https://image.tmdb.org/t/p/original{backdrop_path}"
    except requests.RequestException as e:
        print(f"Error fetching TMDB data: {e}")
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
        try:
            print("Sending report to Telegram...")
            if backdrop_url:
                response = requests.post(
                    f"https://api.telegram.org/bot{token}/sendPhoto",
                    data={
                        "chat_id": chat_id,
                        "caption": report,
                        "parse_mode": "HTML",
                        "photo": backdrop_url,
                    },
                )
            else:
                response = requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data={"chat_id": chat_id, "text": report, "parse_mode": "HTML"},
                )
            response.raise_for_status()
            print("Report sent successfully.")
        except requests.RequestException as e:
            print(f"Error sending report to Telegram: {e}")
