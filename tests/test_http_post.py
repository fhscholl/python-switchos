"""Tests for HTTP POST methods on both aiohttp and httpx backends."""

import pytest
from unittest.mock import AsyncMock, MagicMock

# Check for optional dependencies
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


@pytest.mark.asyncio
async def test_aiohttp_post_sends_content_type():
    """AioHttpClient.post() sends body with Content-Type: text/plain header."""
    import aiohttp
    from python_switchos.http import AioHttpClient

    mock_response = MagicMock(spec=aiohttp.ClientResponse)
    mock_response.status = 200

    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.post = AsyncMock(return_value=mock_response)

    client = AioHttpClient(mock_session)
    await client.post("http://test/", "{en:0x01}")

    mock_session.post.assert_called_once_with(
        "http://test/",
        data="{en:0x01}",
        headers={"Content-Type": "text/plain"}
    )


@pytest.mark.asyncio
@pytest.mark.skipif(not HAS_HTTPX, reason="httpx not installed")
async def test_httpx_post_sends_content_type():
    """HttpxClient.post() sends body with Content-Type: text/plain header."""
    import httpx
    from python_switchos.http import HttpxClient

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200

    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)

    client = HttpxClient(mock_client)
    await client.post("http://test/", "{en:0x01}")

    mock_client.post.assert_called_once_with(
        "http://test/",
        content="{en:0x01}",
        headers={"Content-Type": "text/plain"}
    )


@pytest.mark.asyncio
async def test_aiohttp_post_returns_response():
    """AioHttpClient.post() returns HttpResponse with correct status and text."""
    import aiohttp
    from python_switchos.http import AioHttpClient, AioHttpResponse

    mock_response = MagicMock(spec=aiohttp.ClientResponse)
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="OK")

    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.post = AsyncMock(return_value=mock_response)

    client = AioHttpClient(mock_session)
    response = await client.post("http://test/", "{en:0x01}")

    assert isinstance(response, AioHttpResponse)
    assert response.status == 200
    assert await response.text() == "OK"


@pytest.mark.asyncio
@pytest.mark.skipif(not HAS_HTTPX, reason="httpx not installed")
async def test_httpx_post_returns_response():
    """HttpxClient.post() returns HttpResponse with correct status and text."""
    import httpx
    from python_switchos.http import HttpxClient, HttpxResponse

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "OK"

    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)

    client = HttpxClient(mock_client)
    response = await client.post("http://test/", "{en:0x01}")

    assert isinstance(response, HttpxResponse)
    assert response.status == 200
    assert await response.text() == "OK"
