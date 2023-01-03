from __future__ import annotations

from structlog.stdlib import BoundLogger

from ..repositories.mockdata import MockDataRepository
from ..repositories.projects import ProjectRepository


class ProjectService:
    """Service for working with the project metadata repository."""

    def __init__(self, repo: ProjectRepository, logger: BoundLogger) -> None:
        self._logger = logger
        self._repo = repo

    async def bootstrap_repo(self) -> None:
        # FIXME Default to loading mock data right now; swap this out with a
        # system for scraping the data from the LTD API and S3 bucket.
        mockdata_service = MockDataRepository.load_builtin_data()
        self._repo.ssdc_ms = mockdata_service.load_ssdc_ms()
