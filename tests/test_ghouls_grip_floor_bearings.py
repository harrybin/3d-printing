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
from mesh_kit import box, cylinder, difference
from render_ghouls_grip import lay_arm, rot
from verify_ghouls_grip_mechanics import volume_intersection
from refresh_ghouls_grip_print_geometry import surface


class FloorBearingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chest = build_chest()
        cls.arm = m.build_scissor_arm()

    @staticmethod
    def arm_pose(y: float, mirrored: bool):
        """Same layout as render_ghouls_grip: True arms outboard, -Y flipped."""
        side = np.sign(y)
        return y + (side * 3 if mirrored else -side * 3), side < 0

    def test_individual_arms_do_not_cut_chest_at_any_of_61_states(self):
        for theta in range(18, 79):
            for y in (-m.SCISSOR_Y, m.SCISSOR_Y):
                for mirrored in (False, True):
                    arm_y, flip = self.arm_pose(y, mirrored)
                    arm = lay_arm(self.arm, theta, arm_y, mirrored, flip)
                    self.assertLess(volume_intersection(arm, self.chest),
                                    0.001, (theta, y, mirrored))

    def test_bearing_cheeks_have_solid_roots_and_bore_ligaments(self):
        self.assertTrue(self.chest.is_volume)
        self.assertEqual(len(self.chest.split()), 1)
        bore_r = m.PIVOT_D / 2.0
        cbore_r = m.PIN_CBORE_D / 2.0
        for y in (-m.SCISSOR_Y, m.SCISSOR_Y):
            side = np.sign(y)
            for offset in (-8.0, 8.0):
                centre_y = y + offset
                root = box((9.2, 4.0, 1.0), (0, centre_y, 2.0))
                self.assertAlmostEqual(volume_intersection(root, self.chest),
                                       root.volume, delta=0.002)
                outboard = offset * side > 0
                # Full-depth bore ligament (2.3 mm beside the Ø4.6 bore);
                # the outboard cheek carries the barb counterbore on its
                # outer 1.6 mm, so probe only its plain inner part there.
                depth = 4.0 - m.PIN_CBORE_DEPTH - 0.2 if outboard else 3.8
                probe_y = (centre_y - side * (2.0 - depth / 2.0)
                           if outboard else centre_y)
                width = m.FLOOR_BEARING_R - bore_r - 0.1
                for sx in (-1.0, 1.0):
                    ligament = box((width, depth, 0.4),
                                   (sx * (bore_r + 0.05 + width / 2.0),
                                    probe_y, m.RAIL_Z))
                    self.assertAlmostEqual(
                        volume_intersection(ligament, self.chest),
                        ligament.volume, delta=0.002)
                    if outboard:
                        # Ring left around the Ø6 counterbore.
                        rim_w = m.FLOOR_BEARING_R - cbore_r - 0.1
                        rim = box((rim_w, m.PIN_CBORE_DEPTH - 0.2, 0.4),
                                  (sx * (cbore_r + 0.05 + rim_w / 2.0),
                                   centre_y + side * (2.0 - m.PIN_CBORE_DEPTH / 2.0),
                                   m.RAIL_Z))
                        self.assertAlmostEqual(
                            volume_intersection(rim, self.chest),
                            rim.volume, delta=0.002)

    def floor_pin(self, y: float):
        side = np.sign(y)
        pin = m.build_pin_variant("floor")
        pin.apply_transform(rot(-90 if side > 0 else 90, [1, 0, 0]))
        # Head underside on the inboard cheek face (|y| 30), barb outboard.
        pin.apply_translation([0, side * (abs(y) - 10.0), m.RAIL_Z])
        return pin

    def test_pins_span_both_cheeks_and_insert_without_chest_interference(self):
        for y in (-m.SCISSOR_Y, m.SCISSOR_Y):
            side = np.sign(y)
            # The Ø4.6 bore is free along the whole double-shear line: prove
            # 0.3 mm radial running clearance around the Ø4 shank.
            bore = cylinder(m.PIN_D / 2.0, 20.0, (0, y, m.RAIL_Z), (0, 1, 0))
            self.assertLess(volume_intersection(bore, self.chest), 0.001)
            pin = self.floor_pin(y)
            # Installed: the barb sits in its counterbore without interference.
            self.assertLess(volume_intersection(pin, self.chest), 0.001)
            inboard = min(abs(pin.bounds[0, 1]), abs(pin.bounds[1, 1]))
            outboard = max(abs(pin.bounds[0, 1]), abs(pin.bounds[1, 1]))
            self.assertLessEqual(inboard, abs(y) - 10.0 - m.PIN_HEAD_T + 0.01)
            self.assertLessEqual(outboard, abs(y) + 10.0)
            # Each split half closes by the barb offset (2 x 0.35 of the
            # 1.4 mm slot); closed, the barb arc clears the Ø4.6 bore.
            self.assertLess(2.0 * m.PIN_BARB_OFFSET, m.PIN_SLOT_W - 0.4)
            self.assertLessEqual(m.PIN_BARB_ARC_R, m.PIVOT_D / 2.0 - 0.1 + 1e-9)
            self.assertGreaterEqual(m.PIN_BARB_R - m.PIVOT_D / 2.0, 0.2)
            # Approach from the open centre: everything except the snapping
            # barb (shank, head) stays clear of the chest on the way in.
            shank = cylinder(m.PIN_D / 2.0, m.PIN_GRIPS["floor"] - 2.0,
                             (0, side * (abs(y) - 10.0 + m.PIN_GRIPS["floor"] / 2.0 - 1.0),
                              m.RAIL_Z), (0, 1, 0))
            head = cylinder(m.PIN_HEAD_D / 2.0, m.PIN_HEAD_T,
                            (0, side * (abs(y) - 10.0 - m.PIN_HEAD_T / 2.0),
                             m.RAIL_Z), (0, 1, 0))
            for dy in np.linspace(24, 0, 25):
                for part in (shank, head):
                    candidate = part.copy()
                    candidate.apply_translation([0, -side * dy, 0])
                    self.assertLess(volume_intersection(candidate, self.chest),
                                    0.001, dy)
            inner_cheek = cylinder(1.30, 4, (0, y - side * 8, m.RAIL_Z),
                                   (0, 1, 0))
            self.assertAlmostEqual(volume_intersection(pin, inner_cheek),
                                   inner_cheek.volume, delta=0.002)
            outer_cheek = cylinder(1.30, 2.0, (0, y + side * 7.0, m.RAIL_Z),
                                   (0, 1, 0))
            self.assertGreater(volume_intersection(pin, outer_cheek),
                               0.3 * outer_cheek.volume)

    def test_arm_drop_in_and_default_axial_clearance_are_not_blocked(self):
        for y in (-m.SCISSOR_Y, m.SCISSOR_Y):
            for mirrored in (False, True):
                arm_y, flip = self.arm_pose(y, mirrored)
                arm = lay_arm(self.arm, 18, arm_y, mirrored, flip)
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
                pin = part(f"pivot-pin-floor-{index}")
                head = cylinder(1.5, 1.0,
                                origin + [0, y - np.sign(y) * 10.8, m.RAIL_Z],
                                (0, 1, 0))
                self.assertAlmostEqual(volume_intersection(pin, head),
                                       head.volume, delta=0.002)
                # The relaxed barbs snap through the bore by design; sweep the
                # closed envelope (barb arcs pressed onto r PIN_BARB_ARC_R).
                head_face = abs(y) - 10.0
                barb_zone = difference(
                    cylinder(4.0, 40.0, origin + [0, np.sign(y) * (head_face + 20.05),
                                                  m.RAIL_Z], (0, 1, 0)),
                    [cylinder(m.PIN_BARB_ARC_R + 0.001, 42.0,
                              origin + [0, np.sign(y) * (head_face + 20.05),
                                        m.RAIL_Z], (0, 1, 0))])
                closed = difference(pin, [barb_zone])
                for dy in np.linspace(24, 0, 25):
                    candidate = closed.copy()
                    candidate.apply_translation([0, -np.sign(y) * dy, 0])
                    self.assertLess(volume_intersection(candidate, chest), 0.001)

    def test_repair_keeps_all_saved_plate_settings_and_other_payloads(self):
        root = Path(__file__).resolve().parents[1]
        import json
        with ZipFile(root / "models/ghouls-grip-print.3mf") as new:
            project_settings = json.loads(
                new.read("Metadata/project_settings.config")
            )
            self.assertEqual(project_settings.get("curr_bed_type"), "Textured PEI Plate")
            self.assertLessEqual(float(project_settings.get("layer_height", "1.0")), 0.16)
            self.assertEqual(project_settings.get("seam_position"), "random")
            self.assertEqual(project_settings.get("ironing_type"), "top")
            self.assertEqual(project_settings.get("support_type"), "tree(auto)")
            self.assertEqual(
                project_settings.get("support_top_z_distance"),
                project_settings.get("layer_height"),
            )
            self.assertEqual(
                project_settings.get("support_bottom_z_distance"),
                project_settings.get("layer_height"),
            )
            new_names = set(new.namelist())
            for entry in new_names:
                if entry.startswith("3D/Objects/"):
                    stem = entry.rsplit("/", 1)[-1].rsplit("_", 1)[0]
                    self.assertFalse(
                        stem.startswith(("lid-rack", "pivot-pin-3")), entry)
            new_settings = ET.fromstring(
                new.read("Metadata/model_settings.config"))
            new_configs = {
                obj.get("id"): obj for obj in new_settings.findall("object")
            }

            plates = new_settings.findall("plate")
            self.assertEqual(len(plates), 4)
            mechanism_plate = next(
                plate for plate in plates
                if "Hauptteile" in plate.find(
                    "metadata[@key='plater_name']").get("value")
            )
            mechanism_ids = {
                instance.find("metadata[@key='object_id']").get("value")
                for instance in mechanism_plate.findall("model_instance")
            }
            mechanism_extruders = {
                new_configs[object_id].find("metadata[@key='extruder']").get("value")
                for object_id in mechanism_ids
            }
            self.assertEqual(len(mechanism_extruders), 1)
            mech_extruder = next(iter(mechanism_extruders))
            new_mechanism_ids = {
                object_id for object_id, obj in new_configs.items()
                if obj.find("metadata[@key='extruder']").get("value") == mech_extruder
            }
            self.assertEqual(mechanism_ids, new_mechanism_ids)


if __name__ == "__main__":
    unittest.main()
