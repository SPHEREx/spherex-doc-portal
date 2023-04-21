"""The repository holds the documentation metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self, TypeVar

from redis.asyncio import Redis
from safir.redis import PydanticRedisStorage

from ..domain import (
    SpherexDpDocument,
    SpherexIfDocument,
    SpherexMsDocument,
    SpherexOpDocument,
    SpherexPmDocument,
    SpherexProject,
    SpherexTnDocument,
    SpherexTrDocument,
)

T = TypeVar("T", bound="SpherexProject")


class SpherexProjectStore(PydanticRedisStorage[T]):
    """A Redis-backed store for SPHEREx projects in a specific category."""

    def __init__(self, project_cls: type[T], redis: Redis, key_prefix: str):
        super().__init__(
            datatype=project_cls, redis=redis, key_prefix=key_prefix
        )

    async def get_all(self) -> list[T]:
        """Get all projects, sorted by ID (key)."""
        keys = [m async for m in self.scan("*")]
        keys.sort()
        projects: list[T] = []
        for k in keys:
            project = await self.get(k)
            if project:
                projects.append(project)
        return projects

    async def upsert(self, project: T) -> None:
        """Append a new project or replace an existing project with the new
        data.
        """
        await self.store(project.project_id, project)


@dataclass(kw_only=True)
class ProjectRepository:
    """A repository for accessing documentation projects, organized around
    project categories for fast access.
    """

    ssdc_ms: SpherexProjectStore[SpherexMsDocument]

    ssdc_pm: SpherexProjectStore[SpherexPmDocument]

    ssdc_if: SpherexProjectStore[SpherexIfDocument]

    ssdc_dp: SpherexProjectStore[SpherexDpDocument]

    ssdc_tr: SpherexProjectStore[SpherexTrDocument]

    ssdc_tn: SpherexProjectStore[SpherexTnDocument]

    ssdc_op: SpherexProjectStore[SpherexOpDocument]

    @classmethod
    async def create(cls, redis: Redis) -> Self:
        ms_store = SpherexProjectStore(
            SpherexMsDocument, redis, key_prefix="ssdc_ms:"
        )
        pm_store = SpherexProjectStore(
            SpherexPmDocument, redis, key_prefix="ssdc_pm:"
        )
        if_store = SpherexProjectStore(
            SpherexIfDocument, redis, key_prefix="ssdc_if:"
        )
        dp_store = SpherexProjectStore(
            SpherexDpDocument, redis, key_prefix="ssdc_dp:"
        )
        tr_store = SpherexProjectStore(
            SpherexTrDocument, redis, key_prefix="ssdc_tr:"
        )
        tn_store = SpherexProjectStore(
            SpherexTnDocument, redis, key_prefix="ssdc_tn:"
        )
        op_store = SpherexProjectStore(
            SpherexOpDocument, redis, key_prefix="ssdc_op:"
        )
        return cls(
            ssdc_ms=ms_store,
            ssdc_pm=pm_store,
            ssdc_if=if_store,
            ssdc_dp=dp_store,
            ssdc_tr=tr_store,
            ssdc_tn=tn_store,
            ssdc_op=op_store,
        )
