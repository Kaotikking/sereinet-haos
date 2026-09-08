"""Dependency-free SERN ingress v1 validation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import math
import time
from typing import Any, Mapping

MAX_BODY_BYTES = 16_384
MAX_TELEMETRY_FIELDS = 64


class PacketError(ValueError):
    """Packet did not satisfy the SERN ingress contract."""


@dataclass(frozen=True)
class ValidatedPacket:
    """Validated SERN packet."""

    device_id: str
    timestamp: int
    sequence: int
    telemetry: dict[str, str | int | float | bool | None]


def canonical_payload(packet: Mapping[str, Any]) -> bytes:
    """Return the exact bytes covered by the packet signature."""
    unsigned = {key: value for key, value in packet.items() if key != "signature"}
    return json.dumps(
        unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sign_packet(packet: Mapping[str, Any], key: str) -> str:
    """Create a lowercase hex HMAC-SHA256 signature."""
    return hmac.new(key.encode("utf-8"), canonical_payload(packet), hashlib.sha256).hexdigest()


def validate_packet(
    packet: Mapping[str, Any], key: str, last_sequence: int | None, now: int | None = None
) -> ValidatedPacket:
    """Validate identity, freshness, monotonic sequence, telemetry, and signature."""
    if packet.get("version") != 1:
        raise PacketError("unsupported_version")
    device_id = packet.get("device_id")
    if not isinstance(device_id, str) or not device_id or len(device_id) > 64:
        raise PacketError("invalid_device_id")
    if any(not (ch.isalnum() or ch in "-_.") for ch in device_id):
        raise PacketError("invalid_device_id")
    timestamp = packet.get("timestamp")
    sequence = packet.get("sequence")
    if isinstance(timestamp, bool) or not isinstance(timestamp, int):
        raise PacketError("invalid_timestamp")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise PacketError("invalid_sequence")
    current = int(time.time()) if now is None else now
    if abs(current - timestamp) > 300:
        raise PacketError("stale_timestamp")
    if last_sequence is not None and sequence <= last_sequence:
        raise PacketError("replayed_sequence")
    telemetry = packet.get("telemetry")
    if not isinstance(telemetry, dict) or len(telemetry) > MAX_TELEMETRY_FIELDS:
        raise PacketError("invalid_telemetry")
    clean: dict[str, str | int | float | bool | None] = {}
    for name, value in telemetry.items():
        if not isinstance(name, str) or not name or len(name) > 64:
            raise PacketError("invalid_telemetry_key")
        if any(not (ch.isalnum() or ch == "_") for ch in name):
            raise PacketError("invalid_telemetry_key")
        if value is not None and not isinstance(value, (str, int, float, bool)):
            raise PacketError("invalid_telemetry_value")
        if isinstance(value, float) and not math.isfinite(value):
            raise PacketError("invalid_telemetry_value")
        if isinstance(value, str) and len(value) > 256:
            raise PacketError("invalid_telemetry_value")
        clean[name] = value
    signature = packet.get("signature")
    if not isinstance(signature, str) or len(signature) != 64:
        raise PacketError("invalid_signature")
    expected = sign_packet(packet, key)
    if not hmac.compare_digest(signature.lower(), expected):
        raise PacketError("invalid_signature")
    return ValidatedPacket(device_id, timestamp, sequence, clean)

