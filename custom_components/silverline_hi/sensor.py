"""Sensor platform for Silverline Hi+."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    EntityCategory,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SilverlineConfigEntry
from .entity import SilverlineEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class SilverlineSensorDescription(SensorEntityDescription):
    """Describes a Silverline Hi+ sensor."""

    numeric: bool = True


SENSORS: tuple[SilverlineSensorDescription, ...] = (
    SilverlineSensorDescription(
        key="carbonFilterRemaining",
        translation_key="carbon_filter_remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SilverlineSensorDescription(
        key="greaseFilterRemaining",
        translation_key="grease_filter_remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SilverlineSensorDescription(
        key="airQuality",
        translation_key="air_quality",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SilverlineSensorDescription(
        key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SilverlineSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SilverlineSensorDescription(
        key="co2",
        device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SilverlineSensorDescription(
        key="voc",
        translation_key="voc",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SilverlineSensorDescription(
        key="pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.HPA,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SilverlineSensorDescription(
        key="bleConnectionStatus",
        translation_key="silverconnect_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        numeric=False,
    ),
    SilverlineSensorDescription(
        key="hobToHoodSetting",
        translation_key="hob_to_hood_setting",
        entity_category=EntityCategory.DIAGNOSTIC,
        numeric=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SilverlineConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Silverline Hi+ sensors from config entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        SilverlineSensor(coordinator, appliance_id, description)
        for appliance_id in coordinator.data
        for description in SENSORS
    )


class SilverlineSensor(SilverlineEntity, SensorEntity):
    """Representation of a Silverline Hi+ sensor."""

    entity_description: SilverlineSensorDescription

    def __init__(
        self, coordinator, appliance_id: str, description: SilverlineSensorDescription
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, appliance_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        value = self.appliance_data.get(self.entity_description.key)
        if value is None:
            return None
        if self.entity_description.numeric:
            return float(value)
        return str(value)
