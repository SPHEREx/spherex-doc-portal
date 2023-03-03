"""Configuration definition."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseSettings, Field, FilePath, HttpUrl, SecretStr

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
        "https://docs-api.ipac.caltech.edu",
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

    ltd_api_password: Optional[SecretStr] = Field(
        None,
        description="Password corresponding to ltd_api_username",
        env="PORTAL_LTD_API_PASSWORD",
    )


config = Config()
"""Configuration for the spherex-doc-portal."""
