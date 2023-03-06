from __future__ import annotations

import httpx
from structlog.stdlib import BoundLogger

from ..config import config
from ..domain import GitHubIssueCount, SpherexMsDocument
from ..repositories.ltdapi import LtdApi, LtdOrganizationModel, LtdProjectModel
from ..repositories.mockdata import MockDataRepository
from ..repositories.projects import ProjectRepository
from ..repositories.s3metadata import Bucket, MetadataError


class ProjectService:
    """Service for working with the project metadata repository."""

    def __init__(
        self,
        repo: ProjectRepository,
        logger: BoundLogger,
        http_client: httpx.AsyncClient,
    ) -> None:
        self._logger = logger
        self._repo = repo
        self._http_client = http_client

    async def bootstrap_mock_repo(self) -> None:
        mockdata_repo = MockDataRepository.load_builtin_data()
        mockdata_repo.bootstrap_project_repository(self._repo)

    async def bootstrap_from_api(self) -> None:
        """Bootstrap the project repository using data from the LTD API."""
        ltd_client = LtdApi(self._http_client)
        org = await ltd_client.get_organization()
        bucket = Bucket(
            bucket=org.s3_bucket or "spherex-docs",  # default for sPHEREx
            region=config.s3_region,
            access_key_id=config.aws_access_key_id,
            secret_access_key=config.aws_access_key_secret.get_secret_value(),
            http_client=self._http_client,
        )

        projects = await ltd_client.get_projects()
        for project in projects:
            try:
                if project.slug.startswith("ssdc-ms"):
                    await self._ingest_ssdc_ms(
                        bucket=bucket, project=project, org=org
                    )
            except MetadataError as e:
                self._logger.warning(
                    f"Could ingest metadata for {project.slug}", details=str(e)
                )
                continue

    async def _ingest_ssdc_ms(
        self,
        *,
        bucket: Bucket,
        project: LtdProjectModel,
        org: LtdOrganizationModel,
    ) -> None:
        lander_metadata = await bucket.get_ssdc_ms_metadata(project.slug)
        domain_model = SpherexMsDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix(),
            handle=lander_metadata.identifier,
            title=lander_metadata.title,
            project_id=project.slug,
            organization_id=org.slug,
            github_url=lander_metadata.repository_url,
            github_issues=GitHubIssueCount(
                open_issue_count=0,
                open_pr_count=0,
                issue_url=f"{lander_metadata.repository_url}/issues",
                pr_url=f"{lander_metadata.repository_url}/pulls",
            ),
            github_release=None,
            latest_commit_datetime=project.default_edition.date_rebuilt,
            ssdc_author_name=(
                lander_metadata.ipac_lead.name
                if lander_metadata.ipac_lead
                else "N/A"
            ),
            project_contact_name=(
                lander_metadata.spherex_lead.name
                if lander_metadata.spherex_lead
                else "N/A"
            ),
            diagram_index=lander_metadata.diagram_index,
            pipeline_level=lander_metadata.pipeline_level,
            difficulty=str(lander_metadata.difficulty),
        )
        self._repo.ssdc_ms.upsert(domain_model)
