"""Tests for the Blender-sculpted gothic chest reliefs.

These cover the three properties the sculpted relief pipeline must keep:
a closed solid, the documented relief depth, and 45-degree support neutrality.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from gothic_chest import (  # noqa: E402
    CREATURE_RELIEF_DEPTH,
    PILASTER_ENGRAVE_DEPTH,
    RELIEF_BASE,
    RELIEF_CACHE,
    _creature_panel,
    _relief_field,
)

PANELS = ("front", "rear", "side", "lid")
PILASTER_STOCK = 5.0        # material behind an outward pilaster face
MIN_REMAINING_WALL = 1.8    # AGENTS.md floor for engraved regions


class ReliefCacheTest(unittest.TestCase):
    def test_every_panel_is_cached(self):
        for name in PANELS:
            self.assertTrue((RELIEF_CACHE / f"{name}.npz").is_file(), name)

    def test_fields_are_normalised_and_border_clamped(self):
        for name in PANELS:
            with self.subTest(panel=name):
                xs, ys, grid = _relief_field(name)
                self.assertEqual(grid.shape, (len(ys), len(xs)))
                self.assertGreaterEqual(grid.min(), 0.0)
                self.assertLessEqual(grid.max(), 1.0 + 1e-6)
                # a relief that touches its own border would break the union
                self.assertEqual(grid[0, :].max(), 0.0)
                self.assertEqual(grid[-1, :].max(), 0.0)
                self.assertEqual(grid[:, 0].max(), 0.0)
                self.assertEqual(grid[:, -1].max(), 0.0)
                # and it must actually carry sculpted detail
                self.assertGreater(float(grid.max()), 0.5)


class ReliefSolidTest(unittest.TestCase):
    def test_panels_are_closed_single_bodies(self):
        for name in PANELS:
            with self.subTest(panel=name):
                mesh = _creature_panel(name, CREATURE_RELIEF_DEPTH)
                self.assertTrue(mesh.is_watertight)
                self.assertTrue(mesh.is_volume)
                self.assertEqual(mesh.body_count, 1)

    def test_total_height_stays_inside_the_declared_depth(self):
        # the boolean breaks if a panel is taller than the depth the chest
        # builder offsets it by; shorter is fine (a panel whose smoothed
        # peak is below 1.0 simply protrudes less)
        for name in PANELS:
            with self.subTest(panel=name):
                mesh = _creature_panel(name, CREATURE_RELIEF_DEPTH)
                height = mesh.bounds[1][2] - mesh.bounds[0][2]
                self.assertLessEqual(height, CREATURE_RELIEF_DEPTH + 1e-6)
                self.assertGreater(height, 0.5 * CREATURE_RELIEF_DEPTH)
                self.assertAlmostEqual(mesh.bounds[0][2], -RELIEF_BASE,
                                       places=5)


class SupportNeutralityTest(unittest.TestCase):
    def test_sheared_relief_has_no_facet_steeper_than_45_degrees(self):
        """`y += z` is what keeps the sculpt support neutral - prove it."""
        for name in PANELS:
            with self.subTest(panel=name):
                mesh = _creature_panel(name, CREATURE_RELIEF_DEPTH).copy()
                verts = mesh.vertices.copy()
                verts[:, 1] += verts[:, 2]
                mesh.vertices = verts
                normals = mesh.face_normals
                down = normals[:, 2] < -1e-9
                # overhang angle from vertical: 0 = wall, 90 = ceiling
                horiz = np.linalg.norm(normals[down][:, :2], axis=1)
                angle = np.degrees(np.arctan2(-normals[down][:, 2], horiz))
                # the backing plate itself is the only flat downward face
                steep = angle[angle > 45.0 + 1e-6]
                self.assertTrue(
                    np.allclose(steep, 90.0, atol=1e-6),
                    f"{name}: unsupported overhangs at {np.unique(steep)[:5]}")


class EngravingDepthTest(unittest.TestCase):
    def test_pilaster_flute_leaves_enough_material(self):
        remaining = PILASTER_STOCK - PILASTER_ENGRAVE_DEPTH
        self.assertGreaterEqual(remaining, MIN_REMAINING_WALL)


if __name__ == "__main__":
    unittest.main()
