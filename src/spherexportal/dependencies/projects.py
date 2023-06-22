"""FastAPI dependency for a ProjectRepository instance."""

from __future__ import annotations

from redis.asyncio import Redis

from ..repositories.projects import ProjectRepository

__all__ = ["projects_dependency"]


class ProjectsDependency:
    def __init__(self) -> None:
        self._repo: ProjectRepository | None = None

    async def initialize(self, redis: Redis) -> None:
        self._repo = await ProjectRepository.create(redis)

    async def __call__(self) -> ProjectRepository:
        if self._repo is None:
            raise RuntimeError("ProjectsDependency is not initialized")
        return self._repo


projects_dependency = ProjectsDependency()
