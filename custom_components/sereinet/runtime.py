"""In-memory Sereinet runtime."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .protocol import ValidatedPacket


@dataclass
class DeviceState:
    """Last accepted state for one SERN device."""

    device_id: str
    sequence: int
    timestamp: int
    telemetry: dict[str, str | int | float | bool | None]
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SereinetRuntime:
    """Own accepted state and notify entities without polling."""

    def __init__(self) -> None:
        self.devices: dict[str, DeviceState] = {}
        self._listeners: set[Callable[[str], None]] = set()

    def last_sequence(self, device_id: str) -> int | None:
        state = self.devices.get(device_id)
        return None if state is None else state.sequence

    def accept(self, packet: ValidatedPacket) -> bool:
        is_new = packet.device_id not in self.devices
        self.devices[packet.device_id] = DeviceState(
            packet.device_id, packet.sequence, packet.timestamp, packet.telemetry
        )
        for listener in tuple(self._listeners):
            listener(packet.device_id)
        return is_new

    def subscribe(self, listener: Callable[[str], None]) -> Callable[[], None]:
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

