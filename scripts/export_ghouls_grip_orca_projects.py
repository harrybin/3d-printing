"""Create printable OrcaSlicer project 3MFs for each Ghoul's Grip material.

Unlike the neutral assembly 3MFs, these files embed the Anycubic Kobra S1
0.4-mm machine profile, a Textured PEI plate, filament profile, process
settings and per-object strength overrides. OrcaSlicer performs the final
multi-plate arrangement, so large same-material groups remain directly usable.
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

MATERIAL_PROJECTS = {
    "black-pla": {
        "match": "Schatulle - schwarzes PLA",
        "filament": "Anycubic PLA @Anycubic Kobra S1 0.4 nozzle.json",
        "wall_loops": "4", "infill": "20%", "speed": "standard",
        "filament_type": "PLA",
    },
    "bone-pla": {
        "match": "Knochen - beiges PLA",
        "filament": "Anycubic PLA @Anycubic Kobra S1 0.4 nozzle.json",
        "wall_loops": "4", "infill": "25%", "speed": "standard",
        "filament_type": "PLA",
    },
    "mechanism-petg": {
        "match": "Mechanik - PETG",
        "filament": "Anycubic PETG @Anycubic Kobra S1 0.4 nozzle.json",
        "wall_loops": "5", "infill": "40%", "speed": "mechanism",
        "filament_type": "PETG", "object_overrides": True,
    },
    "accent-pla": {
        "match": "Totenkopf-Ausloeser - graues PLA",
        "filament": "Anycubic PLA @Anycubic Kobra S1 0.4 nozzle.json",
        "wall_loops": "4", "infill": "25%", "speed": "standard",
        "filament_type": "PLA",
    },
    "fingers-tpu": {
        "match": "Finger - TPU 95A (externe Spule)",
        "filament": "Anycubic TPU @Anycubic Kobra S1 0.4 nozzle.json",
        "wall_loops": "3", "infill": "15%", "speed": "tpu",
        "filament_type": "TPU",
    },
}

OBJECT_OVERRIDES = {
    "chest": {"wall_loops": "4", "sparse_infill_density": "20%"},
    "lid": {"wall_loops": "4", "sparse_infill_density": "20%"},
    "scissor-arm": {"wall_loops": "5", "sparse_infill_density": "100%"},
    "slider": {"wall_loops": "5", "sparse_infill_density": "40%"},
    "platform": {"wall_loops": "5", "sparse_infill_density": "40%"},
    "latch-rocker": {"wall_loops": "5", "sparse_infill_density": "50%"},
    "latch-bracket": {"wall_loops": "5", "sparse_infill_density": "50%"},
    "crank": {"wall_loops": "5", "sparse_infill_density": "50%"},
    "band-anchor": {"wall_loops": "5", "sparse_infill_density": "50%"},
    "pivot-pin-3": {"wall_loops": "6", "sparse_infill_density": "100%"},
    "pivot-pin-4": {"wall_loops": "6", "sparse_infill_density": "100%"},
    "forearm": {"wall_loops": "4", "sparse_infill_density": "25%"},
    "hand-palm": {"wall_loops": "4", "sparse_infill_density": "25%"},
    "hand-tendon-guide": {"wall_loops": "4", "sparse_infill_density": "25%"},
    "skull-trigger": {"wall_loops": "4", "sparse_infill_density": "25%"},
    "hand-finger": {
        "wall_loops": "3", "sparse_infill_density": "15%",
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
        "enable_support": "0",
        "enable_prime_tower": "0",
        "xy_hole_compensation": "0.1",
        "xy_contour_compensation": "0",
        "elefant_foot_compensation": "0.15",
        "brim_type": "auto_brim",
        "brim_width": "5",
        "detect_thin_wall": "1",
        "only_one_wall_top": "0",
    }
    if spec["speed"] == "mechanism":
        data.update({
            "outer_wall_speed": "120", "inner_wall_speed": "180",
            "sparse_infill_speed": "160", "top_surface_speed": "100",
            "default_acceleration": "4000", "outer_wall_acceleration": "2000",
        })
    elif spec["speed"] == "tpu":
        data.update({
            "outer_wall_speed": "25", "inner_wall_speed": "35",
            "sparse_infill_speed": "40", "top_surface_speed": "25",
            "initial_layer_speed": "20", "default_acceleration": "1000",
            "outer_wall_acceleration": "500", "inner_wall_acceleration": "800",
            "travel_acceleration": "2000",
        })
    return data


def _patch_project_settings(path: Path, spec: dict) -> dict:
    with ZipFile(path) as archive:
        infos = archive.infolist()
        entries = {info.filename: archive.read(info.filename) for info in infos}

    project_key = "Metadata/project_settings.config"
    project = json.loads(entries[project_key].decode("utf-8"))
    overrides = _process_settings(spec)
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


def _verify_project(path: Path, expected_objects: int) -> dict:
    with ZipFile(path) as archive:
        project = json.loads(archive.read(
            "Metadata/project_settings.config").decode("utf-8"))
        model = ET.fromstring(archive.read(
            "Metadata/model_settings.config"))
    objects = model.findall("object")
    plates = model.findall("plate")
    checks = {
        "printer": project.get("printer_settings_id"),
        "process": project.get("print_settings_id"),
        "filament": project.get("filament_settings_id"),
        "bed": project.get("curr_bed_type"),
        "layer_height": project.get("layer_height"),
        "objects": len(objects),
        "plates": len(plates),
    }
    if checks["printer"] != "Anycubic Kobra S1 0.4 nozzle":
        raise RuntimeError(f"{path.name}: wrong printer: {checks['printer']}")
    if checks["bed"] != "Textured PEI Plate":
        raise RuntimeError(f"{path.name}: wrong bed: {checks['bed']}")
    if checks["layer_height"] != "0.2":
        raise RuntimeError(f"{path.name}: wrong layer height")
    if len(objects) != expected_objects or not plates:
        raise RuntimeError(f"{path.name}: object/plate count mismatch {checks}")
    return checks


def export_material_projects(parts, write_3mf, arrange, material_for) -> list[Path]:
    required = [ORCA_BIN, MACHINE, BASE_PROCESS]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("OrcaSlicer Kobra S1 profiles missing: " + ", ".join(missing))

    outputs = []
    with tempfile.TemporaryDirectory(prefix="ghouls-grip-orca-") as temp_name:
        temp = Path(temp_name)
        for slug, spec in MATERIAL_PROJECTS.items():
            selected = {name: mesh for name, mesh in parts.items()
                        if material_for(name).name == spec["match"]}
            if not selected:
                raise RuntimeError(f"No parts assigned to material project {slug}")
            source = temp / f"{slug}-source.3mf"
            write_3mf(source, arrange(selected))
            filament = PROFILE_ROOT / "filament" / spec["filament"]
            output = MODELS / f"ghouls-grip-{slug}.3mf"
            output.unlink(missing_ok=True)
            cmd = [
                str(ORCA_BIN), "--load-settings", f"{MACHINE};{BASE_PROCESS}",
                "--load-filaments", str(filament),
                "--arrange", "1", "--orient", "0", "--ensure-on-bed",
                "--export-3mf", str(output), str(source),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=600)
            deadline = time.time() + 20.0
            while not output.is_file() and time.time() < deadline:
                time.sleep(0.25)
            if result.returncode or not output.is_file():
                raise RuntimeError(
                    f"Orca export failed for {slug} (exit {result.returncode})\n"
                    f"stdout: {result.stdout[-2000:]}\n"
                    f"stderr: {result.stderr[-2000:]}")
            applied = _patch_project_settings(output, spec)
            checks = _verify_project(output, len(selected))
            if spec.get("object_overrides") and len(applied) != len(selected):
                raise RuntimeError(
                    f"{output.name}: object overrides {len(applied)}/{len(selected)}")
            print(f"orca-project {output.name}: {checks}")
            outputs.append(output)
    return outputs


if __name__ == "__main__":
    raise SystemExit("Run scripts/ghouls_grip.py so geometry and projects stay synchronized.")
