"""Tests for Silverline Hi+ setup, entities and diagnostics."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.silverline_hi.api import SilverlineAuthError, SilverlineError

from .conftest import APPLIANCE_ID, EMAIL, PASSWORD


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_and_unload(
    hass: HomeAssistant, mock_api: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    """Test the entry sets up and unloads."""
    await _setup(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_retry_on_connection_error(
    hass: HomeAssistant, mock_api: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    """Test setup is retried when the cloud is unreachable."""
    mock_api.get_appliances.side_effect = SilverlineError("boom")
    await _setup(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_auth_failure_starts_reauth(
    hass: HomeAssistant, mock_api: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    """Test invalid credentials start a reauth flow."""
    mock_api.get_appliances.side_effect = SilverlineAuthError("bad")
    await _setup(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == SOURCE_REAUTH


async def test_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_api: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test entities are created with the expected names and unique IDs."""
    await _setup(hass, mock_config_entry)

    entries = er.async_entries_for_config_entry(entity_registry, mock_config_entry.entry_id)
    assert {entry.unique_id for entry in entries} == {
        f"{APPLIANCE_ID}_{suffix}"
        for suffix in (
            "light",
            "auto_mode",
            "fan_speed",
            "ventilation_timer",
            "reset_carbon_filter",
            "reset_grease_filter",
            "carbonFilterRemaining",
            "greaseFilterRemaining",
            "airQuality",
            "humidity",
            "temperature",
            "co2",
            "voc",
            "pressure",
            "bleConnectionStatus",
            "hobToHoodSetting",
        )
    }

    assert hass.states.get("light.kitchen_hood").state == STATE_ON
    assert hass.states.get("number.kitchen_hood_fan_speed").state == "2.0"
    assert hass.states.get("sensor.kitchen_hood_temperature").state == "21.5"
    assert hass.states.get("sensor.kitchen_hood_silverconnect_status").state == "1"


async def test_commands(
    hass: HomeAssistant, mock_api: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    """Test entity actions call the API."""
    await _setup(hass, mock_config_entry)

    await hass.services.async_call(
        "light", "turn_off", {ATTR_ENTITY_ID: "light.kitchen_hood"}, blocking=True
    )
    mock_api.set_light.assert_awaited_with(APPLIANCE_ID, False)

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: "number.kitchen_hood_fan_speed", "value": 3},
        blocking=True,
    )
    mock_api.set_fan_speed.assert_awaited_with(APPLIANCE_ID, 3)

    await hass.services.async_call(
        "switch", "turn_on", {ATTR_ENTITY_ID: "switch.kitchen_hood_auto_mode"}, blocking=True
    )
    mock_api.set_auto_mode.assert_awaited_with(APPLIANCE_ID, True)

    await hass.services.async_call(
        "button",
        "press",
        {ATTR_ENTITY_ID: "button.kitchen_hood_reset_grease_filter"},
        blocking=True,
    )
    mock_api.reset_grease_filter.assert_awaited_with(APPLIANCE_ID)


async def test_command_error(
    hass: HomeAssistant, mock_api: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    """Test a failing command raises a user-facing error."""
    await _setup(hass, mock_config_entry)
    mock_api.set_light.side_effect = SilverlineError("nope")

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "light", "turn_on", {ATTR_ENTITY_ID: "light.kitchen_hood"}, blocking=True
        )


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_api: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test diagnostics redact credentials and identifiers."""
    await _setup(hass, mock_config_entry)

    result = await get_diagnostics_for_config_entry(hass, hass_client, mock_config_entry)
    serialized = str(result)
    assert EMAIL not in serialized
    assert PASSWORD not in serialized
    assert APPLIANCE_ID not in serialized
    assert result["appliances"][0]["temperature"] == 21.5
