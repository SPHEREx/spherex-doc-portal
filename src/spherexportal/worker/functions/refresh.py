"""Arq task for refreshing the cache of project data in Redis."""

from __future__ import annotations

from typing import Any


async def refresh_projects(ctx: dict[Any, Any]) -> None:
    """Refresh the cache of project data in Redis."""
    logger = ctx["logger"].bind(task="refresh_projects")
    logger.info("Starting refresh of project data")
