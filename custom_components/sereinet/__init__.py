"""Sereinet Home Assistant integration."""

from __future__ import annotations

import json
import logging

from aiohttp import web
from homeassistant.components import webhook
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_SIGNING_KEY, CONF_WEBHOOK_ID, DOMAIN, PLATFORMS
from .protocol import MAX_BODY_BYTES, PacketError, validate_packet
from .router import RouteError, SernRouter, morphworld_foundation_policy
from .runtime import SereinetRuntime

_LOGGER = logging.getLogger(__name__)
ROUTER_KEY = "sern_router"
ROUTER_VIEW_KEY = "sern_router_view_registered"


class SernRouterView(HomeAssistantView):
    """Evaluate one SERN control route without changing destination state."""

    url = "/api/sereinet/v1/router/evaluate"
    name = "api:sereinet:v1:router:evaluate"
    requires_auth = True

    async def post(self, request: web.Request) -> web.Response:
        router: SernRouter = request.app["hass"].data[DOMAIN][ROUTER_KEY]
        try:
            decision = router.route(await request.json())
            return self.json({
                "ok": True,
                "status": decision.status,
                "reason": decision.reason,
                "protocol": decision.protocol,
                "destination": decision.destination,
                "message_type": decision.message_type,
                "core_mask": decision.core_mask,
                "authority_effect": "NONE",
            })
        except RouteError as err:
            return self.json(
                {"ok": False, "error": {"code": err.code, "message": str(err)}},
                status_code=403,
            )
        except (TypeError, ValueError):
            return self.json(
                {"ok": False, "error": {"code": "INVALID_REQUEST", "message": "request is invalid"}},
                status_code=400,
            )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sereinet from a config entry."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    runtime = SereinetRuntime()
    domain_data[entry.entry_id] = runtime
    if ROUTER_KEY not in domain_data:
        router = SernRouter()
        router.register(morphworld_foundation_policy(expires_at=4102444800))
        domain_data[ROUTER_KEY] = router
    if ROUTER_VIEW_KEY not in domain_data:
        hass.http.register_view(SernRouterView)
        domain_data[ROUTER_VIEW_KEY] = True

    async def handle_webhook(hass: HomeAssistant, webhook_id: str, request: web.Request) -> web.Response:
        if request.content_length is not None and request.content_length > MAX_BODY_BYTES:
            return web.json_response({"status": "rejected", "reason": "body_too_large"}, status=413)
        try:
            raw = await request.content.readexactly(request.content_length) if request.content_length else await request.read()
            if len(raw) > MAX_BODY_BYTES:
                raise PacketError("body_too_large")
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise PacketError("invalid_json_object")
            device_id = payload.get("device_id")
            last_sequence = runtime.last_sequence(device_id) if isinstance(device_id, str) else None
            packet = validate_packet(payload, entry.data[CONF_SIGNING_KEY], last_sequence)
            runtime.accept(packet)
            return web.json_response({"status": "accepted", "sequence": packet.sequence})
        except (PacketError, json.JSONDecodeError, UnicodeDecodeError) as err:
            _LOGGER.warning("Rejected SERN packet: %s", err)
            return web.json_response({"status": "rejected", "reason": str(err)}, status=400)

    webhook.async_register(
        hass, DOMAIN, entry.title, entry.data[CONF_WEBHOOK_ID], handle_webhook,
        allowed_methods=["POST"],
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Sereinet config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        webhook.async_unregister(hass, entry.data[CONF_WEBHOOK_ID])
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded

