"""Domain models for documentation project metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

approval_field = Field(
    None, description="Approval information for the document."
)


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


T = TypeVar("T", bound="SpherexProject")


@dataclass(kw_only=True)
class SpherexCategory(Generic[T]):
    """A collection of SpherexProject items for a specific category."""

    projects: List[T] = field(default_factory=list)

    def upsert(self, project: T) -> None:
        """Append a new project or replace an existing project with the new
        data.

        Projects are assessed to be matching based on a``project_id`` and
        ``organization_id``.
        """
        for i, existing_project in enumerate(self.projects):
            if (existing_project.project_id == project.project_id) and (
                existing_project.organization_id == project.organization_id
            ):
                self.projects[i] = project
                return

        # Only if there isn't a match
        self.projects.append(project)
