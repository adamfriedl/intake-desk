from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Default: OpenRouter + a cheap/reliable instruction-following model for JSON + citations.
    llm_provider: str = "openrouter"
    llm_model: str = "openai/gpt-4.1-mini"
    openrouter_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    database_url: str = "postgresql+psycopg://intake:intake@localhost:5432/intake_desk"

    # Embeddings also go through OpenRouter when openrouter_api_key is set.
    embedding_model: str = "openai/text-embedding-3-small"
    embedding_dimensions: int = 1536
    chunk_size: int = 800
    chunk_overlap: int = 120

    classification_confidence_threshold: float = 0.75
    require_citations: bool = True

    corpus_manifest_path: str = "corpus/manifest.yaml"


@lru_cache
def get_settings() -> Settings:
    return Settings()
