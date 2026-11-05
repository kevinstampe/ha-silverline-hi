"""Data update coordinator for Silverline Hi+."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SilverlineAPI, SilverlineAuthError, SilverlineError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


@dataclass
class SilverlineData:
    """Runtime data stored on the config entry."""

    api: SilverlineAPI
    coordinator: SilverlineCoordinator


type SilverlineConfigEntry = ConfigEntry[SilverlineData]


class SilverlineCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetch state for all appliances on the account."""

    config_entry: SilverlineConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: SilverlineConfigEntry, api: SilverlineAPI
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data from the API."""
        try:
            return await self.api.get_appliances()
        except SilverlineAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="invalid_auth"
            ) from err
        except SilverlineError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err
