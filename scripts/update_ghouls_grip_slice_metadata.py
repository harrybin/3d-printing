"""Patch verified OrcaSlicer statistics into Ghoul's Grip print projects."""

from __future__ import annotations

import os
import re
import time
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
SLICES = ROOT / "build" / "ghoul-final-slices"
METADATA_ENTRY = "Metadata/ghouls_grip_print_metadata.xml"
PROJECT = MODELS / "ghouls-grip-print.3mf"
PLATES = (
    ("Schatulle - Schatulle", "black", 0),
    ("Schatulle - Deckel auf Hinterkante stehend", "black", 0),
    ("Knochen - Plate 1", "bone", 1),
    ("Mechanik - Mechanik-Hauptteile", "mechanism", 2),
    ("Mechanik - Zahnraeder und Verbinder", "mechanism", 2),
    ("Totenkopf-Ausloeser - Plate 1", "accent", 3),
)


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


SUPPORT_TYPES = (";TYPE:Support", ";TYPE:Support interface")


def _support_filament_mm(text: str) -> float:
    """Sum positive extruder deltas emitted under support toolpath types.

    OrcaSlicer reports only a total filament figure, so the support share has
    to be recovered from the G-code itself.
    """
    total = 0.0
    in_support = False
    last_e: float | None = None
    for line in text.splitlines():
        if line.startswith(";TYPE:"):
            in_support = line.strip().startswith(SUPPORT_TYPES)
            continue
        if line.startswith("G92") and "E" in line:
            match = re.search(r"E(-?[0-9.]+)", line)
            if match:
                last_e = float(match.group(1))
            continue
        if not line.startswith(("G0 ", "G1 ")):
            continue
        match = re.search(r"\sE(-?[0-9.]+)", line)
        if not match:
            continue
        value = float(match.group(1))
        if last_e is not None and in_support and value > last_e:
            total += value - last_e
        last_e = value
    return total


def _stats(paths: list[tuple[Path, int]]) -> dict[str, str]:
    totals = {"seconds": 0, "millimetres": 0.0, "cubic_mm": 0.0, "grams": 0.0}
    support_mm = 0.0
    for path, filament_index in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        totals["seconds"] += _seconds(text)
        totals["millimetres"] += _number(
            text, "filament used [mm]", filament_index)
        totals["cubic_mm"] += _number(
            text, "filament used [cm3]", filament_index) * 1000.0
        totals["grams"] += _number(
            text, "filament used [g]", filament_index)
        support_mm += _support_filament_mm(text)
    # Derive the support share from the slicer's own mm-to-mass ratio instead
    # of assuming a filament density.
    per_mm_g = totals["grams"] / totals["millimetres"] if totals[
        "millimetres"] else 0.0
    per_mm_mm3 = totals["cubic_mm"] / totals["millimetres"] if totals[
        "millimetres"] else 0.0
    return {
        "status": "verified",
        "estimatedPrintTimeSeconds": str(int(totals["seconds"])),
        "filamentUsageGrams": f"{totals['grams']:.2f}",
        "filamentUsageMillimeters": f"{totals['millimetres']:.2f}",
        "filamentUsageCubicMillimeters": f"{totals['cubic_mm']:.0f}",
        "supportFilamentGrams": f"{support_mm * per_mm_g:.2f}",
        "supportFilamentMillimeters": f"{support_mm:.2f}",
        "supportFilamentCubicMillimeters": f"{support_mm * per_mm_mm3:.0f}",
        "plateCount": str(len(paths)),
    }


def _patch(project: Path, values: dict[str, str]) -> None:
    with ZipFile(project) as archive:
        infos = archive.infolist()
        entries = {info.filename: archive.read(info.filename) for info in infos}
    root = ET.fromstring(entries[METADATA_ENTRY])
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
    for attempt in range(10):
        try:
            os.replace(temporary, project)
            break
        except OSError:
            if attempt == 9:
                raise
            time.sleep(0.5)


def main() -> None:
    paths = [
        (SLICES / "print" / f"plate_{index}.gcode", plate[2])
        for index, plate in enumerate(PLATES, start=1)
    ]
    missing = [str(path) for path, _slot in paths if not path.is_file()]
    if missing:
        raise RuntimeError("Missing final plate G-code: " + ", ".join(missing))

    overall = _stats(paths)
    by_color: dict[str, dict[str, int | float]] = {}
    plate_details = []
    for (path, slot), (plate_name, color, _slot) in zip(paths, PLATES):
        if slot != _slot:
            raise RuntimeError(f"Filament mapping mismatch for {plate_name}")
        stats = _stats([(path, slot)])
        totals = by_color.setdefault(color, {
            "seconds": 0,
            "grams": 0.0,
            "support_grams": 0.0,
            "plates": 0,
        })
        totals["seconds"] += int(stats["estimatedPrintTimeSeconds"])
        totals["grams"] += float(stats["filamentUsageGrams"])
        totals["support_grams"] += float(stats["supportFilamentGrams"])
        totals["plates"] += 1
        plate_details.append({
            "name": plate_name,
            **stats,
        })
    color_names = {
        "black": "Black PLA",
        "bone": "Bone-beige PLA",
        "mechanism": "Natural-white PLA",
        "accent": "Gray PLA",
    }
    per_color = {
        color_names[color]: {
            "estimatedPrintTimeSeconds": int(values["seconds"]),
            "filamentUsageGrams": round(float(values["grams"]), 2),
            "supportFilamentGrams": round(float(values["support_grams"]), 2),
            "plateCount": values["plates"],
        }
        for color, values in by_color.items()
    }
    overall["filamentUsageByColor"] = json.dumps(
        per_color, sort_keys=True, separators=(",", ":"))
    overall["plateDetails"] = json.dumps(
        plate_details, sort_keys=True, separators=(",", ":"))
    _patch(PROJECT, overall)
    print(PROJECT.name, overall)


if __name__ == "__main__":
    main()
