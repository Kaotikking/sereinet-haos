"""Config flow for Sereinet."""

from __future__ import annotations

import secrets

import voluptuous as vol
from homeassistant import config_entries

from .const import CONF_SIGNING_KEY, CONF_WEBHOOK_ID, DOMAIN


class SereinetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure one Sereinet ingress."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle initial setup."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["name"],
                data={
                    CONF_SIGNING_KEY: user_input[CONF_SIGNING_KEY],
                    CONF_WEBHOOK_ID: user_input[CONF_WEBHOOK_ID],
                },
            )
        schema = vol.Schema(
            {
                vol.Required("name", default="Sereinet"): str,
                vol.Required(CONF_SIGNING_KEY): str,
                vol.Required(CONF_WEBHOOK_ID, default=secrets.token_urlsafe(24)): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
