"""Regression checks for Ghoul's Grip Orca project defaults."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from export_ghouls_grip_orca_projects import (  # noqa: E402
    MATERIAL_PROJECTS,
    OBJECT_OVERRIDES,
    _process_settings,
)


class GhoulOrcaSettingsTests(unittest.TestCase):
    def test_all_projects_use_random_seams_and_top_ironing(self) -> None:
        for slug, spec in MATERIAL_PROJECTS.items():
            with self.subTest(slug=slug):
                settings = _process_settings(spec)
                self.assertEqual(settings["seam_position"], "random")
                self.assertEqual(settings["ironing_type"], "top")

    def test_all_projects_keep_automatic_support_enabled(self) -> None:
        for slug, spec in MATERIAL_PROJECTS.items():
            with self.subTest(slug=slug):
                settings = _process_settings(spec)
                self.assertEqual(settings["enable_support"], "1")
                self.assertIn("auto", settings["support_type"])

    def test_baseline_enables_support_without_a_material_policy(self) -> None:
        spec = {"wall_loops": "4", "infill": "20%", "speed": "standard"}
        settings = _process_settings(spec)
        self.assertEqual(settings["enable_support"], "1")
        self.assertEqual(settings["support_type"], "tree(auto)")

    def test_no_object_override_disables_support(self) -> None:
        for name, override in OBJECT_OVERRIDES.items():
            with self.subTest(part=name):
                self.assertNotEqual(override.get("enable_support"), "0")

    def test_black_project_uses_named_two_plate_layout(self) -> None:
        black = MATERIAL_PROJECTS["black-pla"]
        self.assertEqual(black["plate_row_pitch"], 140.0)
        self.assertEqual(
            black["plate_names"],
            ("Schatulle", "Deckel auf Hinterkante stehend"),
        )

    def test_mechanism_second_plate_identifies_connectors(self) -> None:
        mechanism = MATERIAL_PROJECTS["mechanism-pla"]
        self.assertIn("Verbinder", mechanism["plate_names"][1])


if __name__ == "__main__":
    unittest.main()
