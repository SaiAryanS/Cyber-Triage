import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    lm_studio_base_url: str = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    lm_studio_model: str = os.getenv("LM_STUDIO_MODEL", "meta-llama-3.1-8b-instruct")
    abuseipdb_api_key: str = os.getenv("ABUSEIPDB_API_KEY", "")
    memory_db_path: str = os.getenv("MEMORY_DB_PATH", "./data/memory.db")


settings = Settings()
