from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-20250514"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    database_url: str = "postgresql+psycopg://intake:intake@localhost:5432/intake_desk"

    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    chunk_size: int = 800
    chunk_overlap: int = 120

    classification_confidence_threshold: float = 0.75
    require_citations: bool = True

    corpus_manifest_path: str = "corpus/manifest.yaml"


@lru_cache
def get_settings() -> Settings:
    return Settings()
