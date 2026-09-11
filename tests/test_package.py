"""Repository packaging checks."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]


class PackageTests(unittest.TestCase):
    def test_hacs_shape(self):
        manifest = json.loads((ROOT / "custom_components/sereinet/manifest.json").read_text())
        hacs = json.loads((ROOT / "hacs.json").read_text())
        self.assertEqual(manifest["domain"], "sereinet")
        self.assertEqual(manifest["version"], "1.1.1")
        self.assertEqual(hacs["name"], "Sereinet")

    def test_no_private_values(self):
        forbidden = ("sardonyx" + "sapphire", "192." + "168.", "haos_api" + "_token", "wifi_" + "password")
        for path in ROOT.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".json", ".md", ".yml"}:
                if path == Path(__file__):
                    continue
                text = path.read_text(encoding="utf-8")
                for value in forbidden:
                    self.assertNotIn(value, text, f"{value} leaked in {path}")

    def test_router_is_registered_as_authenticated_no_effect_api(self):
        setup = (ROOT / "custom_components/sereinet/__init__.py").read_text()
        self.assertIn('url = "/api/sereinet/v1/router/evaluate"', setup)
        self.assertIn("requires_auth = True", setup)
        self.assertIn('"authority_effect": "NONE"', setup)
        self.assertIn("morphworld_foundation_policy", setup)
        self.assertIn("local_only=False", setup)


if __name__ == "__main__":
    unittest.main()

