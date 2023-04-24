"""LTD API client for accessing metadata available in the LTD database."""

from __future__ import annotations

import datetime
import urllib.parse
from typing import Optional

from asyncache import cached
from cachetools import TTLCache
from httpx import AsyncClient
from pydantic import BaseModel, HttpUrl

from spherexportal.config import config


class LtdEditionModel(BaseModel):
    """A model for the edition resource."""

    self_url: HttpUrl
    """The URL of the edition resource."""

    organization_url: HttpUrl
    """The URL of the organization resource."""

    project_url: HttpUrl
    """The URL or the edition's associated project resource."""

    build_url: Optional[HttpUrl]
    """The URL or the build's associated product resource. This is null if
    the edition doesn't have a build yet.
    """

    queue_url: Optional[HttpUrl]
    """The URL of any queued task resource."""

    published_url: HttpUrl
    """The web URL for this edition."""

    slug: str
    """The edition's URL-safe slug."""

    title: str
    """The edition's title."""

    date_created: datetime.datetime
    """The date when the build was created (UTC)."""

    date_rebuilt: datetime.datetime
    """The date when associated build was last updated (UTC)."""

    date_ended: Optional[datetime.datetime]
    """The date when the build was created (UTC). Is null if the edition
    has not been deleted.
    """

    surrogate_key: str
    """The surrogate key attached to the headers of all files on S3 belonging
    to this edition. This allows LTD Keeper to notify Fastly when an Edition is
    being re-pointed to a new build. The client is responsible for uploading
    files with this value as the ``x-amz-meta-surrogate-key`` value.
    """

    pending_rebuild: bool
    """Flag indicating if the edition is currently being rebuilt with a new
    build.
    """

    tracked_ref: Optional[str]
    """Git ref that describe the version that this Edition is intended to point
    to when using the ``git_ref`` tracking mode.
    """

    mode: str
    """The edition tracking mode."""


class LtdProjectModel(BaseModel):
    """The project resource."""

    self_url: HttpUrl
    """The URL of the project resource."""

    organization_url: HttpUrl
    """The URL of the organization resource."""

    builds_url: HttpUrl
    """The URL of the project's build resources."""

    editions_url: HttpUrl
    """The URL of the project's edition resources."""

    task_url: Optional[HttpUrl]
    """The URL of async task created by the request, if any."""

    slug: str
    """URL/path-safe identifier for this project (unique within an
    organization).
    """

    source_repo_url: HttpUrl
    """URL of the associated source repository (GitHub homepage)."""

    title: str
    """Title of this project."""

    published_url: HttpUrl
    """URL where this project's default edition is published on the web."""

    surrogate_key: str
    """surrogate_key for Fastly quick purges of dashboards.
    Editions and Builds have independent surrogate keys.
    """

    default_edition: LtdEditionModel
    """The default edition."""


class LtdOrganizationModel(BaseModel):
    """A model for the organization resource."""

    slug: str
    """Identifier for this organization in the API."""

    title: str
    """Presentational name of this organization."""

    layout: str
    """The layout mode."""

    domain: str
    """Domain name serving the documentation."""

    path_prefix: str
    """The path prefix where documentation is served."""

    fastly_support: bool
    """Flag indicating is Fastly CDN support is enabled."""

    fastly_domain: Optional[HttpUrl]
    """The Fastly CDN domain name."""

    fastly_service_id: Optional[str]
    """The Fastly service ID."""

    s3_bucket: Optional[str]
    """Name of the S3 bucket hosting builds."""

    s3_public_read: bool
    """Whether objects in the S3 bucket have a public-read ACL applied or
    not.
    """

    aws_region: str
    """Name of the AWS region for the S3 bucket."""

    self_url: HttpUrl
    """The URL of the organization response."""

    projects_url: HttpUrl
    """The URL for the organization's projects."""


class LtdApi:
    """LTD API client for accessing project metadata."""

    def __init__(self, http_client: AsyncClient) -> None:
        self._http_client = http_client

    def url_for_path(self, path: str) -> str:
        """Get the URL for a given API path."""
        url_parts = urllib.parse.urlparse(str(config.ltd_api_url))
        return url_parts._replace(path=path).geturl()

    @cached(TTLCache(1024, 600))
    async def get_auth_token(self, username: str, password: str) -> str:
        """Get the LTD API auth token."""
        url = self.url_for_path("/token")
        response = await self._http_client.get(url, auth=(username, password))
        response.raise_for_status()
        data = response.json()
        return data["token"]

    async def get_projects(self) -> list[LtdProjectModel]:
        """Get all projects from the LTD API for the organization."""
        url = self.url_for_path(f"/v2/orgs/{config.ltd_organization}/projects")
        if config.ltd_api_password is None:
            raise RuntimeError("Configure PORTAL_LTD_API_USERNAME")
        token = await self.get_auth_token(
            config.ltd_api_username, config.ltd_api_password.get_secret_value()
        )
        response = await self._http_client.get(url, auth=(token, ""))
        response.raise_for_status()
        data = response.json()
        projects = [LtdProjectModel.parse_obj(p) for p in data]
        return projects

    async def get_organization(self) -> LtdOrganizationModel:
        """Get the SPHEREx organization."""
        url = self.url_for_path(f"/v2/orgs/{config.ltd_organization}")
        if config.ltd_api_password is None:
            raise RuntimeError("Configure PORTAL_LTD_API_USERNAME")
        token = await self.get_auth_token(
            config.ltd_api_username, config.ltd_api_password.get_secret_value()
        )
        response = await self._http_client.get(url, auth=(token, ""))
        response.raise_for_status()
        return LtdOrganizationModel.parse_obj(response.json())
