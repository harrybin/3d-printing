"""Regression checks for Ghoul's Grip Orca project defaults."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from export_ghouls_grip_orca_projects import (  # noqa: E402
    FILAMENT_ORDER,
    MATERIAL_PROJECTS,
    OBJECT_OVERRIDES,
    PRINT_OUTPUT,
    _pack_print_layout,
    _write_multi_plate_settings,
    _process_settings,
)
from ghouls_grip import BLACK, MECH, material_for, write_3mf  # noqa: E402
from update_ghouls_grip_slice_metadata import _number  # noqa: E402


class GhoulOrcaSettingsTests(unittest.TestCase):
    def test_deliverables_use_one_view_and_one_multifilament_print_project(self) -> None:
        self.assertEqual(PRINT_OUTPUT.name, "ghouls-grip-print.3mf")
        self.assertEqual(FILAMENT_ORDER, (
            "black-pla", "bone-pla", "mechanism-pla", "accent-pla",
        ))
        self.assertEqual(
            [MATERIAL_PROJECTS[slug]["color"] for slug in FILAMENT_ORDER],
            ["#202124", "#D8C6A5", "#F1EBDD", "#D4AF37"],
        )

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

    def test_multi_plate_export_uses_orca_settings_names_for_objects(self) -> None:
        names = ("chest", "scissor-arm-01")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "names.3mf"
            objects = [
                (names[0], trimesh.creation.box(), BLACK, None),
                (names[1], trimesh.creation.box(), MECH, None),
            ]
            write_3mf(
                path,
                objects,
                plate_names=["Source"],
                object_plates={name: 0 for name in names},
                material_slots={BLACK: 0, MECH: 1},
            )
            with ZipFile(path) as archive:
                entries = {
                    info.filename: archive.read(info.filename)
                    for info in archive.infolist()
                }
                infos = archive.infolist()

            model_key = "3D/3dmodel.model"
            model = ET.fromstring(entries[model_key])
            core = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
            for obj in model.findall(f".//{{{core}}}object"):
                obj.attrib.pop("name", None)
            for item in model.findall(f".//{{{core}}}item"):
                item.set("transform", "1 0 0 0 1 0 0 0 1 0 0 0")
            entries[model_key] = ET.tostring(
                model, encoding="utf-8", xml_declaration=True)
            with ZipFile(path, "w") as archive:
                for info in infos:
                    archive.writestr(info, entries[info.filename])

            _write_multi_plate_settings(
                path,
                ["Black", "Mechanism"],
                {names[0]: 0, names[1]: 1},
                material_for,
            )

            with ZipFile(path) as archive:
                self.assertEqual(archive.read(model_key), entries[model_key])
                settings = ET.fromstring(
                    archive.read("Metadata/model_settings.config"))
            plates = settings.findall("plate")
            self.assertEqual(len(plates), 2)
            assigned = [
                metadata.get("value")
                for plate in plates
                for instance in plate.findall("model_instance")
                for metadata in instance.findall("metadata")
                if metadata.get("key") == "object_id"
            ]
            self.assertCountEqual(assigned, ["2", "3"])

    def test_print_objects_use_orca_grid_offsets_for_their_plate(self) -> None:
        names = ("chest", "lid", "forearm", "slider", "drive-skull-knob")
        parts = {name: trimesh.creation.box() for name in names}

        def arrange(selected, gap, margin):
            arranged = []
            for name, mesh in selected.items():
                placed = mesh.copy()
                row_y = 140.5 if name == "lid" else 0.5
                placed.apply_translation([0.5, row_y + 0.5, 0.5])
                arranged.append((name, placed, material_for(name), None))
            return arranged

        objects, plates, object_plate = _pack_print_layout(
            parts, arrange, material_for)
        self.assertEqual(len(plates), 5)
        self.assertEqual(object_plate, {
            "chest": 0,
            "lid": 1,
            "forearm": 2,
            "slider": 3,
            "drive-skull-knob": 4,
        })
        xy_by_name = {
            name: mesh.centroid[:2] for name, mesh, *_ in objects
        }
        expected_xy = {
            "chest": (0.5, 1.0),
            "lid": (300.5, 1.0),
            "forearm": (600.5, 1.0),
            "slider": (0.5, -299.0),
            "drive-skull-knob": (300.5, -299.0),
        }
        for name, expected in expected_xy.items():
            for axis, value in enumerate(expected):
                self.assertAlmostEqual(xy_by_name[name][axis], value)

    def test_slice_statistics_select_the_assigned_filament_slot(self) -> None:
        header = "; filament used [g] = 0.00, 43.35, 0.00, 0.00"
        self.assertEqual(_number(header, "filament used [g]", 1), 43.35)


if __name__ == "__main__":
    unittest.main()
