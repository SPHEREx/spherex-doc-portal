"""Test fixtures for spherex-doc-portal tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest_asyncio
import redis.asyncio as redis
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from spherexportal import main

if TYPE_CHECKING:
    from typing import AsyncIterator

    from fastapi import FastAPI


@pytest_asyncio.fixture
async def redis_client() -> AsyncIterator[redis.Redis]:
    """A Redis client for testing.

    This fixture connects to the Redis server that runs via tox-docker.
    """
    client: redis.Redis = redis.Redis(host="localhost", port=6379, db=0)
    yield client

    await client.close()


@pytest_asyncio.fixture
async def app() -> AsyncIterator[FastAPI]:
    """Return a configured test application.

    Wraps the application in a lifespan manager so that startup and shutdown
    events are sent during test execution.
    """
    async with LifespanManager(main.app):
        yield main.app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Return an ``httpx.AsyncClient`` configured to talk to the test app."""
    async with AsyncClient(app=app, base_url="https://example.com/") as client:
        yield client
