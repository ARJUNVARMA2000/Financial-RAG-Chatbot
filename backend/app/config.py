import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


# Load environment variables from .env so OPENAI_API_KEY and others are available
load_dotenv()


class Settings(BaseModel):
    openai_api_key: str
    openai_base_url: str | None = None
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-large"

    data_dir: Path = Path("data")
    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")
    index_dir: Path = Path("data/indexes")
    chroma_persist_dir: Path = Path("data/indexes/chroma")


class AppConfig(BaseModel):
    settings: Settings


def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        openai_base_url=os.environ.get("OPENAI_BASE_URL") or None,
        openai_chat_model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
        openai_embedding_model=os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"),
    )



