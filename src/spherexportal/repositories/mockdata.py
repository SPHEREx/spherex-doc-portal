"""Service for accessing mock/test data of repo collections."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import AnyHttpUrl, BaseModel, Field

from ..domain import (
    GitHubIssueCount,
    GitHubRelease,
    SpherexCategory,
    SpherexDpDocument,
    SpherexIfDocument,
    SpherexMsDocument,
    SpherexPmDocument,
    SpherexTrDocument,
)
from .projects import ProjectRepository

__all__ = [
    "MockDataRepository",
    "MockDataModel",
    "SsdcMsModel",
]


class BaseProjectModel(BaseModel):
    """Common attributes for all projects."""

    title: str
    project_id: str
    organization_id: str = "spherex"

    @property
    def url(self) -> str:
        return f"https://spherex-docs.ipac.caltech.edu/{self.project_id}"


class BaseGitHubProjectModel(BaseProjectModel):

    github_url: AnyHttpUrl
    issues: int
    prs: int
    commit_date: datetime
    tag: Optional[str]
    tag_date: Optional[datetime]

    @property
    def github_issues(self) -> GitHubIssueCount:
        github_url = self.github_url.rstrip("/")
        return GitHubIssueCount(
            open_issue_count=self.issues,
            open_pr_count=self.prs,
            issue_url=f"{github_url}/issues",
            pr_url=f"{github_url}/pulls",
        )

    @property
    def github_release(self) -> Optional[GitHubRelease]:
        if self.tag is not None and self.tag_date is not None:
            return GitHubRelease(tag=self.tag, date_created=self.tag_date)
        else:
            return None


class BaseSpherexDocumentModel(BaseGitHubProjectModel):

    handle: str
    commit_date: datetime
    ssdc_author: str


class SsdcMsModel(BaseSpherexDocumentModel):
    """The ssdc-ms field in the MockDataModel."""

    project_author: str
    approval: Optional[str]
    difficulty: str
    pipeline_level: int
    diagram_index: int

    @property
    def domain_model(self) -> SpherexMsDocument:
        """Export as a domain model."""
        return SpherexMsDocument(
            url=self.url,
            series="SSDC-MS",
            handle=self.handle,
            title=self.title,
            project_id=self.project_id,
            organization_id="spherex",
            github_url=self.github_url,
            github_issues=self.github_issues,
            github_release=self.github_release,
            latest_commit_datetime=self.commit_date,
            ssdc_author_name=self.ssdc_author,
            project_contact_name=self.project_author,
            pipeline_level=self.pipeline_level,
            diagram_index=self.diagram_index,
            approval_str=self.approval,
            difficulty=self.difficulty,
        )


class SsdcPmModel(BaseSpherexDocumentModel):
    """The ssdc-pm field in the MockDataModel."""

    approval: Optional[str]

    @property
    def domain_model(self) -> SpherexPmDocument:
        """Export as a domain model."""
        return SpherexPmDocument(
            url=self.url,
            series="SSDC-PM",
            handle=self.handle,
            title=self.title,
            project_id=self.project_id,
            organization_id="spherex",
            github_url=self.github_url,
            github_issues=self.github_issues,
            github_release=self.github_release,
            latest_commit_datetime=self.commit_date,
            ssdc_author_name=self.ssdc_author,
            approval_str=self.approval,
        )


class SsdcIfModel(BaseSpherexDocumentModel):
    """The ssdc-if field in the MockDataModel."""

    approval: Optional[str]

    interface_partner: str

    @property
    def domain_model(self) -> SpherexIfDocument:
        """Export as a domain model."""
        return SpherexIfDocument(
            url=self.url,
            series="SSDC-IF",
            handle=self.handle,
            title=self.title,
            project_id=self.project_id,
            organization_id="spherex",
            github_url=self.github_url,
            github_issues=self.github_issues,
            github_release=self.github_release,
            latest_commit_datetime=self.commit_date,
            ssdc_author_name=self.ssdc_author,
            approval_str=self.approval,
            interface_partner_name=self.interface_partner,
        )


class SsdcDpModel(BaseSpherexDocumentModel):
    """The ssdc-dp field in the MockDataModel."""

    approval: Optional[str]

    @property
    def domain_model(self) -> SpherexDpDocument:
        """Export as a domain model."""
        return SpherexDpDocument(
            url=self.url,
            series="SSDC-IF",
            handle=self.handle,
            title=self.title,
            project_id=self.project_id,
            organization_id="spherex",
            github_url=self.github_url,
            github_issues=self.github_issues,
            github_release=self.github_release,
            latest_commit_datetime=self.commit_date,
            ssdc_author_name=self.ssdc_author,
            approval_str=self.approval,
        )


class SsdcTrModel(BaseSpherexDocumentModel):
    """The ssdc-tr field in the MockDataModel."""

    approval: Optional[str]

    va_doors_id: Optional[str] = None

    req_doors_id: Optional[str] = None

    ipac_jira_id: Optional[str] = None

    @property
    def domain_model(self) -> SpherexTrDocument:
        """Export as a domain model."""
        return SpherexTrDocument(
            url=self.url,
            series="SSDC-TR",
            handle=self.handle,
            title=self.title,
            project_id=self.project_id,
            organization_id="spherex",
            github_url=self.github_url,
            github_issues=self.github_issues,
            github_release=self.github_release,
            latest_commit_datetime=self.commit_date,
            ssdc_author_name=self.ssdc_author,
            approval_str=self.approval,
            va_doors_id=self.va_doors_id,
            req_doors_id=self.req_doors_id,
            ipac_jira_id=self.ipac_jira_id,
        )


class MockDataModel(BaseModel):
    """A Pydantic model for the YAML mock dataset."""

    ssdc_ms: List[SsdcMsModel] = Field(alias="ssdc-ms", default_factory=list)

    ssdc_pm: List[SsdcPmModel] = Field(alias="ssdc-pm", default_factory=list)

    ssdc_if: List[SsdcIfModel] = Field(alias="ssdc-if", default_factory=list)

    ssdc_dp: List[SsdcDpModel] = Field(alias="ssdc-dp", default_factory=list)

    ssdc_tr: List[SsdcTrModel] = Field(alias="ssdc-tr", default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> MockDataModel:
        data = yaml.safe_load(path.read_text())
        return cls.parse_obj(data)

    @property
    def ssdc_ms_projects(self) -> SpherexCategory[SpherexMsDocument]:
        return SpherexCategory(
            projects=[doc.domain_model for doc in self.ssdc_ms]
        )

    @property
    def ssdc_pm_projects(self) -> SpherexCategory[SpherexPmDocument]:
        return SpherexCategory(
            projects=[doc.domain_model for doc in self.ssdc_pm]
        )

    @property
    def ssdc_if_projects(self) -> SpherexCategory[SpherexIfDocument]:
        return SpherexCategory(
            projects=[doc.domain_model for doc in self.ssdc_if]
        )

    @property
    def ssdc_dp_projects(self) -> SpherexCategory[SpherexDpDocument]:
        return SpherexCategory(
            projects=[doc.domain_model for doc in self.ssdc_dp]
        )

    @property
    def ssdc_tr_projects(self) -> SpherexCategory[SpherexTrDocument]:
        return SpherexCategory(
            projects=[doc.domain_model for doc in self.ssdc_tr]
        )


class MockDataRepository:
    """A repository that loads mock project data from a YAML file for testing.

    See ``load_builtin_data`` to create a MockDataRepository from a file.
    """

    def __init__(self, mock_data: MockDataModel) -> None:
        self._data = mock_data

    @classmethod
    def load_builtin_data(cls) -> MockDataRepository:
        """Load the built-in dataset.example.yaml file.

        If the ``PORTAL_DATASET_PATH`` environment variable is set, that path
        is used instead.
        """
        path = Path(os.getenv("PORTAL_DATASET_PATH") or "dataset.example.yaml")
        data = MockDataModel.from_yaml(path)
        return cls(data)

    def bootstrap_project_repository(self, repo: ProjectRepository) -> None:
        """Add mock data to the `ProjectRepository`."""
        repo.ssdc_ms = self._data.ssdc_ms_projects
        repo.ssdc_pm = self._data.ssdc_pm_projects
        repo.ssdc_if = self._data.ssdc_if_projects
        repo.ssdc_dp = self._data.ssdc_dp_projects
        repo.ssdc_tr = self._data.ssdc_tr_projects
