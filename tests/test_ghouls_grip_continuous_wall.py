"""Rear-wall and rigid lid-transfer regressions."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import mechanism as m
from gothic_chest import build_chest
from mesh_kit import box


def place_gear(mesh, y: float, angle: float):
    part = mesh.copy()
    part.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2.0, [0, 1, 0]))
    part.apply_transform(trimesh.transformations.rotation_matrix(
        np.deg2rad(angle), [1, 0, 0]))
    part.apply_translation([-m.DRIVE_PITCH_R, y, m.LID_HINGE_Z])
    return part


def overlap(a, b) -> float:
    return abs(float(trimesh.boolean.intersection(
        [a, b], engine="manifold").volume))


class ContinuousWallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chest = build_chest(include_decoration=False)
        cls.gear = m.build_lid_transfer_gear()
        cls.crank = m.build_lid_crank()
        cls.rack = m.build_lid_follower_rack()

    def test_former_window_is_closed_at_every_height(self):
        for z in np.arange(63.25, 85.76, 0.5):
            probe = box((13.5, 0.8, 0.5), (-27.0, 59.5, z))
            self.assertAlmostEqual(overlap(self.chest, probe),
                                   probe.volume, delta=0.002)

    def follower_at(self, rise: float):
        follower = self.rack.copy()
        follower.apply_transform(np.linalg.inv(m.FOLLOWER_PRINT_MATRIX))
        follower.apply_translation([0.0, 0.0, rise])
        return follower

    def test_whole_follower_translation_envelope_is_inside(self):
        # The follower runs inside the chest's guide channel, so check the
        # swept positions individually instead of a convex hull.
        for rise in np.linspace(0.0, m.LID_OPEN_TRAVEL, 15):
            follower = self.follower_at(rise)
            self.assertLess(overlap(follower, self.chest), 0.001, rise)
            self.assertLess(follower.bounds[1, 1], 58.0 - m.FIT)

    def test_transfer_gears_and_rack_clear_through_lid_opening(self):
        for rise in np.linspace(0, m.LID_OPEN_TRAVEL, 109):
            angle = m.lid_angle_from_travel(rise)
            gears = [
                place_gear(self.gear, m.LID_TRANSFER_Y, angle),
                place_gear(self.gear, m.LID_IDLER_Y, -angle),
                place_gear(self.crank, m.LID_HINGE_Y, angle),
            ]
            rack = self.follower_at(rise)
            self.assertLess(overlap(gears[0], gears[1]), 0.001)
            self.assertLess(overlap(gears[1], gears[2]), 0.001)
            self.assertLess(overlap(gears[0], rack), 0.001)

    def test_transfer_journals_can_be_inserted_axially(self):
        for y, angle in ((m.LID_TRANSFER_Y, 0.0), (m.LID_IDLER_Y, 0.0)):
            installed = place_gear(self.gear, y, angle)
            for dx in np.linspace(8.5, 0.0, 61):
                part = installed.copy()
                part.apply_translation([dx, 0, 0])
                self.assertLess(overlap(part, self.chest), 0.001)

    def test_transfer_does_not_change_motion_datums(self):
        self.assertAlmostEqual(m.LID_TRANSFER_STEP, 2.0 * m.LID_SECTOR_R)
        self.assertAlmostEqual(m.LID_HINGE_Y, 61.0)
        self.assertAlmostEqual(m.LID_HINGE_Z, 93.0)
        self.assertAlmostEqual(m.LID_OPEN_TRAVEL, 7.0)
        self.assertAlmostEqual(m.lid_angle(18), 0.0)
        self.assertAlmostEqual(m.lid_angle(48), -108.0)
        self.assertAlmostEqual(m.lid_angle(78), -108.0)

    def test_delivered_lid_key_is_insertable_and_transmits_torque(self):
        path = Path(__file__).resolve().parents[1] / "models" / "ghouls-grip-view.3mf"
        scene = trimesh.load(path, force="scene")

        def part(name):
            transform, geometry = scene.graph.get("retracted-" + name)
            mesh = scene.geometry[geometry].copy()
            mesh.apply_transform(transform)
            return mesh

        lid, crank, chest = part("lid"), part("lid-crank"), part("chest")
        self.assertLess(overlap(crank, lid), 0.001)
        for dx in np.linspace(-6.0, 0.0, 25):
            candidate = crank.copy()
            candidate.apply_translation([dx, 0, 0])
            self.assertLess(overlap(candidate, lid), 0.001)
        for dz in np.linspace(-30.0, 0.0, 31):
            candidate = crank.copy()
            candidate.apply_translation([-6.0, 0, dz])
            self.assertLess(overlap(candidate, lid), 0.001)
        hinge = [
            float(np.mean(chest.bounds[:, 0])) - m.DRIVE_PITCH_R,
            float(chest.bounds[1, 1]) - 66.0 + m.LID_HINGE_Y,
            m.LID_HINGE_Z,
        ]
        for angle in (-5.0, 5.0):
            candidate = crank.copy()
            candidate.apply_transform(trimesh.transformations.rotation_matrix(
                np.deg2rad(angle), [1, 0, 0], hinge))
            self.assertGreater(overlap(candidate, lid), 0.05)


if __name__ == "__main__":
    unittest.main()
