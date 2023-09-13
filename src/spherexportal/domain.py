"""Domain models for documentation project metadata."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, validator

approval_field = Field(
    None, description="Approval information for the document."
)

PROJECT_TIMEZONE = ZoneInfo("America/Los_Angeles")
"""Timezone to use for project times when displaying in the UI."""


def _ensure_timezone(dt: datetime) -> datetime:
    """Ensure that the datetime is timezone-aware in UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)

    return dt


class SpherexProject(BaseModel):
    """A generic SPHEREx documentation project hosted on
    spherex-docs.ipac.caltech.edu.
    """

    url: str = Field(..., description="Root HTML URL.")

    title: str = Field(..., description="Title of the documentation project.")

    project_id: str = Field(
        ..., description="ID of the project in the LTD API."
    )

    organization_id: str = Field(
        "spherex", description="ID of the organization in the LTD API."
    )


class GitHubIssueCount(BaseModel):
    """Summary info about GitHub issues."""

    open_issue_count: int = Field(
        ..., description="Number of open GitHub issues."
    )

    open_pr_count: int = Field(..., description="Number of open GitHub PRs.")

    issue_url: str = Field(
        ..., description="Base URL of the GitHub issue tracker."
    )

    pr_url: str = Field(..., description="Base URL of the GitHub PR tracker.")


class GitHubRelease(BaseModel):
    """Summary of the latest GitHub release."""

    tag: str = Field(..., description="Git tag.")
    """Git tag."""

    date_created: datetime = Field(
        ..., description="Times (UTC) when the release was created."
    )

    @property
    def formatted_date(self) -> str:
        """The formatted date of the release."""
        return self.date_created.astimezone(tz=PROJECT_TIMEZONE).strftime(
            "%Y-%m-%d"
        )

    _normalize_datetime = validator(
        "date_created", allow_reuse=True, pre=False
    )(_ensure_timezone)


class SpherexGitHubProject(SpherexProject):
    """A GitHub-based SPHEREx documentation project."""

    github_url: str = Field(
        ..., description="URL of the project's GitHub repo."
    )

    github_issues: GitHubIssueCount = Field(
        ..., description="Summary info about open GitHub issues and PRs."
    )

    latest_commit_datetime: datetime = Field(
        ...,
        description=(
            "Datetime of the latest commit to the default branch (UTC)."
        ),
    )

    github_release: Optional[GitHubRelease] = Field(
        None,
        description=(
            "Information about the latest GitHub release. None if a release "
            "isn't available."
        ),
    )

    @property
    def formatted_latest_commit_date(self) -> str:
        """The formatted date of the latest commit."""
        if self.github_release is not None:
            if self.latest_commit_datetime < self.github_release.date_created:
                return ""
        return self.latest_commit_datetime.astimezone(
            tz=PROJECT_TIMEZONE
        ).strftime("%Y-%m-%d")

    @property
    def sortable_latest_commit_date(self) -> str:
        """The sortable date of the latest commit."""
        return str(self.latest_commit_datetime.timestamp())

    @property
    def sortable_release_date(self) -> str:
        """The sortable date of the latest release."""
        if self.github_release is not None:
            return str(self.github_release.date_created.timestamp())
        return "0"

    _normalize_datetime = validator(
        "latest_commit_datetime", allow_reuse=True, pre=False
    )(_ensure_timezone)


class SpherexDocument(SpherexGitHubProject):
    """A general SPHEREx document."""

    series: str = Field(
        ..., description="The document series; typically the handle's prefix."
    )

    handle: str = Field(..., description="The document's handle.")

    ssdc_author_name: str = Field(
        ..., description="Name of the lead SSDC author."
    )


class SpherexMsDocument(SpherexDocument):
    """A SPHEREx Module Specification, SSDC-MS."""

    project_contact_name: str = Field(
        ..., description="Name of the project contact (SPHEREx POC)."
    )

    diagram_index: int = Field(..., description="The module's diagram index.")

    pipeline_level: int = Field(
        ..., description="The module's pipeline level."
    )

    approval_str: Optional[str] = approval_field

    difficulty: str = Field(..., description="The module's difficulty level.")

    @property
    def diagram_ref(self) -> str:
        """The displayable diagram reference for the module."""
        return f"L{self.pipeline_level}.{self.diagram_index}"

    @property
    def sortable_diagram_ref(self) -> str:
        """The sortable diagram reference (zero-padded) for the module."""
        return f"L{self.pipeline_level}.{self.diagram_index:02d}"


class SpherexPmDocument(SpherexDocument):
    """A SPHEREx Project Management, SSDC-PM."""

    approval_str: Optional[str] = approval_field


class SpherexIfDocument(SpherexDocument):
    """A SPHEREx Interface, SSDC-IF."""

    approval_str: Optional[str] = approval_field

    interface_partner_name: str = Field(
        ..., description="Name of the interface partner (institution)."
    )


class SpherexDpDocument(SpherexDocument):
    """A SPHEREx Interface, SSDC-DP."""

    approval_str: Optional[str] = approval_field


class SpherexTrDocument(SpherexDocument):
    """A SPHEREx Test Report, SSDC-TR."""

    approval_str: Optional[str] = approval_field

    va_doors_id: Optional[str] = Field(None, description="VA DOORS ID.")

    req_doors_id: Optional[str] = Field(None, description="REQ DOORS ID.")

    ipac_jira_id: Optional[str] = Field(None, description="IPAC JIRA ID.")

    @property
    def has_verification_ids(self) -> bool:
        """Flag indicating whether the document has any verification IDs."""
        return (
            (self.va_doors_id is not None)
            | (self.req_doors_id is not None)
            | (self.ipac_jira_id is not None)
        )

    @property
    def ipac_jira_url(self) -> str:
        """The URL of the IPAC JIRA ticket, or an empty string if none is
        available.
        """
        if self.ipac_jira_id:
            return f"https://jira.ipac.caltech.edu/browse/{self.ipac_jira_id}"
        else:
            return ""


class SpherexTnDocument(SpherexDocument):
    """A SPHEREx Technical Note, SSDC-TN."""


class SpherexOpDocument(SpherexDocument):
    """A SPHEREx Operations Note, SSDC-OP."""


class SpherexGitHubSoftwareProject(BaseModel):
    """A GitHub-based SPHEREx software project.

    This project may or may not have an associated LTD-deployed documentation
    project. However, if the URL in the project's GitHub metadata matches
    a LTD URL, the repository can be correlated with LTD.
    """

    github_url: str = Field(
        ..., description="URL of the project's GitHub repo (`html_url`)."
    )

    github_owner: str = Field(
        ..., description="GitHub owner (user or organization)."
    )

    github_repo: str = Field(..., description="GitHub repository name.")

    documentation_url: Optional[str] = Field(
        None,
        description=(
            "URL of the project's documentation, based on GitHub metadata."
        ),
    )

    description: str = Field(..., description="Description of the project.")

    github_topics: list[str] = Field(
        description="List of GitHub topics for the repository.",
        default_factory=list,
    )

    github_issues: GitHubIssueCount = Field(
        ..., description="Summary info about open GitHub issues and PRs."
    )

    latest_commit_datetime: datetime = Field(
        ...,
        description=(
            "Datetime of the latest commit to the default branch (UTC)."
        ),
    )

    github_release: Optional[GitHubRelease] = Field(
        None,
        description=(
            "Information about the latest GitHub release. None if a release "
            "isn't available."
        ),
    )

    @property
    def formatted_latest_commit_date(self) -> str:
        """The formatted date of the latest commit."""
        if self.github_release is not None:
            if self.latest_commit_datetime < self.github_release.date_created:
                return ""
        return self.latest_commit_datetime.astimezone(
            tz=PROJECT_TIMEZONE
        ).strftime("%Y-%m-%d")

    @property
    def sortable_latest_commit_date(self) -> str:
        """The sortable date of the latest commit."""
        return str(self.latest_commit_datetime.timestamp())

    @property
    def sortable_release_date(self) -> str:
        """The sortable date of the latest release."""
        if self.github_release is not None:
            return str(self.github_release.date_created.timestamp())
        return "0"
