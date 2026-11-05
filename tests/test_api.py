"""Tests for the Silverline Hi+ API client."""

from __future__ import annotations

import json

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.silverline_hi.api import (
    SilverlineAPI,
    SilverlineAuthError,
    SilverlineConnectionError,
    SilverlineError,
)
from custom_components.silverline_hi.const import (
    AUTH_URL,
    COMMAND_URL,
    DEVICE_STATE_URL,
    FIRESTORE_URL,
)

APPLIANCE_ID = "abc"
USER_ID = "user1"
USER_URL = f"{FIRESTORE_URL}/users/{USER_ID}"

AUTH_OK = {"idToken": "token", "localId": USER_ID}
USER_DOC = {
    "fields": {
        "appliances": {
            "mapValue": {
                "fields": {
                    APPLIANCE_ID: {
                        "stringValue": json.dumps(
                            {
                                "description": "Kitchen hood",
                                "serialNumber": "123",
                                "attributes": {"maxVentilationSpeed": 3},
                            }
                        )
                    }
                }
            }
        }
    }
}
DEVICE_STATE = {
    APPLIANCE_ID: json.dumps(
        {"device_state": {"ventilation": 2, "lighting": 1, "temperatureCelcius": 22.5}}
    )
}


def _api(hass: HomeAssistant) -> SilverlineAPI:
    return SilverlineAPI(async_get_clientsession(hass), "user@example.com", "pw")


async def test_get_appliances(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Test login and parsing of appliance state."""
    aioclient_mock.post(AUTH_URL, json=AUTH_OK)
    aioclient_mock.get(USER_URL, json=USER_DOC)
    aioclient_mock.get(DEVICE_STATE_URL, json=DEVICE_STATE)

    appliances = await _api(hass).get_appliances()

    hood = appliances[APPLIANCE_ID]
    assert hood["name"] == "Kitchen hood"
    assert hood["serialNumber"] == "123"
    assert hood["maxVentilationSpeed"] == 3
    assert hood["ventilationSpeed"] == 2
    assert hood["lightBrightness"] == 1
    assert hood["temperature"] == 22.5
    assert hood["humidity"] == 0


@pytest.mark.parametrize(
    ("message", "error"),
    [
        ("INVALID_LOGIN_CREDENTIALS", SilverlineAuthError),
        ("INVALID_PASSWORD : extra detail", SilverlineAuthError),
        ("TOO_MANY_ATTEMPTS_TRY_LATER", SilverlineError),
    ],
)
async def test_authenticate_errors(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    message: str,
    error: type[Exception],
) -> None:
    """Test Firebase login errors are mapped to the right exception."""
    aioclient_mock.post(AUTH_URL, status=400, json={"error": {"message": message}})
    with pytest.raises(error):
        await _api(hass).authenticate()


async def test_connection_error(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Test network errors raise a connection error."""
    aioclient_mock.post(AUTH_URL, exc=aiohttp.ClientError())
    with pytest.raises(SilverlineConnectionError):
        await _api(hass).authenticate()


async def test_reauthenticates_on_401(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test an expired token triggers one new login."""
    aioclient_mock.post(AUTH_URL, json=AUTH_OK)
    aioclient_mock.post(COMMAND_URL, status=401)
    api = _api(hass)

    with pytest.raises(SilverlineAuthError):
        await api.set_fan_speed(APPLIANCE_ID, 2)

    auth_calls = [call for call in aioclient_mock.mock_calls if str(call[1]).startswith(AUTH_URL)]
    assert len(auth_calls) == 2


async def test_command_payloads(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Test commands send the expected payloads."""
    aioclient_mock.post(AUTH_URL, json=AUTH_OK)
    aioclient_mock.post(COMMAND_URL, json={})
    api = _api(hass)

    await api.set_fan_speed(APPLIANCE_ID, 3)
    await api.set_light(APPLIANCE_ID, True)
    await api.set_auto_mode(APPLIANCE_ID, True)
    await api.set_ventilation_timer(APPLIANCE_ID, 600)
    await api.reset_carbon_filter(APPLIANCE_ID)
    await api.reset_grease_filter(APPLIANCE_ID)

    payloads = [call[2] for call in aioclient_mock.mock_calls if str(call[1]) == COMMAND_URL]
    assert payloads == [
        {"id": APPLIANCE_ID, "component": 1, "value": 3},
        {"id": APPLIANCE_ID, "component": 2, "value": 1},
        {"id": APPLIANCE_ID, "component": 1, "value": 5},
        {"id": APPLIANCE_ID, "component": 1, "params": {"hood": {"ventilationTimerSecs": 600}}},
        {"id": APPLIANCE_ID, "component": 2, "params": {"hood": {"carbonFilterTimerMins": 18000}}},
        {"id": APPLIANCE_ID, "component": 2, "params": {"hood": {"greaseFilterTimerMins": 7200}}},
    ]


async def test_command_http_error(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Test a non-auth HTTP error raises a generic error."""
    aioclient_mock.post(AUTH_URL, json=AUTH_OK)
    aioclient_mock.post(COMMAND_URL, status=500, text="oops")
    with pytest.raises(SilverlineError, match="500"):
        await _api(hass).set_light(APPLIANCE_ID, False)
