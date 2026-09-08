# Sereinet for Home Assistant

Sereinet is the Home Assistant adapter for signed SERN device telemetry. It gives
mobile SERN nodes an outbound HTTPS road back to Home Assistant without exposing
a Home Assistant access token to device firmware.

## Install with HACS

1. In HACS, add `https://github.com/Kaotikking/sereinet-haos` as a custom
   **Integration** repository.
2. Install **Sereinet** and restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration > Sereinet**.
4. Enter a name and a newly generated shared signing key. Copy the generated
   ingress ID before submitting.
5. The endpoint is `https://YOUR-HA-HOST/api/webhook/YOUR-INGRESS-ID`.

The key remains in the Home Assistant config entry. It is never placed in this
repository, entity state, diagnostics, or logs.

## SERN ingress v1

Send a JSON `POST` to the generated webhook URL:

```json
{
  "version": 1,
  "device_id": "serein-power",
  "timestamp": 1788777600,
  "sequence": 42,
  "telemetry": {
    "battery_percent": 81,
    "input_voltage": 5.12,
    "input_current": 1.43,
    "power_w": 7.32,
    "location": "mobile"
  },
  "signature": "lowercase hex HMAC-SHA256"
}
```

The signature is HMAC-SHA256 over canonical compact JSON of every field except
`signature`, with keys sorted lexicographically. Timestamps may differ from Home
Assistant by at most 300 seconds. A sequence number must increase for each
device; replayed or stale packets are rejected.

This v1 release is deliberately ingress-only. It does not claim remote device
control, OTA, or SFOS Gateway authority.

## Privacy and ownership

This public integration contains no private topology, device keys, founder DNA,
or operator credentials. SFOS owns the canonical Sereinet Gateway service;
this repository is its HAOS adapter and uses a versioned SERN boundary.

## Development

Run the dependency-free contract tests with:

```text
python -m unittest discover -s tests -v
```
