"""Configuration definition."""

from __future__ import annotations

import os
from enum import Enum
from typing import Annotated, TypeAlias
from urllib.parse import urlparse

from arq.connections import RedisSettings
from pydantic import (
    AfterValidator,
    Field,
    FilePath,
    HttpUrl,
    SecretStr,
    UrlConstraints,
)
from pydantic_core import Url
from pydantic_settings import BaseSettings
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


def _validate_env_redis_dsn(v: Url) -> Url:
    """Possibly adjust a Redis DSN based on environment variables.
    When run via tox and tox-docker, the Redis hostname and port will be
    randomly selected and exposed only in environment variables. We have to
    patch that into the Redis URL at runtime since `tox doesn't have a way of
    substituting it into the environment
    <https://github.com/tox-dev/tox-docker/issues/55>`__.
    """
    if port := os.getenv("REDIS_6379_TCP_PORT"):
        return Url.build(
            scheme=v.scheme,
            username=v.username,
            password=v.password,
            host=os.getenv("REDIS_HOST", v.unicode_host() or "localhost"),
            port=int(port),
            path=v.path.lstrip("/") if v.path else v.path,
            query=v.query,
            fragment=v.fragment,
        )
    else:
        return v


EnvRedisDsn: TypeAlias = Annotated[
    Url,
    UrlConstraints(
        allowed_schemes=["redis"],
        default_host="localhost",
        default_port=6379,
        default_path="/0",
    ),
    AfterValidator(_validate_env_redis_dsn),
]
"""Redis data source URL honoring Docker environment variables.

Unlike the standard Pydantic ``RedisDsn`` type, this does not support the
``rediss`` scheme, which indicates the use of TLS.
"""


class Config(BaseSettings):
    name: str = Field("spherexportal", validation_alias="SAFIR_NAME")

    profile: Profile = Field(
        Profile.production, validation_alias="SAFIR_PROFILE"
    )

    log_level: LogLevel = Field(
        LogLevel.INFO, validation_alias="SAFIR_LOG_LEVEL"
    )

    logger_name: str = Field("spherexportal", validation_alias="SAFIR_LOGGER")

    dataset_path: FilePath = Field(..., validation_alias="PORTAL_DATASET_PATH")

    ltd_api_url: HttpUrl = Field(
        HttpUrl("https://docs-api.ipac.caltech.edu/"),
        description="Root URL of the LTD API server.",
        validation_alias="PORTAL_LTD_API_URL",
    )

    ltd_organization: str = Field(
        "spherex",
        description="Organization name in the LTD API.",
        validation_alias="PORTAL_LTD_API_ORG",
    )

    ltd_api_username: str = Field(
        "spherex-portal",
        description="Username for LTD API",
        validation_alias="PORTAL_LTD_API_USERNAME",
    )

    ltd_api_password: SecretStr | None = Field(
        None,
        description="Password corresponding to ltd_api_username",
        validation_alias="PORTAL_LTD_API_PASSWORD",
    )

    # Ideally this should come from the LTD API, since the bucket's name is
    # declared there, but it's current absent. us-west-1 is where we're
    # deploying SPHEREx's LTD.
    s3_region: str = Field(
        "us-west-1",
        description="AWS region for the S3 bucket.",
        validation_alias="PORTAL_S3_REGION",
    )

    aws_access_key_id: str | None = Field(
        None,
        description="AWS access key ID; for getting metadata objects from S3.",
        validation_alias="PORTAL_AWS_ACCESS_KEY_ID",
    )

    aws_access_key_secret: SecretStr | None = Field(
        None,
        description=(
            "AWS access key secret; for getting metadata objects from S3."
        ),
        validation_alias="PORTAL_AWS_ACCESS_KEY_SECRET",
    )

    use_mock_data: bool = Field(
        True,
        description=(
            "Use the YAML dataset rather than obtaining metadata from live "
            "sources like LTD and S3"
        ),
        validation_alias="PORTAL_USE_MOCK_DATA",
    )

    redis_url: EnvRedisDsn = Field(
        Url("redis://localhost:6379/0"),
        description="URL of the Redis server.",
        validation_alias="PORTAL_REDIS_URL",
    )

    arq_redis_url: EnvRedisDsn = Field(
        Url("redis://localhost:6379/1"),
        description="URL of the Redis server for Arq.",
        validation_alias="PORTAL_ARQ_REDIS_URL",
    )

    arq_mode: ArqMode = Field(
        ArqMode.production, validation_alias="PORTAL_ARQ_MODE"
    )

    github_app_id: int | None = Field(
        None,
        validation_alias="PORTAL_GITHUB_APP_ID",
        description="GitHub App ID for the SPHEREx Doc Portal",
    )

    github_webhook_secret: SecretStr | None = Field(
        None,
        validation_alias="PORTAL_GITHUB_WEBHOOK_SECRET",
        description="GitHub webhook secret for the SPHEREx Doc Portal",
    )

    github_app_private_key: SecretStr | None = Field(
        None,
        validation_alias="PORTAL_GITHUB_APP_PRIVATE_KEY",
        description="GitHub App private key for the SPHEREx Doc Portal",
    )

    @property
    def arq_redis_settings(self) -> RedisSettings:
        """Create a Redis settings instance for arq."""
        url_parts = urlparse(str(self.arq_redis_url))
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
