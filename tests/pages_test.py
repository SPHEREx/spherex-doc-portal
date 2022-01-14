"""Test webpages."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_homepage(client: AsyncClient) -> None:
    """Test ``GET /``"""
    response = await client.get("/")
    assert response.status_code == 200
