"""Light platform for Silverline Hi+."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
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
    """Set up Silverline Hi+ light from config entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        SilverlineLight(coordinator, appliance_id) for appliance_id in coordinator.data
    )


class SilverlineLight(SilverlineEntity, LightEntity):
    """Representation of a Silverline Hi+ light."""

    _attr_name = None
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, coordinator, appliance_id: str) -> None:
        """Initialize the light."""
        super().__init__(coordinator, appliance_id, "light")

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self.appliance_data.get("lightBrightness", 0) > 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        await self._async_command(self.coordinator.api.set_light(self._appliance_id, True))

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self._async_command(self.coordinator.api.set_light(self._appliance_id, False))
