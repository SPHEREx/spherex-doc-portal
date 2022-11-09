"""The repository holds the documentation metadata."""

from __future__ import annotations

from dataclasses import dataclass, field

from .domain import (
    SpherexCategory,
    SpherexDpDocument,
    SpherexIfDocument,
    SpherexMsDocument,
    SpherexPmDocument,
    SpherexTrDocument,
)


@dataclass(kw_only=True)
class ProjectRepository:
    """A repository for access documentation projects, organized around
    project categories for fast access.
    """

    ssdc_ms: SpherexCategory[SpherexMsDocument] = field(
        default_factory=SpherexCategory
    )

    ssdc_pm: SpherexCategory[SpherexPmDocument] = field(
        default_factory=SpherexCategory
    )

    ssdc_if: SpherexCategory[SpherexIfDocument] = field(
        default_factory=SpherexCategory
    )

    ssdc_dp: SpherexCategory[SpherexDpDocument] = field(
        default_factory=SpherexCategory
    )

    ssdc_tr: SpherexCategory[SpherexTrDocument] = field(
        default_factory=SpherexCategory
    )


class RepositoryDependency:
    def __init__(self) -> None:
        self._repo = ProjectRepository()

    async def __call__(self) -> ProjectRepository:
        return self._repo


repository_dependency = RepositoryDependency()
