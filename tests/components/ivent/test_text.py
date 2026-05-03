# tests/components/ivent/test_text.py
import pytest
from homeassistant.core import HomeAssistant

async def test_text_entities(hass: HomeAssistant, mock_config_entry, mock_api_client):
    """Test text entities for i-Vent."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Ime skupine (Rename group)
    group_text_entity = "text.dnevna_soba_group_name"
    state = hass.states.get(group_text_entity)
    assert state is not None
    assert state.state == "Dnevna soba"

    await hass.services.async_call(
        "text", "set_value",
        {"entity_id": group_text_entity, "value": "Novo ime"},
        blocking=True,
    )
    mock_api_client.async_modify_group.assert_called_once()
    args = mock_api_client.async_modify_group.call_args
    assert args[0][1] == {"name": "Novo ime"}

    # Ime enote (Rename device)
    device_text_entity = "text.enota_1_device_name"
    state = hass.states.get(device_text_entity)
    assert state is not None
    assert state.state == "Enota 1"

    await hass.services.async_call(
        "text", "set_value",
        {"entity_id": device_text_entity, "value": "Nova Enota"},
        blocking=True,
    )
    mock_api_client.async_modify_device.assert_called_once()
    args = mock_api_client.async_modify_device.call_args
    assert args[0][1] == {"name": "Nova Enota"}
