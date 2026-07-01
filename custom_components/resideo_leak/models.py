"""Data model for a Resideo water leak / freeze detector.

Kept free of Home Assistant imports so it can be unit-tested standalone
against the sanitized API fixture.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, tzinfo
from typing import Any, Self

ALARM_DEVICE_OFFLINE = "DeviceOffline"


def _parse_dt(value: Any, tz: tzinfo | None) -> datetime | None:
    """Parse an API timestamp into a datetime.

    The API returns naive local timestamps (e.g. ``2026-07-01T11:12:02``);
    the location time zone is attached when the parsed value is naive.

    Args:
        value: Raw timestamp string from the API, or any non-string value.
        tz: Time zone to attach when the parsed timestamp is naive.

    Returns:
        A timezone-aware datetime, or None when the value cannot be parsed.
    """
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None and tz is not None:
        parsed = parsed.replace(tzinfo=tz)
    return parsed


def _nested(data: Mapping[str, Any], *keys: str) -> Any:
    """Walk nested mappings, returning None on any missing key.

    Args:
        data: Mapping to walk.
        *keys: Keys describing the path to follow, outermost first.

    Returns:
        The value at the nested path, or None if any key is missing.
    """
    current: Any = data
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


@dataclass
class LeakDevice:
    """Normalized view of one water leak detector."""

    device_id: str
    name: str
    location_id: int | None
    mac: str | None
    water_present: bool
    temperature: float | None
    humidity: float | None
    temp_high_limit: float | None
    temp_low_limit: float | None
    humidity_high_limit: float | None
    humidity_low_limit: float | None
    battery: int | None
    wifi_signal: int | None
    is_offline: bool
    is_alive: bool
    last_checkin: datetime | None
    reading_time: datetime | None
    firmware: str | None
    model: str | None
    alarms: list[dict[str, Any]] = field(default_factory=list)
    raw: Mapping[str, Any] = field(default_factory=dict)

    @property
    def online(self) -> bool:
        """Return whether the device is currently reachable.

        Returns:
            True when the detector is not reported offline.
        """
        return not self.is_offline

    @property
    def alarm_types(self) -> list[str]:
        """Return the active alarm type strings.

        Returns:
            The ``type`` value of each active alarm.
        """
        return [a["type"] for a in self.alarms if a.get("type")]

    @property
    def has_problem(self) -> bool:
        """Return whether a non-connectivity alarm is active.

        Returns:
            True when any active alarm other than ``DeviceOffline`` exists.
        """
        return any(t != ALARM_DEVICE_OFFLINE for t in self.alarm_types)

    @classmethod
    def from_api(
        cls,
        location_id: int | None,
        data: Mapping[str, Any],
        tz: tzinfo | None = None,
    ) -> Self:
        """Build a LeakDevice from a raw API device mapping.

        Args:
            location_id: Identifier of the location the device belongs to.
            data: Raw device mapping from the ``/locations`` payload.
            tz: Location time zone used to make timestamps timezone-aware.

        Returns:
            A populated LeakDevice instance.
        """
        readings = data.get("currentSensorReadings") or {}
        return cls(
            device_id=data["deviceID"],
            name=(
                data.get("userDefinedDeviceName")
                or data.get("deviceType")
                or "Leak Detector"
            ),
            location_id=location_id,
            mac=data.get("macID"),
            water_present=bool(data.get("waterPresent")),
            temperature=readings.get("temperature"),
            humidity=readings.get("humidity"),
            temp_high_limit=_nested(
                data, "deviceSettings", "temp", "high", "limit"
            ),
            temp_low_limit=_nested(
                data, "deviceSettings", "temp", "low", "limit"
            ),
            humidity_high_limit=_nested(
                data, "deviceSettings", "humidity", "high", "limit"
            ),
            humidity_low_limit=_nested(
                data, "deviceSettings", "humidity", "low", "limit"
            ),
            battery=data.get("batteryRemaining"),
            wifi_signal=data.get("wifiSignalStrength"),
            is_offline=bool(data.get("isDeviceOffline")),
            is_alive=bool(data.get("isAlive", True)),
            last_checkin=_parse_dt(data.get("lastCheckin"), tz),
            reading_time=_parse_dt(readings.get("time"), tz),
            firmware=data.get("firmwareVer"),
            model=data.get("deviceType") or data.get("deviceVariant"),
            alarms=list(data.get("currentAlarms") or []),
            raw=data,
        )
