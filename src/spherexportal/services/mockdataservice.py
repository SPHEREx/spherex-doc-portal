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
    SpherexMsDocument,
)

__all__ = [
    "MockDataService",
    "MockDataModel",
    "SsdcMsModel",
]


class SsdcMsModel(BaseModel):
    """The ssdc-ms field."""

    handle: str
    title: str
    url: AnyHttpUrl
    issues: int
    prs: int
    tag: Optional[str]
    tag_date: datetime
    commit_date: datetime
    ssdc_author: str
    project_author: str
    diagram_index: str
    approval: Optional[str]
    difficulty: str


class MockDataModel(BaseModel):

    ssdc_ms: List[SsdcMsModel] = Field(..., alias="ssdc-ms")

    @classmethod
    def from_yaml(cls, path: Path) -> MockDataModel:
        data = yaml.safe_load(path.read_text())
        return cls.parse_obj(data)


class MockDataService:
    """A service for working with the mock datasets."""

    def __init__(self, mock_data: MockDataModel) -> None:
        self._data = mock_data

    @classmethod
    def load_builtin_data(cls) -> MockDataService:
        """Load the built-in dataset.example.yaml file."""
        path = Path(os.getenv("PORTAL_DATASET_PATH") or "dataset.example.yaml")
        data = MockDataModel.from_yaml(path)
        return cls(data)

    def load_ssdc_ms(self) -> SpherexCategory[SpherexMsDocument]:
        """Transform the example SSDC-MS data into the repository format."""
        projects: List[SpherexMsDocument] = []
        for mock_ssdcms in self._data.ssdc_ms:
            if mock_ssdcms.tag is not None:
                release = GitHubRelease(
                    tag=mock_ssdcms.tag, date_created=mock_ssdcms.tag_date
                )
            else:
                release = None
            doc = SpherexMsDocument(
                url=mock_ssdcms.url,
                series="SSDC-MS",
                handle=mock_ssdcms.handle,
                title=mock_ssdcms.title,
                project_id=mock_ssdcms.handle.lower(),
                organization_id="spherex",
                github_url=(
                    f"https://github.com/SPHEREx/{mock_ssdcms.handle.lower()}"
                ),
                github_issues=GitHubIssueCount(
                    open_issue_count=mock_ssdcms.issues,
                    open_pr_count=mock_ssdcms.prs,
                    issue_url=(
                        "https://github.com/SPHEREx/"
                        f"{mock_ssdcms.handle.lower()}/issues"
                    ),
                    pr_url=(
                        "https://github.com/SPHEREx/"
                        f"{mock_ssdcms.handle.lower()}/pulls"
                    ),
                ),
                github_release=release,
                latest_commit_datetime=mock_ssdcms.commit_date,
                ssdc_author_name=mock_ssdcms.ssdc_author,
                project_contact_name=mock_ssdcms.project_author,
                diagram_index=mock_ssdcms.diagram_index,
                approval_str=mock_ssdcms.approval,
                difficulty=mock_ssdcms.difficulty,
            )
            projects.append(doc)
        return SpherexCategory(projects=projects)
