"""Tests for the data repository."""

from __future__ import annotations

import pytest
import redis.asyncio as redis

from spherexportal.repositories.mockdata import MockDataRepository
from spherexportal.repositories.projects import ProjectRepository


@pytest.mark.asyncio
async def test_loading_mock_data(redis_client: redis.Redis) -> None:
    project_repo = await ProjectRepository.create(redis_client)
    mock_repo = MockDataRepository.load_builtin_data()
    await mock_repo.bootstrap_project_repository(project_repo)
