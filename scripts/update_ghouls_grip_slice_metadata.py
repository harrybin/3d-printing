"""Patch verified OrcaSlicer statistics into Ghoul's Grip print projects."""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
SLICES = ROOT / "build" / "ghoul-final-slices"
METADATA_ENTRY = "Metadata/ghouls_grip_print_metadata.xml"
PROJECTS = {
    "black-pla": ("black-p1", "black-p2"),
    "bone-pla": ("bone-p1",),
    "mechanism-pla": ("mechanism-p1", "mechanism-p2"),
    "accent-pla": ("accent-p1",),
}


def _number(text: str, label: str) -> float:
    match = re.search(rf"; {re.escape(label)} = ([0-9.]+)", text)
    if not match:
        raise RuntimeError(f"Missing {label}")
    return float(match.group(1))


def _seconds(text: str) -> int:
    match = re.search(
        r"; estimated printing time \(normal mode\) = "
        r"(?:(\d+)h )?(?:(\d+)m )?(\d+)s", text)
    if not match:
        raise RuntimeError("Missing estimated printing time")
    hours, minutes, seconds = (int(value or 0) for value in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def _stats(paths: list[Path]) -> dict[str, str]:
    totals = {"seconds": 0, "millimetres": 0.0, "cubic_mm": 0.0, "grams": 0.0}
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        totals["seconds"] += _seconds(text)
        totals["millimetres"] += _number(text, "filament used [mm]")
        totals["cubic_mm"] += _number(text, "filament used [cm3]") * 1000.0
        totals["grams"] += _number(text, "filament used [g]")
    return {
        "status": "verified",
        "estimatedPrintTimeSeconds": str(int(totals["seconds"])),
        "filamentUsageGrams": f"{totals['grams']:.2f}",
        "filamentUsageMillimeters": f"{totals['millimetres']:.2f}",
        "filamentUsageCubicMillimeters": f"{totals['cubic_mm']:.0f}",
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
        for info in infos:
            archive.writestr(info, entries[info.filename])
    for attempt in range(10):
        try:
            os.replace(temporary, project)
            break
        except OSError:
            if attempt == 9:
                raise
            time.sleep(0.5)


def main() -> None:
    for slug, directories in PROJECTS.items():
        paths = [
            path
            for directory in directories
            for path in sorted((SLICES / directory).glob("plate_*.gcode"))
        ]
        if not paths:
            raise RuntimeError(f"No G-code found for {slug}")
        values = _stats(paths)
        project = MODELS / f"ghouls-grip-print-{slug}.3mf"
        _patch(project, values)
        print(project.name, values)


if __name__ == "__main__":
    main()
