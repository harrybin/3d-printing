"""Create the consolidated printable OrcaSlicer project for Ghoul's Grip.

The single project contains one plate group per spool/color and carries each
part's virtual filament assignment and functional process overrides.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"

ORCA_BIN = Path(os.environ.get(
    "ORCA_SLICER_BIN", r"C:\Program Files\OrcaSlicer\orca-slicer.exe"))
PROFILE_ROOT = ORCA_BIN.parent / "resources" / "profiles" / "Anycubic"
MACHINE = PROFILE_ROOT / "machine" / "Anycubic Kobra S1 0.4 nozzle.json"
BASE_PROCESS = PROFILE_ROOT / "process" / \
    "0.20mm Standard @Anycubic Kobra S1 0.4 nozzle.json"
METADATA_ENTRY = "Metadata/ghouls_grip_print_metadata.xml"
PLATE_X_PITCH = 300.0
PLATE_GRID_COLUMNS = 3

MATERIAL_PROJECTS = {
    "black-pla": {
        "match": "Schatulle - schwarzes PLA",
        "color": "#202124",
        "filament": "Anycubic PLA @Anycubic Kobra S1 0.4 nozzle.json",
        # Economy shell: the 3 mm source walls still retain a durable
        # 1.2 mm perimeter envelope. Lower infill limits cosmetic mass; the
        # rebuilt slopes, short explicit bridges and vertical lid orientation
        # are verified with automatic tree support enabled. Zero generated
        # support is therefore a slicer result, not a forced setting.
        "wall_loops": "3", "infill": "10%", "speed": "standard",
        "filament_type": "PLA", "support": "tree",
        "support_threshold_angle": "45",
        "support_critical_regions_only": True,
        "bridge_no_support": True,
        "manual_gap": 20.0,
        "object_overrides": True,
        # arrange() places the 129 mm-deep lid on the second row at y≈150 mm.
        # A 140 mm row pitch converts that row into a separate Orca plate.
        "plate_row_pitch": 140.0,
        "plate_x_pitch": 300.0,
        "plate_names": (
            "Schatulle",
            "Deckel auf Hinterkante stehend",
        ),
    },
    "bone-pla": {
        "match": "Knochen - beiges PLA",
        "color": "#D8C6A5",
        "filament": "Anycubic PLA @Anycubic Kobra S1 0.4 nozzle.json",
        "wall_loops": "4", "infill": "25%", "speed": "standard",
        "filament_type": "PLA", "support": "tree", "manual_gap": 18.0,
        "object_overrides": True,
    },
    "mechanism-pla": {
        "match": "Mechanik - naturweisses PLA",
        "color": "#F1EBDD",
        "filament": "Anycubic PLA @Anycubic Kobra S1 0.4 nozzle.json",
        "wall_loops": "5", "infill": "40%", "speed": "mechanism",
        "filament_type": "PLA", "object_overrides": True, "support": "normal",
        "manual_gap": 10.0,
        "bed_margin": 10.0,
        # Compact packing keeps the complete mechanism BOM on two plates.
        # The 240 mm split preserves a 10 mm edge margin on both plates.
        "plate_row_pitch": 240.0,
        "plate_x_pitch": 300.0,
        "plate_names": (
            "Mechanik-Hauptteile",
            "Zahnraeder und Verbinder",
        ),
    },
    "accent-pla": {
        "match": "Totenkopf-Ausloeser - goldenes PLA",
        "color": "#D4AF37",
        "filament": "Anycubic PLA @Anycubic Kobra S1 0.4 nozzle.json",
        "wall_loops": "4", "infill": "25%", "speed": "standard",
        "filament_type": "PLA", "support": "tree",
    },
}

PRINT_OUTPUT = MODELS / "ghouls-grip-print.3mf"
FILAMENT_ORDER = tuple(MATERIAL_PROJECTS)

OBJECT_OVERRIDES = {
    "chest": {
        "wall_loops": "3", "sparse_infill_density": "10%",
    },
    "lid": {
        "wall_loops": "3", "sparse_infill_density": "10%",
    },
    "scissor-arm": {
        "wall_loops": "5", "sparse_infill_density": "100%",
    },
    "slider": {
        "wall_loops": "5", "sparse_infill_density": "25%",
        "enable_support": "1",
    },
    "platform": {
        "wall_loops": "5", "sparse_infill_density": "20%",
        "enable_support": "1",
    },
    "drive-pinion": {
        "wall_loops": "5", "sparse_infill_density": "30%",
    },
    "lid-follower-rack": {
        "wall_loops": "5", "sparse_infill_density": "25%",
        "enable_support": "1",
    },
    "lid-crank": {
        "wall_loops": "5", "sparse_infill_density": "100%",
    },
    "crank-spacer": {
        "wall_loops": "5", "sparse_infill_density": "100%",
    },
    "scissor-drive-gear": {
        "wall_loops": "5", "sparse_infill_density": "50%",
    },
    "idler-gear": {
        "wall_loops": "5", "sparse_infill_density": "50%",
    },
    "forearm-output-gear": {
        "wall_loops": "6", "sparse_infill_density": "50%",
        "enable_support": "1",
    },
    **{
        f"pivot-pin-{variant}": {
            "wall_loops": "6", "sparse_infill_density": "100%",
        }
        for variant in ("floor", "slider", "centre", "gear", "short",
                        "idler", "follower")
    },
    "forearm": {"wall_loops": "4", "sparse_infill_density": "25%"},
    "hand-palm": {"wall_loops": "4", "sparse_infill_density": "25%"},
    "drive-skull-knob": {
        "wall_loops": "5", "sparse_infill_density": "40%",
    },
    "candy-dish": {
        "wall_loops": "4", "sparse_infill_density": "15%",
        "enable_support": "1", "support_type": "tree(auto)",
    },
    "hand-finger": {
        "wall_loops": "2", "sparse_infill_density": "15%",
        "outer_wall_speed": "30", "inner_wall_speed": "40",
        "sparse_infill_speed": "50", "top_surface_speed": "30",
        "default_acceleration": "1500", "outer_wall_acceleration": "800",
        "inner_wall_acceleration": "1000",
    },
}


def _base_name(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"-\d{2}$", "", stem)
    return "hand-finger" if stem.startswith("hand-finger-") else stem


def _process_settings(spec: dict) -> dict:
    """Project overrides layered on Orca's recognized Kobra S1 preset."""
    data = {
        "curr_bed_type": "Textured PEI Plate",
        "layer_height": "0.2",
        "initial_layer_print_height": "0.2",
        "wall_loops": spec["wall_loops"],
        "sparse_infill_density": spec["infill"],
        "sparse_infill_pattern": "gyroid",
        "seam_position": "random",
        "ironing_type": "top",
        # Repo default: automatic support stays enabled in every generated
        # project so a slice that reports zero support is a geometry result
        # rather than a disabled setting.
        "enable_support": "1",
        "support_type": "tree(auto)",
        "support_on_build_plate_only": "1",
        "support_threshold_angle": "30",
        "enable_prime_tower": "0",
        "xy_hole_compensation": "0.1",
        "xy_contour_compensation": "0",
        "elefant_foot_compensation": "0.15",
        "brim_type": "auto_brim",
        "brim_width": "5",
        "detect_thin_wall": "1",
        "only_one_wall_top": "0",
    }
    support = spec.get("support")
    if support == "tree":
        data.update({
            "enable_support": "1", "support_type": "tree(auto)",
            "support_on_build_plate_only": "1",
            "support_threshold_angle": spec.get("support_threshold_angle", "30"),
        })
    elif support == "normal":
        data.update({
            "enable_support": "1",
            "support_type": "normal(auto)", "support_style": "snug",
            "support_on_build_plate_only": "1",
            "support_threshold_angle": "30",
        })
    if spec.get("support_critical_regions_only"):
        data["support_critical_regions_only"] = "1"
    if spec.get("bridge_no_support"):
        data["bridge_no_support"] = "1"
    if spec["speed"] == "mechanism":
        data.update({
            "outer_wall_speed": "120", "inner_wall_speed": "180",
            "sparse_infill_speed": "160", "top_surface_speed": "100",
            "default_acceleration": "4000", "outer_wall_acceleration": "2000",
        })
    elif spec["speed"] == "flexure":
        # Rigid PLA film hinges survive only if the 0.8 mm web is laid down
        # slowly, cooled hard and never thinned by a wide extrusion.
        data.update({
            "outer_wall_speed": "30", "inner_wall_speed": "40",
            "sparse_infill_speed": "50", "top_surface_speed": "30",
            "initial_layer_speed": "20", "default_acceleration": "1500",
            "outer_wall_acceleration": "800", "inner_wall_acceleration": "1000",
            "travel_acceleration": "3000",
            "wall_generator": "classic", "top_shell_layers": "4",
            "bottom_shell_layers": "4",
            "enable_support": "1", "support_type": "tree(auto)",
            "support_on_build_plate_only": "1",
            "support_threshold_angle": "30",
        })
    return data


def _patch_project_settings(path: Path, spec: dict) -> dict:
    with ZipFile(path) as archive:
        infos = archive.infolist()
        entries = {info.filename: archive.read(info.filename) for info in infos}

    project_key = "Metadata/project_settings.config"
    project = json.loads(entries[project_key].decode("utf-8"))
    overrides = _process_settings(spec)
    color = spec["color"].upper()
    overrides.update({
        "default_filament_colour": [color],
        "extruder_colour": [color],
        "filament_colour": [color],
    })
    project.update(overrides)
    changed = ";".join(sorted(key for key in overrides
                              if key != "filament_type"))
    project["different_settings_to_system"] = ["", changed, ""]
    entries[project_key] = json.dumps(project, indent=2).encode("utf-8")

    applied = {}
    if spec.get("object_overrides"):
        key = "Metadata/model_settings.config"
        root = ET.fromstring(entries[key])
        for obj in root.findall("object"):
            name_node = next((m for m in obj.findall("metadata")
                              if m.get("key") == "name"), None)
            if name_node is None:
                continue
            name = name_node.get("value", "")
            base = _base_name(name)
            settings = OBJECT_OVERRIDES.get(base)
            if not settings:
                continue
            for setting, value in settings.items():
                for old in [m for m in obj.findall("metadata")
                            if m.get("key") == setting]:
                    obj.remove(old)
                # Orca's model-settings schema requires object metadata before
                # the first <part>; appending after parts rejects slicing.
                insert_at = next((i for i, child in enumerate(list(obj))
                                  if child.tag == "part"), len(obj))
                obj.insert(insert_at, ET.Element(
                    "metadata", key=setting, value=value))
            applied[name] = settings
        entries[key] = ET.tostring(
            root, encoding="utf-8", xml_declaration=True)

    with ZipFile(path, "w") as archive:
        for info in infos:
            archive.writestr(info, entries[info.filename])
    return applied


def _filament_slot(name: str, material_for) -> int:
    match = material_for(_base_name(name)).name
    for index, slug in enumerate(FILAMENT_ORDER):
        if MATERIAL_PROJECTS[slug]["match"] == match:
            return index
    raise RuntimeError(f"No filament slot for {name} ({match})")


def _add_metadata(parent: ET.Element, key: str, value: str) -> ET.Element:
    node = next((item for item in parent.findall("metadata")
                 if item.get("key") == key), None)
    if node is None:
        node = ET.SubElement(parent, "metadata", key=key)
    node.set("value", value)
    return node


def _write_multi_plate_settings(
    path: Path,
    plate_names: list[str],
    object_plate: dict[str, int],
    material_for,
) -> None:
    """Assign imported objects to their material plate and ACE Pro slot."""
    core = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    with ZipFile(path) as archive:
        infos = archive.infolist()
        entries = {info.filename: archive.read(info.filename) for info in infos}

    model = ET.fromstring(entries["3D/3dmodel.model"])
    resources = model.find(f"{{{core}}}resources")
    if resources is None:
        raise RuntimeError(f"{path.name}: missing 3MF resources")
    key = "Metadata/model_settings.config"
    root = ET.fromstring(entries[key])
    names_by_id = {
        obj.get("id"): name_node.get("value", "")
        for obj in root.findall("object")
        for name_node in obj.findall("metadata")
        if name_node.get("key") == "name"
    }
    ids_by_name = {name: object_id for object_id, name in names_by_id.items()}
    resource_ids = {
        obj.get("id")
        for obj in resources.findall(f"{{{core}}}object")
    }
    if (set(object_plate) != set(ids_by_name)
            or not set(names_by_id).issubset(resource_ids)):
        missing = sorted(set(object_plate) - set(ids_by_name))
        unexpected = sorted(set(ids_by_name) - set(object_plate))
        raise RuntimeError(
            f"{path.name}: exported object names do not match layout "
            f"(missing={missing}, unexpected={unexpected})")

    ids_by_plate: dict[int, list[str]] = {}
    found_names: set[str] = set()
    for obj in root.findall("object"):
        name_node = next((node for node in obj.findall("metadata")
                          if node.get("key") == "name"), None)
        if name_node is None:
            continue
        name = name_node.get("value", "")
        if name not in object_plate:
            continue
        object_id = obj.get("id")
        if object_id is None:
            raise RuntimeError(f"{path.name}: object {name} has no ID")
        slot = _filament_slot(name, material_for)
        _add_metadata(obj, "extruder", str(slot + 1))
        _add_metadata(obj, "enable_support", "1")
        overrides = OBJECT_OVERRIDES.get(_base_name(name), {})
        for setting, value in overrides.items():
            _add_metadata(obj, setting, value)

        spec = next(
            MATERIAL_PROJECTS[slug]
            for slug in FILAMENT_ORDER
            if MATERIAL_PROJECTS[slug]["match"] == material_for(
                _base_name(name)).name
        )
        if spec.get("support") == "normal":
            _add_metadata(obj, "support_type", "normal(auto)")
            _add_metadata(obj, "support_style", "snug")
        else:
            _add_metadata(obj, "support_type", "tree(auto)")
        if spec.get("support_threshold_angle"):
            _add_metadata(obj, "support_threshold_angle",
                          spec["support_threshold_angle"])
        if spec.get("support_critical_regions_only"):
            _add_metadata(obj, "support_critical_regions_only", "1")
        if spec.get("bridge_no_support"):
            _add_metadata(obj, "bridge_no_support", "1")
        ids_by_plate.setdefault(object_plate[name], []).append(object_id)
        found_names.add(name)

    if found_names != set(object_plate):
        missing = sorted(set(object_plate) - found_names)
        raise RuntimeError(f"{path.name}: missing objects in model settings: {missing}")

    for plate in root.findall("plate"):
        root.remove(plate)
    assemble = root.find("assemble")
    insert_at = list(root).index(assemble) if assemble is not None else len(root)
    for plate_index, plate_name in enumerate(plate_names):
        plate = ET.Element("plate")
        for field, value in (
            ("plater_id", str(plate_index + 1)),
            ("plater_name", plate_name),
            ("locked", "false"),
            ("filament_map_mode", "Auto For Flush"),
            ("gcode_file", ""),
        ):
            ET.SubElement(plate, "metadata", key=field, value=value)
        for object_id in ids_by_plate.get(plate_index, []):
            instance = ET.SubElement(plate, "model_instance")
            ET.SubElement(instance, "metadata", key="object_id",
                          value=object_id)
            ET.SubElement(instance, "metadata", key="instance_id", value="0")
            ET.SubElement(instance, "metadata", key="identify_id",
                          value=object_id)
        root.insert(insert_at, plate)
        insert_at += 1
    entries[key] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    with ZipFile(path, "w") as archive:
        for info in infos:
            archive.writestr(info, entries[info.filename])


def _pack_print_layout(parts: dict, arrange, material_for):
    """Build one source scene and retain material-specific plate grouping."""
    scene_items = []
    plate_names: list[str] = []
    object_plate: dict[str, int] = {}
    for slug, spec in MATERIAL_PROJECTS.items():
        selected = {
            name: mesh for name, mesh in parts.items()
            if material_for(name).name == spec["match"]
        }
        if spec.get("include") is not None:
            selected = {
                name: mesh for name, mesh in selected.items()
                if _base_name(name) in spec["include"]
            }
        selected = {
            name: mesh for name, mesh in selected.items()
            if _base_name(name) not in spec.get("exclude", set())
        }
        if not selected:
            raise RuntimeError(f"No parts assigned to filament slot {slug}")
        items = arrange(
            selected,
            gap=spec.get("manual_gap", 6.0),
            margin=spec.get("bed_margin", 0.0),
        )
        row_pitch = spec.get("plate_row_pitch")
        local_indices = {
            name: max(0, int(mesh.centroid[1] // row_pitch))
            if row_pitch is not None else 0
            for name, mesh, _material, _transform in items
        }
        group_names = sorted(set(local_indices.values()))
        for local_index in group_names:
            global_index = len(plate_names)
            local_name = spec.get("plate_names", ())
            suffix = (
                local_name[local_index]
                if local_index < len(local_name)
                else f"Plate {local_index + 1}"
            )
            color_name = spec["match"].split(" - ")[0]
            plate_names.append(f"{color_name} - {suffix}")
            for name, mesh, material, transform in items:
                if local_indices[name] != local_index:
                    continue
                if name in object_plate:
                    raise RuntimeError(f"Duplicate print object name: {name}")
                local_y = local_index * row_pitch if row_pitch else 0.0
                placed = mesh.copy()
                placed.apply_translation([0.0, 0.0, -placed.bounds[0, 2]])
                normalized = placed.copy()
                normalized.apply_translation([0.0, -local_y, 0.0])
                if (normalized.bounds[0, 0] < -0.01
                        or normalized.bounds[0, 1] < -0.01
                        or normalized.bounds[1, 0] > 250.01
                        or normalized.bounds[1, 1] > 250.01):
                    raise RuntimeError(
                        f"{name} does not fit its 250 mm plate: "
                        f"{normalized.extents.tolist()}"
                    )
                pitch = spec.get("plate_x_pitch", PLATE_X_PITCH)
                plate_column = global_index % PLATE_GRID_COLUMNS
                plate_row = global_index // PLATE_GRID_COLUMNS
                normalized.apply_translation([
                    plate_column * pitch,
                    -plate_row * pitch,
                    0.0,
                ])
                scene_items.append((name, normalized, material, transform))
                object_plate[name] = global_index
    if len(scene_items) != len(object_plate):
        raise RuntimeError("Print layout contains duplicate or missing objects")
    return scene_items, plate_names, object_plate


def _expand_filament_settings(project: dict) -> None:
    """Populate four virtual ACE Pro slots from the same installed PLA preset."""
    specs = [MATERIAL_PROJECTS[slug] for slug in FILAMENT_ORDER]
    colors = [spec["color"].upper() for spec in specs]
    profile = specs[0]["filament"].removesuffix(".json")
    for key, value in list(project.items()):
        if (key.startswith("filament_") and isinstance(value, list)
                and value):
            project[key] = [value[0]] * len(specs)
    project["default_filament_profile"] = [profile] * len(specs)
    project["default_filament_colour"] = colors
    project["extruder_colour"] = colors
    project["filament_colour"] = colors
    project["filament_settings_id"] = [profile] * len(specs)
    project["filament_type"] = ["PLA"] * len(specs)
    project["filament_map"] = [str(index + 1) for index in range(len(specs))]
    project["filament_self_index"] = [
        str(index + 1) for index in range(len(specs))
    ]
    project["filament_printable"] = ["3"] * len(specs)
    project["filament_is_support"] = ["0"] * len(specs)
    project["print_extruder_id"] = [str(index + 1)
                                    for index in range(len(specs))]
    project["printer_extruder_id"] = [str(index + 1)
                                      for index in range(len(specs))]


def _patch_combined_project(path: Path) -> None:
    with ZipFile(path) as archive:
        infos = archive.infolist()
        entries = {info.filename: archive.read(info.filename) for info in infos}
    key = "Metadata/project_settings.config"
    project = json.loads(entries[key].decode("utf-8"))
    spec = {
        "wall_loops": "4", "infill": "25%", "speed": "standard",
        "filament_type": "PLA", "support": "tree",
    }
    project.update(_process_settings(spec))
    _expand_filament_settings(project)
    project["enable_prime_tower"] = "0"
    changed = set(project.get("different_settings_to_system", ["", "", ""])[1].split(";"))
    changed.update({
        "default_filament_colour", "default_filament_profile",
        "extruder_colour", "filament_colour", "filament_settings_id",
        "filament_map", "filament_self_index", "filament_type",
        "print_extruder_id", "printer_extruder_id",
    })
    current = project.get("different_settings_to_system", ["", "", ""])
    current[1] = ";".join(sorted(changed - {""}))
    project["different_settings_to_system"] = current
    entries[key] = json.dumps(project, indent=2).encode("utf-8")
    with ZipFile(path, "w") as archive:
        for info in infos:
            archive.writestr(info, entries[info.filename])


def _write_project_metadata(path: Path, checks: dict) -> None:
    """Add a stable, slicer-neutral summary for the canvas and other tools.

    Orca remains authoritative for calculated time/material values.  Until a
    successful slice supplies those values, the fields are explicit
    ``unknown`` rather than misleading estimates.
    """
    with ZipFile(path) as archive:
        infos = archive.infolist()
        entries = {info.filename: archive.read(info.filename) for info in infos}
    values = {
        "status": "not-verified",
        "estimatedPrintTimeSeconds": "unknown",
        "filamentUsageGrams": "unknown",
        "filamentUsageMillimeters": "unknown",
        "filamentUsageCubicMillimeters": "unknown",
        "supportFilamentGrams": "unknown",
        "supportFilamentMillimeters": "unknown",
        "supportFilamentCubicMillimeters": "unknown",
        "printerProfile": checks["printer"],
        "nozzleDiameterMm": "0.4",
        "processProfile": checks["process"],
        "layerHeightMm": checks["layer_height"],
        "filamentProfile": ", ".join(checks["filament"]) if isinstance(
            checks["filament"], list) else checks["filament"],
        "materialType": "PLA",
        "materialColorName": "Four separate PLA colors",
        "materialColorHex": ", ".join(
            MATERIAL_PROJECTS[slug]["color"].upper()
            for slug in FILAMENT_ORDER
        ),
        "bedType": checks["bed"],
        "wallLoops": "Per-object overrides",
        "infillDensity": "Per-object overrides",
        "supportPolicy": "Automatic; object-specific tree/normal",
        "supportCriticalRegionsOnly": "object-specific",
        "supportThresholdAngleDeg": "object-specific",
        "plateCount": str(checks["plates"]),
    }
    root = ET.Element("ghouls-grip-print-metadata", version="1")
    for name, value in values.items():
        ET.SubElement(root, "metadata", name=name, value=str(value))
    entries[METADATA_ENTRY] = ET.tostring(
        root, encoding="utf-8", xml_declaration=True)
    with ZipFile(path, "w") as archive:
        written = set()
        for info in infos:
            if info.filename in written:
                continue
            archive.writestr(info, entries[info.filename])
            written.add(info.filename)
        if METADATA_ENTRY not in written:
            archive.writestr(METADATA_ENTRY, entries[METADATA_ENTRY])


def _verify_combined_project(
    path: Path,
    expected_objects: int,
    expected_plates: int,
    material_for,
) -> dict:
    with ZipFile(path) as archive:
        project = json.loads(archive.read(
            "Metadata/project_settings.config").decode("utf-8"))
        model = ET.fromstring(archive.read(
            "Metadata/model_settings.config"))
    objects = model.findall("object")
    plates = model.findall("plate")
    assigned_object_ids = []
    for plate in plates:
        for instance in plate.findall("model_instance"):
            object_id = next((
                node.get("value") for node in instance.findall("metadata")
                if node.get("key") == "object_id"), None)
            if object_id is not None:
                assigned_object_ids.append(object_id)
    checks = {
        "printer": project.get("printer_settings_id"),
        "process": project.get("print_settings_id"),
        "filament": project.get("filament_settings_id"),
        "bed": project.get("curr_bed_type"),
        "layer_height": project.get("layer_height"),
        "color": project.get("filament_colour"),
        "objects": len(objects),
        "plates": len(plates),
    }
    if checks["printer"] != "Anycubic Kobra S1 0.4 nozzle":
        raise RuntimeError(f"{path.name}: wrong printer: {checks['printer']}")
    if checks["bed"] != "Textured PEI Plate":
        raise RuntimeError(f"{path.name}: wrong bed: {checks['bed']}")
    if checks["layer_height"] != "0.2":
        raise RuntimeError(f"{path.name}: wrong layer height")
    expected_color = [
        MATERIAL_PROJECTS[slug]["color"].upper() for slug in FILAMENT_ORDER
    ]
    if checks["color"] != expected_color:
        raise RuntimeError(
            f"{path.name}: wrong filament color: {checks['color']}")
    if (len(objects) != expected_objects
            or len(plates) != expected_plates):
        raise RuntimeError(f"{path.name}: object/plate count mismatch {checks}")
    expected_ids = sorted(obj.get("id") for obj in objects)
    if (sorted(assigned_object_ids) != expected_ids
            or len(assigned_object_ids) != len(set(assigned_object_ids))):
        raise RuntimeError(
            f"{path.name}: incomplete or duplicate plate assignments")
    if not all(project.get(key) == "1" for key in (
            "enable_support",)) \
            or project.get("seam_position") != "random" \
            or project.get("ironing_type") != "top":
        raise RuntimeError(f"{path.name}: missing required print defaults")
    profile = MATERIAL_PROJECTS[FILAMENT_ORDER[0]]["filament"].removesuffix(
        ".json")
    if (project.get("filament_settings_id") != [profile] * len(FILAMENT_ORDER)
            or project.get("filament_type") != ["PLA"] * len(FILAMENT_ORDER)):
        raise RuntimeError(f"{path.name}: filament profiles are incomplete")
    for obj in objects:
        name_node = next((node for node in obj.findall("metadata")
                          if node.get("key") == "name"), None)
        extruder_node = next((node for node in obj.findall("metadata")
                              if node.get("key") == "extruder"), None)
        if name_node is None or extruder_node is None:
            raise RuntimeError(f"{path.name}: missing object filament mapping")
        expected_slot = _filament_slot(name_node.get("value", ""), material_for)
        if extruder_node.get("value") != str(expected_slot + 1):
            raise RuntimeError(
                f"{path.name}: incorrect filament slot for "
                f"{name_node.get('value')}")
    return checks


def export_print_project(parts, write_3mf, arrange, material_for) -> list[Path]:
    required = [ORCA_BIN, MACHINE, BASE_PROCESS]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("OrcaSlicer Kobra S1 profiles missing: " + ", ".join(missing))

    scene_items, plate_names, object_plate = (
        _pack_print_layout(parts, arrange, material_for)
    )
    if not plate_names:
        raise RuntimeError("The print project has no plates")
    with tempfile.TemporaryDirectory(
            prefix="ghouls-grip-orca-", dir=MODELS) as temp_name:
        temp = Path(temp_name)
        source = temp / "ghouls-grip-print-source.3mf"
        staged_output = temp / PRINT_OUTPUT.name
        write_3mf(source, scene_items)
        filament = PROFILE_ROOT / "filament" / \
            MATERIAL_PROJECTS[FILAMENT_ORDER[0]]["filament"]
        cmd = [
            str(ORCA_BIN), "--load-settings", f"{MACHINE};{BASE_PROCESS}",
            "--load-filaments", ";".join(
                [str(filament)] * len(FILAMENT_ORDER)),
            "--arrange", "0", "--orient", "0", "--ensure-on-bed",
            "--export-3mf", str(staged_output), str(source),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=600)
        deadline = time.time() + 20.0
        while not staged_output.is_file() and time.time() < deadline:
            time.sleep(0.25)
        if result.returncode or not staged_output.is_file():
            raise RuntimeError(
                f"Orca export failed (exit {result.returncode})\n"
                f"stdout: {result.stdout[-2000:]}\n"
                f"stderr: {result.stderr[-2000:]}")
        _patch_combined_project(staged_output)
        _write_multi_plate_settings(
            staged_output, plate_names, object_plate, material_for,
        )
        checks = _verify_combined_project(
            staged_output, len(scene_items), len(plate_names), material_for)
        _write_project_metadata(staged_output, checks)
        PRINT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged_output, PRINT_OUTPUT)
        print(f"orca-project {PRINT_OUTPUT.name}: {checks}")
    return [PRINT_OUTPUT]


if __name__ == "__main__":
    raise SystemExit("Run scripts/ghouls_grip.py so geometry and projects stay synchronized.")
