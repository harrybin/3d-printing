"""Regression tests for analytical print-orientation checks."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mesh_tool  # noqa: E402


class OverhangTests(unittest.TestCase):
    def test_upright_cube_does_not_count_vertical_walls_as_unsupported(self) -> None:
        cube = trimesh.creation.box((10.0, 10.0, 10.0))
        cube.apply_translation((0.0, 0.0, 5.0))
        args = SimpleNamespace(file="cube.stl", limit=45.0)

        with patch.object(mesh_tool, "load_mesh", return_value=cube), \
                patch("builtins.print") as output:
            mesh_tool.cmd_overhang(args)

        unsupported = next(
            str(call.args[0]) for call in output.call_args_list
            if "unsupported area" in str(call.args[0])
        )
        ceilings = next(
            str(call.args[0]) for call in output.call_args_list
            if "ceilings" in str(call.args[0])
        )
        bridge_span = next(
            str(call.args[0]) for call in output.call_args_list
            if "max ceiling short span" in str(call.args[0])
        )
        self.assertIn("0.00 mm^2", unsupported)
        self.assertIn("0.00 mm^2", ceilings)
        self.assertIn("0.00 mm", bridge_span)

    def test_floating_horizontal_floor_is_counted_as_unsupported(self) -> None:
        bed_cube = trimesh.creation.box((2.0, 2.0, 2.0))
        bed_cube.apply_translation((0.0, 0.0, 1.0))
        floating_cube = trimesh.creation.box((10.0, 10.0, 10.0))
        floating_cube.apply_translation((0.0, 0.0, 15.0))
        cube = trimesh.util.concatenate([bed_cube, floating_cube])
        args = SimpleNamespace(file="cube.stl", limit=45.0)

        with patch.object(mesh_tool, "load_mesh", return_value=cube), \
                patch("builtins.print") as output:
            mesh_tool.cmd_overhang(args)

        unsupported = next(
            str(call.args[0]) for call in output.call_args_list
            if "unsupported area" in str(call.args[0])
        )
        ceilings = next(
            str(call.args[0]) for call in output.call_args_list
            if "ceilings" in str(call.args[0])
        )
        bridge_span = next(
            str(call.args[0]) for call in output.call_args_list
            if "max ceiling short span" in str(call.args[0])
        )
        self.assertIn("100.00 mm^2", unsupported)
        self.assertIn("100.00 mm^2", ceilings)
        self.assertIn("10.00 mm", bridge_span)


if __name__ == "__main__":
    unittest.main()
