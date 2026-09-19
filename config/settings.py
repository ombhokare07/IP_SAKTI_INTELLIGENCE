from pathlib import Path

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and an optional .env."""

    app_name: str = "IP-SAKTI Intelligence"
    app_env: str = "development"
    debug: bool = True

    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-2.5-flash"

    embedding_model: str = "BAAI/bge-base-en-v1.5"
    vector_db_path: Path = Path("chroma_db")
    vector_collection: str = "ip_sakti_documents"

    prior_art_provider: str = ""
    prior_art_api_key: SecretStr = SecretStr("")
    prior_art_api_url: str = ""
    prior_art_timeout: float = Field(default=15.0, gt=0, le=120)
    prior_art_cache_ttl: float = Field(default=900.0, ge=0, le=86_400)
    prior_art_allow_mock: bool = False
    epo_ops_consumer_key: SecretStr = SecretStr("")
    epo_ops_consumer_secret: SecretStr = SecretStr("")

    app_data_dir: Path = Path("data/runtime")
    allow_mock_data: bool = False
    provider_timeout: float = Field(default=15, gt=0, le=120)
    api_auth_required: bool = False
    api_auth_token: SecretStr = SecretStr("")
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    tk_provider: str = ""
    tk_corpus_path: Path | None = None
    tk_api_url: str = ""
    tk_api_key: SecretStr = SecretStr("")
    tk_search_authorized: bool = False
    regulation_provider: str = ""
    regulation_corpus_path: Path | None = None
    regulation_api_url: str = ""
    regulation_api_key: SecretStr = SecretStr("")
    translation_provider: str = ""
    translation_api_url: str = ""
    translation_api_key: SecretStr = SecretStr("")
    stt_provider: str = ""
    stt_api_url: str = ""
    stt_api_key: SecretStr = SecretStr("")
    tts_provider: str = ""
    tts_api_url: str = ""
    tts_api_key: SecretStr = SecretStr("")

    top_k: int = Field(default=5, gt=0)
    chunk_size: int = Field(default=800, gt=0)
    chunk_overlap: int = Field(default=150, ge=0)
    evidence_relevance_threshold: float = Field(default=0.55, ge=0, le=1)
    evidence_sufficiency_threshold: float = Field(default=0.55, ge=0, le=1)
    evidence_min_relevant_chunks: int = Field(default=1, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def validate_chunk_window(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self


settings = Settings()
