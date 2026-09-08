"""Sereinet sensor platform."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .runtime import SereinetRuntime

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create sensors for devices known at platform setup."""
    runtime: SereinetRuntime = hass.data[DOMAIN][entry.entry_id]
    known: set[tuple[str, str]] = set()

    @callback
    def add_for_device(device_id: str) -> None:
        state = runtime.devices.get(device_id)
        if state is None:
            return
        additions = []
        for key in state.telemetry:
            marker = (device_id, key)
            if marker not in known:
                known.add(marker)
                additions.append(SereinetSensor(entry, runtime, device_id, key))
        if additions:
            async_add_entities(additions)

    for device_id in runtime.devices:
        add_for_device(device_id)
    entry.async_on_unload(runtime.subscribe(add_for_device))


class SereinetSensor(SensorEntity):
    """One projected SERN telemetry value."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, runtime: SereinetRuntime, device_id: str, key: str) -> None:
        self._runtime = runtime
        self._device_id = device_id
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{device_id}_{key}"
        self._attr_name = key.replace("_", " ").title()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_id,
            manufacturer="Serein",
            model="SERN node",
        )

    @property
    def native_value(self):
        """Return the last accepted value from memory."""
        return self._runtime.devices[self._device_id].telemetry.get(self._key)

    async def async_added_to_hass(self) -> None:
        @callback
        def updated(device_id: str) -> None:
            if device_id == self._device_id:
                self.async_write_ha_state()

        self.async_on_remove(self._runtime.subscribe(updated))

