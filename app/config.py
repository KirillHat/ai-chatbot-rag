"""Typed configuration loaded from .env via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide configuration.

    Loaded once at startup. All values are validated up front so a misspelt
    environment variable fails the boot instead of surfacing as a runtime
    error in the middle of a chat session.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Anthropic ---
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-sonnet-4-6", alias="CLAUDE_MODEL")
    claude_max_tokens: int = Field(default=1024, alias="CLAUDE_MAX_TOKENS", ge=64, le=8192)

    # --- Admin auth ---
    admin_api_token: str = Field(default="change-me", alias="ADMIN_API_TOKEN")

    # --- Storage ---
    chroma_dir: Path = Field(default=Path("./data/chroma"), alias="CHROMA_DIR")
    sqlite_path: Path = Field(default=Path("./data/app.db"), alias="SQLITE_PATH")
    upload_dir: Path = Field(default=Path("./data/uploads"), alias="UPLOAD_DIR")

    # --- Retrieval / chunking ---
    chunk_size: int = Field(default=900, alias="CHUNK_SIZE", ge=200, le=4000)
    chunk_overlap: int = Field(default=150, alias="CHUNK_OVERLAP", ge=0, le=1000)
    top_k: int = Field(default=4, alias="TOP_K", ge=1, le=20)
    # Wider candidate pool fed into the BM25/vector hybrid before we trim
    # to `top_k` for the model. Should be 3-4× top_k for best recall.
    retrieval_pool: int = Field(default=16, alias="RETRIEVAL_POOL", ge=1, le=100)
    # `default` = English-only ONNX MiniLM-L6-v2 (small, no extra deps).
    # `multilingual` = paraphrase-multilingual-MiniLM-L12-v2 via
    # sentence-transformers (50+ languages, including Russian).
    # `none` = disable embeddings entirely (BM25-only fallback for tests).
    embedding_model: str = Field(default="default", alias="EMBEDDING_MODEL")
    # Weight of vector-similarity vs BM25 in hybrid retrieval.
    # 1.0 = pure vector (legacy behaviour), 0.0 = pure BM25,
    # 0.6 = vector preferred but lexical hits still surface.
    hybrid_alpha: float = Field(default=0.6, alias="HYBRID_ALPHA", ge=0.0, le=1.0)

    # --- Server ---
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT", ge=1, le=65535)
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")

    # --- Rate limiting ---
    rate_limit_per_minute: int = Field(default=20, alias="RATE_LIMIT_PER_MINUTE", ge=1, le=600)

    # --- Tenant ---
    assistant_name: str = Field(default="AI Assistant", alias="ASSISTANT_NAME")
    assistant_tenant: str = Field(default="demo", alias="ASSISTANT_TENANT")

    # --- Hand-off (escalation to a human) ---
    # Slack incoming-webhook URL — if set, escalation events are POSTed here.
    escalation_slack_webhook: str = Field(default="", alias="ESCALATION_SLACK_WEBHOOK")
    # Or an email address — if set, the same payload goes to logs tagged for
    # downstream forwarding by your mail relay (we deliberately don't ship
    # SMTP code to keep the dependency surface small).
    escalation_email: str = Field(default="", alias="ESCALATION_EMAIL")

    # --- Optional re-ranking ---
    # `none` (default) = no re-ranking. `cohere` = use COHERE_API_KEY to
    # re-score the retrieval pool with rerank-multilingual-v3.0.
    rerank_provider: str = Field(default="none", alias="RERANK_PROVIDER")
    cohere_api_key: str = Field(default="", alias="COHERE_API_KEY")

    @field_validator("chunk_overlap")
    @classmethod
    def _overlap_smaller_than_chunk(cls, v: int, info) -> int:
        size = info.data.get("chunk_size", 900)
        if v >= size:
            raise ValueError("CHUNK_OVERLAP must be strictly smaller than CHUNK_SIZE")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def ensure_dirs(self) -> None:
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
