"""Verify the consolidated mechanism plate remains safe and reproducible."""

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

from consolidate_ghouls_grip_mechanism_plates import consolidate

CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PRODUCTION = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
NS = {"c": CORE}


def _entries(path: Path) -> dict[str, bytes]:
    with ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


class MechanismPlateConsolidationTests(unittest.TestCase):
    def test_consolidation_is_idempotent_and_keeps_every_part_on_bed(self):
        source = ROOT / "models" / "ghouls-grip-print.3mf"
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / source.name
            shutil.copyfile(source, project)
            before = _entries(project)
            consolidate(project)
            after = _entries(project)
            consolidate(project)
            repeated = _entries(project)

        self.assertEqual(after, repeated)
        for name, payload in before.items():
            if name.startswith("3D/Objects/"):
                self.assertEqual(payload, after[name], name)

        settings = ET.fromstring(after["Metadata/model_settings.config"])
        model = ET.fromstring(after["3D/3dmodel.model"])
        plates = settings.findall("plate")
        self.assertEqual(len(plates), 4)
        mechanism_plate = next(
            plate for plate in plates
            if "Hauptteile" in plate.find(
                "metadata[@key='plater_name']").get("value")
        )
        instances = mechanism_plate.findall("model_instance")
        self.assertEqual(len(instances), 31)
        object_configs = {
            obj.get("id"): obj for obj in settings.findall("object")
        }
        names = {
            object_id: obj.find("metadata[@key='name']").get("value")
            for object_id, obj in object_configs.items()
        }
        resources = {
            obj.get("id"): obj
            for obj in model.findall("c:resources/c:object", NS)
        }
        transforms = {
            item.get("objectid"): [
                float(value) for value in item.get("transform").split()
            ]
            for item in model.findall("c:build/c:item", NS)
        }
        boxes = []
        mechanism_extruders = set()
        for instance in instances:
            object_id = instance.find(
                "metadata[@key='object_id']").get("value")
            config = object_configs[object_id]
            mechanism_extruders.add(
                config.find("metadata[@key='extruder']").get("value")
            )
            self.assertEqual(len(mechanism_extruders), 1)
            component = resources[object_id].find(
                "c:components/c:component", NS)
            entry = component.get(f"{{{PRODUCTION}}}path").lstrip("/")
            mesh_root = ET.fromstring(after[entry])
            vertices = [
                tuple(float(vertex.get(axis)) for axis in ("x", "y", "z"))
                for vertex in mesh_root.findall(".//c:vertex", NS)
            ]
            matrix = transforms[object_id]
            points = [
                (
                    matrix[0] * x + matrix[1] * y + matrix[2] * z
                    + matrix[9],
                    matrix[3] * x + matrix[4] * y + matrix[5] * z
                    + matrix[10],
                )
                for x, y, z in vertices
            ]
            x_values, y_values = zip(*points)
            box = (
                min(x_values), min(y_values) + 300.0,
                max(x_values), max(y_values) + 300.0,
            )
            self.assertGreaterEqual(box[0], 10.0)
            self.assertGreaterEqual(box[1], 10.0)
            self.assertLessEqual(box[2], 240.0)
            self.assertLessEqual(box[3], 240.0)
            boxes.append((names[object_id], box))

        for index, (name, first) in enumerate(boxes):
            for other_name, second in boxes[index + 1:]:
                overlaps = (
                    first[0] < second[2] and second[0] < first[2]
                    and first[1] < second[3] and second[1] < first[3]
                )
                self.assertFalse(overlaps, f"{name} overlaps {other_name}")

        assigned = [
            instance.find("metadata[@key='object_id']").get("value")
            for plate in plates for instance in plate.findall("model_instance")
        ]
        self.assertEqual(len(assigned), 41)
        self.assertEqual(len(set(assigned)), 41)


if __name__ == "__main__":
    unittest.main()
