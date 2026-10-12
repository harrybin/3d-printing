"""Actual arm sweeps and load-path/assembly checks for the floor yokes."""

import sys
import unittest
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import mechanism as m
from gothic_chest import build_chest
from mesh_kit import box, cylinder
from render_ghouls_grip import lay_arm, rot
from verify_ghouls_grip_mechanics import volume_intersection
from refresh_ghouls_grip_print_geometry import surface


class FloorBearingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chest = build_chest()
        cls.arm = m.build_scissor_arm()

    def test_individual_arms_do_not_cut_chest_at_any_of_61_states(self):
        for theta in range(18, 79):
            for y in (-m.SCISSOR_Y, m.SCISSOR_Y):
                for mirrored in (False, True):
                    arm = lay_arm(self.arm, theta,
                                  y + (3 if mirrored else -3), mirrored)
                    self.assertLess(volume_intersection(arm, self.chest),
                                    0.001, (theta, y, mirrored))

    def test_bearing_cheeks_have_solid_roots_and_three_mm_bore_ligaments(self):
        self.assertTrue(self.chest.is_volume)
        self.assertEqual(len(self.chest.split()), 1)
        for y in (-m.SCISSOR_Y, m.SCISSOR_Y):
            for offset in (-8.0, 8.0):
                root = box((9.2, 4.0, 1.0), (0, y + offset, 2.0))
                self.assertAlmostEqual(volume_intersection(root, self.chest),
                                       root.volume, delta=0.002)
                for x in (-3.1, 3.1):
                    ligament = box((2.9, 3.8, 0.4),
                                   (x, y + offset, m.RAIL_Z))
                    self.assertAlmostEqual(
                        volume_intersection(ligament, self.chest),
                        ligament.volume, delta=0.002)

    def test_pins_span_both_cheeks_and_insert_without_chest_interference(self):
        for y in (-m.SCISSOR_Y, m.SCISSOR_Y):
            # Avoid coincident faceted cutter surfaces; prove at least 0.2 mm
            # radial clearance around the actual 2.7 mm printed shank.
            bore = cylinder(1.55, 20.0, (0, y, m.RAIL_Z), (0, 1, 0))
            self.assertLess(volume_intersection(bore, self.chest), 0.001)
            pin = m.build_pin(3.0, 26.0)
            pin.apply_transform(rot(-90 if y > 0 else 90, [1, 0, 0]))
            pin.apply_translation([0, y - 13 if y > 0 else y + 13, m.RAIL_Z])
            self.assertLessEqual(pin.bounds[0, 1] + (1.6 if y > 0 else 0),
                                 y - 10)
            self.assertGreaterEqual(pin.bounds[1, 1] - (1.6 if y < 0 else 0),
                                    y + 10)
            # Tip starts 1 mm before the inboard cheek; longer arbitrary
            # excursions would pass through the unrelated opposite wall.
            for dy in np.linspace(24, 0, 25):
                candidate = pin.copy()
                candidate.apply_translation([0, -dy if y > 0 else dy, 0])
                self.assertLess(volume_intersection(candidate, self.chest), 0.001)
            for offset in (-8, 8):
                engagement = cylinder(1.30, 4, (0, y + offset, m.RAIL_Z),
                                      (0, 1, 0))
                self.assertAlmostEqual(volume_intersection(pin, engagement),
                                       engagement.volume, delta=0.002)

    def test_arm_drop_in_and_default_axial_clearance_are_not_blocked(self):
        for y in (-m.SCISSOR_Y, m.SCISSOR_Y):
            for mirrored in (False, True):
                arm = lay_arm(self.arm, 18, y + (3 if mirrored else -3), mirrored)
                # Expand only along the pin axis to prove a 0.4 mm running gap.
                expanded = arm.copy()
                expanded.vertices[:, 1] = (
                    (expanded.vertices[:, 1] - arm.bounds.mean(axis=0)[1])
                    * (1 + 2 * m.FIT / m.ARM_T)
                    + arm.bounds.mean(axis=0)[1])
                self.assertLess(volume_intersection(expanded, self.chest), 0.001)
                for dz in np.linspace(20, 0, 21):
                    candidate = arm.copy()
                    candidate.apply_translation([0, 0, dz])
                    self.assertLess(volume_intersection(candidate, self.chest), 0.001)

    def test_delivered_print_chest_matches_repaired_source_not_stale_posts(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "models/ghouls-grip-print.3mf"
        ns = {"c": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
        with ZipFile(path) as archive:
            settings = ET.fromstring(archive.read("Metadata/model_settings.config"))
            model = ET.fromstring(archive.read("3D/3dmodel.model"))
            config = next(obj for obj in settings.findall("object")
                          if obj.find("metadata[@key='name']").get("value") == "chest")
            obj = next(obj for obj in model.findall("c:resources/c:object", ns)
                       if obj.get("id") == config.get("id"))
            component = obj.find("c:components/c:component", ns)
            entry = component.get(
                "{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}path")
            mesh_xml = ET.fromstring(archive.read(entry.lstrip("/")))
        vertices = np.array([[float(v.get(a)) for a in ("x", "y", "z")]
                             for v in mesh_xml.findall(".//c:vertex", ns)])
        faces = np.array([[int(f.get(a)) for a in ("v1", "v2", "v3")]
                          for f in mesh_xml.findall(".//c:triangle", ns)])
        source = self.chest.vertices - self.chest.bounds.mean(axis=0)
        self.assertEqual(surface(vertices, faces), surface(source, self.chest.faces))

    def test_delivered_floor_pin_heads_face_open_centre_not_closed_outer_wall(self):
        root = Path(__file__).resolve().parents[1]
        scene = trimesh.load(root / "models/ghouls-grip-view.3mf", force="scene")
        for pose in ("retracted", "intermediate", "deployed"):
            def part(name):
                transform, geometry = scene.graph.get(pose + "-" + name)
                mesh = scene.geometry[geometry].copy()
                mesh.apply_transform(transform)
                return mesh

            chest = part("chest")
            origin = np.array([chest.bounds[:, 0].mean(),
                               chest.bounds[1, 1] - 66, 0])
            for index, y in enumerate((-m.SCISSOR_Y, m.SCISSOR_Y)):
                pin = part(f"pivot-pin-3-{index}-0")
                head = cylinder(3.0, 1.0,
                                origin + [0, y - np.sign(y) * 12.2, m.RAIL_Z],
                                (0, 1, 0))
                self.assertAlmostEqual(volume_intersection(pin, head),
                                       head.volume, delta=0.002)
                for dy in np.linspace(24, 0, 25):
                    candidate = pin.copy()
                    candidate.apply_translation([0, -np.sign(y) * dy, 0])
                    self.assertLess(volume_intersection(candidate, chest), 0.001)

    def test_repair_keeps_all_saved_plate_settings_and_other_payloads(self):
        root = Path(__file__).resolve().parents[1]
        import io
        previous = subprocess.run(
            ["git", "show", "HEAD:models/ghouls-grip-print.3mf"],
            cwd=root, check=True, capture_output=True).stdout
        with ZipFile(io.BytesIO(previous)) as old, ZipFile(
                root / "models/ghouls-grip-print.3mf") as new:
            for entry in old.namelist():
                if entry == "Metadata/project_settings.config" or (
                        entry.startswith("3D/Objects/") and
                        not entry.rsplit("/", 1)[-1].startswith("chest_")):
                    self.assertEqual(old.read(entry), new.read(entry), entry)
            ns = {"c": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
            for entry, selector in (
                ("3D/3dmodel.model", "c:build/c:item"),
                ("Metadata/model_settings.config", "object"),
                ("Metadata/model_settings.config", "plate/model_instance"),
            ):
                before = ET.fromstring(old.read(entry)).findall(selector, ns)
                after = ET.fromstring(new.read(entry)).findall(selector, ns)
                self.assertEqual([ET.tostring(node) for node in before],
                                 [ET.tostring(node) for node in after], entry)


if __name__ == "__main__":
    unittest.main()
