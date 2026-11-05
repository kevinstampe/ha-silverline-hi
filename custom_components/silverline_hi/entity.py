"""Base entity for Silverline Hi+."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Any

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SilverlineError
from .const import DOMAIN
from .coordinator import SilverlineCoordinator


class SilverlineEntity(CoordinatorEntity[SilverlineCoordinator]):
    """Base class for Silverline Hi+ entities."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: SilverlineCoordinator, appliance_id: str, unique_suffix: str
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        appliance = coordinator.data[appliance_id]
        self._appliance_id = appliance_id
        self._attr_unique_id = f"{appliance_id}_{unique_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, appliance_id)},
            name=appliance["name"],
            manufacturer="Silverline",
            model="Hi+",
            serial_number=appliance.get("serialNumber"),
        )

    @property
    def available(self) -> bool:
        """Return if the appliance is still reported by the API."""
        return super().available and self._appliance_id in self.coordinator.data

    @property
    def appliance_data(self) -> dict[str, Any]:
        """Return the latest coordinator data for this appliance."""
        return self.coordinator.data.get(self._appliance_id, {})

    async def _async_command(self, command: Awaitable[None]) -> None:
        """Run an API command, raise a user-facing error on failure and refresh."""
        try:
            await command
        except SilverlineError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        await self.coordinator.async_request_refresh()
