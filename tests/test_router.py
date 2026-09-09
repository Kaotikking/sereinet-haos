"""Default-deny SERN Router tests."""

import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = Path(__file__).parents[1] / "custom_components" / "sereinet" / "router.py"
SPEC = importlib.util.spec_from_file_location("sereinet_router", MODULE)
router = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = router
SPEC.loader.exec_module(router)


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.router = router.SernRouter()
        self.router.register(router.morphworld_foundation_policy(expires_at=200))
        self.packet = {
            "protocol": "MORPHWORLD", "destination": "MORPH_DOMAIN",
            "message_type": "COMMAND", "core_mask": 0x01FF,
        }

    def test_admitted_morphworld_control_routes(self):
        self.assertEqual(self.router.route(self.packet, now=100).status, "ROUTED")

    def test_unknown_protocol_fails_closed(self):
        self.packet["protocol"] = "UNKNOWN"
        with self.assertRaisesRegex(router.RouteError, "no admitted route"):
            self.router.route(self.packet, now=100)

    def test_projection_is_bounded(self):
        limited = router.RoutePolicy("MORPHWORLD", "FRAME", frozenset({"EVENT"}), 0x0010, 200)
        self.router.register(limited)
        request = {"protocol": "MORPHWORLD", "destination": "FRAME", "message_type": "EVENT", "core_mask": 0x0011}
        with self.assertRaisesRegex(router.RouteError, "exceeds policy"):
            self.router.route(request, now=100)

    def test_stale_route_is_withdrawn(self):
        with self.assertRaisesRegex(router.RouteError, "expired"):
            self.router.route(self.packet, now=200)
        with self.assertRaisesRegex(router.RouteError, "no admitted route"):
            self.router.route(self.packet, now=201)

    def test_open_transport_is_reserved_but_unimplemented(self):
        self.packet["message_type"] = "OPEN_TRANSPORT"
        result = self.router.route(self.packet, now=100)
        self.assertEqual((result.status, result.reason), ("DENIED", "TRANSPORT_NOT_ADMITTED"))


if __name__ == "__main__":
    unittest.main()

