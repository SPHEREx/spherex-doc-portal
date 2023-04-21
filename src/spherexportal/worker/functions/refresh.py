"""Arq task for refreshing the cache of project data in Redis."""

from __future__ import annotations

from typing import Any

from ..servicefactory import create_project_service


async def refresh_projects(ctx: dict[Any, Any]) -> None:
    """Refresh the cache of project data in Redis."""
    logger = ctx["logger"].bind(task="refresh_projects")
    logger.info("Starting refresh of project data")

    project_service = await create_project_service(logger=logger)

    # The bootstrap project refreshes the cache of project data for all
    # projects registered with the LTD API.
    await project_service.bootstrap_from_api()

    logger.info("Finished refresh of project data")
