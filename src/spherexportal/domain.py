"""Domain models for documentation project metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(kw_only=True)
class SpherexProject:
    """A generic SPHEREx documentation project hosted on
    spherex-docs.ipac.caltech.edu.
    """

    url: str
    """Root HTML URL."""

    title: str
    """The title of the documentation project."""

    project_id: str
    """ID of the project in the LTD API."""

    organization_id: str = "spherex"
    """ID of the organization in the LTD API."""


@dataclass(kw_only=True)
class GitHubIssueCount:
    """Summary info about GitHub issues."""

    open_issue_count: int

    open_pr_count: int

    issue_url: str

    pr_url: str


@dataclass(kw_only=True)
class GitHubRelease:
    """Summary of the latest GitHub release."""

    tag: str
    """Git tag."""

    date_created: datetime
    """Time (UTC) when the release was created."""


@dataclass(kw_only=True)
class SpherexGitHubProject(SpherexProject):
    """A GitHub-based SPHEREx documentation project."""

    github_url: str
    """URL of the project's GitHub repository."""

    github_issues: GitHubIssueCount
    """Summary info about open GitHub issues and PRs."""

    latest_commit_datetime: datetime
    """The datetime (with a UTC timezone) of the latest commit to the default
    branch on GitHub.
    """

    github_release: Optional[GitHubRelease]
    """Information about the current GitHub release, or None if a release
    isn't available.
    """


@dataclass(kw_only=True)
class SpherexDocument(SpherexGitHubProject):
    """A general SPHEREx document."""

    series: str
    """The document series; typically the handle's prefix."""

    handle: str
    """The document's identifier."""

    ssdc_author_name: str
    """Name of the lead SSDC author."""


@dataclass(kw_only=True)
class SpherexMsDocument(SpherexDocument):
    """A SPHEREx Module Specification, SSDC-MS."""

    project_contact_name: str

    diagram_index: str

    approval_str: Optional[str] = None

    difficulty: str


@dataclass(kw_only=True)
class SpherexPmDocument(SpherexDocument):
    """A SPHEREx Project Management, SSDC-PM."""

    approval_str: Optional[str] = None


@dataclass(kw_only=True)
class SpherexIfDocument(SpherexDocument):
    """A SPHEREx Interface, SSDC-IF."""

    approval_str: Optional[str] = None

    interface_partner_name: str


@dataclass(kw_only=True)
class SpherexDpDocument(SpherexDocument):
    """A SPHEREx Interface, SSDC-DP."""

    approval_str: Optional[str] = None


@dataclass(kw_only=True)
class SpherexTrDocument(SpherexDocument):
    """A SPHEREx Test Report, SSDC-TR."""

    verification_ids: List[str]

    approval_str: Optional[str] = None
