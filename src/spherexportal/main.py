"""The main application factory for the spherex-doc-portal service.

Notes
-----
Be aware that, following the normal pattern for FastAPI services, the app is
constructed when this module is loaded and is not deferred until a function is
called.
"""

from importlib.metadata import metadata, version

from fastapi import FastAPI
from safir.dependencies.http_client import http_client_dependency
from safir.logging import configure_logging
from safir.middleware.x_forwarded import XForwardedMiddleware
from structlog import get_logger

from .config import config
from .dependencies.projects import projects_dependency
from .pages.handlers import router
from .services.projectservice import ProjectService

__all__ = ["app", "config"]


configure_logging(
    profile=config.profile,
    log_level=config.log_level,
    name=config.logger_name,
)

app = FastAPI(
    title="SPHEREx Documentation Portal",
    description=metadata("spherex-doc-portal")["Summary"],
    version=version("spherex-doc-portal"),
)
app.include_router(router)


@app.on_event("startup")
async def startup_event() -> None:
    logger = get_logger(__name__)
    logger.bind(app_event="startup")

    app.add_middleware(XForwardedMiddleware)

    projects_repo = await projects_dependency()

    project_service = ProjectService(repo=projects_repo, logger=logger)
    # FIXME Default to loading mock data right now; swap this out with a
    # system for scraping the data from the LTD API and S3 bucket.
    await project_service.bootstrap_repo()

    logger.info("Finished startup")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await http_client_dependency.aclose()
