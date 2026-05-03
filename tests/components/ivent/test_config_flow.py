# tests/components/ivent/test_config_flow.py
import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.data_entry_flow import FlowResultType
from custom_components.ivent.api import IVentApiAuthError, IVentApiClientError
from custom_components.ivent.const import DOMAIN
from .conftest import MOCK_INFO_DATA

# TEST 1: Uspešen setup (ena lokacija)
async def test_full_flow_success(hass):
    with patch("custom_components.ivent.config_flow.IVentApiClient") as mock:
        # Mockamo vrnjeno lokacijo
        mock.return_value.async_get_locations = AsyncMock(return_value=[{"id": "loc-1", "name": "Stanovanje"}])
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={'source': 'user'}
        )
        assert result['type'] is FlowResultType.FORM
        assert result['step_id'] == 'user'

        result = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            {'api_key': 'valid-key'},
        )
    # Ker je samo ena lokacija, gre direktno v CREATE_ENTRY
    assert result['type'] is FlowResultType.CREATE_ENTRY
    assert result['data']['api_key'] == 'valid-key'
    assert result['data']['location_id'] == 'loc-1'
    assert "Stanovanje" in result["title"]

# TEST 2: Več lokacij (multi-step)
async def test_multi_location_flow(hass):
    with patch("custom_components.ivent.config_flow.IVentApiClient") as mock:
        mock.return_value.async_get_locations = AsyncMock(return_value=[
            {"id": "loc-1", "name": "Stanovanje"},
            {"id": "loc-2", "name": "Pisarna"}
        ])
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={'source': 'user'}
        )
        result = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            {'api_key': 'valid-key'},
        )
        
        # Pojaviti se mora drugi korak 'location'
        assert result['type'] is FlowResultType.FORM
        assert result['step_id'] == 'location'

        # Izberemo Pisarno
        result = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            {'location_id': 'loc-2'},
        )
        
    assert result['type'] is FlowResultType.CREATE_ENTRY
    assert result['data']['location_id'] == 'loc-2'
    assert "Pisarna" in result["title"]


# TEST 3: Napačen API ključ
async def test_flow_auth_error(hass):
    with patch('custom_components.ivent.config_flow.IVentApiClient') as mock:
        mock.return_value.async_get_locations.side_effect = IVentApiAuthError()
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={'source': 'user'}
        )
        result = await hass.config_entries.flow.async_configure(
            result['flow_id'], {'api_key': 'bad'}
        )
    assert result['type'] is FlowResultType.FORM
    assert result['errors']['base'] == 'auth_error'

# TEST 4: Napaka pri povezavi
async def test_flow_cannot_connect(hass):
    with patch('custom_components.ivent.config_flow.IVentApiClient') as mock:
        mock.return_value.async_get_locations.side_effect = IVentApiClientError()
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={'source': 'user'}
        )
        result = await hass.config_entries.flow.async_configure(
            result['flow_id'], {'api_key': 'key'}
        )
    assert result['errors']['base'] == 'cannot_connect'

# TEST 5: Duplikat — ista lokacija
async def test_flow_duplicate(hass, mock_config_entry):
    with patch("custom_components.ivent.config_flow.IVentApiClient") as mock:
        mock.return_value.async_get_locations = AsyncMock(return_value=[{"id": "test-location-99", "name": "Test"}])
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={'source': 'user'}
        )
        result = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            {'api_key': 'key'},
        )
    assert result['type'] is FlowResultType.ABORT
    assert result['reason'] == 'already_configured'

# TEST 5: Reauth flow success
async def test_reauth_flow_success(hass, mock_config_entry):
    """Test the reauthentication flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reauth", "entry_id": mock_config_entry.entry_id, "title_placeholders": {"name": mock_config_entry.title}},
        data=mock_config_entry.data,
    )
    
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch("custom_components.ivent.config_flow.IVentApiClient") as mock:
        mock.return_value.async_get_info = AsyncMock(return_value=MOCK_INFO_DATA)
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"api_key": "new-valid-key"},
        )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert mock_config_entry.data["api_key"] == "new-valid-key"

# TEST 6: Reauth flow auth error
async def test_reauth_flow_auth_error(hass, mock_config_entry):
    """Test the reauthentication flow resulting in auth error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reauth", "entry_id": mock_config_entry.entry_id, "title_placeholders": {"name": mock_config_entry.title}},
        data=mock_config_entry.data,
    )

    with patch("custom_components.ivent.config_flow.IVentApiClient") as mock:
        mock.return_value.async_get_info.side_effect = IVentApiAuthError()
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"api_key": "new-invalid-key"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "reauth_confirm"
    assert result2["errors"]["base"] == "auth_error"

# TEST 7: Reconfigure flow
async def test_reconfigure_flow_success(hass, mock_config_entry):
    """Test the reconfiguration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": mock_config_entry.entry_id},
    )
    
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    with patch("custom_components.ivent.config_flow.IVentApiClient") as mock:
        mock.return_value.async_get_info = AsyncMock(return_value=MOCK_INFO_DATA)
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"api_key": "new-valid-key-2", "location_id": "new-location"},
        )

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"
    assert mock_config_entry.data["api_key"] == "new-valid-key-2"
    assert mock_config_entry.data["location_id"] == "new-location"

# TEST 8: Reconfigure flow auth error
async def test_reconfigure_flow_auth_error(hass, mock_config_entry):
    """Test the reconfiguration flow resulting in auth error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": mock_config_entry.entry_id},
    )

    with patch("custom_components.ivent.config_flow.IVentApiClient") as mock:
        mock.return_value.async_get_info.side_effect = IVentApiAuthError()
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"api_key": "bad-key", "location_id": "bad-location"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "reconfigure"
    assert result2["errors"]["base"] == "auth_error"