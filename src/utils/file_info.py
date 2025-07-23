import re
from typing import Optional, Dict

# Regular expression pattern to match new anime structure
# Format: "Title (Year) - S01E01 - 001 - [Quality Info] - Group.mkv"
# Also supports multi-episode format: "Title (Year) - S01E01-E03 - 001-003 - [Quality Info] - Group.mkv"
# Series pattern: absolute episode number segment (###) is optional; episode title segment optional too
FILE_PATTERN = (
    r"^(.+?) \((\d{4})\) - S(\d{2})E(\d{2})(?:-E(\d{2}))?"  # title, year, season, episode, optional end episode
    r"(?: - (\d{3})(?:-(\d{3}))?)?"  # optional absolute episode number(s)
    r"(?: - [^\[]+)?"  # optional episode title
    r" - \[.+?\] .+ - .+\.(\w+)$"  # quality block and extension
)

# Alternative pattern for old format compatibility
OLD_FILE_PATTERN = (
    r"^(.+?) \((\d{4})\)"  # Title and year
    r"(?: - S(\d{2})E(\d{2}))?"  # Season and episode (optional for movies)
    r" - \[(\d{3,4}p)\] \[([^\]]+)\]"  # Resolution and platform
    r" \[(tmdbid|tvdbid)=(\d+)\]\.(\w+)$"  # ID type, ID value, and file extension
)

# Pattern to extract TVDB ID from folder name
FOLDER_PATTERN = r"\[tvdbid-(\d+)\]$"

# Pattern for extended movie naming with id before quality blocks
EXT_MOVIE_PATTERN = (
    r"^(.+?) \((\d{4})\) "  # Title and year
    r"\[(tmdbid|tvdbid)-(\d+)\]"  # ID block with dash
    r"(?: - (.+))?"  # The rest of the name (quality info blocks)
    r"\.(\w+)$"  # Extension
)


# Helper to detect platform from quality string
def _detect_platform(qi: str) -> str:
    qi_upper = qi.upper()

    # Check for streaming service with WEB-DL/WEBRip combinations first
    streaming_services = [
        "AMZN",
        "CR", 
        "NF",
        "HULU",
        "DSNP",
        "ATVP",
        "PMTP",
        "MAX",
        "STAN",
        "AO",
    ]
    
    for service in streaming_services:
        if service in qi_upper:
            # Check if it's combined with WEB-DL or WEBRip
            if "WEB-DL" in qi_upper:
                return f"{service} WEB-DL"
            elif "WEBRIP" in qi_upper:
                return f"{service} WEBRip"
            else:
                return service

    # Check for standalone web formats
    if "WEBRIP" in qi_upper:
        return "WEBRip"

    if "WEB-DL" in qi_upper:
        return "WEB-DL"

    if "BD" in qi_upper or "BLURAY" in qi_upper:
        return "BD"

    # Return "Unknown" instead of defaulting to WEB-DL when no platform indicators are found
    return "Unknown"


def get_file_info(file_path: str) -> Optional[Dict[str, Optional[str]]]:
    """
    Extracts metadata information from a file path following anime structure patterns.
    The function supports both new anime structure and old formats.

    New anime structure:
        - "Series Name (Year) [tvdbid-123456]/Season 01/Series Name (Year) - S01E01 - 001 - [Quality] - Group.mkv"
        - "Series Name (Year) [tvdbid-123456]/Season 01/Series Name (Year) - S01E04-E06 - 030-032 - [Quality] - Group.mkv" (multi-episode)

    Old formats:
        - Series: "Title (Year) - S01E01 - [1080p] [Platform] [tmdbid=123456].mkv"
        - Movie:  "Title (Year) - [1080p] [Platform] [tvdbid=654321].mp4"

    Args:
        file_path (str): The full file path to be analyzed.

    Returns:
        Optional[Dict[str, Optional[str]]]: A dictionary containing metadata extracted
        from the file path if it matches any pattern, or None if no match is found.

        The returned dictionary includes:
            - "title" (str): The title of the series or movie.
            - "year" (str): The release year.
            - "season" (Optional[str]): The season number (None for movies).
            - "episode" (Optional[str]): The episode number or range (e.g., "01" or "04-06") (None for movies).
            - "episode_number" (Optional[str]): The absolute episode number or range (e.g., "030" or "030-032").
            - "resolution" (str): The video resolution (e.g., "1080p").
            - "platform" (str): The streaming platform or source (e.g., "Netflix").
            - "id_type" (str): The ID type, either "tmdbid" or "tvdbid".
            - "id" (str): The numeric ID value.
            - "extension" (str): The file extension (e.g., "mkv", "mp4").
            - "type" (str): The type of content, either "series" or "movie".
            - "quality_info" (str): Additional quality information.
    """
    import os

    file_name = os.path.basename(file_path)
    folder_path = os.path.dirname(file_path)

    # Try new anime structure first
    match = re.match(FILE_PATTERN, file_name)
    if match:
        # Extract TVDB ID from parent folder
        folder_name = os.path.basename(os.path.dirname(folder_path))
        folder_match = re.search(FOLDER_PATTERN, folder_name)

        if folder_match:
            tvdb_id = folder_match.group(1)
            # Extract quality info from filename
            quality_match = re.search(r"\[([^\]]+)\]", file_name)
            quality_info = quality_match.group(1) if quality_match else "Unknown"

            # Extract resolution from quality info
            resolution_match = re.search(r"(\d{3,4}p)", quality_info)
            resolution = resolution_match.group(1) if resolution_match else "Unknown"

            # Detect platform using helper
            platform = _detect_platform(quality_info)

            # Handle both single and multi-episode formats
            episode_start = match.group(4)
            episode_end = match.group(5)  # None for single episodes
            absolute_start = match.group(6)
            absolute_end = match.group(7)  # None for single episodes
            
            # For episode field, use range format if it's multi-episode
            if episode_end:
                episode_display = f"{episode_start}-{episode_end}"
            else:
                episode_display = episode_start
                
            # For absolute episode number, use range format if available
            if absolute_start and absolute_end:
                absolute_display = f"{absolute_start}-{absolute_end}"
            elif absolute_start:
                absolute_display = absolute_start
            else:
                absolute_display = None

            return {
                "title": match.group(1),
                "year": match.group(2),
                "season": match.group(3),
                "episode": episode_display,
                "episode_number": absolute_display,
                "resolution": resolution,
                "platform": platform,
                "id_type": "tvdbid",
                "id": tvdb_id,
                "extension": match.group(8),
                "type": "series",
                "quality_info": quality_info,
            }

    # Extended movie format with ID before quality
    match = re.match(EXT_MOVIE_PATTERN, file_name)
    if match:
        title, year, id_type, id_val, rest_info, extension = match.groups()

        quality_info = rest_info or ""

        # Extract resolution
        resolution_match = re.search(r"(\d{3,4}p)", quality_info)
        resolution = resolution_match.group(1) if resolution_match else "Unknown"

        # Detect platform using helper
        platform = _detect_platform(quality_info)

        return {
            "title": title,
            "year": year,
            "season": None,
            "episode": None,
            "episode_number": None,
            "resolution": resolution,
            "platform": platform,
            "id_type": id_type,
            "id": id_val,
            "extension": extension,
            "type": "movie",
            "quality_info": quality_info,
        }

    # Fallback to old format
    match = re.match(OLD_FILE_PATTERN, file_name)
    if not match:
        return None

    # Determine if the file is a series based on the presence of season and episode
    is_series = match.group(3) is not None and match.group(4) is not None

    # Return extracted metadata
    return {
        "title": match.group(1),
        "year": match.group(2),
        "season": match.group(3),  # None for movies
        "episode": match.group(4),  # None for movies
        "episode_number": None,
        "resolution": match.group(5),
        "platform": match.group(6),
        "id_type": match.group(7),  # Either "tmdbid" or "tvdbid"
        "id": match.group(8),  # The numeric ID value
        "extension": match.group(9),
        "type": "series" if is_series else "movie",
        "quality_info": f"{match.group(5)} {match.group(6)}",
    }
