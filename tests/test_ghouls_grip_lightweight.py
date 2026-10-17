"""Regression checks for the lightweight Ghoul's Grip enclosure."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from gothic_chest import (  # noqa: E402
    CREATURE_RELIEF_DEPTH,
    LID_DROP,
    LID_H,
    SERVICE_HOOD_TOP,
    _dragon,
    _rib_cage,
    _serpent,
    build_chest,
    build_lid,
)
from ghouls_grip import expand_print_parts  # noqa: E402
import mechanism  # noqa: E402


class LightweightEnclosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.chest = build_chest()
        cls.lid = build_lid()

    def test_chest_is_a_lightweight_single_watertight_body(self) -> None:
        self.assertTrue(self.chest.is_watertight)
        self.assertEqual(len(self.chest.split(only_watertight=False)), 1)
        # Budget includes the +Y lid-follower guide rib/channel (~5.6 cm3)
        # added by the cam-follower lid drive.
        self.assertLess(self.chest.volume, 203_000.0)
        self.assertAlmostEqual(self.chest.extents[2], 98.0, delta=0.05)

    def test_undecorated_control_preserves_functional_envelope(self) -> None:
        control = build_chest(include_decoration=False)
        self.assertTrue(control.is_watertight)
        self.assertEqual(len(control.split(only_watertight=False)), 1)
        self.assertTrue(
            all(abs(a - b) < 0.05
                for a, b in zip(control.extents, self.chest.extents))
        )
        self.assertLess(control.volume, self.chest.volume)

    def test_creature_reliefs_have_organic_anatomical_layering(self) -> None:
        serpent = _serpent(1.0)
        tail = serpent.vertices[
            (serpent.vertices[:, 1] > -24.5)
            & (serpent.vertices[:, 1] < -23.0)
        ]
        torso = serpent.vertices[
            (serpent.vertices[:, 1] > -8.0)
            & (serpent.vertices[:, 1] < 0.0)
        ]
        self.assertLess(np.ptp(tail[:, 0]), np.ptp(torso[:, 0]))
        textured_torso = serpent.vertices[
            (serpent.vertices[:, 1] > -15.0)
            & (serpent.vertices[:, 1] < 22.0)
        ]
        serpent_layers = {
            round(abs(float(value)), 2)
            for value in textured_torso[:, 2]
        }
        self.assertGreaterEqual(len(serpent_layers), 5)

        dragon = _dragon(1.0)
        membranes = [
            component
            for component in dragon.split(only_watertight=False)
            if component.extents[2] <= 0.65
            and component.extents[0] >= 8.0
            and component.extents[1] >= 8.0
        ]
        self.assertGreaterEqual(len(membranes), 2)

        rib_cage = _rib_cage(1.0)
        vertebral_column = rib_cage.vertices[
            (abs(rib_cage.vertices[:, 0]) < 2.0)
            & (rib_cage.vertices[:, 1] > -20.0)
            & (rib_cage.vertices[:, 1] < 18.0)
        ]
        vertebral_depths = {
            round(abs(float(value)), 2)
            for value in vertebral_column[:, 2]
        }
        self.assertGreaterEqual(len(vertebral_depths), 4)

    def test_lid_keeps_connected_truss_and_seating_guides(self) -> None:
        self.assertTrue(self.lid.is_watertight)
        self.assertEqual(len(self.lid.split(only_watertight=False)), 1)
        self.assertLess(self.lid.volume, 140_000.0)
        self.assertAlmostEqual(self.lid.bounds[0, 2], 0.0, delta=0.01)
        # The sculpted cartouche grows out of the LID_H shell, so the total
        # height is the shell plus however much relief stands proud of it.
        self.assertGreaterEqual(self.lid.extents[2], LID_H - 0.05)
        self.assertLessEqual(
            self.lid.extents[2],
            max(LID_H + CREATURE_RELIEF_DEPTH, SERVICE_HOOD_TOP) + 0.05,
        )

    def test_print_lid_stands_on_its_rear_edge(self) -> None:
        """The measured lowest-support orientation (4598.9 vs 20336.1 E)."""
        printable = expand_print_parts({"lid": self.lid})["lid"]
        self.assertAlmostEqual(printable.bounds[0, 2], 0.0, delta=0.01)
        # Rotating -90 deg about X swaps the lid depth into the build height.
        self.assertAlmostEqual(
            printable.extents[2], self.lid.extents[1], delta=0.05)
        self.assertAlmostEqual(
            printable.extents[1], self.lid.extents[2], delta=0.05)
        self.assertLess(printable.extents[2], 250.0)

    def test_closed_lid_service_channel_has_a_solid_roof(self) -> None:
        """The internal rack channel may not open through the closed lid."""
        probe = trimesh.creation.box(extents=(8.0, 8.0, 1.0))
        probe.apply_translation((
            -mechanism.DRIVE_PITCH_R,
            mechanism.LID_RACK_Y - 1.8,
            SERVICE_HOOD_TOP - 0.5,
        ))
        overlap = self.lid.intersection(probe, engine="manifold")
        self.assertGreater(abs(float(overlap.volume)), 20.0)

        # In the assembled pose the roof hides the full hinge-sector envelope.
        self.assertGreater(
            LID_DROP + SERVICE_HOOD_TOP,
            mechanism.LID_HINGE_Z + 6.0,
        )

        footprint = trimesh.creation.box(extents=(25.0, 32.3, 1.0))
        footprint.apply_translation((-30.5, 48.65, SERVICE_HOOD_TOP - 0.5))
        skin = self.lid.intersection(footprint, engine="manifold")
        self.assertAlmostEqual(abs(float(skin.volume)),
                               footprint.volume, delta=0.05)


if __name__ == "__main__":
    unittest.main()
