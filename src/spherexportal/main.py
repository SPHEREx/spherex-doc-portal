"""The main application factory for the spherex-doc-portal service.

Notes
-----
Be aware that, following the normal pattern for FastAPI services, the app is
constructed when this module is loaded and is not deferred until a function is
called.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import metadata, version
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from safir.dependencies.http_client import http_client_dependency
from safir.logging import configure_logging
from safir.middleware.x_forwarded import XForwardedMiddleware
from structlog import get_logger

from .config import config
from .dependencies.projects import projects_dependency
from .dependencies.redis import redis_dependency
from .pages.handlers import router
from .services.projectservice import ProjectService

__all__ = ["app", "config"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator:
    """Context manager for the application lifespan."""
    logger = get_logger(__name__)
    logger.bind(app_event="startup")

    http_client = await http_client_dependency()
    await redis_dependency.initialize(str(config.redis_url))
    logger.info("Initialized redis dependency")
    redis = await redis_dependency()
    await projects_dependency.initialize(redis)
    projects_repo = await projects_dependency()
    logger.info("Initialized projects dependency")

    project_service = ProjectService(
        repo=projects_repo, logger=logger, http_client=http_client
    )
    if config.use_mock_data:
        await project_service.bootstrap_mock_repo()

    logger.info("Finished startup")

    yield

    await redis_dependency.close()
    await http_client_dependency.aclose()
    logger.info("Finished shutdown")


configure_logging(
    profile=config.profile,
    log_level=config.log_level,
    name=config.logger_name,
)

app = FastAPI(
    title="SPHEREx Documentation Portal",
    description=metadata("spherex-doc-portal")["Summary"],
    version=version("spherex-doc-portal"),
    lifespan=lifespan,
)
app.include_router(router)

static_path = Path(__file__).parent.joinpath("static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

app.add_middleware(XForwardedMiddleware)
