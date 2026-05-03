# tests/components/ivent/test_sensor.py
import pytest
from homeassistant.core import HomeAssistant

async def test_sensor_entities(hass: HomeAssistant, mock_config_entry, mock_api_client):
    """Test sensor entities for i-Vent."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # RSSI Sensor
    rssi_state = hass.states.get("sensor.enota_1_signal")
    assert rssi_state is not None
    assert rssi_state.state == "-65"
    assert rssi_state.attributes.get("unit_of_measurement") == "dBm"

    # Last Changed Timestamp Sensor
    last_changed_state = hass.states.get("sensor.dnevna_soba_last_mode_change")
    assert last_changed_state is not None
    # 1700000000 is 2023-11-14T22:13:20+00:00
    assert "2023-11-14" in last_changed_state.state

    ends_at_state = hass.states.get("sensor.dnevna_soba_special_mode_ends_at")
    assert ends_at_state is not None
    assert ends_at_state.state == "unknown"  # 0 in mock means None

async def test_sensor_updates(hass: HomeAssistant, mock_config_entry, mock_api_client):
    """Test that sensor values update correctly from API changes."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Initial state
    rssi_state = hass.states.get("sensor.enota_1_signal")
    assert rssi_state.state == "-65"

    # Mock new data
    from .conftest import MOCK_INFO_DATA
    import copy
    new_data = copy.deepcopy(MOCK_INFO_DATA)
    new_data["groups"][0]["devices"][0]["rssi"] = -70
    mock_api_client.async_get_info.return_value = new_data

    # Trigger update
    from custom_components.ivent.const import DOMAIN
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Verify updated state
    rssi_state = hass.states.get("sensor.enota_1_signal")
    assert rssi_state.state == "-70"
