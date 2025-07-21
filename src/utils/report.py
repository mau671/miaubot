import requests
from typing import Dict, Optional
from src.config import TMDB_API_KEY, TVDB_API_KEY

_CACHED_TVDB_TOKEN: Optional[str] = None


def normalize_audio_codecs(audio_info: str) -> str:
    """
    Normalizes audio codec names to shorter, standard formats.

    :param audio_info: Original audio information string
    :return: Normalized audio information string
    """
    if not audio_info:
        return audio_info

    # Audio codec normalization mappings
    codec_mappings = {
        "E-AC-3": "DD+",
        "EAC3": "DD+",
        "AC-3": "DD",
        "AC3": "DD",
        "AAC": "AAC",
        "DTS-HD": "DTS-HD",
        "DTS": "DTS",
        "FLAC": "FLAC",
        "PCM": "PCM",
        "Opus": "Opus",
        "Vorbis": "Vorbis",
    }

    normalized = audio_info
    for original, short in codec_mappings.items():
        normalized = normalized.replace(original, short)

    return normalized


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

    video_details = (
        media_info["video"].split(", ")[0] if media_info["video"] else "Unknown"
    )

    # Extract codec from video details
    try:
        codec = video_details.split(' ')[1] if len(video_details.split(' ')) > 1 else "Unknown"
    except (IndexError, AttributeError):
        codec = "Unknown"

    # Build quality string based on available platform information
    if platform.lower() == "unknown":
        # No platform information available, show only resolution and codec
        final_quality = f"{resolution} ({codec})"
    elif platform.lower() in ["dvd", "bd", "encode"]:
        # Physical media or encode
        final_quality = f"{resolution} {platform} ({codec})"
    else:
        # Web platform (streaming services, WEB-DL, WEBRip)
        final_quality = f"{resolution} {platform} ({codec})"

    return (
        f"#miauporte <b>{title} ({year}){f' - {season_episode}' if content_type == 'series' else ''}</b>\n\n"
        f"<b>Calidad:</b> {final_quality}\n"
        f"<b>Audio:</b> {normalize_audio_codecs(media_info['audio'])}\n"
        f"<b>Subtítulos:</b> {media_info['subtitles']}\n\n"
        f"<b>Ruta:</b> <em>{remote_path.split(':', 1)[-1]}</em>\n"
    )


def format_consolidated_report(episodes: list, base_remote_path: str) -> str:
    """
    Generates a consolidated report for multiple episodes of the same season.

    :param episodes: List of episode dictionaries with info, media_info, remote_path, and episode number
    :param base_remote_path: Base remote path for the series
    :return: Formatted consolidated report as text.
    """
    if not episodes:
        return ""

    # Use first episode as base for common information
    base_info = episodes[0]["info"]
    base_media_info = episodes[0]["media_info"]

    title = base_info["title"]
    year = base_info["year"]
    season = base_info["season"]
    resolution = base_info["resolution"]
    platform = base_info["platform"]

    # Determine episode range
    episode_numbers = [ep["episode"] for ep in episodes]
    min_episode = min(episode_numbers)
    max_episode = max(episode_numbers)

    if min_episode == max_episode:
        season_episode = f"S{season}E{min_episode:02d}"
    else:
        season_episode = f"S{season}E{min_episode:02d}-E{max_episode:02d}"

    video_details = (
        base_media_info["video"].split(", ")[0]
        if base_media_info["video"]
        else "Unknown"
    )

    # Extract codec from video details
    try:
        codec = video_details.split(' ')[1] if len(video_details.split(' ')) > 1 else "Unknown"
    except (IndexError, AttributeError):
        codec = "Unknown"

    # Build quality string based on available platform information
    if platform.lower() == "unknown":
        # No platform information available, show only resolution and codec
        final_quality = f"{resolution} ({codec})"
    elif platform.lower() in ["dvd", "bd", "encode"]:
        # Physical media or encode
        final_quality = f"{resolution} {platform} ({codec})"
    else:
        # Web platform (streaming services, WEB-DL, WEBRip)
        final_quality = f"{resolution} {platform} ({codec})"

    # Extract base path from remote path (remove specific episode filename)
    import os

    # Get the path without the remote prefix and remove the filename
    path_without_remote = (
        base_remote_path.split(":", 1)[-1]
        if ":" in base_remote_path
        else base_remote_path
    )
    base_path = os.path.dirname(path_without_remote)

    return (
        f"#miauporte <b>{title} ({year}) - {season_episode}</b>\n\n"
        f"<b>Calidad:</b> {final_quality}\n"
        f"<b>Audio:</b> {normalize_audio_codecs(base_media_info['audio'])}\n"
        f"<b>Subtítulos:</b> {base_media_info['subtitles']}\n\n"
        f"<b>Ruta:</b> <em>{base_path}</em>\n"
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
            # Try backdrop first, then poster
            backdrop_path = data.get("backdrop_path")
            poster_path = data.get("poster_path")
            if backdrop_path:
                return f"https://image.tmdb.org/t/p/original{backdrop_path}"
            if poster_path:
                return f"https://image.tmdb.org/t/p/original{poster_path}"
        elif id_type == "tvdbid":

            def _extract_first(arts, art_type=None):
                for art in arts:
                    if art_type is None or art.get("type") == art_type:
                        return art.get("image")
                return None

            if content_type == "movie":
                artworks = data.get("data", {}).get("artworks", [])
                # 15 = hero/backdrop, 14 = poster (movie)
                url = _extract_first(artworks, 15)
                if not url:
                    url = _extract_first(artworks, 14)
                if url:
                    return url
            else:
                artworks = data.get("data", []).get("artworks", [])
                # Attempt to get backdrop (type 3) else poster (type 2)
                url = _extract_first(artworks, 3)
                if not url:
                    # Fallback: make another request for posters (type 2) if initial request was for type 3
                    try:
                        # Request posters
                        poster_resp = requests.get(
                            f"https://api4.thetvdb.com/v4/series/{content_id}/artworks?type=2",
                            headers=headers,
                            timeout=10,
                        )
                        poster_resp.raise_for_status()
                        poster_arts = (
                            poster_resp.json().get("data", []).get("artworks", [])
                        )
                        url = _extract_first(poster_arts)
                    except requests.RequestException:
                        url = None
                if url:
                    return url

                # Final fallback: request extended info and try to extract any hero or poster image
                try:
                    ext_resp = requests.get(
                        f"https://api4.thetvdb.com/v4/series/{content_id}/extended",
                        headers=headers,
                        timeout=10,
                    )
                    ext_resp.raise_for_status()
                    ext_data = ext_resp.json()
                    artworks_ext = ext_data.get("data", {}).get("artworks", [])
                    url = (
                        _extract_first(artworks_ext, 3)
                        or _extract_first(artworks_ext, 2)
                        or _extract_first(artworks_ext)
                    )
                except requests.RequestException:
                    url = None
                if url:
                    return url
    except requests.RequestException as e:
        print(f"Error fetching data for {id_type}: {e}")
    return None


def get_tvdb_token(api_key: str) -> Optional[str]:
    """
    Fetches the Bearer token from TheTVDB API using the provided API key.

    :param api_key: API key for TheTVDB.
    :return: Bearer token or None if the request fails.
    """
    # Re-use cached token during the lifetime of the process (TVDB tokens are valid ~1 month)
    global _CACHED_TVDB_TOKEN

    if _CACHED_TVDB_TOKEN:
        return _CACHED_TVDB_TOKEN

    try:
        url = "https://api4.thetvdb.com/v4/login"
        payload = {"apikey": api_key}
        headers = {"accept": "application/json", "Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        _CACHED_TVDB_TOKEN = response.json().get("data", {}).get("token")
        return _CACHED_TVDB_TOKEN
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

        # Display the HTTP request that would be sent to the Telegram API
        if backdrop_url:
            method = "sendPhoto"
            payload = {
                "chat_id": chat_id,
                "caption": report,
                "parse_mode": "HTML",
                "photo": backdrop_url,
            }
        else:
            method = "sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": report,
                "parse_mode": "HTML",
            }

        url = f"https://api.telegram.org/bot{token}/{method}"
        import json

        print("Telegram request (simulated):")
        print(f"POST {url}")
        print("Payload:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        try:
            print("Sending report to Telegram...")
            # If the caption is too long for sendPhoto (1024-char limit) we fall back to sendMessage
            use_photo = backdrop_url is not None and len(report) <= 1024

            if use_photo:
                url = f"https://api.telegram.org/bot{token}/sendPhoto"

                # Download image locally to send as multipart/form-data
                import tempfile
                import os

                try:
                    img_resp = requests.get(backdrop_url, timeout=15, stream=True)
                    img_resp.raise_for_status()

                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".jpg"
                    ) as tmp_img:
                        for chunk in img_resp.iter_content(chunk_size=8192):
                            tmp_img.write(chunk)
                        temp_image_path = tmp_img.name

                    payload = {
                        "chat_id": chat_id,
                        "caption": report,
                        "parse_mode": "HTML",
                    }

                    with open(temp_image_path, "rb") as img_file:
                        response = requests.post(
                            url, data=payload, files={"photo": img_file}
                        )
                finally:
                    # Ensure the temporary image is removed
                    try:
                        os.remove(temp_image_path)
                    except Exception:
                        pass
            else:
                # Either there is no backdrop or the caption is too long
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": report,
                    "parse_mode": "HTML",
                }

            # When use_photo branch already executed a request, ensure we don't reassign
            if not use_photo:
                response = requests.post(url, data=payload)

            # If sendPhoto fails (e.g. invalid URL), fall back to sendMessage
            if response.status_code != 200:
                print("Error response from Telegram:")
                print(response.text)

                if use_photo:
                    print("Falling back to sendMessage without photo…")
                    url_fallback = f"https://api.telegram.org/bot{token}/sendMessage"
                    payload_fallback = {
                        "chat_id": chat_id,
                        "text": report,
                        "parse_mode": "HTML",
                    }
                    response_fb = requests.post(url_fallback, data=payload_fallback)

                    if response_fb.status_code != 200:
                        print("Fallback sendMessage also failed:")
                        print(response_fb.text)
                        response_fb.raise_for_status()
                else:
                    response.raise_for_status()

            print("Report sent successfully.")
        except requests.RequestException as e:
            print(f"Error sending report to Telegram: {e}")
