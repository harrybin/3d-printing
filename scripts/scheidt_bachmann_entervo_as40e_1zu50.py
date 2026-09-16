"""Generate a printable 1:50 Scheidt & Bachmann entervo.barrier AS40E display.

The official AS40E product data defines the scale-critical envelope.  Visual
details reconstructed from the supplied reference remain deliberately simple;
see docs/scheidt-bachmann-entervo-as40e-1zu50-masse.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import numpy as np
import trimesh


SCALE = 50.0  # User-selected display scale.
BOOM_LENGTH = 2500.0 / SCALE  # Official AS40E standard dimension A.
CABINET_HEIGHT = 1074.0 / SCALE  # Official AS40E drawing.
CABINET_WIDTH = 360.0 / SCALE  # Official AS40E drawing.
CABINET_DEPTH = 300.0 / SCALE  # Official AS40E drawing.
BOOM_HEIGHT = 69.0 / SCALE  # Official AS40E standard boom profile C.

MIN_FEATURE = 0.8
CAP_HEIGHT = 2.2  # Visual approximation from the supplied AS40E image.
BOOM_THICKNESS = 1.6
RED_INLAY_HEIGHT = 0.4
MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
OUT_3MF = MODEL_DIR / "scheidt-bachmann-entervo-as40e-1zu50.3mf"
OUT_PREVIEW = MODEL_DIR / "scheidt-bachmann-entervo-as40e-1zu50-vorschau.stl"


@dataclass(frozen=True)
class Material:
    name: str
    color: str


WHITE = Material("Traffic White (RAL 9016 approximation)", "#F4F4F0FF")
GREY = Material("Traffic Grey B (RAL 7043 approximation)", "#414647FF")
RED = Material("Reflector Red", "#E63632FF")


def box(extents, center) -> trimesh.Trimesh:
    mesh = trimesh.creation.box(extents=extents)
    mesh.apply_translation(center)
    return mesh


def cleaned(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    mesh = mesh.copy()
    mesh.vertices = np.round(mesh.vertices, 3)
    mesh.merge_vertices()
    mesh.update_faces(mesh.unique_faces())
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals()
    return mesh


def cabinet_parts() -> list[tuple[str, trimesh.Trimesh, Material]]:
    """A support-free upright cabinet with colour breaks at physical seams."""
    lower_height = CABINET_HEIGHT - CAP_HEIGHT
    cabinet = box(
        (CABINET_WIDTH, CABINET_DEPTH, lower_height),
        (0.0, 0.0, lower_height / 2.0),
    )
    base = box(
        (CABINET_WIDTH + 0.28, CABINET_DEPTH + 0.28, MIN_FEATURE),
        (0.0, 0.0, MIN_FEATURE / 2.0),
    )
    cap = box(
        (CABINET_WIDTH + 0.5, CABINET_DEPTH + 0.5, CAP_HEIGHT),
        (0.0, 0.0, CABINET_HEIGHT - CAP_HEIGHT / 2.0),
    )
    pivot = trimesh.creation.cylinder(radius=1.25, height=CABINET_DEPTH + 0.16, sections=32)
    pivot.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2.0, (1.0, 0.0, 0.0)))
    pivot.apply_translation((CABINET_WIDTH / 2.0 + 0.12, 0.0, CABINET_HEIGHT - 5.7))
    return [
        ("cabinet", cleaned(cabinet), WHITE),
        ("cabinet_base", cleaned(base), GREY),
        ("cabinet_cap", cleaned(cap), GREY),
        ("boom_pivot", cleaned(pivot), GREY),
    ]


def boom_parts() -> list[tuple[str, trimesh.Trimesh, Material]]:
    """Flat print layout: white boom plus red raised reflector islands."""
    y = -(CABINET_DEPTH / 2.0 + 4.0)
    boom = box(
        (BOOM_LENGTH, BOOM_HEIGHT, BOOM_THICKNESS),
        (BOOM_LENGTH / 2.0, y, BOOM_THICKNESS / 2.0),
    )
    end_cap = box(
        (1.0, BOOM_HEIGHT + 0.16, BOOM_THICKNESS + RED_INLAY_HEIGHT),
        (BOOM_LENGTH - 0.5, y, (BOOM_THICKNESS + RED_INLAY_HEIGHT) / 2.0),
    )
    parts = [("boom", cleaned(boom), WHITE), ("boom_end_cap", cleaned(end_cap), GREY)]
    for index, x in enumerate((5.0, 16.0, 27.0, 38.0), start=1):
        reflector = box(
            (6.2, max(MIN_FEATURE, BOOM_HEIGHT * 0.62), RED_INLAY_HEIGHT),
            (x, y, BOOM_THICKNESS + RED_INLAY_HEIGHT / 2.0),
        )
        parts.append((f"reflector_{index}", cleaned(reflector), RED))
    return parts


def display_preview(parts: list[tuple[str, trimesh.Trimesh, Material]]) -> trimesh.Trimesh:
    """Show the separately printed boom in its intended 28-degree display pose."""
    cabinet = [mesh.copy() for name, mesh, _material in parts if not name.startswith(("boom", "reflector"))]
    boom_meshes = [mesh.copy() for name, mesh, _material in parts if name.startswith(("boom", "reflector"))]
    boom = trimesh.util.concatenate(boom_meshes)
    boom.apply_translation((-BOOM_LENGTH / 2.0, CABINET_DEPTH / 2.0 + 4.0, 0.0))
    boom.apply_transform(
        trimesh.transformations.rotation_matrix(np.deg2rad(-28.0), (0.0, 1.0, 0.0), point=(0.0, 0.0, 0.0))
    )
    boom.apply_translation((CABINET_WIDTH / 2.0 + 0.3, 0.0, CABINET_HEIGHT - 5.7))
    preview = cleaned(trimesh.util.concatenate([*cabinet, boom]))
    preview.apply_translation(-preview.bounds.mean(axis=0) * np.array([1.0, 1.0, 0.0]))
    preview.apply_translation((0.0, 0.0, -preview.bounds[0, 2]))
    return preview


def write_3mf(path: Path, objects: list[tuple[str, trimesh.Trimesh, Material]]) -> None:
    core = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    ET.register_namespace("", core)
    model = ET.Element(f"{{{core}}}model", unit="millimeter")
    resources = ET.SubElement(model, f"{{{core}}}resources")
    materials = ET.SubElement(resources, f"{{{core}}}basematerials", id="1")
    unique_materials = list(dict.fromkeys(material for _name, _mesh, material in objects))
    material_index = {material: index for index, material in enumerate(unique_materials)}
    for material in unique_materials:
        ET.SubElement(materials, f"{{{core}}}base", name=material.name, displaycolor=material.color)

    build = ET.SubElement(model, f"{{{core}}}build")
    for object_id, (name, mesh, material) in enumerate(objects, start=2):
        obj = ET.SubElement(
            resources,
            f"{{{core}}}object",
            id=str(object_id),
            name=name,
            type="model",
            pid="1",
            pindex=str(material_index[material]),
        )
        mesh_xml = ET.SubElement(obj, f"{{{core}}}mesh")
        vertices = ET.SubElement(mesh_xml, f"{{{core}}}vertices")
        for vertex in mesh.vertices:
            ET.SubElement(vertices, f"{{{core}}}vertex", x=f"{vertex[0]:.3f}", y=f"{vertex[1]:.3f}", z=f"{vertex[2]:.3f}")
        triangles = ET.SubElement(mesh_xml, f"{{{core}}}triangles")
        for face in mesh.faces:
            ET.SubElement(triangles, f"{{{core}}}triangle", v1=str(face[0]), v2=str(face[1]), v3=str(face[2]))
        ET.SubElement(build, f"{{{core}}}item", objectid=str(object_id))

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
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for name, payload in (
            ("[Content_Types].xml", content_types),
            ("_rels/.rels", relationships),
            ("3D/3dmodel.model", ET.tostring(model, encoding="utf-8", xml_declaration=True)),
        ):
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, payload)


def validate(name: str, mesh: trimesh.Trimesh) -> None:
    degenerate = int(np.count_nonzero(mesh.area_faces <= 1e-12))
    if not mesh.is_watertight or not mesh.is_winding_consistent or degenerate:
        raise RuntimeError(f"{name} invalid: watertight={mesh.is_watertight}, winding={mesh.is_winding_consistent}, degenerate={degenerate}")
    print(f"{name}: facets={len(mesh.faces)}, bounds={np.round(mesh.bounds, 3).tolist()}, extents={np.round(mesh.extents, 3).tolist()}, watertight={mesh.is_watertight}, winding={mesh.is_winding_consistent}, volume_mm3={mesh.volume:.3f}, degenerate={degenerate}")


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    parts = cabinet_parts() + boom_parts()
    for name, mesh, _material in parts:
        validate(name, mesh)
    preview = display_preview(parts)
    if preview.bounds[0, 2] < -0.01 or preview.extents[0] > 250.0 or preview.extents[1] > 250.0:
        raise RuntimeError(f"Preview does not fit bed: {preview.bounds.tolist()}")
    validate("assembled_preview", preview)
    write_3mf(OUT_3MF, parts)
    OUT_PREVIEW.write_text(trimesh.exchange.stl.export_stl_ascii(preview), encoding="ascii")
    print(f"files: {OUT_3MF} {OUT_PREVIEW}")


if __name__ == "__main__":
    main()
