"""Button platform for Silverline Hi+."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SilverlineConfigEntry
from .entity import SilverlineEntity

PARALLEL_UPDATES = 1

FILTER_TYPES = ("carbon", "grease")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SilverlineConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Silverline Hi+ buttons from config entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        SilverlineFilterResetButton(coordinator, appliance_id, filter_type)
        for appliance_id in coordinator.data
        for filter_type in FILTER_TYPES
    )


class SilverlineFilterResetButton(SilverlineEntity, ButtonEntity):
    """Representation of a filter reset button."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, appliance_id: str, filter_type: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator, appliance_id, f"reset_{filter_type}_filter")
        self._filter_type = filter_type
        self._attr_translation_key = f"reset_{filter_type}_filter"

    async def async_press(self) -> None:
        """Handle the button press."""
        api = self.coordinator.api
        if self._filter_type == "carbon":
            await self._async_command(api.reset_carbon_filter(self._appliance_id))
        else:
            await self._async_command(api.reset_grease_filter(self._appliance_id))
