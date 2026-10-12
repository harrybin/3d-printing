"""Keep the bone-only plate layout compact and preserve project semantics."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from arrange_ghouls_grip_bone_plate import (  # noqa: E402
    BED_SIZE,
    EDGE_MARGIN,
    PART_CLEARANCE,
    PART_NAMES,
    PLATE_X_OFFSET,
    arrange,
    _build_id_by_name,
    _xy_bounds,
)

CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
NS = {"c": CORE}


def project_entries(path: Path) -> dict[str, bytes]:
    with ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


class BonePlateLayoutTests(unittest.TestCase):
    def test_layout_is_centered_compact_and_idempotent(self) -> None:
        source = ROOT / "models" / "ghouls-grip-print.3mf"
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / source.name
            shutil.copyfile(source, project)
            before = project_entries(project)
            arrange(project)
            after = project_entries(project)
            arrange(project)
            repeated = project_entries(project)

        model = ET.fromstring(after["3D/3dmodel.model"])
        settings = ET.fromstring(after["Metadata/model_settings.config"])
        names_to_ids = _build_id_by_name(settings)
        self.assertEqual(len(settings.findall("plate")), 5)
        self.assertEqual(len(model.findall("c:build/c:item", NS)), 37)
        self.assertEqual(after["Metadata/project_settings.config"],
                         before["Metadata/project_settings.config"])
        self.assertEqual(after["Metadata/model_settings.config"],
                         before["Metadata/model_settings.config"])
        self.assertEqual(after, repeated)

        expected_minima = {
            "forearm": (69.0, 72.0),
            "hand-palm": (100.79, 72.0),
            "hand-finger-thumb": (69.0, 103.18),
        }
        bounds_by_name = {}
        for name in PART_NAMES:
            bounds = _xy_bounds(after, model, names_to_ids[name])
            local = (bounds[0] - PLATE_X_OFFSET, bounds[1],
                     bounds[2] - PLATE_X_OFFSET, bounds[3])
            bounds_by_name[name] = local
            self.assertGreaterEqual(local[0], EDGE_MARGIN)
            self.assertGreaterEqual(local[1], EDGE_MARGIN)
            self.assertLessEqual(local[2], BED_SIZE - EDGE_MARGIN)
            self.assertLessEqual(local[3], BED_SIZE - EDGE_MARGIN)
        for name, minimum in expected_minima.items():
            self.assertAlmostEqual(bounds_by_name[name][0], minimum[0], places=2)
            self.assertAlmostEqual(bounds_by_name[name][1], minimum[1], places=2)
        for index, first_name in enumerate(PART_NAMES):
            first = bounds_by_name[first_name]
            for second_name in PART_NAMES[index + 1:]:
                second = bounds_by_name[second_name]
                gap_x = max(second[0] - first[2], first[0] - second[2], 0.0)
                gap_y = max(second[1] - first[3], first[1] - second[3], 0.0)
                self.assertTrue(
                    gap_x >= PART_CLEARANCE - 0.01
                    or gap_y >= PART_CLEARANCE - 0.01,
                    f"{first_name} and {second_name} are too close",
                )

        for name in PART_NAMES:
            object_id = names_to_ids[name]
            previous_model = ET.fromstring(before["3D/3dmodel.model"])
            old_item = next(
                item for item in previous_model.findall("c:build/c:item", NS)
                if item.get("objectid") == object_id)
            new_item = next(
                item for item in model.findall("c:build/c:item", NS)
                if item.get("objectid") == object_id)
            old_transform = old_item.get("transform").split()
            new_transform = new_item.get("transform").split()
            self.assertEqual(old_transform[:9], new_transform[:9])
            self.assertEqual(old_transform[11], new_transform[11])

        for name, payload in before.items():
            if name.startswith("3D/Objects/"):
                self.assertEqual(payload, after[name], name)


if __name__ == "__main__":
    unittest.main()
