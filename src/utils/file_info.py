import re
from typing import Optional, Dict

# Regular expression pattern to match series and movie file names.
# "SxxExx" (season and episode) is optional to allow matching movie file names as well.
FILE_PATTERN = (
    r"^(.+?) \((\d{4})\)"                # Title and year
    r"(?: - S(\d{2})E(\d{2}))?"          # Season and episode (optional for movies)
    r" - \[(\d{3,4}p)\] \[([^\]]+)\]"    # Resolution and platform
    r" \[(tmdbid|tvdbid)=(\d+)\]\.(\w+)$" # ID type, ID value, and file extension
)


def get_file_info(file_name: str) -> Optional[Dict[str, Optional[str]]]:
    """
    Extracts metadata information from a file name following a specific pattern.
    The function supports both series and movie file names.

    File name formats:
        - Series: "Title (Year) - S01E01 - [1080p] [Platform] [tmdbid=123456].mkv"
        - Movie:  "Title (Year) - [1080p] [Platform] [tvdbid=654321].mp4"

    Args:
        file_name (str): The file name to be analyzed.

    Returns:
        Optional[Dict[str, Optional[str]]]: A dictionary containing metadata extracted
        from the file name if it matches the pattern, or None if no match is found.

        The returned dictionary includes:
            - "title" (str): The title of the series or movie.
            - "year" (str): The release year.
            - "season" (Optional[str]): The season number (None for movies).
            - "episode" (Optional[str]): The episode number (None for movies).
            - "resolution" (str): The video resolution (e.g., "1080p").
            - "platform" (str): The streaming platform or source (e.g., "Netflix").
            - "id_type" (str): The ID type, either "tmdbid" or "tvdbid".
            - "id" (str): The numeric ID value.
            - "extension" (str): The file extension (e.g., "mkv", "mp4").
            - "type" (str): The type of content, either "series" or "movie".
    """
    # Match the file name against the pattern
    match = re.match(FILE_PATTERN, file_name)
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
        "resolution": match.group(5),
        "platform": match.group(6),
        "id_type": match.group(7),  # Either "tmdbid" or "tvdbid"
        "id": match.group(8),       # The numeric ID value
        "extension": match.group(9),
        "type": "series" if is_series else "movie"
    }