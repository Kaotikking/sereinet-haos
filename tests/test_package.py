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
        self.assertEqual(manifest["version"], "1.1.0")
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


if __name__ == "__main__":
    unittest.main()

