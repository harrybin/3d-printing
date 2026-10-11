"""Focused regression tests for the Ghoul's Grip skull accent."""

from __future__ import annotations

import sys
import unittest
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mesh_kit import box, cylinder, intersection  # noqa: E402
from skull import build_drive_knob, build_skull, skull_relief  # noqa: E402


def _probe_volume(mesh, extents, centre) -> float:
    return float(intersection([mesh, box(extents, centre)]).volume)


class SkullGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skull = build_skull()
        cls.knob = build_drive_knob()
        cls.relief = skull_relief(depth=5.0)

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

    def test_dental_arcade_has_visible_individually_separated_crowns(self) -> None:
        # Clip away the roots and alveolar backing. A machined bite line with
        # vertical slits remains two continuous blocks here, while anatomical
        # crowns appear as many disconnected islands in upper and lower rows.
        crowns = intersection([
            self.skull,
            box((27.0, 12.0, 2.0), (0.0, -16.0, 13.5)),
        ])
        components = [
            part for part in crowns.split(only_watertight=False)
            if part.volume > 0.1 and part.centroid[1] < -12.0
        ]
        centres = [part.centroid for part in components]

        self.assertGreaterEqual(len(components), 20)
        upper = [c for c in centres if c[1] > -15.0]
        lower = [c for c in centres if c[1] < -15.2]
        self.assertGreaterEqual(len(upper), 10)
        self.assertGreaterEqual(len(lower), 10)
        self.assertGreater(max(abs(c[0]) for c in centres), 10.0)
        self.assertGreater(max(c[1] for c in upper) - min(c[1] for c in upper), 1.0)

    def test_lid_relief_preserves_watertight_separated_teeth(self) -> None:
        self.assertTrue(self.relief.is_watertight)
        self.assertEqual(len(self.relief.split(only_watertight=False)), 1)

        crown_tips = intersection([
            self.relief,
            box((27.0, 12.0, 1.5), (0.0, -16.0, 4.25)),
        ])
        components = [
            part for part in crown_tips.split(only_watertight=False)
            if part.volume > 0.02
        ]
        self.assertGreaterEqual(len(components), 12)


if __name__ == "__main__":
    unittest.main()
