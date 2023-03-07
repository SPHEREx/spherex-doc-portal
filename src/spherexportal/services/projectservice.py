from __future__ import annotations

from typing import Optional

import httpx
from spherexlander.parsers.pipelinemodule import (
    SpherexPipelineModuleMetadata as LanderSsdcMsModel,
)
from spherexlander.parsers.projectmanagement import (
    SpherexProjectManagementMetadata as LanderSsdcPmModel,
)
from spherexlander.parsers.spherexdata import ApprovalInfo
from spherexlander.parsers.spherexdata import (
    SpherexMetadata as BaseLanderMetadata,
)
from spherexlander.parsers.ssdcdp import (
    SpherexSsdcDpMetadata as LanderSsdcDpModel,
)
from spherexlander.parsers.ssdcif import (
    SpherexSsdcIfMetadata as LanderSsdcIfModel,
)
from spherexlander.parsers.ssdcop import (
    SpherexSsdcOpMetadata as LanderSsdcOpModel,
)
from spherexlander.parsers.ssdctn import (
    SpherexSsdcTnMetadata as LanderSsdcTnModel,
)
from spherexlander.parsers.ssdctr import (
    SpherexSsdcTrMetadata as LanderSsdcTrModel,
)
from structlog.stdlib import BoundLogger

from ..config import config
from ..domain import (
    GitHubIssueCount,
    SpherexDpDocument,
    SpherexIfDocument,
    SpherexMsDocument,
    SpherexOpDocument,
    SpherexPmDocument,
    SpherexTnDocument,
    SpherexTrDocument,
)
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
        if (
            config.aws_access_key_id is None
            or config.aws_access_key_secret is None
        ):
            raise RuntimeError(
                "PORTAL_AWS_ACCESS_KEY_ID and PORTAL_AWS_ACCESS_KEY_SECRET "
                "are needed to bootstrap metadata"
            )
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
                elif project.slug.startswith("ssdc-pm"):
                    await self._ingest_ssdc_pm(
                        bucket=bucket, project=project, org=org
                    )
                elif project.slug.startswith("ssdc-if"):
                    await self._ingest_ssdc_if(
                        bucket=bucket, project=project, org=org
                    )
                elif project.slug.startswith("ssdc-dp"):
                    await self._ingest_ssdc_dp(
                        bucket=bucket, project=project, org=org
                    )
                elif project.slug.startswith("ssdc-tr"):
                    await self._ingest_ssdc_tr(
                        bucket=bucket, project=project, org=org
                    )
                elif project.slug.startswith("ssdc-tn"):
                    await self._ingest_ssdc_tn(
                        bucket=bucket, project=project, org=org
                    )
                elif project.slug.startswith("ssdc-op"):
                    await self._ingest_ssdc_op(
                        bucket=bucket, project=project, org=org
                    )
            except MetadataError as e:
                self._logger.warning(
                    f"Could ingest metadata for {project.slug}", details=str(e)
                )
                continue

    def _format_lander_approval_str(
        self, approval: Optional[ApprovalInfo]
    ) -> Optional[str]:
        """Convert a ApprovalInfo from the SPHEREx Lander metadata model into
        a string with the approval date and name for display.
        """
        if approval is None:
            return None

        return f"{approval.date}, {approval.name}"

    def _get_ssdc_lead(self, lander_metadata: BaseLanderMetadata) -> str:
        for author in lander_metadata.authors:
            if author.role == "IPAC Lead":
                return author.name
        return ""

    def _get_spherex_lead(self, lander_metadata: BaseLanderMetadata) -> str:
        for author in lander_metadata.authors:
            if author.role == "SPHEREx Lead":
                return author.name
        return ""

    async def _ingest_ssdc_ms(
        self,
        *,
        bucket: Bucket,
        project: LtdProjectModel,
        org: LtdOrganizationModel,
    ) -> None:
        lander_metadata = await bucket.get_lander_metadata(
            project.slug, LanderSsdcMsModel
        )
        domain_model = SpherexMsDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
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
            ssdc_author_name=self._get_ssdc_lead(lander_metadata),
            project_contact_name=self._get_spherex_lead(lander_metadata),
            diagram_index=lander_metadata.diagram_index,
            # The pipeline level may actually be published as a string with
            # an L prefix
            pipeline_level=(
                lander_metadata.pipeline_level
                if isinstance(lander_metadata.pipeline_level, int)
                else lander_metadata.pipeline_level.lstrip("L")
            ),
            approval_str=self._format_lander_approval_str(
                lander_metadata.approval
            ),
            difficulty=str(lander_metadata.difficulty),
        )
        self._repo.ssdc_ms.upsert(domain_model)

    async def _ingest_ssdc_pm(
        self,
        *,
        bucket: Bucket,
        project: LtdProjectModel,
        org: LtdOrganizationModel,
    ) -> None:
        lander_metadata = await bucket.get_lander_metadata(
            project.slug, LanderSsdcPmModel
        )
        domain_model = SpherexPmDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
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
            ssdc_author_name=self._get_ssdc_lead(lander_metadata),
            approval_str=self._format_lander_approval_str(
                lander_metadata.approval
            ),
        )
        self._repo.ssdc_pm.upsert(domain_model)

    async def _ingest_ssdc_if(
        self,
        *,
        bucket: Bucket,
        project: LtdProjectModel,
        org: LtdOrganizationModel,
    ) -> None:
        lander_metadata = await bucket.get_lander_metadata(
            project.slug, LanderSsdcIfModel
        )
        domain_model = SpherexIfDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
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
            ssdc_author_name=self._get_ssdc_lead(lander_metadata),
            approval_str=self._format_lander_approval_str(
                lander_metadata.approval
            ),
            interface_partner_name=lander_metadata.interface_partner,
        )
        self._repo.ssdc_if.upsert(domain_model)

    async def _ingest_ssdc_dp(
        self,
        *,
        bucket: Bucket,
        project: LtdProjectModel,
        org: LtdOrganizationModel,
    ) -> None:
        lander_metadata = await bucket.get_lander_metadata(
            project.slug, LanderSsdcDpModel
        )
        domain_model = SpherexDpDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
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
            ssdc_author_name=self._get_ssdc_lead(lander_metadata),
            approval_str=self._format_lander_approval_str(
                lander_metadata.approval
            ),
        )
        self._repo.ssdc_dp.upsert(domain_model)

    async def _ingest_ssdc_tr(
        self,
        *,
        bucket: Bucket,
        project: LtdProjectModel,
        org: LtdOrganizationModel,
    ) -> None:
        lander_metadata = await bucket.get_lander_metadata(
            project.slug, LanderSsdcTrModel
        )
        domain_model = SpherexTrDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
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
            ssdc_author_name=self._get_ssdc_lead(lander_metadata),
            approval_str=self._format_lander_approval_str(
                lander_metadata.approval
            ),
            va_doors_id=lander_metadata.va_doors_id,
            req_doors_id=lander_metadata.req_doors_id,
            ipac_jira_id=lander_metadata.ipac_jira_id,
        )
        self._repo.ssdc_tr.upsert(domain_model)

    async def _ingest_ssdc_tn(
        self,
        *,
        bucket: Bucket,
        project: LtdProjectModel,
        org: LtdOrganizationModel,
    ) -> None:
        lander_metadata = await bucket.get_lander_metadata(
            project.slug, LanderSsdcTnModel
        )
        domain_model = SpherexTnDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
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
            ssdc_author_name=self._get_ssdc_lead(lander_metadata),
        )
        self._repo.ssdc_tn.upsert(domain_model)

    async def _ingest_ssdc_op(
        self,
        *,
        bucket: Bucket,
        project: LtdProjectModel,
        org: LtdOrganizationModel,
    ) -> None:
        lander_metadata = await bucket.get_lander_metadata(
            project.slug, LanderSsdcOpModel
        )
        domain_model = SpherexOpDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
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
            ssdc_author_name=self._get_ssdc_lead(lander_metadata),
        )
        self._repo.ssdc_op.upsert(domain_model)
