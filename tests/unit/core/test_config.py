"""Unit tests for platform configuration loading."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from core.config import (
    DatabaseConfig,
    GenerationConfig,
    IngestionConfig,
    PlatformConfig,
    RedisConfig,
    RetrievalConfig,
    VectorDBConfig,
    _build_config,
    _load_yaml_config,
)


class TestLoadYamlConfig:
    """Tests for YAML config file loading."""

    def test_loads_valid_yaml(self, tmp_path):
        """A valid YAML file should be parsed into a dict."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            yaml.dump({
                "app_name": "TestApp",
                "ingestion": {"default_chunk_size": 256},
            })
        )

        result = _load_yaml_config(str(config_file))

        assert result["app_name"] == "TestApp"
        assert result["ingestion"]["default_chunk_size"] == 256

    def test_returns_empty_dict_for_missing_file(self):
        """A non-existent config path should return an empty dict."""
        result = _load_yaml_config("/nonexistent/config.yaml")
        assert result == {}

    def test_uses_config_path_env_var(self, tmp_path):
        """CONFIG_PATH env var should be used when no explicit path is given."""
        config_file = tmp_path / "env_config.yaml"
        config_file.write_text(yaml.dump({"app_name": "FromEnv"}))

        with patch.dict(os.environ, {"CONFIG_PATH": str(config_file)}):
            result = _load_yaml_config()

        assert result["app_name"] == "FromEnv"

    def test_empty_yaml_returns_empty_dict(self, tmp_path):
        """An empty YAML file should return an empty dict, not None."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        result = _load_yaml_config(str(config_file))
        assert result == {}


class TestPlatformConfigDefaults:
    """Tests for default configuration values."""

    def test_default_app_name(self):
        """The default app name should be 'Retrieva'."""
        config = PlatformConfig()
        assert config.app_name == "Retrieva"

    def test_default_environment(self):
        """The default environment should be 'development'."""
        config = PlatformConfig()
        assert config.environment == "development"

    def test_default_debug_is_false(self):
        """Debug should default to False."""
        config = PlatformConfig()
        assert config.debug is False

    def test_ingestion_defaults(self):
        """Ingestion config should have sensible defaults."""
        config = IngestionConfig()
        assert config.default_chunking_strategy == "semantic"
        assert config.default_chunk_size == 512
        assert config.chunk_overlap == 64
        assert config.embedding_provider == "openai"
        assert ".pdf" in config.supported_extensions
        assert ".docx" in config.supported_extensions

    def test_retrieval_defaults(self):
        """Retrieval config should default to hybrid strategy."""
        config = RetrievalConfig()
        assert config.default_strategy == "hybrid"
        assert config.default_top_k == 10
        assert config.rerank_enabled is True
        assert config.hybrid_vector_weight == 0.7
        assert config.hybrid_keyword_weight == 0.3

    def test_generation_defaults(self):
        """Generation config should default to OpenAI gpt-4o."""
        config = GenerationConfig()
        assert config.default_provider == "openai"
        assert config.default_model == "gpt-4o"
        assert config.temperature == 0.1
        assert config.enable_guardrails is True

    def test_database_dsn_format(self):
        """Database DSN should follow the asyncpg format."""
        config = DatabaseConfig()
        assert config.dsn.startswith("postgresql+asyncpg://")
        assert "localhost" in config.dsn
        assert "5432" in config.dsn

    def test_redis_url_format(self):
        """Redis URL should follow the redis:// format."""
        config = RedisConfig()
        assert config.url.startswith("redis://")

    def test_vector_db_defaults(self):
        """Vector DB config should default to Qdrant on localhost."""
        config = VectorDBConfig()
        assert config.host == "localhost"
        assert config.port == 6333
        assert config.prefer_grpc is True


class TestBuildConfig:
    """Tests for the _build_config function."""

    def test_builds_from_yaml_overrides(self):
        """YAML overrides should be applied to the resulting config."""
        yaml_data = {
            "app_name": "Custom App",
            "debug": True,
            "ingestion": {"default_chunk_size": 1024},
        }

        config = _build_config(yaml_overrides=yaml_data)

        assert config.app_name == "Custom App"
        assert config.debug is True
        assert config.ingestion.default_chunk_size == 1024

    def test_sub_configs_are_independent(self):
        """Each sub-config section should be independently constructable."""
        yaml_data = {
            "retrieval": {"default_top_k": 20},
            "generation": {"temperature": 0.5},
        }

        config = _build_config(yaml_overrides=yaml_data)

        assert config.retrieval.default_top_k == 20
        assert config.generation.temperature == 0.5
        # Other sections should retain defaults
        assert config.ingestion.default_chunk_size == 512

    def test_empty_yaml_uses_all_defaults(self):
        """An empty YAML dict should produce a config with all defaults."""
        config = _build_config(yaml_overrides={})

        assert config.app_name == "Retrieva"
        assert config.environment == "development"
        assert config.ingestion.default_chunking_strategy == "semantic"


class TestEnvVarOverride:
    """Tests for environment variable overrides of configuration."""

    def test_env_overrides_database_host(self):
        """DB_HOST env var should override the database host."""
        with patch.dict(os.environ, {"DB_HOST": "db.example.com"}):
            config = DatabaseConfig()
        assert config.host == "db.example.com"

    def test_env_overrides_redis_port(self):
        """REDIS_PORT env var should override the Redis port."""
        with patch.dict(os.environ, {"REDIS_PORT": "6380"}):
            config = RedisConfig()
        assert config.port == 6380

    def test_env_overrides_qdrant_api_key(self):
        """QDRANT_API_KEY env var should set the Qdrant API key."""
        with patch.dict(os.environ, {"QDRANT_API_KEY": "secret-key"}):
            config = VectorDBConfig()
        assert config.api_key == "secret-key"

    def test_env_overrides_ingestion_settings(self):
        """INGESTION_ prefixed env vars should override ingestion config."""
        with patch.dict(os.environ, {"INGESTION_DEFAULT_CHUNK_SIZE": "2048"}):
            config = IngestionConfig()
        assert config.default_chunk_size == 2048

    def test_env_overrides_generation_settings(self):
        """GENERATION_ prefixed env vars should override generation config."""
        with patch.dict(os.environ, {"GENERATION_TEMPERATURE": "0.7"}):
            config = GenerationConfig()
        assert config.temperature == 0.7
