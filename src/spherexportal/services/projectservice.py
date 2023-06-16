from __future__ import annotations

from datetime import datetime
from typing import Optional

import httpx
from gidgethub.httpx import GitHubAPI
from safir.github import GitHubAppClientFactory

# from safir.github.models import GitHubRepositoryModel
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

from spherexportal.githubapi import GitHubReleaseModel, GitHubRepositoryModel

from ..config import config
from ..domain import (
    GitHubIssueCount,
    GitHubRelease,
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

        self._github_factory: GitHubAppClientFactory | None = None
        if (
            config.github_app_id is not None
            and config.github_app_private_key is not None
        ):
            self._github_factory = GitHubAppClientFactory(
                id=config.github_app_id,
                key=config.github_app_private_key.get_secret_value(),
                name="SPHEREx/spherex-doc-portal",
                http_client=http_client,
            )
        else:
            self._logger.info("GitHub App client factory not configured")
        self._installed_repos: list[str] = []

    async def bootstrap_mock_repo(self) -> None:
        mockdata_repo = MockDataRepository.load_builtin_data()
        await mockdata_repo.bootstrap_project_repository(self._repo)

    async def bootstrap_from_api(self) -> None:
        """Bootstrap the project repository using data from the LTD API."""
        if self._github_factory is not None:
            app_client = self._github_factory.create_app_client()
            installed_repos: list[str] = []
            async for repo in app_client.getiter(
                "/installation/repositories", iterable_key="repositories"
            ):
                installed_repos.append(repo["full_name"])
            self._logger.info(
                "GitHub App is installed in repos", repos=installed_repos
            )
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
            bucket=org.s3_bucket or "spherex-docs",  # default for SPHEREx
            region=config.s3_region,
            access_key_id=config.aws_access_key_id,
            secret_access_key=config.aws_access_key_secret.get_secret_value(),
            http_client=self._http_client,
        )

        projects = await ltd_client.get_projects()
        for project in projects:
            await self._ingest_project(
                bucket=bucket,
                project=project,
                org=org,
            )

    def _parse_github_repo_url(self, repo_url: str) -> tuple[str, str]:
        owner, repo = repo_url[:19].split("/")[:2]
        if repo.endswith(".git"):
            repo = repo[:-4]
        elif repo.endswith(".git/"):
            repo = repo[:-5]
        return owner, repo

    async def _create_github_repo_client(
        self, repo_url: Optional[str] = None
    ) -> GitHubAPI | None:
        if repo_url is None:
            self._logger.debug("No repo URL provided")
            return None
        if self._github_factory is None:
            return None
        if not repo_url.startswith("https://github.com/"):
            return None
        owner, repo = self._parse_github_repo_url(repo_url)
        try:
            return (
                await self._github_factory.create_installation_client_for_repo(
                    owner=owner,
                    repo=repo,
                )
            )
        except Exception as exc:
            self._logger.warning(
                "Failed to create GitHub client for repo",
                repo_url=repo_url,
                exc_info=exc,
            )
            return None

    async def _get_github_repository(
        self, repo_url: str, github_client: GitHubAPI
    ) -> GitHubRepositoryModel:
        owner, repo = self._parse_github_repo_url(repo_url)
        api_url = f"/repos/{owner}/{repo}"
        data = await github_client.getitem(
            api_url, url_vars={"owner": owner, "repo": repo}
        )
        return GitHubRepositoryModel.parse_obj(data)

    async def _get_github_issue_count(
        self, *, client: GitHubAPI, repo: GitHubRepositoryModel
    ) -> GitHubIssueCount:
        api_url = "/repos/{owner}/{repo}/issues?state=open"
        issue_count = 0
        pr_count = 0
        async for issue_data in client.getiter(
            api_url, url_vars={"owner": repo.owner.login, "repo": repo.name}
        ):
            if "pull_request" in issue_data:
                pr_count += 1
            else:
                issue_count += 1

        return GitHubIssueCount(
            open_issue_count=0,
            open_pr_count=0,
            issue_url=(
                f"https://github.com/{repo.owner.login}/{repo.name}/issues"
            ),
            pr_url=f"https://github.com/{repo.owner.login}/{repo.name}/pulls",
        )

    async def _get_github_release(
        self, *, client: GitHubAPI, repo: GitHubRepositoryModel
    ) -> GitHubRelease:
        api_url = "/repos/{owner}/{repo}/releases/latest"
        data = await client.getitem(
            api_url, url_vars={"owner": repo.owner.login, "repo": repo.name}
        )
        release_model = GitHubReleaseModel.parse_obj(data)

        return GitHubRelease(
            tag=release_model.tag_name,
            date_created=release_model.published_at,
        )

    async def _get_common_github_metadata(
        self, repository_url: str, default_updated_datetime: datetime
    ) -> tuple[GitHubIssueCount, GitHubRelease | None, datetime]:
        self._logger.debug("Getting GitHub metadata", repo_url=repository_url)
        github_installation_client = await self._create_github_repo_client(
            repo_url=repository_url
        )
        if github_installation_client is None:
            self._logger.debug(
                "No GitHub client available for repository",
                repo_url=repository_url,
            )

        # Defaults for GitHub-based metadata
        github_issues: GitHubIssueCount = GitHubIssueCount(
            open_issue_count=0,
            open_pr_count=0,
            issue_url=f"{repository_url}/issues",
            pr_url=f"{repository_url}/pulls",
        )
        github_release: GitHubRelease | None = None
        commit_date = default_updated_datetime

        if github_installation_client is not None:
            repo_data = await self._get_github_repository(
                repository_url, github_installation_client
            )
            github_issues = await self._get_github_issue_count(
                client=github_installation_client,
                repo=repo_data,
            )
            github_release = await self._get_github_release(
                client=github_installation_client,
                repo=repo_data,
            )
            commit_date = repo_data.pushed_at
            self._logger.debug(
                "Got GitHub metadata",
                repo_url=repository_url,
                github_issues=github_issues,
                github_release=github_release,
                commit_date=commit_date,
            )

        return github_issues, github_release, commit_date

    async def _ingest_project(
        self,
        *,
        bucket: Bucket,
        project: LtdProjectModel,
        org: LtdOrganizationModel,
    ) -> None:
        """Ingest a project from the LTD API."""

        try:
            if project.slug.startswith("ssdc-ms"):
                await self._ingest_ssdc_ms(
                    bucket=bucket,
                    project=project,
                    org=org,
                )
            elif project.slug.startswith("ssdc-pm"):
                await self._ingest_ssdc_pm(
                    bucket=bucket,
                    project=project,
                    org=org,
                )
            elif project.slug.startswith("ssdc-if"):
                await self._ingest_ssdc_if(
                    bucket=bucket,
                    project=project,
                    org=org,
                )
            elif project.slug.startswith("ssdc-dp"):
                await self._ingest_ssdc_dp(
                    bucket=bucket,
                    project=project,
                    org=org,
                )
            elif project.slug.startswith("ssdc-tr"):
                await self._ingest_ssdc_tr(
                    bucket=bucket,
                    project=project,
                    org=org,
                )
            elif project.slug.startswith("ssdc-tn"):
                await self._ingest_ssdc_tn(
                    bucket=bucket,
                    project=project,
                    org=org,
                )
            elif project.slug.startswith("ssdc-op"):
                await self._ingest_ssdc_op(
                    bucket=bucket,
                    project=project,
                    org=org,
                )
        except MetadataError as e:
            self._logger.warning(
                f"Could not ingest metadata for {project.slug}",
                details=str(e),
            )

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

        (
            github_issues,
            github_release,
            github_date_updated,
        ) = await self._get_common_github_metadata(
            lander_metadata.repository_url,
            default_updated_datetime=project.default_edition.date_rebuilt,
        )

        domain_model = SpherexMsDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
            handle=lander_metadata.identifier,
            title=lander_metadata.title,
            project_id=project.slug,
            organization_id=org.slug,
            github_url=lander_metadata.repository_url,
            github_issues=github_issues,
            github_release=github_release,
            latest_commit_datetime=github_date_updated,
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
        await self._repo.ssdc_ms.upsert(domain_model)

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

        (
            github_issues,
            github_release,
            github_date_updated,
        ) = await self._get_common_github_metadata(
            lander_metadata.repository_url,
            default_updated_datetime=project.default_edition.date_rebuilt,
        )

        domain_model = SpherexPmDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
            handle=lander_metadata.identifier,
            title=lander_metadata.title,
            project_id=project.slug,
            organization_id=org.slug,
            github_url=lander_metadata.repository_url,
            github_issues=github_issues,
            github_release=github_release,
            latest_commit_datetime=github_date_updated,
            ssdc_author_name=self._get_ssdc_lead(lander_metadata),
            approval_str=self._format_lander_approval_str(
                lander_metadata.approval
            ),
        )
        await self._repo.ssdc_pm.upsert(domain_model)

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

        (
            github_issues,
            github_release,
            github_date_updated,
        ) = await self._get_common_github_metadata(
            lander_metadata.repository_url,
            default_updated_datetime=project.default_edition.date_rebuilt,
        )

        domain_model = SpherexIfDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
            handle=lander_metadata.identifier,
            title=lander_metadata.title,
            project_id=project.slug,
            organization_id=org.slug,
            github_url=lander_metadata.repository_url,
            github_issues=github_issues,
            github_release=github_release,
            latest_commit_datetime=project.default_edition.date_rebuilt,
            ssdc_author_name=self._get_ssdc_lead(lander_metadata),
            approval_str=self._format_lander_approval_str(
                lander_metadata.approval
            ),
            interface_partner_name=lander_metadata.interface_partner,
        )
        await self._repo.ssdc_if.upsert(domain_model)

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

        (
            github_issues,
            github_release,
            github_date_updated,
        ) = await self._get_common_github_metadata(
            lander_metadata.repository_url,
            default_updated_datetime=project.default_edition.date_rebuilt,
        )

        domain_model = SpherexDpDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
            handle=lander_metadata.identifier,
            title=lander_metadata.title,
            project_id=project.slug,
            organization_id=org.slug,
            github_url=lander_metadata.repository_url,
            github_issues=github_issues,
            github_release=github_release,
            latest_commit_datetime=github_date_updated,
            ssdc_author_name=self._get_ssdc_lead(lander_metadata),
            approval_str=self._format_lander_approval_str(
                lander_metadata.approval
            ),
        )
        await self._repo.ssdc_dp.upsert(domain_model)

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

        (
            github_issues,
            github_release,
            github_date_updated,
        ) = await self._get_common_github_metadata(
            lander_metadata.repository_url,
            default_updated_datetime=project.default_edition.date_rebuilt,
        )

        domain_model = SpherexTrDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
            handle=lander_metadata.identifier,
            title=lander_metadata.title,
            project_id=project.slug,
            organization_id=org.slug,
            github_url=lander_metadata.repository_url,
            github_issues=github_issues,
            github_release=github_release,
            latest_commit_datetime=github_date_updated,
            ssdc_author_name=self._get_ssdc_lead(lander_metadata),
            approval_str=self._format_lander_approval_str(
                lander_metadata.approval
            ),
            va_doors_id=lander_metadata.va_doors_id,
            req_doors_id=lander_metadata.req_doors_id,
            ipac_jira_id=lander_metadata.ipac_jira_id,
        )
        await self._repo.ssdc_tr.upsert(domain_model)

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

        (
            github_issues,
            github_release,
            github_date_updated,
        ) = await self._get_common_github_metadata(
            lander_metadata.repository_url,
            default_updated_datetime=project.default_edition.date_rebuilt,
        )

        domain_model = SpherexTnDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
            handle=lander_metadata.identifier,
            title=lander_metadata.title,
            project_id=project.slug,
            organization_id=org.slug,
            github_url=lander_metadata.repository_url,
            github_issues=github_issues,
            github_release=github_release,
            latest_commit_datetime=github_date_updated,
            ssdc_author_name=self._get_ssdc_lead(lander_metadata),
        )
        await self._repo.ssdc_tn.upsert(domain_model)

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

        (
            github_issues,
            github_release,
            github_date_updated,
        ) = await self._get_common_github_metadata(
            lander_metadata.repository_url,
            default_updated_datetime=project.default_edition.date_rebuilt,
        )

        domain_model = SpherexOpDocument(
            url=lander_metadata.canonical_url,
            series=lander_metadata.document_handle_prefix,
            handle=lander_metadata.identifier,
            title=lander_metadata.title,
            project_id=project.slug,
            organization_id=org.slug,
            github_url=lander_metadata.repository_url,
            github_issues=github_issues,
            github_release=github_release,
            latest_commit_datetime=project.default_edition.date_rebuilt,
            ssdc_author_name=self._get_ssdc_lead(lander_metadata),
        )
        await self._repo.ssdc_op.upsert(domain_model)
