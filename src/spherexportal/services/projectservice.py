from __future__ import annotations

from structlog.stdlib import BoundLogger

from ..repositories.mockdata import MockDataRepository
from ..repositories.projects import ProjectRepository


class ProjectService:
    """Service for working with the project metadata repository."""

    def __init__(self, repo: ProjectRepository, logger: BoundLogger) -> None:
        self._logger = logger
        self._repo = repo

    async def bootstrap_mock_repo(self) -> None:
        mockdata_service = MockDataRepository.load_builtin_data()
        mockdata_service.bootstrap_project_repository(self._repo)
