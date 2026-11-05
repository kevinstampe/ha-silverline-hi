"""Fixtures for Silverline Hi+ tests."""

from __future__ import annotations

from collections.abc import Generator
from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.silverline_hi.const import DOMAIN

APPLIANCE_ID = "test-appliance-id"
EMAIL = "user@example.com"
PASSWORD = "secret"

APPLIANCES: dict[str, dict[str, Any]] = {
    APPLIANCE_ID: {
        "id": APPLIANCE_ID,
        "name": "Kitchen hood",
        "serialNumber": "1234567890",
        "deviceType": "hood",
        "maxVentilationSpeed": 4,
        "maxLightingIntensity": 1,
        "ventilationSpeed": 2,
        "lightBrightness": 1,
        "carbonFilterRemaining": 17000,
        "greaseFilterRemaining": 7000,
        "ventilationTimer": 0,
        "airQuality": 95,
        "humidity": 45,
        "temperature": 21.5,
        "co2": 600,
        "voc": 120,
        "pressure": 1013.25,
        "isAuto": 0,
        "bleConnectionStatus": 1,
        "hobToHoodSetting": 0,
    }
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading custom integrations in all tests."""


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"Silverline Hi+ ({EMAIL})",
        unique_id=EMAIL,
        data={CONF_EMAIL: EMAIL, CONF_PASSWORD: PASSWORD},
    )


@pytest.fixture
def mock_api() -> Generator[AsyncMock]:
    """Patch the API client used by the integration and the config flow."""
    with (
        patch("custom_components.silverline_hi.SilverlineAPI", autospec=True) as api_cls,
        patch("custom_components.silverline_hi.config_flow.SilverlineAPI", new=api_cls),
    ):
        api = api_cls.return_value
        api.get_appliances.return_value = deepcopy(APPLIANCES)
        yield api
