"""Patch verified OrcaSlicer statistics into Ghoul's Grip print projects."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
SLICES = ROOT / "build" / "ghoul-current-final-slices"
METADATA_ENTRY = "Metadata/ghouls_grip_print_metadata.xml"
PROJECT = MODELS / "ghouls-grip-print.3mf"
FILAMENT_NAMES = {
    "#202124": "Black PLA",
    "#d8c6a5": "Bone-beige PLA",
    "#f1ebdd": "Natural-white PLA",
    "#777777": "Gray PLA",
    "#1c1e21": "Black PLA (Drache)",
    "#4cc936": "Green PLA (Augen)",
    "#d62828": "Red PLA (Schwanzflosse)",
    "#f4f5f7": "White PLA (Emblem)",
}


def _number(text: str, label: str, filament_index: int) -> float:
    match = re.search(rf"; {re.escape(label)} = ([0-9., ]+)", text)
    if not match:
        raise RuntimeError(f"Missing {label}")
    values = [value.strip() for value in match.group(1).split(",")]
    if filament_index >= len(values):
        raise RuntimeError(
            f"Missing filament {filament_index + 1} in {label}")
    return float(values[filament_index])


def _seconds(text: str) -> int:
    match = re.search(
        r"; estimated printing time \(normal mode\) = "
        r"(?:(\d+)h )?(?:(\d+)m )?(\d+)s", text)
    if not match:
        raise RuntimeError("Missing estimated printing time")
    hours, minutes, seconds = (int(value or 0) for value in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def _filament_index(text: str) -> int:
    match = re.search(r"; filament used \[g\] = ([0-9., ]+)", text)
    if not match:
        raise RuntimeError("Missing per-filament mass in G-code")
    values = [float(value.strip()) for value in match.group(1).split(",")]
    active = [index for index, value in enumerate(values) if value > 0]
    if len(active) != 1:
        raise RuntimeError(f"Expected one active filament per plate, found {active}")
    return active[0]


SUPPORT_TYPES = (";TYPE:Support", ";TYPE:Support interface")


def _support_filament_mm(text: str) -> float:
    """Sum positive extruder deltas emitted under support toolpath types.

    OrcaSlicer reports only a total filament figure, so the support share has
    to be recovered from the G-code itself.
    """
    total = 0.0
    in_support = False
    last_e = 0.0
    relative_e = False
    for line in text.splitlines():
        if line.startswith(";TYPE:"):
            in_support = line.strip().startswith(SUPPORT_TYPES)
            continue
        command = line.split(";", 1)[0].strip()
        code = command.split(maxsplit=1)[0] if command else ""
        if code in ("M82", "M83"):
            relative_e = code == "M83"
            continue
        if code == "G92":
            match = re.search(r"\sE(-?[0-9.]+)", command)
            if match:
                last_e = float(match.group(1))
            continue
        if code not in ("G0", "G1", "G2", "G3"):
            continue
        match = re.search(r"\sE(-?[0-9.]+)", command)
        if not match:
            continue
        value = float(match.group(1))
        delta = value if relative_e else value - last_e
        # Extruder-only unretractions prime the nozzle but do not print support.
        if in_support and delta > 0 and re.search(r"\s[XYZ]-?[0-9.]+", command):
            total += delta
        last_e = last_e + value if relative_e else value
    return total


def _stats(paths: list[tuple[Path, int]]) -> dict[str, str]:
    totals = {"seconds": 0, "millimetres": 0.0, "cubic_mm": 0.0, "grams": 0.0}
    support_mm = 0.0
    support_grams = 0.0
    support_cubic_mm = 0.0
    for path, filament_index in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        totals["seconds"] += _seconds(text)
        totals["millimetres"] += _number(
            text, "filament used [mm]", filament_index)
        totals["cubic_mm"] += _number(
            text, "filament used [cm3]", filament_index) * 1000.0
        totals["grams"] += _number(
            text, "filament used [g]", filament_index)
        plate_support_mm = _support_filament_mm(text)
        plate_mm = _number(text, "filament used [mm]", filament_index)
        if plate_support_mm > 0 and plate_mm <= 0:
            raise RuntimeError(f"Support extrusion without filament usage in {path}")
        ratio = plate_support_mm / plate_mm if plate_mm else 0.0
        support_mm += plate_support_mm
        support_grams += ratio * _number(text, "filament used [g]", filament_index)
        support_cubic_mm += ratio * _number(text, "filament used [cm3]", filament_index) * 1000
    return {
        "status": "verified",
        "estimatedPrintTimeSeconds": str(int(totals["seconds"])),
        "filamentUsageGrams": f"{totals['grams']:.2f}",
        "filamentUsageMillimeters": f"{totals['millimetres']:.2f}",
        "filamentUsageCubicMillimeters": f"{totals['cubic_mm']:.0f}",
        "supportFilamentGrams": f"{support_grams:.2f}",
        "supportFilamentMillimeters": f"{support_mm:.2f}",
        "supportFilamentCubicMillimeters": f"{support_cubic_mm:.0f}",
        "plateCount": str(len(paths)),
    }


def _patch(project: Path, values: dict[str, str]) -> None:
    with ZipFile(project) as archive:
        infos = archive.infolist()
        entries = {info.filename: archive.read(info.filename) for info in infos}
    root = ET.fromstring(entries[METADATA_ENTRY]) if METADATA_ENTRY in entries else ET.Element(
        "ghouls-grip-print-metadata", version="1")
    fields = {node.get("name"): node for node in root.findall("metadata")}
    for name, value in values.items():
        if name not in fields:
            fields[name] = ET.SubElement(root, "metadata", name=name)
        fields[name].set("value", value)
    entries[METADATA_ENTRY] = ET.tostring(
        root, encoding="utf-8", xml_declaration=True)
    temporary = project.with_suffix(project.suffix + ".metadata-tmp")
    temporary.unlink(missing_ok=True)
    with ZipFile(temporary, "w") as archive:
        written = set()
        for info in infos:
            if info.filename in written:
                continue
            archive.writestr(info, entries[info.filename])
            written.add(info.filename)
        if METADATA_ENTRY not in written:
            archive.writestr(METADATA_ENTRY, entries[METADATA_ENTRY])
    for attempt in range(10):
        try:
            os.replace(temporary, project)
            break
        except OSError:
            if attempt == 9:
                raise
            time.sleep(0.5)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slices", type=Path, nargs="?", default=SLICES)
    parser.add_argument("--project", type=Path, default=PROJECT)
    args = parser.parse_args()
    paths = sorted(args.slices.glob("plate_*.gcode"),
                   key=lambda path: int(path.stem.removeprefix("plate_")))
    if not paths:
        raise RuntimeError(f"No plate G-code found in {args.slices}")
    indexed_paths = [(path, _filament_index(
        path.read_text(encoding="utf-8", errors="replace"))) for path in paths]
    overall = _stats(indexed_paths)
    by_color: dict[str, dict[str, int | float]] = {}
    plate_details = []
    for index, (path, slot) in enumerate(indexed_paths, start=1):
        with ZipFile(args.project) as archive:
            project_settings = json.loads(
                archive.read("Metadata/project_settings.config"))
        colors = project_settings.get("filament_colour", [])
        if slot >= len(colors):
            raise RuntimeError(f"No saved color for filament slot {slot + 1}")
        color = colors[slot].lower()
        color_name = FILAMENT_NAMES.get(color, f"Filament {slot + 1}")
        stats = _stats([(path, slot)])
        totals = by_color.setdefault(color_name, {
            "seconds": 0, "grams": 0.0, "support_grams": 0.0,
            "millimetres": 0.0, "cubic_mm": 0.0, "plates": 0,
        })
        totals["seconds"] += int(stats["estimatedPrintTimeSeconds"])
        totals["grams"] += float(stats["filamentUsageGrams"])
        totals["support_grams"] += float(stats["supportFilamentGrams"])
        totals["millimetres"] += float(stats["filamentUsageMillimeters"])
        totals["cubic_mm"] += float(stats["filamentUsageCubicMillimeters"])
        totals["plates"] += 1
        plate_details.append({"name": f"Plate {index} - {color_name}", **stats})

    per_color = {
        color_name: {
            "estimatedPrintTimeSeconds": int(values["seconds"]),
            "filamentUsageGrams": round(float(values["grams"]), 2),
            "supportFilamentGrams": round(float(values["support_grams"]), 2),
            "filamentUsageMillimeters": round(float(values["millimetres"]), 2),
            "filamentUsageCubicMillimeters": round(float(values["cubic_mm"])),
            "plateCount": int(values["plates"]),
        }
        for color_name, values in by_color.items()
    }
    overall["filamentUsageByColor"] = json.dumps(
        per_color, sort_keys=True, separators=(",", ":"))
    overall["plateDetails"] = json.dumps(
        plate_details, sort_keys=True, separators=(",", ":"))

    with ZipFile(args.project) as archive:
        project_settings = json.loads(
            archive.read("Metadata/project_settings.config"))
        model_settings = ET.fromstring(archive.read("Metadata/model_settings.config"))
    colors = project_settings.get("filament_colour", [])
    color_names = [FILAMENT_NAMES.get(color.lower(), color) for color in colors]
    profiles = project_settings.get("filament_settings_id", [])
    material_types = sorted(set(project_settings.get("filament_type", [])))
    object_count = sum(
        len(plate.findall("model_instance"))
        for plate in model_settings.findall("plate"))
    overrides = [node for node in model_settings.findall("object/metadata")]
    global_support = project_settings.get("enable_support", "unknown")
    support_overrides = any(
        node.get("key") == "enable_support" and node.get("value") == "1"
        for node in overrides)
    profile_deviations = []
    expected_settings = {
        "curr_bed_type": "Textured PEI Plate",
        "seam_position": "random",
        "ironing_type": "top",
        "enable_support": "1",
    }
    for key, expected in expected_settings.items():
        actual = str(project_settings.get(key, "unknown"))
        if actual != expected:
            profile_deviations.append(f"{key}={actual} (expected {expected})")
    if not project_settings.get("process_settings_id"):
        profile_deviations.append("named process profile is not saved")
    overall["status"] = "not-verified" if profile_deviations else "verified"
    plate_details = json.loads(overall["plateDetails"])
    for plate in plate_details:
        plate["status"] = overall["status"]
    overall["plateDetails"] = json.dumps(
        plate_details, sort_keys=True, separators=(",", ":"))
    overall.update({
        "validationNotes": "; ".join(profile_deviations) or "None",
        "printerProfile": project_settings.get("printer_settings_id", "unknown"),
        "nozzleDiameterMm": project_settings.get("printer_variant", "unknown"),
        "processProfile": project_settings.get(
            "process_settings_id") or "Embedded project settings",
        "layerHeightMm": project_settings.get("layer_height", "unknown"),
        "filamentProfile": ", ".join(dict.fromkeys(profiles)) or "unknown",
        "materialType": ", ".join(material_types) or "unknown",
        "materialColorName": ", ".join(dict.fromkeys(color_names)),
        "materialColorHex": ", ".join(colors),
        "bedType": project_settings.get("curr_bed_type", "unknown"),
        "wallLoops": f"Per-object overrides; global {project_settings.get('wall_loops', 'unknown')}",
        "infillDensity": f"Per-object overrides; global {project_settings.get('sparse_infill_density', 'unknown')}",
        "supportPolicy": (
            f"Global enable_support={global_support}; object support overrides="
            f"{'enabled' if support_overrides else 'none'}; "
            f"{project_settings.get('support_type', 'unknown')}"),
        "supportThresholdAngleDeg": project_settings.get(
            "support_threshold_angle", "unknown"),
        "seamPosition": project_settings.get("seam_position", "unknown"),
        "ironingType": project_settings.get("ironing_type", "unknown"),
        "objectCount": str(object_count),
    })
    _patch(args.project, overall)
    print(args.project.name, overall)


if __name__ == "__main__":
    main()
