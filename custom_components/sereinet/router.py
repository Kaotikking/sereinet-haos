"""Generic default-deny SERN domain router.

The router understands protocol identity, capability projection and transport
control.  It deliberately contains no Morph lifecycle or DNA rules.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Mapping

ROUTER_SCHEMA = "sern.router.v1"
MORPHWORLD_PROTOCOL = "MORPHWORLD"
MESSAGE_TYPES = {"COMMAND", "EVENT", "RECEIPT", "OPEN_TRANSPORT", "CLOSE_TRANSPORT"}
NINE_CORE_MASK = 0x01FF


class RouteError(ValueError):
    """Routing was denied by an attributable rule."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RoutePolicy:
    protocol: str
    destination: str
    message_types: frozenset[str]
    core_mask: int
    expires_at: int


@dataclass(frozen=True)
class RouteDecision:
    status: str
    protocol: str
    destination: str
    message_type: str
    core_mask: int
    reason: str


class SernRouter:
    """Register explicit domain roads and fail every other route closed."""

    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], RoutePolicy] = {}

    def register(self, policy: RoutePolicy) -> None:
        if not policy.protocol or not policy.destination:
            raise RouteError("INVALID_ROUTE", "protocol and destination are required")
        if not policy.message_types or not policy.message_types <= MESSAGE_TYPES:
            raise RouteError("INVALID_ROUTE", "message types are invalid")
        if type(policy.core_mask) is not int or policy.core_mask & ~NINE_CORE_MASK:
            raise RouteError("INVALID_ROUTE", "core projection is invalid")
        self._routes[(policy.protocol, policy.destination)] = policy

    def withdraw(self, protocol: str, destination: str) -> None:
        self._routes.pop((protocol, destination), None)

    def route(self, telemetry: Mapping[str, Any], *, now: int | None = None) -> RouteDecision:
        """Apply generic protocol, destination, expiry and projection policy."""
        required = {"protocol", "destination", "message_type", "core_mask"}
        if set(telemetry) != required:
            raise RouteError("INVALID_ROUTE_REQUEST", "route fields are not exact")
        protocol = telemetry["protocol"]
        destination = telemetry["destination"]
        message_type = telemetry["message_type"]
        core_mask = telemetry["core_mask"]
        if not all(isinstance(value, str) and value for value in (protocol, destination, message_type)):
            raise RouteError("INVALID_ROUTE_REQUEST", "route identity is invalid")
        if type(core_mask) is not int or core_mask < 0 or core_mask & ~NINE_CORE_MASK:
            raise RouteError("INVALID_CORE_PROJECTION", "requested core projection is invalid")
        policy = self._routes.get((protocol, destination))
        if policy is None:
            raise RouteError("ROUTE_NOT_ADMITTED", "no admitted route")
        current = int(time.time()) if now is None else now
        if current >= policy.expires_at:
            self.withdraw(protocol, destination)
            raise RouteError("ROUTE_STALE", "route expired and was withdrawn")
        if message_type not in policy.message_types:
            raise RouteError("MESSAGE_NOT_ADMITTED", "message type is not admitted")
        if core_mask & ~policy.core_mask:
            raise RouteError("PROJECTION_NOT_ADMITTED", "core projection exceeds policy")
        if message_type == "OPEN_TRANSPORT":
            return RouteDecision(
                "DENIED", protocol, destination, message_type, core_mask,
                "TRANSPORT_NOT_ADMITTED",
            )
        return RouteDecision("ROUTED", protocol, destination, message_type, core_mask, "ADMITTED")


def morphworld_foundation_policy(*, expires_at: int) -> RoutePolicy:
    """Register Morphworld SERN control traffic, never a bulk transport."""
    return RoutePolicy(
        protocol=MORPHWORLD_PROTOCOL,
        destination="MORPH_DOMAIN",
        message_types=frozenset({"COMMAND", "EVENT", "RECEIPT", "OPEN_TRANSPORT"}),
        core_mask=NINE_CORE_MASK,
        expires_at=expires_at,
    )

