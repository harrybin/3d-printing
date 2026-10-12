import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from render_ghouls_grip_print_projects import plate_filament
from render_ghouls_grip_supports import support_segments
from update_ghouls_grip_slice_metadata import _filament_index


class SupportRenderTests(unittest.TestCase):
    def parse(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plate.gcode"
            path.write_text(text, encoding="utf-8")
            return support_segments(path)

    def test_relative_extrusion_and_support_interface(self):
        result = self.parse(
            "G90\nM83\nG1 X1 Y2 Z.2\n;TYPE:Support\n"
            "G1 X3 E.1\nG1 X4 E.05\nG1 X5 E-.1\n"
            "G1 X6\n;TYPE:Support interface\nG1 Y4 E.1\n"
            ";TYPE:Outer wall\nG1 X7 E.1\n")
        self.assertEqual(len(result), 3)
        np.testing.assert_allclose(result[0], [[1, 2, .2], [3, 2, .2]])
        np.testing.assert_allclose(result[-1], [[6, 2, .2], [6, 4, .2]])

    def test_absolute_extrusion_resets_and_relative_coordinates(self):
        result = self.parse(
            "G90\nM82\nG1 X1 E5\n;TYPE:Support\n"
            "G1 X2 E6\nG92 E0\nG91\nG1 X2 E.5\n"
            "G1 E1\nG1 X1 E.2\n")
        self.assertEqual(len(result), 2)
        np.testing.assert_allclose(result[1], [[2, 0, 0], [4, 0, 0]])

    def test_one_filament_per_plate_maps_to_project_color(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plate_2.gcode"
            path.write_text("; filament used [g] = 0.00, 43.51, 0.00, 0.00\n")
            self.assertEqual(plate_filament(path), ("Bone-beige PLA", "#D8C6A5"))
        self.assertEqual(_filament_index(
            "; filament used [g] = 0.00, 0.00, 9.66, 0.00"), 2)


if __name__ == "__main__":
    unittest.main()
