"""Support-material accounting for verified slice metadata."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from update_ghouls_grip_slice_metadata import (  # noqa: E402
    _support_filament_mm,
)

GCODE = "\n".join([
    "G92 E0",
    ";TYPE:Outer wall",
    "G1 X10 Y10 E1.0",
    "G1 X20 Y10 E2.0",
    ";TYPE:Support",
    "G1 X30 Y10 E5.0",
    ";TYPE:Support interface",
    "G1 X40 Y10 E6.5",
    ";TYPE:Inner wall",
    "G1 X50 Y10 E9.0",
    ";TYPE:Support",
    "G1 X60 Y10 E9.0",
    "G92 E0",
    "G1 X70 Y10 E0.5",
])


class SupportUsageTests(unittest.TestCase):
    def test_sums_only_positive_support_extrusions(self) -> None:
        self.assertAlmostEqual(_support_filament_mm(GCODE), 5.0, places=6)

    def test_returns_zero_without_support_paths(self) -> None:
        plain = ";TYPE:Outer wall\nG92 E0\nG1 X10 Y10 E1.0\n"
        self.assertEqual(_support_filament_mm(plain), 0.0)


if __name__ == "__main__":
    unittest.main()
