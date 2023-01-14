"""Handlers for the portal's webpages."""

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from safir.dependencies.logger import logger_dependency
from starlette.requests import Request
from starlette.templating import Jinja2Templates, _TemplateResponse
from structlog.stdlib import BoundLogger

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
        "category": projects_repo.ssdc_ms,
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
        "category": projects_repo.ssdc_pm,
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
        "category": projects_repo.ssdc_if,
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
        "category": projects_repo.ssdc_dp,
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
        "category": projects_repo.ssdc_tr,
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
        "category": projects_repo.ssdc_tn,
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
        "category": projects_repo.ssdc_op,
        "request": request,
    }
    return templates.TemplateResponse("ssdc-op.html.jinja", context)


@router.get("/__healthz")
async def get_healthz(
    projects_repo: ProjectRepository = Depends(projects_dependency),
) -> PlainTextResponse:
    return PlainTextResponse("OK")
