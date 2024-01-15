"""Configuration definition."""

from __future__ import annotations

from enum import Enum
from urllib.parse import urlparse

from arq.connections import RedisSettings
from pydantic import (
    BaseSettings,
    Field,
    FilePath,
    HttpUrl,
    RedisDsn,
    SecretStr,
)
from safir.arq import ArqMode

__all__ = ["Config", "Profile", "LogLevel"]


class Profile(str, Enum):
    production = "production"

    development = "development"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"

    INFO = "INFO"

    WARNING = "WARNING"

    ERROR = "ERROR"

    CRITICAL = "CRITICAL"


class Config(BaseSettings):
    name: str = Field("spherexportal", env="SAFIR_NAME")

    profile: Profile = Field(Profile.production, env="SAFIR_PROFILE")

    log_level: LogLevel = Field(LogLevel.INFO, env="SAFIR_LOG_LEVEL")

    logger_name: str = Field("spherexportal", env="SAFIR_LOGGER")

    dataset_path: FilePath = Field(..., env="PORTAL_DATASET_PATH")

    ltd_api_url: HttpUrl = Field(
        HttpUrl("https://docs-api.ipac.caltech.edu/", scheme="https"),
        description="Root URL of the LTD API server.",
        env="PORTAL_LTD_API_URL",
    )

    ltd_organization: str = Field(
        "spherex",
        description="Organization name in the LTD API.",
        env="PORTAL_LTD_API_ORG",
    )

    ltd_api_username: str = Field(
        "spherex-portal",
        description="Username for LTD API",
        env="PORTAL_LTD_API_USERNAME",
    )

    ltd_api_password: SecretStr | None = Field(
        None,
        description="Password corresponding to ltd_api_username",
        env="PORTAL_LTD_API_PASSWORD",
    )

    # Ideally this should come from the LTD API, since the bucket's name is
    # declared there, but it's current absent. us-west-1 is where we're
    # deploying SPHEREx's LTD.
    s3_region: str = Field(
        "us-west-1",
        description="AWS region for the S3 bucket.",
        env="PORTAL_S3_REGION",
    )

    aws_access_key_id: str | None = Field(
        None,
        description="AWS access key ID; for getting metadata objects from S3.",
        env="PORTAL_AWS_ACCESS_KEY_ID",
    )

    aws_access_key_secret: SecretStr | None = Field(
        None,
        description=(
            "AWS access key secret; for getting metadata objects from S3."
        ),
        env="PORTAL_AWS_ACCESS_KEY_SECRET",
    )

    use_mock_data: bool = Field(
        True,
        description=(
            "Use the YAML dataset rather than obtaining metadata from live "
            "sources like LTD and S3"
        ),
        env="PORTAL_USE_MOCK_DATA",
    )

    redis_url: RedisDsn = Field(
        RedisDsn("redis://localhost:6379/0", scheme="redis"),
        env="PORTAL_REDIS_URL",
        description="Redis database URL for caching project metadata.",
    )

    arq_redis_url: RedisDsn = Field(
        RedisDsn("redis://localhost:6379/1", scheme="redis"),
        env="PORTAL_ARQ_REDIS_URL",
        description="Redis database URL for the arq queue.",
    )

    arq_mode: ArqMode = Field(ArqMode.production, env="PORTAL_ARQ_MODE")

    github_app_id: str | None = Field(
        None,
        env="PORTAL_GITHUB_APP_ID",
        description="GitHub App ID for the SPHEREx Doc Portal",
    )

    github_webhook_secret: SecretStr | None = Field(
        None,
        env="PORTAL_GITHUB_WEBHOOK_SECRET",
        description="GitHub webhook secret for the SPHEREx Doc Portal",
    )

    github_app_private_key: SecretStr | None = Field(
        None,
        env="PORTAL_GITHUB_APP_PRIVATE_KEY",
        description="GitHub App private key for the SPHEREx Doc Portal",
    )

    github_owners: list[str] = Field(
        ["SPHEREx", "IPAC-SW"],
        env="PORTAL_GITHUB_OWNERS",
        description="GitHub owners to watch for SPHEREx software projects",
    )

    @property
    def arq_redis_settings(self) -> RedisSettings:
        """Create a Redis settings instance for arq."""
        url_parts = urlparse(self.arq_redis_url)
        redis_settings = RedisSettings(
            host=url_parts.hostname or "localhost",
            port=url_parts.port or 6379,
            database=int(url_parts.path.lstrip("/")) if url_parts.path else 0,
        )
        return redis_settings

    @property
    def is_github_app_enabled(self) -> bool:
        """Return whether GitHub App integration is enabled."""
        return all(
            [
                self.github_app_id,
                self.github_webhook_secret,
                self.github_app_private_key,
            ]
        )


config = Config()
"""Configuration for the spherex-doc-portal."""
