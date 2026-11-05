"""Async API client for the Silverline Hi+ cloud."""

from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp

from .const import (
    AUTH_URL,
    CARBON_FILTER_LIFETIME,
    COMMAND_URL,
    COMPONENT_FILTER,
    COMPONENT_LIGHT,
    COMPONENT_VENTILATION,
    DEVICE_STATE_URL,
    FIREBASE_API_KEY,
    FIRESTORE_URL,
    GREASE_FILTER_LIFETIME,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)

AUTH_ERROR_CODES = {
    "EMAIL_NOT_FOUND",
    "INVALID_EMAIL",
    "INVALID_LOGIN_CREDENTIALS",
    "INVALID_PASSWORD",
    "USER_DISABLED",
}


class SilverlineError(Exception):
    """Base error for the Silverline Hi+ API."""


class SilverlineAuthError(SilverlineError):
    """Invalid credentials."""


class SilverlineConnectionError(SilverlineError):
    """Could not communicate with the Silverline Hi+ cloud."""


class SilverlineAPI:
    """Silverline Hi+ API client."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str) -> None:
        """Initialize the API client."""
        self._session = session
        self._email = email
        self._password = password
        self._id_token: str | None = None
        self._user_id: str | None = None

    async def authenticate(self) -> None:
        """Sign in with Firebase and store the ID token."""
        try:
            async with self._session.post(
                AUTH_URL,
                params={"key": FIREBASE_API_KEY},
                json={
                    "email": self._email,
                    "password": self._password,
                    "returnSecureToken": True,
                },
                timeout=REQUEST_TIMEOUT,
            ) as response:
                data = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise SilverlineConnectionError(f"Error connecting to Silverline Hi+: {err}") from err

        if "error" in data:
            message = str(data["error"].get("message", ""))
            if message.split(" ", 1)[0] in AUTH_ERROR_CODES:
                raise SilverlineAuthError(message)
            raise SilverlineError(f"Authentication failed: {message}")

        self._id_token = data["idToken"]
        self._user_id = data["localId"]
        _LOGGER.debug("Authenticated with Silverline Hi+ cloud")

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        retry_auth: bool = True,
    ) -> Any:
        """Make an authenticated request, re-authenticating once on 401."""
        if self._id_token is None:
            await self.authenticate()

        try:
            async with self._session.request(
                method,
                url,
                params=params,
                json=payload,
                headers={"Authorization": f"Bearer {self._id_token}"},
                timeout=REQUEST_TIMEOUT,
            ) as response:
                if response.status == 401 and retry_auth:
                    _LOGGER.debug("Token expired, re-authenticating")
                    self._id_token = None
                    return await self._request(
                        method, url, params=params, payload=payload, retry_auth=False
                    )
                if response.status == 401:
                    raise SilverlineAuthError("Unauthorized")
                if response.status >= 400:
                    text = await response.text()
                    raise SilverlineError(f"Request failed ({response.status}): {text}")
                return await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise SilverlineConnectionError(f"Error connecting to Silverline Hi+: {err}") from err

    async def get_appliances(self) -> dict[str, dict[str, Any]]:
        """Return all appliances on the account with their current state, keyed by ID."""
        if self._user_id is None:
            await self.authenticate()

        user_doc = await self._request("GET", f"{FIRESTORE_URL}/users/{self._user_id}")
        appliance_fields = (
            user_doc.get("fields", {}).get("appliances", {}).get("mapValue", {}).get("fields", {})
        )

        appliances: dict[str, dict[str, Any]] = {}
        for appliance_id, value in appliance_fields.items():
            if "stringValue" not in value:
                continue
            appliance_data = json.loads(value["stringValue"])

            state_data = await self._request("GET", DEVICE_STATE_URL, params={"id": appliance_id})
            device_state = json.loads(state_data.get(appliance_id, "{}")).get("device_state", {})
            attributes = appliance_data.get("attributes", {})

            appliances[appliance_id] = {
                "id": appliance_id,
                "name": appliance_data.get("description", "Hood"),
                "serialNumber": appliance_data.get("serialNumber"),
                "deviceType": appliance_data.get("deviceType"),
                "maxVentilationSpeed": attributes.get("maxVentilationSpeed", 4),
                "maxLightingIntensity": attributes.get("maxLightingIntensity", 1),
                "ventilationSpeed": device_state.get("ventilation", 0),
                "lightBrightness": device_state.get("lighting", 0),
                "carbonFilterRemaining": device_state.get("carbonFilterRemaningTime", 0),
                "greaseFilterRemaining": device_state.get("greaseFilterRemaningTime", 0),
                "ventilationTimer": device_state.get("ventilationTimerSecs", 0),
                "airQuality": device_state.get("airQualityPercentage", 0),
                "humidity": device_state.get("humidityPercentage", 0),
                "temperature": device_state.get("temperatureCelcius", 0),
                "co2": device_state.get("co2Eq_ppm", 0),
                "voc": device_state.get("vocEq_ppm", 0),
                "pressure": device_state.get("pres_hpa", 0),
                "isAuto": device_state.get("isAuto", 0),
                "bleConnectionStatus": device_state.get("bleConnectionStatus", 0),
                "hobToHoodSetting": device_state.get("hobToHoodSetting", 0),
            }

        return appliances

    async def _send_command(self, payload: dict[str, Any]) -> None:
        """Send a command to an appliance."""
        _LOGGER.debug("Sending command: %s", payload)
        await self._request("POST", COMMAND_URL, payload=payload)

    async def set_fan_speed(self, appliance_id: str, speed: int) -> None:
        """Set fan speed (0 = off)."""
        await self._send_command(
            {"id": appliance_id, "component": COMPONENT_VENTILATION, "value": speed}
        )

    async def set_light(self, appliance_id: str, on: bool) -> None:
        """Turn the light on or off."""
        await self._send_command(
            {"id": appliance_id, "component": COMPONENT_LIGHT, "value": 1 if on else 0}
        )

    async def set_auto_mode(self, appliance_id: str, enabled: bool) -> None:
        """Turn auto mode on or off."""
        await self._send_command(
            {
                "id": appliance_id,
                "component": COMPONENT_VENTILATION,
                "value": 5 if enabled else 0,  # 5 = auto
            }
        )

    async def set_ventilation_timer(self, appliance_id: str, seconds: int) -> None:
        """Set the ventilation timer in seconds."""
        await self._send_command(
            {
                "id": appliance_id,
                "component": COMPONENT_VENTILATION,
                "params": {"hood": {"ventilationTimerSecs": seconds}},
            }
        )

    async def reset_carbon_filter(self, appliance_id: str) -> None:
        """Reset the carbon filter timer."""
        await self._send_command(
            {
                "id": appliance_id,
                "component": COMPONENT_FILTER,
                "params": {"hood": {"carbonFilterTimerMins": CARBON_FILTER_LIFETIME}},
            }
        )

    async def reset_grease_filter(self, appliance_id: str) -> None:
        """Reset the grease filter timer."""
        await self._send_command(
            {
                "id": appliance_id,
                "component": COMPONENT_FILTER,
                "params": {"hood": {"greaseFilterTimerMins": GREASE_FILTER_LIFETIME}},
            }
        )
