"""Base entity for the Resideo Leak Detectors integration."""

from typing import Any

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import ResideoLeakCoordinator
from .models import LeakDevice


class ResideoLeakEntity(CoordinatorEntity[ResideoLeakCoordinator]):
    """Base entity keyed by the detector's stable device id."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ResideoLeakCoordinator,
        device_id: str,
        key: str,
    ) -> None:
        """Initialize the entity.

        Args:
            coordinator: Coordinator providing device state.
            device_id: Stable Resideo device id this entity represents.
            key: Entity description key, unique per device.
        """
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{key}"

    @property
    def device(self) -> LeakDevice:
        """Return the current device snapshot from the coordinator.

        Returns:
            The latest LeakDevice for this entity.
        """
        return self.coordinator.data[self._device_id]

    @property
    def available(self) -> bool:
        """Return whether the entity is available.

        Returns:
            True when the last update succeeded and the device is present.
        """
        return super().available and self._device_id in self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry info for this detector.

        Returns:
            Device registry metadata (identifiers, model, firmware, name).
        """
        device = self.device
        connections = set()
        if device.mac:
            connections.add((dr.CONNECTION_NETWORK_MAC, device.mac))
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            connections=connections,
            manufacturer=MANUFACTURER,
            model=device.model,
            name=device.name,
            sw_version=device.firmware,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return attributes from the description's attrs_fn, if any.

        Returns:
            The mapping produced by the entity description's ``attrs_fn``, or
            None when the description defines no attributes.
        """
        attrs_fn = getattr(self.entity_description, "attrs_fn", None)
        if attrs_fn is None:
            return None
        return attrs_fn(self.device)
