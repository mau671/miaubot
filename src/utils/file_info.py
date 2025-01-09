import re
from typing import Optional, Dict

FILE_PATTERN = r"^(.+?) \((\d{4})\) - S(\d{2})E(\d{2}) - \[(\d{3,4}p)\] \[([^\]]+)\] \[tmdbid=(\d+)\]\.(\w+)$"


def get_file_info(file_name: str) -> Optional[Dict[str, str]]:
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
