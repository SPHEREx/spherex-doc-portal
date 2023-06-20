"""Additional models for GitHub API resources."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, validator
from safir.github.models import (
    GitHubRepositoryModel as GitHubRepositoryModelBase,
)
from safir.github.models import GitHubUserModel
from safir.pydantic import normalize_datetime


class GitHubReleaseModel(BaseModel):
    """A model for a GitHub Release resources.

    https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28#get-a-release
    or
    https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28#get-the-latest-release
    """

    url: str = Field(
        description="API URL of the release.",
    )

    html_url: str = Field(
        description="HTML URL of the release.",
    )

    assets_url: str = Field(
        description="API URL of the release assets.",
    )

    tarball_url: str = Field(
        description="URL of the release tarball.",
    )

    zipball_url: str = Field(
        description="URL of the release zipball.",
    )

    tag_name: str = Field(
        description="Name of the release tag.",
    )

    target_commitish: str = Field(
        description=(
            "Commitish value that determines where the Git tag is "
            "created from."
        )
    )

    name: str = Field(
        description="Name of the release (set by the release author)",
    )

    body: str = Field(
        description="Description of the release.",
    )

    draft: bool = Field(
        description="Whether the release is a draft.",
    )

    prerelease: bool = Field(
        description="Whether the release is a prerelease.",
    )

    created_at: datetime = Field(
        description="Time when the release was created.",
    )

    published_at: datetime = Field(
        description="Time when the release was published.",
    )

    author: GitHubUserModel = Field(
        description="User who created the release.",
    )

    @validator("created_at", "published_at", pre=True, allow_reuse=True)
    def normalize_datetime(cls, value: datetime) -> datetime:
        """Normalize datetime values."""
        d = normalize_datetime(value)
        if d is None:
            raise ValueError("Invalid datetime")
        return d


class GitHubRepositoryModel(GitHubRepositoryModelBase):
    """A model for a GitHub repository resource.

    https://docs.github.com/en/rest/reference/repos#get-a-repository
    """

    pushed_at: datetime = Field(
        description="API URL of the releases.",
    )

    @validator("pushed_at", pre=True, allow_reuse=True)
    def normalize_pushed_at(cls, value: datetime) -> datetime:
        """Normalize datetime values."""
        print("pushed_at", value, type(value))
        d = normalize_datetime(value)
        if d is None:
            raise ValueError("Invalid datetime")
        return d
