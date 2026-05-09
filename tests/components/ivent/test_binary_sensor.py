# tests/components/ivent/test_binary_sensor.py
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

async def test_binary_sensors(hass: HomeAssistant, mock_config_entry, mock_api_client):
    """Test standard binary sensors for i-Vent."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Stanje naprave (Problem sensor)
    problem_state = hass.states.get("binary_sensor.enota_1_device_state")
    assert problem_state is not None
    assert problem_state.state == "off"  # status_esp is 0 in mock

    # Povezljivost (Alive sensor)
    alive_state = hass.states.get("binary_sensor.enota_1_connectivity")
    assert alive_state is not None
    assert alive_state.state == "on"  # alive is True in mock

async def test_binary_sensors_edge_cases(hass: HomeAssistant, mock_config_entry, mock_api_client):
    """Test binary sensors with alternative states (problem on, connectivity off)."""
    from .conftest import MOCK_INFO_DATA
    import copy

    # Mock problem state
    problem_data = copy.deepcopy(MOCK_INFO_DATA)
    problem_data["groups"][0]["devices"][0]["status_esp"] = 1
    problem_data["groups"][0]["devices"][0]["alive"] = False
    
    mock_api_client.async_get_info.return_value = problem_data

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Stanje naprave (Problem sensor)
    problem_state = hass.states.get("binary_sensor.enota_1_device_state")
    assert problem_state.state == "on"
    assert problem_state.attributes.get("status_code") == 1

    # Povezljivost (Alive sensor)
    alive_state = hass.states.get("binary_sensor.enota_1_connectivity")
    assert alive_state.state == "off"

async def test_binary_sensors_diagnostic_flags(hass: HomeAssistant, mock_config_entry, mock_api_client):
    """Test dynamic diagnostic sensors based on STATUS_FLAGS bitmask."""
    from .conftest import MOCK_INFO_DATA
    import copy

    # Mock filter flag (1024)
    flag_data = copy.deepcopy(MOCK_INFO_DATA)
    flag_data["groups"][0]["devices"][0]["status_esp"] = 1024
    flag_data["groups"][0]["devices"][0]["diagnostic_flags"] = 1024
    
    mock_api_client.async_get_info.return_value = flag_data

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Generic problem sensor should be ON
    problem_state = hass.states.get("binary_sensor.enota_1_device_state")
    assert problem_state.state == "on"

    # Specific Filter diagnostic sensor should be ON.
    # Resolve entity_id from unique_id to avoid coupling test to translated name slug.
    entity_registry = er.async_get(hass)
    filter_unique_id = "AA:BB:CC:DD:EE:FF_filter"
    filter_entry = entity_registry.async_get_entity_id(
        "binary_sensor",
        "ivent",
        filter_unique_id,
    )
    assert filter_entry is not None

    filter_state = hass.states.get(filter_entry)
    assert filter_state is not None
    assert filter_state.state == "on"

async def test_problem_sensor_ignores_connectivity_status_bit(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test that status bit 16 alone does not make the problem sensor stay on."""
    from .conftest import MOCK_INFO_DATA
    import copy

    problem_data = copy.deepcopy(MOCK_INFO_DATA)
    problem_data["groups"][0]["devices"][0]["alive"] = False
    problem_data["groups"][0]["devices"][0]["status_esp"] = 16
    mock_api_client.async_get_info.return_value = problem_data

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    problem_state = hass.states.get("binary_sensor.enota_1_device_state")
    assert problem_state is not None
    assert problem_state.state == "off"
    assert problem_state.attributes.get("status_code") == 16


async def test_registered_binary_sensors_are_added_on_setup(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test that existing registry entries are still added as active entities."""
    entity_registry = er.async_get(hass)
    entity_registry.async_get_or_create(
        "binary_sensor",
        "ivent",
        "AA:BB:CC:DD:EE:FF_problem",
        suggested_object_id="enota_1_device_state",
        config_entry=mock_config_entry,
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    problem_state = hass.states.get("binary_sensor.enota_1_device_state")
    assert problem_state is not None
    assert problem_state.state == "off"
