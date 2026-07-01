"""Binary sensor platform for the Resideo Leak Detectors integration."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)

from .coordinator import ResideoLeakConfigEntry, ResideoLeakCoordinator
from .entity import ResideoLeakEntity
from .models import LeakDevice


@dataclass(frozen=True, kw_only=True)
class ResideoBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a Resideo leak detector binary sensor.

    Attributes:
        value_fn: Maps a device to the binary state.
        attrs_fn: Optional map of a device to extra state attributes.
    """

    value_fn: Callable[[LeakDevice], bool | None]
    attrs_fn: Callable[[LeakDevice], dict[str, Any]] | None = None


BINARY_SENSORS: tuple[ResideoBinarySensorDescription, ...] = (
    ResideoBinarySensorDescription(
        key="leak",
        translation_key="leak",
        device_class=BinarySensorDeviceClass.MOISTURE,
        value_fn=lambda device: device.water_present,
    ),
    ResideoBinarySensorDescription(
        key="connectivity",
        translation_key="connectivity",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda device: device.online,
        attrs_fn=lambda device: {"is_alive": device.is_alive},
    ),
    ResideoBinarySensorDescription(
        key="problem",
        translation_key="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda device: device.has_problem,
        attrs_fn=lambda device: {"active_alarms": device.alarm_types},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ResideoLeakConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the binary sensor platform from a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry holding the coordinator in ``runtime_data``.
        async_add_entities: Callback used to register new entities.
    """
    coordinator = entry.runtime_data
    async_add_entities(
        ResideoBinarySensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in BINARY_SENSORS
    )


class ResideoBinarySensor(ResideoLeakEntity, BinarySensorEntity):
    """A binary sensor for one water leak detector."""

    entity_description: ResideoBinarySensorDescription

    def __init__(
        self,
        coordinator: ResideoLeakCoordinator,
        device_id: str,
        description: ResideoBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor.

        Args:
            coordinator: Coordinator providing device state.
            device_id: Stable Resideo device id this entity represents.
            description: Entity description describing the binary sensor.
        """
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the current binary state.

        Returns:
            The value produced by the description's ``value_fn``.
        """
        return self.entity_description.value_fn(self.device)
