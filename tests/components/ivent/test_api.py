# tests/components/ivent/test_api.py
import asyncio
import pytest
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch, ANY, call
from custom_components.ivent.api import (
    IVentApiClient, IVentApiAuthError, IVentApiClientError
)

@pytest.fixture
def api_client():
    session = AsyncMock(spec=aiohttp.ClientSession)
    return IVentApiClient(session, 'test-key', 'loc-1')

async def test_get_info_success(api_client):
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.content_type = 'application/json'
    mock_resp.json.return_value = {'groups': []}
    mock_resp.raise_for_status = MagicMock()
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    api_client._session.request.return_value = mock_resp
    result = await api_client.async_get_info()
    assert result == {'groups': []}

async def test_auth_error_401(api_client):
    mock_resp = AsyncMock()
    mock_resp.status = 401
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    api_client._session.request.return_value = mock_resp
    with pytest.raises(IVentApiAuthError):
        await api_client.async_get_info()

async def test_timeout(api_client):
    api_client._session.request.side_effect = asyncio.TimeoutError()
    with pytest.raises(IVentApiClientError):
        await api_client.async_get_info()

async def test_auth_error_403(api_client):
    """Test 403 Forbidden error."""
    mock_resp = AsyncMock()
    mock_resp.status = 403
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    api_client._session.request.return_value = mock_resp
    with pytest.raises(IVentApiAuthError):
        await api_client.async_get_info()

async def test_client_error(api_client):
    """Test general ClientError."""
    api_client._session.request.side_effect = aiohttp.ClientError()
    with pytest.raises(IVentApiClientError):
        await api_client.async_get_info()

async def test_get_schedules(api_client):
    """Test async_get_schedules."""
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.content_type = 'application/json'
    mock_resp.json.return_value = []
    mock_resp.raise_for_status = MagicMock()
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    api_client._session.request.return_value = mock_resp
    result = await api_client.async_get_schedules()
    assert result == []

async def test_modify_group(api_client):
    """Test async_modify_group."""
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.content_type = 'application/json'
    mock_resp.json.return_value = {"status": "ok"}
    mock_resp.raise_for_status = MagicMock()
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    api_client._session.request.return_value = mock_resp
    await api_client.async_modify_group(1, {"name": "New Name"})
    api_client._session.request.assert_called_with(
        "post",
        "https://cloud.i-vent.com/api/v1/live/loc-1/modify_group",
        headers=api_client._headers,
        timeout=ANY,
        json={"group_id": 1, "name": "New Name"}
    )

async def test_modify_device(api_client):
    """Test async_modify_device."""
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.content_type = 'application/json'
    mock_resp.json.return_value = {"status": "ok"}
    mock_resp.raise_for_status = MagicMock()
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    api_client._session.request.return_value = mock_resp
    await api_client.async_modify_device("AA:BB", {"name": "New Device"})
    api_client._session.request.assert_called_with(
        "post",
        "https://cloud.i-vent.com/api/v1/live/loc-1/modify_device",
        headers=api_client._headers,
        timeout=ANY,
        json={"device_mac": "AA:BB", "name": "New Device"}
    )

async def test_create_group(api_client):
    """Test async_create_group."""
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.content_type = 'application/json'
    mock_resp.json.return_value = {"group_id": 2}
    mock_resp.raise_for_status = MagicMock()
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    api_client._session.request.return_value = mock_resp
    await api_client.async_create_group("New Group")
    api_client._session.request.assert_called_with(
        "post",
        "https://cloud.i-vent.com/api/v1/live/loc-1/create_group",
        headers=api_client._headers,
        timeout=ANY,
        json={"name": "New Group"}
    )

async def test_modify_schedules(api_client):
    """Test async_modify_schedules."""
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.content_type = 'application/json'
    mock_resp.json.return_value = {"status": "ok"}
    mock_resp.raise_for_status = MagicMock()
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    api_client._session.request.return_value = mock_resp
    await api_client.async_modify_schedules([])
    api_client._session.request.assert_called_with(
        "post",
        "https://cloud.i-vent.com/api/v1/live/loc-1/modify_schedules",
        headers=api_client._headers,
        timeout=ANY,
        json={"schedules": []}
    )

async def test_empty_response(api_client):
    """Test 204 No Content response."""
    mock_resp = AsyncMock()
    mock_resp.status = 204
    mock_resp.raise_for_status = MagicMock()
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    api_client._session.request.return_value = mock_resp
    result = await api_client.async_get_info()
    assert result is None


async def test_request_retries_on_failure(api_client):
    """Test _request retries on transient server errors with backoff."""
    def make_response(status, json_data=None):
        resp = AsyncMock()
        resp.status = status
        resp.content_type = "application/json"
        resp.json = AsyncMock(return_value=json_data or {})
        resp.raise_for_status = MagicMock()

        cm = AsyncMock()
        cm.__aenter__.return_value = resp
        cm.__aexit__.return_value = False
        return cm

    # 2 failures, then success
    api_client._session.request.side_effect = [
        make_response(500),
        make_response(500),
        make_response(200, {"ok": True}),
    ]

    with patch("custom_components.ivent.api.asyncio.sleep", new=AsyncMock()) as mock_sleep:
        result = await api_client._request("get", "/live/loc-1/info")

    assert api_client._session.request.call_count == 3
    assert result == {"ok": True}
    mock_sleep.assert_has_awaits([call(1.0), call(2.0)])