import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
TG_BOT_TOKEN: str = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID: int = int(os.getenv("TG_CHAT_ID", "0"))
TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
TVDB_API_KEY: str = os.getenv("TVDB_API_KEY", "")
