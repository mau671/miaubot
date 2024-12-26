import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(dotenv_path=".env.local")

# Variables de entorno
TG_BOT_TOKEN: str = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID: int = int(os.getenv("TG_CHAT_ID", "0"))
TMDB_API_TOKEN: str = os.getenv("TMDB_API_TOKEN", "")