"""The repository holds the documentation metadata."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..domain import (
    SpherexCategory,
    SpherexDpDocument,
    SpherexIfDocument,
    SpherexMsDocument,
    SpherexPmDocument,
    SpherexTnDocument,
    SpherexTrDocument,
)


@dataclass(kw_only=True)
class ProjectRepository:
    """A repository for accessing documentation projects, organized around
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

    ssdc_tn: SpherexCategory[SpherexTnDocument] = field(
        default_factory=SpherexCategory
    )
