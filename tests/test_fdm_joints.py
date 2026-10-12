"""Focused geometry and dimension tests for the reusable FDM joint library."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fdm_joints import (  # noqa: E402
    CLEARANCE_CLOSE_PER_SIDE,
    CLEARANCE_FILAMENT_HOLE_DIAMETER,
    CLEARANCE_SLIDING_PER_SIDE,
    FILAMENT_NOMINAL_DIAMETER,
    assert_single_watertight_body,
    captive_hex_nut_trap,
    cross_pin_hole,
    d_bore_cutter,
    d_shaft,
    dovetail_groove_cutter,
    dovetail_tongue,
    keyed_shaft_coupling,
    tongue,
    tongue_groove_cutter,
)


class FdmJointGeometryTests(unittest.TestCase):
    def assert_valid(self, mesh, name: str) -> None:
        assert_single_watertight_body(mesh, name)

    def test_d_shaft_and_bore_keep_length_and_clearance_contract(self) -> None:
        shaft = d_shaft(8.0, 20.0, 1.4)
        bore = d_bore_cutter(8.0, 22.0, 1.4)
        self.assert_valid(shaft, "shaft")
        self.assert_valid(bore, "bore")
        self.assertAlmostEqual(shaft.extents[2], 20.0, delta=0.02)
        self.assertAlmostEqual(bore.extents[2], 22.0, delta=0.02)
        self.assertAlmostEqual(
            bore.extents[1] - shaft.extents[1],
            2.0 * CLEARANCE_CLOSE_PER_SIDE,
            delta=0.03,
        )
        self.assertGreater(bore.volume, shaft.volume)

    def test_keyed_coupling_is_one_body_with_open_d_bore(self) -> None:
        coupling = keyed_shaft_coupling(8.0, 1.4, 16.0, 15.0)
        self.assert_valid(coupling, "coupling")
        self.assertAlmostEqual(coupling.extents[2], 16.0, delta=0.02)
        self.assertAlmostEqual(coupling.extents[0], 15.0, delta=0.03)
        # A through bore leaves no mesh volume around the centreline.
        nearest = np.linalg.norm(coupling.vertices[:, :2], axis=1).min()
        self.assertGreater(nearest, 3.0)

    def test_filament_cross_pin_hole_uses_named_diameter_allowance(self) -> None:
        hole = cross_pin_hole(10.0)
        self.assert_valid(hole, "cross-pin")
        self.assertAlmostEqual(hole.extents[0], 12.0, delta=0.02)
        expected = FILAMENT_NOMINAL_DIAMETER + CLEARANCE_FILAMENT_HOLE_DIAMETER
        self.assertAlmostEqual(hole.extents[1], expected, delta=0.03)
        self.assertAlmostEqual(hole.extents[2], expected, delta=0.03)

    def test_captive_hex_trap_matches_across_flats_and_entry_path(self) -> None:
        trap = captive_hex_nut_trap(5.5, 2.4)
        side_load = captive_hex_nut_trap(5.5, 2.4, entry_length=5.0)
        self.assert_valid(trap, "nut-trap")
        self.assert_valid(side_load, "side-load-nut-trap")
        expected_af = 5.5 + 2.0 * CLEARANCE_CLOSE_PER_SIDE
        self.assertAlmostEqual(min(trap.extents[:2]), expected_af, delta=0.03)
        self.assertAlmostEqual(trap.extents[2], 2.65, delta=0.02)
        self.assertGreater(side_load.extents[0], trap.extents[0])

    def test_dovetail_and_tongue_grooves_expand_for_sliding_fit(self) -> None:
        tail = dovetail_tongue(8.0, 12.0, 4.0, 25.0)
        tail_groove = dovetail_groove_cutter(8.0, 12.0, 4.0, 25.0)
        rail = tongue(8.0, 3.0, 25.0)
        rail_groove = tongue_groove_cutter(8.0, 3.0, 25.0)
        for name, mesh in (
            ("tail", tail),
            ("tail-groove", tail_groove),
            ("rail", rail),
            ("rail-groove", rail_groove),
        ):
            self.assert_valid(mesh, name)
        self.assertAlmostEqual(
            tail_groove.extents[0] - tail.extents[0],
            2.0 * CLEARANCE_SLIDING_PER_SIDE,
            delta=0.03,
        )
        self.assertGreater(tail_groove.extents[2], tail.extents[2])
        self.assertAlmostEqual(
            rail_groove.extents[0] - rail.extents[0],
            2.0 * CLEARANCE_SLIDING_PER_SIDE,
            delta=0.03,
        )


if __name__ == "__main__":
    unittest.main()
