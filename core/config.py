"""Platform configuration management.

Loads configuration from config.yaml and environment variables using pydantic-settings.
Provides a singleton accessor for global config access.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_yaml_config(path: Optional[str] = None) -> dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        path: Path to config.yaml. Defaults to CONFIG_PATH env var
              or ./config.yaml relative to project root.

    Returns:
        Parsed YAML as a dictionary, or empty dict if file not found.
    """
    config_path = Path(path or os.getenv("CONFIG_PATH", "config.yaml"))
    if not config_path.is_absolute():
        config_path = Path(__file__).resolve().parent.parent / config_path
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


class DatabaseConfig(BaseSettings):
    """PostgreSQL database connection settings."""

    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = "localhost"
    port: int = 5432
    name: str = "retrieva"
    user: str = "retrieva"
    password: str = ""
    pool_min_size: int = 2
    pool_max_size: int = 10

    @property
    def dsn(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisConfig(BaseSettings):
    """Redis connection settings for caching and task queues."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""

    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class VectorDBConfig(BaseSettings):
    """Qdrant vector database connection settings."""

    model_config = SettingsConfigDict(env_prefix="QDRANT_")

    host: str = "localhost"
    port: int = 6333
    grpc_port: int = 6334
    api_key: str = ""
    prefer_grpc: bool = True
    collection_prefix: str = "retrieva_"


class IngestionConfig(BaseSettings):
    """Settings governing the ingestion pipeline."""

    model_config = SettingsConfigDict(env_prefix="INGESTION_")

    default_chunking_strategy: str = "semantic"
    default_chunk_size: int = 512
    chunk_overlap: int = 64
    default_embedding_model: str = "text-embedding-3-small"
    embedding_provider: str = "openai"
    embedding_dimensions: int = 1536
    max_file_size_mb: int = 100
    supported_extensions: list[str] = Field(
        default_factory=lambda: [
            ".pdf", ".docx", ".xlsx", ".txt", ".md", ".csv", ".html", ".htm",
        ]
    )
    batch_size: int = 64


class RetrievalConfig(BaseSettings):
    """Settings for the retrieval engine."""

    model_config = SettingsConfigDict(env_prefix="RETRIEVAL_")

    default_strategy: str = "hybrid"
    default_top_k: int = 10
    rerank_enabled: bool = True
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_top_k: int = 5
    hybrid_vector_weight: float = 0.7
    hybrid_keyword_weight: float = 0.3
    score_threshold: float = 0.3


class GenerationConfig(BaseSettings):
    """Settings for the generation engine."""

    model_config = SettingsConfigDict(env_prefix="GENERATION_")

    default_provider: str = "openai"
    default_model: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 2048
    max_context_chunks: int = 8
    default_persona: str = "You are a helpful assistant that answers questions based on the provided context."
    enable_guardrails: bool = True
    hallucination_threshold: float = 0.5


class PermissionsConfig(BaseSettings):
    """Settings for role-based access control."""

    model_config = SettingsConfigDict(env_prefix="PERMISSIONS_")

    enabled: bool = True
    default_role: str = "viewer"
    admin_roles: list[str] = Field(default_factory=lambda: ["admin", "owner"])


class AnalyticsConfig(BaseSettings):
    """Settings for usage analytics and telemetry."""

    model_config = SettingsConfigDict(env_prefix="ANALYTICS_")

    enabled: bool = True
    track_queries: bool = True
    track_latency: bool = True
    retention_days: int = 90


class PluginsConfig(BaseSettings):
    """Settings for the plugin system."""

    model_config = SettingsConfigDict(env_prefix="PLUGINS_")

    directory: str = "plugins"
    # Override active plugin per type (empty = infer from other config sections).
    chunker: str = ""
    embedder: str = ""
    retriever: str = ""
    generator: str = ""


class PlatformConfig(BaseSettings):
    """Root configuration aggregating all sub-configs.

    Values are loaded from config.yaml then overridden by environment variables.
    """

    model_config = SettingsConfigDict(env_prefix="RETRIEVA_")

    app_name: str = "Retrieva"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    permissions: PermissionsConfig = Field(default_factory=PermissionsConfig)
    analytics: AnalyticsConfig = Field(default_factory=AnalyticsConfig)
    plugins: PluginsConfig = Field(default_factory=PluginsConfig)


def _build_config(yaml_overrides: dict[str, Any] | None = None) -> PlatformConfig:
    """Build a PlatformConfig merging YAML defaults with env-var overrides."""
    yaml_data = yaml_overrides or _load_yaml_config()

    sub_configs: dict[str, Any] = {}
    mapping = {
        "database": DatabaseConfig,
        "redis": RedisConfig,
        "vector_db": VectorDBConfig,
        "ingestion": IngestionConfig,
        "retrieval": RetrievalConfig,
        "generation": GenerationConfig,
        "permissions": PermissionsConfig,
        "analytics": AnalyticsConfig,
        "plugins": PluginsConfig,
    }
    for key, cls in mapping.items():
        section = yaml_data.get(key, {})
        if isinstance(section, dict):
            sub_configs[key] = cls(**section)
        else:
            sub_configs[key] = cls()

    top_level = {
        k: v for k, v in yaml_data.items() if k not in mapping and not isinstance(v, dict)
    }
    return PlatformConfig(**top_level, **sub_configs)


@lru_cache(maxsize=1)
def get_config() -> PlatformConfig:
    """Return the global singleton PlatformConfig instance.

    Configuration is loaded once and cached. Call ``get_config.cache_clear()``
    to force a reload.
    """
    return _build_config()
