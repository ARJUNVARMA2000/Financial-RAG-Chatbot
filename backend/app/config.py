import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


# Load environment variables from .env so OPENAI_API_KEY and others are available
load_dotenv()

# OpenRouter configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class Settings(BaseModel):
    openai_api_key: str
    openai_base_url: str | None = None
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-large"

    # OpenRouter settings for multi-model evaluation
    openrouter_api_key: str = ""
    openrouter_base_url: str = OPENROUTER_BASE_URL

    data_dir: Path = Path("data")
    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")
    index_dir: Path = Path("data/indexes")
    chroma_persist_dir: Path = Path("data/indexes/chroma")


class AppConfig(BaseModel):
    settings: Settings


def get_settings() -> Settings:
    settings = Settings(
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        openai_base_url=os.environ.get("OPENAI_BASE_URL") or None,
        openai_chat_model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
        openai_embedding_model=os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"),
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        openrouter_base_url=os.environ.get("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL),
    )

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required but missing. Add it to your .env file.")

    # Ensure important directories exist to avoid runtime errors
    for path in [
        settings.data_dir,
        settings.raw_dir,
        settings.index_dir,
        settings.chroma_persist_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)

    return settings



