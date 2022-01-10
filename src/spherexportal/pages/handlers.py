"""Handlers for the portal's webpages."""

from fastapi import APIRouter, Depends
from safir.dependencies.logger import logger_dependency
from starlette.responses import HTMLResponse
from structlog.stdlib import BoundLogger

__all__ = ["router"]

router = APIRouter()
"""FastAPI router for webpages."""


@router.get("/")
async def get_homepage(
    logger: BoundLogger = Depends(logger_dependency),
) -> HTMLResponse:
    return HTMLResponse("<html><body><h1>Hello, world!</h1></body></html>")
