"""Unit tests for the standalone LeakDevice model.

The model module is imported directly from its file path so these tests run
without Home Assistant installed (the package __init__ imports HA).
"""

from datetime import datetime
import importlib.util
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

BASE = Path(__file__).resolve().parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "leak_locations.json"

_spec = importlib.util.spec_from_file_location(
    "resideo_models",
    BASE / "custom_components" / "resideo_leak" / "models.py",
)
assert _spec is not None
assert _spec.loader is not None
models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(models)


def _load_devices() -> list:
    """Parse leak detectors out of the sanitized fixture."""
    data = json.loads(FIXTURE.read_text())
    tz = ZoneInfo("America/Los_Angeles")
    devices = []
    for location in data:
        for raw in location["devices"]:
            if raw.get("deviceClass") != "LeakDetector":
                continue
            devices.append(
                models.LeakDevice.from_api(location["locationID"], raw, tz)
            )
    return devices


@pytest.fixture
def devices() -> list:
    """Return the parsed fixture devices."""
    return _load_devices()


def test_non_leak_devices_are_filtered(devices: list) -> None:
    """Only LeakDetector devices are parsed; the thermostat is dropped."""
    assert len(devices) == 2


def test_normal_device_fields(devices: list) -> None:
    """A healthy detector maps to the expected values."""
    device = next(d for d in devices if d.name == "Test Laundry")
    assert device.water_present is False
    assert device.temperature == 19.94
    assert device.humidity == 49.9
    assert device.battery == 39
    assert device.wifi_signal == -52
    assert device.online is True
    assert device.has_problem is False
    assert device.alarm_types == []
    assert device.mac == "AA:BB:CC:00:00:01"
    assert device.temp_high_limit == 37
    assert device.humidity_low_limit == 20


def test_leak_and_offline_device(devices: list) -> None:
    """A leaking, offline detector with an alarm maps correctly."""
    device = next(d for d in devices if d.name == "Test Garage")
    assert device.water_present is True
    assert device.online is False
    assert device.is_alive is False
    assert device.has_problem is True
    assert "HighHumidity" in device.alarm_types


def test_timestamps_are_timezone_aware(devices: list) -> None:
    """Parsed timestamps carry tz info (required by HA TIMESTAMP sensors)."""
    for device in devices:
        assert device.last_checkin is not None
        assert device.last_checkin.tzinfo is not None
        if device.reading_time is not None:
            assert device.reading_time.tzinfo is not None


def test_missing_timezone_leaves_naive_when_none() -> None:
    """No zone -> naive timestamps (the coordinator supplies the tz)."""
    device = models.LeakDevice.from_api(
        1,
        {
            "deviceID": "x",
            "lastCheckin": "2026-07-01T05:58:49",
            "currentSensorReadings": {},
        },
        None,
    )
    assert isinstance(device.last_checkin, datetime)
    assert device.last_checkin.tzinfo is None
