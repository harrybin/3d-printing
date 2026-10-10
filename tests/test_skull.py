"""Focused regression tests for the Ghoul's Grip skull accent."""

from __future__ import annotations

import sys
import unittest
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mesh_kit import box, cylinder, intersection  # noqa: E402
from skull import build_drive_knob, build_skull  # noqa: E402


def _probe_volume(mesh, extents, centre) -> float:
    return float(intersection([mesh, box(extents, centre)]).volume)


class SkullGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skull = build_skull()
        cls.knob = build_drive_knob()

    def test_drive_knob_preserves_fit_contract_and_control_envelope(self) -> None:
        self.assertTrue(self.knob.is_watertight)
        self.assertEqual(len(self.knob.split(only_watertight=False)), 1)
        self.assertAlmostEqual(self.knob.extents[0], 48.5, delta=1.0)
        self.assertAlmostEqual(self.knob.extents[1], 55.1, delta=1.5)
        self.assertAlmostEqual(self.knob.extents[2], 27.0, delta=1.0)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            rear_socket = float(intersection([
                self.knob, cylinder(3.6, 7.0, (0.0, 0.0, -8.0))
            ]).volume)
        socket_floor = float(intersection([
            self.knob, cylinder(3.0, 1.0, (0.0, 0.0, -1.0))
        ]).volume)
        self.assertLess(rear_socket, 1.0, "Ø7.8 mm shaft socket must remain open")
        self.assertGreater(socket_floor, 20.0, "shaft socket must remain blind")

    def test_zygomatic_buttresses_are_present_beside_the_orbits(self) -> None:
        # The former capsule-only face had almost no cheekbone at these
        # landmarks, so its eye sockets read as holes cut into an egg.
        for side in (-1.0, 1.0):
            volume = _probe_volume(
                self.skull, (3.0, 5.0, 5.0), (side * 17.0, -6.0, 8.0)
            )
            self.assertGreater(volume, 30.0)


if __name__ == "__main__":
    unittest.main()
