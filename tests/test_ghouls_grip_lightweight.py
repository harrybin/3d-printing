"""Regression checks for the lightweight Ghoul's Grip enclosure."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from gothic_chest import build_chest, build_lid  # noqa: E402


class LightweightEnclosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.chest = build_chest()
        cls.lid = build_lid()

    def test_chest_is_a_lightweight_single_watertight_body(self) -> None:
        self.assertTrue(self.chest.is_watertight)
        self.assertEqual(len(self.chest.split(only_watertight=False)), 1)
        self.assertLess(self.chest.volume, 200_000.0)
        self.assertAlmostEqual(self.chest.extents[2], 98.0, delta=0.05)

    def test_lid_keeps_connected_truss_and_seating_guides(self) -> None:
        self.assertTrue(self.lid.is_watertight)
        self.assertEqual(len(self.lid.split(only_watertight=False)), 1)
        self.assertLess(self.lid.volume, 140_000.0)
        self.assertAlmostEqual(self.lid.bounds[0, 2], 0.0, delta=0.01)
        self.assertAlmostEqual(self.lid.extents[2], 24.0, delta=0.05)


if __name__ == "__main__":
    unittest.main()
