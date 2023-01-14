"""FastAPI dependency for a ProjectRepository instance."""

from __future__ import annotations

from ..repositories.projects import ProjectRepository

__all__ = ["projects_dependency"]


class ProjectsDependency:
    def __init__(self) -> None:
        self._repo = ProjectRepository()

    async def __call__(self) -> ProjectRepository:
        return self._repo


projects_dependency = ProjectsDependency()
