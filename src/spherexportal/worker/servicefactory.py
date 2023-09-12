"""Create services for the worker."""


import httpx
from structlog.stdlib import BoundLogger

from spherexportal.dependencies.projects import projects_dependency
from spherexportal.dependencies.redis import redis_dependency
from spherexportal.services.projectservice import ProjectService


async def create_project_service(*, logger: BoundLogger) -> ProjectService:
    """Create a project service."""
    redis = await redis_dependency()
    await projects_dependency.initialize(redis)
    projects_repo = await projects_dependency()

    http_client = httpx.AsyncClient()

    return ProjectService(
        repo=projects_repo, logger=logger, http_client=http_client
    )
