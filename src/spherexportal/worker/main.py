"""Configuration for the Arq-based worker process."""

import uuid
from typing import Any

import httpx
import structlog
from arq import cron
from safir.logging import configure_logging

from spherexportal.config import config
from spherexportal.dependencies.projects import projects_dependency
from spherexportal.dependencies.redis import redis_dependency

from .functions import refresh_projects


async def startup(ctx: dict[Any, Any]) -> None:
    """Runs during working start-up to set up the worker context."""
    configure_logging(
        profile=config.profile,
        log_level=config.log_level,
        name="timessquare",
    )
    logger = structlog.get_logger(config.logger_name)
    # The instance key uniquely identifies this worker in logs
    instance_key = uuid.uuid4().hex
    logger = logger.bind(worker_instance=instance_key)

    logger.info("Starting up worker")

    http_client = httpx.AsyncClient()
    ctx["http_client"] = http_client

    ctx["logger"] = logger
    logger.info("Start up complete")

    # Set up FastAPI dependencies; we can use them "manually" with
    # arq to provide resources similarly to FastAPI endpoints
    await redis_dependency.initialize(config.redis_url)
    redis = await redis_dependency()
    await projects_dependency.initialize(redis)


async def shutdown(ctx: dict[Any, Any]) -> None:
    """Runs during worker shut-down to resources."""
    if "logger" in ctx.keys():
        logger = ctx["logger"]
    else:
        logger = structlog.get_logger(config.logger_name)
    logger.info("Running worker shutdown.")

    await redis_dependency.close()

    try:
        await ctx["http_client"].aclose()
    except Exception as e:
        logger.warning("Issue closing the http_client: %s", str(e))

    logger.info("Worker shutdown complete.")


# For info on ignoring the type checking here, see
# https://github.com/samuelcolvin/arq/issues/249
cron_jobs: list[cron] = []  # type: ignore
cron_jobs.append(
    cron(refresh_projects, minute={0, 15, 30, 45})  # type: ignore
)


class WorkerSettings:
    """Configuration for a Times Square arq worker.

    See `arq.worker.Worker` for details on these attributes.
    """

    cron_jobs = cron_jobs

    redis_settings = config.arq_redis_settings

    on_startup = startup

    on_shutdown = shutdown
