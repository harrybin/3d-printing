"""Generate the Ghoul's Grip mechanical Halloween automaton box.

The geometry lives in four focused modules and this file only assembles them,
validates every part and writes the deliverables:

    gothic_chest.py   chest and lid with real gothic relief
    mechanism.py      gears, racks, scissors and forearm
    skeleton_hand.py  anatomical hand rebuilt from the NIH 3D bone scan
    skull.py          skull relief and the skull push button

The hand derives from "Wrist Bones Full Hand_Human Skeleton" by My Segmenter,
NIH 3D Print Exchange 3DPX-016815, licensed CC BY 4.0.

The complete box drive is rigid and manually reversible: one skull-handled
skull knob turns the rack-and-pinion slider, the scissor lift, the captured lid
crank and the five-gear forearm train.  There are no cords, rubber bands,
springs or winding spools.

All dimensions are millimetres. Parts are exported in print orientation as
validated in memory and delivered through settings-bearing material 3MF projects.
Only the assembled preview is also exported as ASCII STL for the canvas.
"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mechanism
from gothic_chest import build_chest, build_lid
from mesh_kit import clean, orient_for_print
from skeleton_hand import FLAT_POSE, RAYS, assemble, load_skeleton
from skull import build_drive_knob

ROOT = Path(__file__).resolve().parents[1]
OUT_3MF = ROOT / "models" / "ghouls-grip-master.3mf"
OUT_RETRACTED_3MF = ROOT / "models" / "ghouls-grip-master-retracted.3mf"
OUT_PREVIEW = ROOT / "models" / "ghouls-grip-preview.stl"

LEGACY_OUTPUTS = (
    ROOT / "models" / "ghouls-grip.3mf",
    ROOT / "models" / "ghouls-grip-retracted.3mf",
    ROOT / "models" / "ghouls-grip-black-pla.3mf",
    ROOT / "models" / "ghouls-grip-bone-pla.3mf",
    ROOT / "models" / "ghouls-grip-mechanism-pla.3mf",
    ROOT / "models" / "ghouls-grip-accent-pla.3mf",
    ROOT / "models" / "ghouls-grip-fingers-pla.3mf",
)

BED = 250.0


@dataclass(frozen=True)
class Material:
    name: str
    color: str


BLACK = Material("Schatulle - schwarzes PLA", "#202124FF")
BONE = Material("Knochen - beiges PLA", "#D8C6A5FF")
MECH = Material("Mechanik - naturweisses PLA", "#F1EBDDFF")
FLEX = BONE
ACCENT = Material("Totenkopf-Ausloeser - graues PLA", "#777777FF")


def validate(name: str, mesh: trimesh.Trimesh) -> None:
    degenerate = int(np.count_nonzero(mesh.area_faces <= 1e-12))
    body_count = len(mesh.split(only_watertight=False))
    if (not mesh.is_watertight or not mesh.is_winding_consistent
            or degenerate or body_count != 1):
        raise RuntimeError(
            f"{name}: watertight={mesh.is_watertight}, "
            f"winding={mesh.is_winding_consistent}, degenerate={degenerate}, "
            f"bodies={body_count}"
        )
    extents = mesh.extents
    if extents[0] > 250.0 or extents[1] > 250.0:
        raise RuntimeError(f"{name}: exceeds 250 mm bed: {extents.tolist()}")
    print(
        f"{name}: facets={len(mesh.faces)}, extents={np.round(extents, 3).tolist()}, "
        f"watertight=True, winding=True, degenerate=0, volume={mesh.volume:.3f}"
    )


def write_ascii(mesh: trimesh.Trimesh, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        trimesh.exchange.stl.export_stl_ascii(mesh),
        encoding="ascii",
    )
    for attempt in range(10):
        try:
            os.replace(temporary, path)
            return
        except OSError:
            if attempt == 9:
                raise
            time.sleep(0.5)


def write_3mf(path: Path, objects) -> None:
    core = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    ET.register_namespace("", core)
    model = ET.Element(
        f"{{{core}}}model",
        unit="millimeter",
        **{"{http://www.w3.org/XML/1998/namespace}lang": "de-DE"},
    )
    resources = ET.SubElement(model, f"{{{core}}}resources")
    materials = ET.SubElement(resources, f"{{{core}}}basematerials", id="1")
    used = []
    for _name, _mesh, material, _transform in objects:
        if material not in used:
            used.append(material)
    for material in used:
        ET.SubElement(
            materials,
            f"{{{core}}}base",
            name=material.name,
            displaycolor=material.color,
        )

    build = ET.SubElement(model, f"{{{core}}}build")
    for object_id, (name, mesh, material, transform) in enumerate(objects, start=2):
        obj = ET.SubElement(
            resources,
            f"{{{core}}}object",
            id=str(object_id),
            name=name,
            type="model",
            pid="1",
            pindex=str(used.index(material)),
        )
        mesh_xml = ET.SubElement(obj, f"{{{core}}}mesh")
        vertices = ET.SubElement(mesh_xml, f"{{{core}}}vertices")
        for vertex in mesh.vertices:
            ET.SubElement(
                vertices,
                f"{{{core}}}vertex",
                x=f"{vertex[0]:.3f}",
                y=f"{vertex[1]:.3f}",
                z=f"{vertex[2]:.3f}",
            )
        triangles = ET.SubElement(mesh_xml, f"{{{core}}}triangles")
        for face in mesh.faces:
            ET.SubElement(
                triangles,
                f"{{{core}}}triangle",
                v1=str(face[0]),
                v2=str(face[1]),
                v3=str(face[2]),
            )
        attrs = {"objectid": str(object_id)}
        if transform is not None:
            attrs["transform"] = " ".join(f"{v:.5f}" for v in transform)
        ET.SubElement(build, f"{{{core}}}item", **attrs)

    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
"""
    relationships = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""
    metadata = ET.Element("ghouls-grip-print-metadata", version="1")
    neutral_values = {
        "status": "not-verified",
        "estimatedPrintTimeSeconds": "unknown",
        "filamentUsageGrams": "unknown",
        "filamentUsageMillimeters": "unknown",
        "filamentUsageCubicMillimeters": "unknown",
        "printerProfile": "unknown",
        "nozzleDiameterMm": "unknown",
        "processProfile": "unknown",
        "layerHeightMm": "unknown",
        "filamentProfile": "unknown",
        "materialType": "unknown",
        "bedType": "unknown",
        "plateCount": "1",
        "objectCount": str(len(objects)),
    }
    for name, value in neutral_values.items():
        ET.SubElement(metadata, "metadata", name=name, value=value)

    def member(archive: ZipFile, name: str, data) -> None:
        info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        archive.writestr(info, data)

    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        member(archive, "[Content_Types].xml", content_types)
        member(archive, "_rels/.rels", relationships)
        member(
            archive,
            "3D/3dmodel.model",
            ET.tostring(model, encoding="utf-8", xml_declaration=True),
        )
        member(
            archive,
            "Metadata/ghouls_grip_print_metadata.xml",
            ET.tostring(metadata, encoding="utf-8", xml_declaration=True),
        )


def place(mesh: trimesh.Trimesh, translation, rotations=()) -> trimesh.Trimesh:
    result = mesh.copy()
    for angle, axis in rotations:
        result.apply_transform(
            trimesh.transformations.rotation_matrix(angle, axis, result.centroid)
        )
    result.apply_translation(np.asarray(translation, dtype=float))
    return clean(result)



PART_MATERIAL = {
    "chest": BLACK, "lid": BLACK,
    "scissor-arm": MECH, "slider": MECH, "platform": MECH,
    "drive-pinion": MECH, "lid-rack": MECH,
    "lid-follower-rack": MECH, "lid-crank": MECH,
    "scissor-drive-gear": MECH, "idler-gear": MECH,
    "forearm-output-gear": MECH,
    "pivot-pin-3": MECH, "pivot-pin-4": MECH,
    "drive-skull-knob": ACCENT,
    "forearm": BONE, "hand-palm": BONE,
}

PRINT_QUANTITIES = {
    "scissor-arm": 4,
    "idler-gear": 3,
    "pivot-pin-3": 10,
    "pivot-pin-4": 4,
}


def build_parts() -> dict:
    parts = {"chest": build_chest(), "lid": build_lid()}
    for name, fn in mechanism.PARTS.items():
        parts[name] = fn()
    parts["pivot-pin-3"] = mechanism.build_pin(3.0, 26.0)
    parts["pivot-pin-4"] = mechanism.build_pin(4.0, 34.0)
    parts["drive-skull-knob"] = build_drive_knob(
        shaft_d=mechanism.DRIVE_SHAFT_D)
    skeleton = load_skeleton()
    parts.update(assemble(skeleton, FLAT_POSE))
    return {k: orient_for_print(v) for k, v in parts.items()}


def base_part_name(name: str) -> str:
    return re.sub(r"-\d{2}$", "", name)


def material_for(name: str) -> Material:
    base = base_part_name(name)
    if base.startswith("hand-finger"):
        return FLEX
    return PART_MATERIAL.get(base, BONE)


def expand_print_parts(parts: dict) -> dict:
    """Expand repeated hardware so print projects contain the full BOM."""
    expanded = {}
    for name, mesh in parts.items():
        quantity = PRINT_QUANTITIES.get(name, 1)
        for index in range(quantity):
            instance = name if quantity == 1 else f"{name}-{index + 1:02d}"
            expanded[instance] = mesh.copy()
    return expanded



def assembly_material(name: str) -> Material:
    if name.startswith("hand-finger"):
        return FLEX
    if name in {"chest", "lid"}:
        return BLACK
    if name == "drive-skull-knob":
        return ACCENT
    if name in {"forearm", "hand-palm"}:
        return BONE
    return MECH


def assembly_objects(pose: str) -> list:
    # Imported lazily to avoid coupling the part generator to vedo.  The render
    # scene is the single source of truth for every deployed/stowed transform.
    import render_ghouls_grip
    return [(name, mesh, assembly_material(name), None)
            for name, mesh, _colour in render_ghouls_grip.build_scene(pose)]

def arrange(parts: dict, gap: float = 6.0, margin: float = 0.0) -> list:
    """Lay every part out on the 250 x 250 bed, in rows, nothing overlapping."""
    items, x, y, row = [], margin, margin, 0.0
    for name, mesh in parts.items():
        ext = mesh.extents
        if x + ext[0] > BED - margin and x > margin:
            x, y, row = margin, y + row + gap, 0.0
        placed = mesh.copy()
        placed.apply_translation([x - mesh.bounds[0][0],
                                  y - mesh.bounds[0][1],
                                  -mesh.bounds[0][2]])
        items.append((name, placed, material_for(name), None))
        x += ext[0] + gap
        row = max(row, ext[1])
    return items


def main() -> None:
    for path in LEGACY_OUTPUTS:
        path.unlink(missing_ok=True)
    for path in (ROOT / "models").glob("ghouls-grip-print-*.3mf"):
        path.unlink()

    parts = build_parts()
    for name, mesh in parts.items():
        validate(name, mesh)

    print_parts = expand_print_parts(parts)
    # OrcaSlicer project 3MFs retain the Kobra S1 machine, filament and
    # process settings and contain the full repeated-part quantities.
    from export_ghouls_grip_orca_projects import export_material_projects
    material_projects = export_material_projects(
        print_parts, write_3mf, arrange, material_for)

    deployed = assembly_objects("deployed")
    retracted = assembly_objects("retracted")
    write_3mf(OUT_3MF, deployed)
    write_3mf(OUT_RETRACTED_3MF, retracted)
    preview = trimesh.util.concatenate([m for _, m, _, _ in deployed])
    write_ascii(clean(preview), OUT_PREVIEW)
    print(f"files: {len(parts)} validated part types, {OUT_3MF}, "
          f"{OUT_RETRACTED_3MF}, {OUT_PREVIEW}, "
          f"material projects={len(material_projects)}")


if __name__ == "__main__":
    main()
