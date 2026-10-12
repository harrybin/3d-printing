"""Support audit: undecorated control chest versus the sculpted chest.

The ornaments are only acceptable if they cost no extra support.  Both chests
are packed into the *same* OrcaSlicer project template, so every process
setting - including automatic tree support at the same threshold - is bitwise
identical and the only difference is the geometry.

    .\\.venv\\Scripts\\python.exe scripts\\audit_chest_support.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "build" / "ornament-audit"
TEMPLATE = OUT / "control.3mf"
OBJECT_ENTRY = "3D/Objects/chest_1.model"
ROOT_ENTRY = "3D/3dmodel.model"
ORCA = Path(r"C:\Program Files\OrcaSlicer\orca-slicer.exe")

import gothic_chest  # noqa: E402

OBJECT_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" \
xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" \
xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" \
xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" \
requiredextensions="p">
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <resources>
  <object id="1" p:UUID="00010000-81cb-4c03-9d28-80fed5dfa1dc" type="model">
   <mesh>
    <vertices>
"""
OBJECT_FOOTER = """    </triangles>
   </mesh>
  </object>
 </resources>
</model>
"""


def _object_model(mesh: trimesh.Trimesh) -> bytes:
    centre = mesh.bounds.mean(axis=0)
    verts = mesh.vertices - centre
    chunks = [OBJECT_HEADER]
    chunks.extend(
        f'     <vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>\n'
        for x, y, z in verts)
    chunks.append("    </vertices>\n    <triangles>\n")
    chunks.extend(
        f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>\n'
        for a, b, c in mesh.faces)
    chunks.append(OBJECT_FOOTER)
    return "".join(chunks).encode("utf-8")


def _project(mesh: trimesh.Trimesh, name: str) -> Path:
    """Clone the template project, swapping only the mesh and its placement."""
    target = OUT / f"{name}.3mf"
    extents = mesh.extents
    with ZipFile(TEMPLATE) as archive:
        infos = archive.infolist()
        entries = {i.filename: archive.read(i.filename) for i in infos}
    entries[OBJECT_ENTRY] = _object_model(mesh)
    root = entries[ROOT_ENTRY].decode("utf-8")
    placement = (f'transform="1 0 0 0 1 0 0 0 1 '
                 f'{extents[0] / 2.0:.4f} {extents[1] / 2.0:.4f} '
                 f'{extents[2] / 2.0:.4f}"')
    root = re.sub(r'transform="1 0 0 0 1 0 0 0 1 [^"]*"(?=\s+printable)',
                  placement, root)
    entries[ROOT_ENTRY] = root.encode("utf-8")
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for info in infos:
            archive.writestr(info.filename, entries[info.filename])
    return target


def _slice(project: Path, name: str) -> Path:
    outdir = OUT / f"{name}-slice"
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True)
    log = OUT / f"{name}-slice.log"
    subprocess.run(
        [str(ORCA), str(project), "--slice=0", f"--outputdir={outdir}",
         "--debug=3", f"--logfile={log}"],
        check=False, capture_output=True, text=True, timeout=1800)
    gcodes = sorted(outdir.glob("*.gcode"))
    if not gcodes:
        raise RuntimeError(f"{name}: OrcaSlicer produced no gcode; see {log}")
    return gcodes[0]


SUPPORT_TYPES = (";TYPE:Support", ";TYPE:Support interface")


def _support_stats(gcode: Path) -> dict:
    extrusion = 0.0
    paths = 0
    in_support = False
    last_e = 0.0
    relative = False
    for line in gcode.read_text(errors="ignore").splitlines():
        if line.startswith(";TYPE:"):
            was = in_support
            in_support = line.strip() in SUPPORT_TYPES
            if in_support and not was:
                paths += 1
            continue
        if line.startswith("M83"):
            relative = True
        elif line.startswith("M82"):
            relative = False
        if not line.startswith(("G1", "G0")):
            continue
        match = re.search(r"\sE(-?\d*\.?\d+)", line)
        if match is None:
            continue
        value = float(match.group(1))
        delta = value if relative else value - last_e
        if not relative:
            last_e = value
        if in_support and delta > 0.0:
            extrusion += delta
    return {"paths": paths, "support_e": round(extrusion, 3)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, mesh in (("audit-control", gothic_chest.build_chest(False)),
                       ("audit-sculpted", gothic_chest.build_chest(True))):
        if not mesh.is_volume:
            raise RuntimeError(f"{name} is not a closed volume")
        project = _project(mesh, name)
        gcode = _slice(project, name)
        stats = _support_stats(gcode)
        stats["faces"] = len(mesh.faces)
        stats["volume_cm3"] = round(float(mesh.volume) / 1000.0, 2)
        results[name] = stats
        print(f"{name:16s} {stats}")

    control = results["audit-control"]
    sculpted = results["audit-sculpted"]
    verdict = (sculpted["paths"] <= control["paths"]
               and sculpted["support_e"] <= control["support_e"] + 1e-6)
    print(f"\nsupport paths  control {control['paths']} "
          f"-> sculpted {sculpted['paths']}")
    print(f"support E      control {control['support_e']} "
          f"-> sculpted {sculpted['support_e']}")
    print("VERDICT:", "PASS" if verdict else "FAIL")
    if not verdict:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
