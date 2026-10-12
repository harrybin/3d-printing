"""Keep user plate placement and Orca overrides during source mesh updates."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import trimesh
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from refresh_ghouls_grip_print_geometry import refresh

NS = {"c": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


def entries(path):
    with ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def lowest_vertex(entries_by_name, object_id):
    model = ET.fromstring(entries_by_name["3D/3dmodel.model"])
    obj = next(node for node in model.findall("c:resources/c:object", NS)
               if node.get("id") == object_id)
    component = obj.find("c:components/c:component", NS)
    path = component.get(
        "{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}path")
    mesh = ET.fromstring(entries_by_name[path.lstrip("/")])
    vertices = np.asarray([
        [float(node.get(axis)) for axis in ("x", "y", "z")]
        for node in mesh.findall(".//c:vertex", NS)
    ])
    item = next(node for node in model.findall("c:build/c:item", NS)
                if node.get("objectid") == object_id)
    matrix = np.asarray([float(value) for value in item.get("transform").split()])
    return float(np.min(vertices @ matrix[:9].reshape((3, 3)).T[2]) + matrix[11])


class SavedPrintRefreshTests(unittest.TestCase):
    def test_refresh_preserves_existing_transforms_settings_and_plate_membership(self):
        source = ROOT / "models" / "ghouls-grip-print.3mf"
        before = entries(source)
        old_model = ET.fromstring(before["3D/3dmodel.model"])
        old_settings = ET.fromstring(before["Metadata/model_settings.config"])
        replacements = {
            name: trimesh.creation.box(extents=(4, 4, 4))
            for name in ("chest", "lid-transfer-gear-01", "lid-transfer-gear-02")
        }
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / source.name
            shutil.copyfile(source, project)
            refresh(project, replacements, {"chest"})
            after = entries(project)
            refresh(project, replacements, {"chest"})
            repeated = entries(project)
        self.assertEqual(before["Metadata/project_settings.config"],
                         after["Metadata/project_settings.config"])
        chest_id = next(node.get("id") for node in old_settings.findall("object")
                        if node.find("metadata[@key='name']").get("value") == "chest")
        self.assertAlmostEqual(lowest_vertex(before, chest_id),
                               lowest_vertex(after, chest_id), places=3)
        for name, payload in before.items():
            if (name.startswith("3D/Objects/")
                    and not name.rsplit("/", 1)[-1].startswith(
                        ("chest_", "lid-transfer-gear-"))):
                self.assertEqual(payload, after[name], name)
        new_model = ET.fromstring(after["3D/3dmodel.model"])
        new_items = {
            node.get("objectid"): node.attrib
            for node in new_model.findall("c:build/c:item", NS)
        }
        for node in old_model.findall("c:build/c:item", NS):
            self.assertEqual(node.attrib, new_items[node.get("objectid")])
        new_settings = ET.fromstring(after["Metadata/model_settings.config"])
        new_configs = {node.get("id"): ET.tostring(node)
                       for node in new_settings.findall("object")}
        for node in old_settings.findall("object"):
            self.assertEqual(ET.tostring(node), new_configs[node.get("id")])
        self.assertEqual(len(new_settings.findall("plate")), 5)
        for old, new in zip(old_settings.findall("plate"),
                            new_settings.findall("plate")):
            old_ids = {node.find("metadata[@key='object_id']").get("value")
                       for node in old.findall("model_instance")}
            new_ids = {node.find("metadata[@key='object_id']").get("value")
                       for node in new.findall("model_instance")}
            self.assertTrue(old_ids <= new_ids)
        self.assertEqual(len(new_items), 37)
        self.assertEqual(after, repeated)
        self.assertIn(b'xmlns:p=', after["3D/3dmodel.model"])
        self.assertIn(b"<Relationships ", after["3D/_rels/3dmodel.model.rels"])
        self.assertIn(b"<Relationship ", after["3D/_rels/3dmodel.model.rels"])
        metadata = ET.fromstring(after["Metadata/ghouls_grip_print_metadata.xml"])
        self.assertEqual(metadata.find("metadata[@name='status']").get("value"),
                         "not-verified")


if __name__ == "__main__":
    unittest.main()
