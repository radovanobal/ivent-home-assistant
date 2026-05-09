import pytest
import copy

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ivent.const import DOMAIN
from .conftest import MOCK_INFO_DATA, MOCK_SCHEDULES_DATA

async def test_stale_device_and_entity_entries_are_not_removed(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test that registry entries are not removed when API data disappears."""
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

    problem_uid = "AA:BB:CC:DD:EE:FF_problem"
    problem_entity_id = entity_registry.async_get_entity_id(
        "binary_sensor", DOMAIN, problem_uid
    )
    assert problem_entity_id is not None

    # Now we mutate API response to remove ONE device and the SCHEDULE.
    # The integration should not delete registry entries; that can break
    # user automations and is unsafe during startup/reconnect races.
    new_data = copy.deepcopy(MOCK_INFO_DATA)
    new_data["groups"][0]["devices"] = [] # Removing the device "Enota 1"
    mock_api_client.async_get_info.return_value = new_data
    mock_api_client.async_get_schedules.return_value = [] # Removed the schedule

    # Refresh coordinator
    entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
    coordinator = entry_data["coordinator"]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Device registry entries are intentionally preserved.
    devices = dr.async_entries_for_config_entry(device_registry, mock_config_entry.entry_id)
    assert len(devices) == 3
    
    # Entity registry entries are intentionally preserved.
    assert entity_registry.async_get_entity_id("switch", DOMAIN, schedule_uid) is not None
    assert (
        entity_registry.async_get_entity_id("binary_sensor", DOMAIN, problem_uid)
        == problem_entity_id
    )

    problem_state = hass.states.get(problem_entity_id)
    assert problem_state is not None
    assert problem_state.state == "unavailable"
