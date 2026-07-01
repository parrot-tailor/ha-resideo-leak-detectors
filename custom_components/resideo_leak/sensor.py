"""Sensor platform for the Resideo Leak Detectors integration."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)
from homeassistant.helpers.typing import StateType

from .coordinator import ResideoLeakConfigEntry, ResideoLeakCoordinator
from .entity import ResideoLeakEntity
from .models import LeakDevice


@dataclass(frozen=True, kw_only=True)
class ResideoSensorDescription(SensorEntityDescription):
    """Describes a Resideo leak detector sensor.

    Attributes:
        value_fn: Maps a device to the sensor's native value.
        attrs_fn: Optional map of a device to extra state attributes.
    """

    value_fn: Callable[[LeakDevice], StateType | datetime]
    attrs_fn: Callable[[LeakDevice], dict[str, Any]] | None = None


def _temp_attrs(device: LeakDevice) -> dict[str, Any]:
    """Return the configured temperature alarm thresholds.

    Args:
        device: Device to read the thresholds from.

    Returns:
        Mapping with ``high_limit`` and ``low_limit`` in degrees Celsius.
    """
    return {
        "high_limit": device.temp_high_limit,
        "low_limit": device.temp_low_limit,
    }


def _humidity_attrs(device: LeakDevice) -> dict[str, Any]:
    """Return the configured humidity alarm thresholds.

    Args:
        device: Device to read the thresholds from.

    Returns:
        Mapping with ``high_limit`` and ``low_limit`` as percentages.
    """
    return {
        "high_limit": device.humidity_high_limit,
        "low_limit": device.humidity_low_limit,
    }


SENSORS: tuple[ResideoSensorDescription, ...] = (
    ResideoSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda device: device.temperature,
        attrs_fn=_temp_attrs,
    ),
    ResideoSensorDescription(
        key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda device: device.humidity,
        attrs_fn=_humidity_attrs,
    ),
    ResideoSensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda device: device.battery,
    ),
    ResideoSensorDescription(
        key="wifi_signal",
        translation_key="wifi_signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        value_fn=lambda device: device.wifi_signal,
    ),
    ResideoSensorDescription(
        key="last_checkin",
        translation_key="last_checkin",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.last_checkin,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ResideoLeakConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform from a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry holding the coordinator in ``runtime_data``.
        async_add_entities: Callback used to register new entities.
    """
    coordinator = entry.runtime_data
    async_add_entities(
        ResideoSensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in SENSORS
    )


class ResideoSensor(ResideoLeakEntity, SensorEntity):
    """A sensor for one water leak detector."""

    entity_description: ResideoSensorDescription

    def __init__(
        self,
        coordinator: ResideoLeakCoordinator,
        device_id: str,
        description: ResideoSensorDescription,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Coordinator providing device state.
            device_id: Stable Resideo device id this entity represents.
            description: Entity description describing the sensor.
        """
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType | datetime:
        """Return the current sensor value.

        Returns:
            The value produced by the description's ``value_fn``.
        """
        return self.entity_description.value_fn(self.device)
