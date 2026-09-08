# Sereinet for Home Assistant

Sereinet is the Home Assistant adapter for signed SERN device telemetry. It gives mobile SERN nodes an outbound HTTPS road back to Home Assistant without exposing a Home Assistant access token to device firmware.

## Install with HACS

1. In HACS, add `https://github.com/Kaotikking/sereinet-haos` as a custom **Integration** repository.
2. Install **Sereinet** and restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration > Sereinet**.
4. Enter a name and a newly generated shared signing key. Copy the generated ingress ID before submitting.
5. The endpoint is `https://YOUR-HA-HOST/api/webhook/YOUR-INGRESS-ID`.

The key remains in the Home Assistant config entry. It is never placed in this repository, entity state, diagnostics, or logs.

## Scope

The first release provides authenticated SERN ingress, replay protection, device registration, and read-only telemetry sensors. It does not claim remote device control, OTA, or SFOS Gateway authority.

SFOS owns the canonical Sereinet Gateway service; this repository is its HAOS adapter and uses a versioned SERN boundary.

## Privacy

This public integration contains no private topology, device keys, founder DNA, or operator credentials.

## Status

Source and contract tests are prepared for the initial v1.0.0 publication.
