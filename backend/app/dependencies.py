from functools import lru_cache

from .config import Settings, get_settings
from .openai_client import OpenAIClient


@lru_cache
def get_app_settings() -> Settings:
    return get_settings()


@lru_cache
def get_openai_client() -> OpenAIClient:
    settings = get_app_settings()
    return OpenAIClient(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        chat_model=settings.openai_chat_model,
        embedding_model=settings.openai_embedding_model,
    )



