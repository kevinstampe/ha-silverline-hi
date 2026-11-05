"""Diagnostics support for Silverline Hi+."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .coordinator import SilverlineConfigEntry

TO_REDACT_ENTRY = {CONF_EMAIL, CONF_PASSWORD, "title", "unique_id"}
TO_REDACT_APPLIANCE = {"id", "serialNumber"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SilverlineConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT_ENTRY),
        "appliances": [
            async_redact_data(appliance, TO_REDACT_APPLIANCE)
            for appliance in coordinator.data.values()
        ],
    }
