import pytest
import copy

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ivent.const import DOMAIN
from .conftest import MOCK_INFO_DATA, MOCK_SCHEDULES_DATA

async def test_stale_device_and_entity_removal(hass: HomeAssistant, mock_config_entry, mock_api_client):
    """Test that stale devices and orphaned schedule entities are removed."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    
    # Initially we should have the service device + 1 group device + 1 node device
    devices = dr.async_entries_for_config_entry(device_registry, mock_config_entry.entry_id)
    assert len(devices) == 3

    # Ensure schedule entity is present initially
    schedule_uid = f"{mock_config_entry.entry_id}_schedule_101"
    assert entity_registry.async_get_entity_id("switch", DOMAIN, schedule_uid) is not None

    # Now we mutate API response to remove ONE device and the SCHEDULE
    new_data = copy.deepcopy(MOCK_INFO_DATA)
    new_data["groups"][0]["devices"] = [] # Removing the device "Enota 1"
    mock_api_client.async_get_info.return_value = new_data
    mock_api_client.async_get_schedules.return_value = [] # Removed the schedule

    # Refresh coordinator
    entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
    coordinator = entry_data["coordinator"]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Device assertions: should have 2 devices left (System + Group)
    devices = dr.async_entries_for_config_entry(device_registry, mock_config_entry.entry_id)
    assert len(devices) == 2
    
    # Entity assertions: orphaned schedule entity must be removed from ER
    assert entity_registry.async_get_entity_id("switch", DOMAIN, schedule_uid) is None

