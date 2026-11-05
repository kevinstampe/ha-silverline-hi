"""Number platform for Silverline Hi+."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
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
    """Set up Silverline Hi+ number entities from config entry."""
    coordinator = entry.runtime_data.coordinator
    entities: list[NumberEntity] = []
    for appliance_id in coordinator.data:
        entities.append(SilverlineFanSpeedNumber(coordinator, appliance_id))
        entities.append(SilverlineVentilationTimerNumber(coordinator, appliance_id))
    async_add_entities(entities)


class SilverlineFanSpeedNumber(SilverlineEntity, NumberEntity):
    """Representation of fan speed number entity."""

    _attr_translation_key = "fan_speed"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_step = 1

    def __init__(self, coordinator, appliance_id: str) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, appliance_id, "fan_speed")
        self._attr_native_max_value = self.appliance_data.get("maxVentilationSpeed", 4)

    @property
    def native_value(self) -> float:
        """Return the current fan speed."""
        return float(self.appliance_data.get("ventilationSpeed", 0))

    async def async_set_native_value(self, value: float) -> None:
        """Set the fan speed."""
        speed = int(value)
        # Optimistic update so the UI responds immediately
        self.appliance_data["ventilationSpeed"] = speed
        self.async_write_ha_state()
        await self._async_command(self.coordinator.api.set_fan_speed(self._appliance_id, speed))


class SilverlineVentilationTimerNumber(SilverlineEntity, NumberEntity):
    """Representation of ventilation timer number entity."""

    _attr_translation_key = "ventilation_timer"
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = 15359  # From device state
    _attr_native_step = 60
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(self, coordinator, appliance_id: str) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, appliance_id, "ventilation_timer")

    @property
    def native_value(self) -> float:
        """Return the current timer value."""
        return float(self.appliance_data.get("ventilationTimer", 0))

    async def async_set_native_value(self, value: float) -> None:
        """Set the ventilation timer."""
        await self._async_command(
            self.coordinator.api.set_ventilation_timer(self._appliance_id, int(value))
        )
