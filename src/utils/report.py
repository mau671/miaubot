import requests
from typing import Dict, Optional
from src.config import TMDB_API_KEY, TVDB_API_KEY


def format_report(
    info: Dict[str, str], media_info: Dict[str, str], remote_path: str
) -> str:
    """
    Generates a detailed report for console or Telegram.

    :param info: File information.
    :param media_info: Multimedia file details.
    :param remote_path: Remote path in the cloud.
    :return: Formatted report as text.
    """
    title = info["title"]
    year = info["year"]
    resolution = info["resolution"]
    platform = info["platform"]
    content_type = info["type"]  # Either "movie" or "series"

    # Include season and episode only if the content is a series
    season_episode = (
        f"S{info['season']}E{info['episode']}" if content_type == "series" else "Movie"
    )

    quality_type = "WEB-DL" if platform.lower() not in ["dvd", "bd"] else platform
    video_details = (
        media_info["video"].split(", ")[0] if media_info["video"] else "Unknown"
    )
    final_quality = f"{resolution} {platform} {quality_type} ({video_details.split(' ')[1]})".strip()

    return (
        f"#miauporte <b>{title} ({year}){ f"- {season_episode}" if content_type == "series" else ""}</b>\n\n"
        f"<b>Calidad:</b> {final_quality}\n"
        f"<b>Audio:</b> {media_info['audio']}\n"
        f"<b>Subtítulos:</b> {media_info['subtitles']}\n\n"
        f"<b>Ruta:</b> <em>{remote_path.split(':', 1)[-1]}</em>\n"
    )


def get_backdrop_url(content_id: str, id_type: str, content_type: str) -> Optional[str]:
    """
    Gets the backdrop URL from either TMDB or TVDB using the ID.

    :param content_id: The content's ID (e.g., TMDB ID or TVDB ID).
    :param id_type: The type of ID, either "tmdbid" or "tvdbid".
    :param content_type: The type of content, either "movie" or "series".
    :return: Backdrop URL or None if not found.
    """
    try:
        if id_type == "tmdbid":
            # Fetch from TMDB
            tmdb_url = f"https://api.themoviedb.org/3/{'movie' if content_type == 'movie' else 'tv'}/{content_id}"
            tmdb_url += f"?api_key={TMDB_API_KEY}"
            response = requests.get(tmdb_url, timeout=10)
        elif id_type == "tvdbid":
            # Fetch token and determine TVDB endpoint
            token = get_tvdb_token(TVDB_API_KEY)
            if not token:
                print("Failed to retrieve TVDB token.")
                return None

            if content_type == "movie":
                # Use /extended endpoint for movies
                tvdb_url = f"https://api4.thetvdb.com/v4/movies/{content_id}/extended"
            else:
                # Use /artworks endpoint for series
                tvdb_url = (
                    f"https://api4.thetvdb.com/v4/series/{content_id}/artworks?type=3"
                )

            headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
            response = requests.get(tvdb_url, headers=headers, timeout=10)
        else:
            print(f"Unsupported ID type: {id_type}")
            return None

        response.raise_for_status()
        data = response.json()

        if id_type == "tmdbid":
            return f"https://image.tmdb.org/t/p/original{data.get('backdrop_path')}"
        elif id_type == "tvdbid":
            if content_type == "movie":
                # Extract the first artwork with type 15 from /extended
                artworks = data.get("data", {}).get("artworks", [])
                for artwork in artworks:
                    if artwork.get("type") == 15:
                        return artwork.get("image")
            else:
                # Extract the first artwork from /artworks
                artworks = data.get("data", []).get("artworks", [])
                if artworks:
                    return artworks[0].get("image")
    except requests.RequestException as e:
        print(f"Error fetching data for {id_type}: {e}")
    return None


def get_tvdb_token(api_key: str) -> Optional[str]:
    """
    Fetches the Bearer token from TheTVDB API using the provided API key.

    :param api_key: API key for TheTVDB.
    :return: Bearer token or None if the request fails.
    """
    try:
        # Define the API endpoint and payload
        url = "https://api4.thetvdb.com/v4/login"
        payload = {"apikey": api_key}
        headers = {"accept": "application/json", "Content-Type": "application/json"}
        # Make the POST request
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        # Extract the token from the response
        return response.json().get("data", {}).get("token")
    except requests.RequestException as e:
        print(f"Error obtaining TVDB token: {e}")
    return None


def send_report(
    chat_id: int,
    token: str,
    report: str,
    backdrop_url: Optional[str],
    dry_run: bool = False,
) -> None:
    """
    Sends the report to Telegram as a photo with caption or displays it in the console in dry-run mode.

    :param chat_id: Telegram chat ID.
    :param token: Telegram bot token.
    :param report: Report to send.
    :param backdrop_url: Backdrop URL.
    :param dry_run: True to simulate the send.
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
