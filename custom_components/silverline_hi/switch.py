"""Switch platform for Silverline Hi+."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SilverlineConfigEntry
from .entity import SilverlineEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SilverlineConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Silverline Hi+ switches from config entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        SilverlineAutoModeSwitch(coordinator, appliance_id) for appliance_id in coordinator.data
    )


class SilverlineAutoModeSwitch(SilverlineEntity, SwitchEntity):
    """Representation of auto mode switch."""

    _attr_translation_key = "auto_mode"

    def __init__(self, coordinator, appliance_id: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, appliance_id, "auto_mode")

    @property
    def is_on(self) -> bool:
        """Return true if auto mode is on."""
        return self.appliance_data.get("isAuto", 0) == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on auto mode."""
        await self._async_command(self.coordinator.api.set_auto_mode(self._appliance_id, True))

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off auto mode."""
        await self._async_command(self.coordinator.api.set_auto_mode(self._appliance_id, False))
