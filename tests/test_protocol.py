"""SERN ingress v1 contract tests."""

import copy
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = Path(__file__).parents[1] / "custom_components" / "sereinet" / "protocol.py"
SPEC = importlib.util.spec_from_file_location("sereinet_protocol", MODULE)
protocol = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = protocol
SPEC.loader.exec_module(protocol)


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.key = "test-key-not-a-secret"
        self.packet = {
            "version": 1,
            "device_id": "serein-power",
            "timestamp": 1_788_777_600,
            "sequence": 42,
            "telemetry": {"battery_percent": 81, "location": "mobile"},
        }
        self.packet["signature"] = protocol.sign_packet(self.packet, self.key)

    def test_valid_packet(self):
        result = protocol.validate_packet(self.packet, self.key, 41, now=1_788_777_600)
        self.assertEqual(result.device_id, "serein-power")
        self.assertEqual(result.telemetry["battery_percent"], 81)

    def test_signature_is_order_independent(self):
        reordered = dict(reversed(list(self.packet.items())))
        self.assertEqual(protocol.sign_packet(reordered, self.key), self.packet["signature"])

    def test_replay_is_rejected(self):
        with self.assertRaisesRegex(protocol.PacketError, "replayed_sequence"):
            protocol.validate_packet(self.packet, self.key, 42, now=1_788_777_600)

    def test_stale_timestamp_is_rejected(self):
        with self.assertRaisesRegex(protocol.PacketError, "stale_timestamp"):
            protocol.validate_packet(self.packet, self.key, None, now=1_788_778_000)

    def test_tamper_is_rejected(self):
        tampered = copy.deepcopy(self.packet)
        tampered["telemetry"]["battery_percent"] = 1
        with self.assertRaisesRegex(protocol.PacketError, "invalid_signature"):
            protocol.validate_packet(tampered, self.key, None, now=1_788_777_600)

    def test_nested_telemetry_is_rejected(self):
        invalid = copy.deepcopy(self.packet)
        invalid["telemetry"]["nested"] = {"no": "objects"}
        invalid["signature"] = protocol.sign_packet(invalid, self.key)
        with self.assertRaisesRegex(protocol.PacketError, "invalid_telemetry_value"):
            protocol.validate_packet(invalid, self.key, None, now=1_788_777_600)


if __name__ == "__main__":
    unittest.main()
