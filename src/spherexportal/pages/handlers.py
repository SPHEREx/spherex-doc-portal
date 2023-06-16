"""Handlers for the portal's webpages."""

import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import PlainTextResponse
from gidgethub.sansio import Event
from safir.dependencies.logger import logger_dependency
from starlette.templating import Jinja2Templates, _TemplateResponse
from structlog.stdlib import BoundLogger

from spherexportal.config import config
from spherexportal.dependencies.projects import projects_dependency
from spherexportal.repositories.projects import ProjectRepository

__all__ = ["router"]

router = APIRouter()
"""FastAPI router for webpages."""


templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@router.get("/")
async def get_homepage(
    request: Request,
    logger: BoundLogger = Depends(logger_dependency),
) -> _TemplateResponse:
    context = {"request": request}
    return templates.TemplateResponse("index.html.jinja", context)


@router.get("/ssdc-ms")
async def get_ssdc_ms(
    request: Request,
    projects_repo: ProjectRepository = Depends(projects_dependency),
) -> _TemplateResponse:
    context = {
        "current_path": "/ssdc-ms",
        "projects": await projects_repo.ssdc_ms.get_all(),
        "request": request,
    }
    return templates.TemplateResponse("ssdc-ms.html.jinja", context)


@router.get("/ssdc-pm")
async def get_ssdc_pm(
    request: Request,
    projects_repo: ProjectRepository = Depends(projects_dependency),
) -> _TemplateResponse:
    context = {
        "current_path": "/ssdc-pm",
        "projects": await projects_repo.ssdc_pm.get_all(),
        "request": request,
    }
    return templates.TemplateResponse("ssdc-pm.html.jinja", context)


@router.get("/ssdc-if")
async def get_ssdc_if(
    request: Request,
    projects_repo: ProjectRepository = Depends(projects_dependency),
) -> _TemplateResponse:
    context = {
        "current_path": "/ssdc-if",
        "projects": await projects_repo.ssdc_if.get_all(),
        "request": request,
    }
    return templates.TemplateResponse("ssdc-if.html.jinja", context)


@router.get("/ssdc-dp")
async def get_ssdc_dp(
    request: Request,
    projects_repo: ProjectRepository = Depends(projects_dependency),
) -> _TemplateResponse:
    context = {
        "current_path": "/ssdc-dp",
        "projects": await projects_repo.ssdc_dp.get_all(),
        "request": request,
    }
    return templates.TemplateResponse("ssdc-dp.html.jinja", context)


@router.get("/ssdc-tr")
async def get_ssdc_tr(
    request: Request,
    projects_repo: ProjectRepository = Depends(projects_dependency),
) -> _TemplateResponse:
    context = {
        "current_path": "/ssdc-tr",
        "projects": await projects_repo.ssdc_tr.get_all(),
        "request": request,
    }
    return templates.TemplateResponse("ssdc-tr.html.jinja", context)


@router.get("/ssdc-tn")
async def get_ssdc_tn(
    request: Request,
    projects_repo: ProjectRepository = Depends(projects_dependency),
) -> _TemplateResponse:
    context = {
        "current_path": "/ssdc-tn",
        "projects": await projects_repo.ssdc_tn.get_all(),
        "request": request,
    }
    return templates.TemplateResponse("ssdc-tn.html.jinja", context)


@router.get("/ssdc-op")
async def get_ssdc_op(
    request: Request,
    projects_repo: ProjectRepository = Depends(projects_dependency),
) -> _TemplateResponse:
    context = {
        "current_path": "/ssdc-op",
        "projects": await projects_repo.ssdc_op.get_all(),
        "request": request,
    }
    return templates.TemplateResponse("ssdc-op.html.jinja", context)


@router.post(
    "/api/github/webhook",
    summary="GitHub App webhook",
    description="This endpoint receives webhook events from GitHub",
    status_code=status.HTTP_200_OK,
)
async def post_github_webhook(
    request: Request,
    logger: BoundLogger = Depends(logger_dependency),
) -> Response:
    """Process GitHub webhook events."""
    if not config.is_github_app_enabled:
        return Response(
            "GitHub App is not enabled",
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
        )

    if config.github_webhook_secret is None:
        # type assertion
        raise RuntimeError("GitHub webhook secret is not configured")

    webhook_secret = config.github_webhook_secret.get_secret_value()
    body = await request.body()
    event = Event.from_http(request.headers, body, secret=webhook_secret)

    # Bind the X-GitHub-Delivery header to the logger context; this identifies
    # the webhook request in GitHub's API and UI for diagnostics
    logger = logger.bind(github_delivery=event.delivery_id)

    logger.debug("Received GitHub webhook", payload=event.data)
    # Give GitHub some time to reach internal consistency.
    await asyncio.sleep(1)

    # TODO: Implement webhook router
    # await webhook_router.dispatch(event, logger)

    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.get("/__healthz")
async def get_healthz(
    projects_repo: ProjectRepository = Depends(projects_dependency),
) -> PlainTextResponse:
    return PlainTextResponse("OK")
