"""Generate the 240 mm multi-material number-5 wall lamp.

The reference photograph defines the silhouette and curved panel layout.  The
user supplied the overall height and wall-normal construction dimensions; see
``docs/lampe-5-masse.md``.  All coordinates are millimetres.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import manifold3d as manifold
import numpy as np
import trimesh


HEIGHT = 240.0
DEPTH = 40.0
LAYER_DEPTH = 20.0
FRAME_WIDTH = 6.0
DIVIDER_WIDTH = 5.0
LEDGE_WIDTH = 10.0
LEDGE_BOTTOM_Z = 36.0
LEDGE_TOP_Z = 38.0
PANEL_THICKNESS = 2.0
PANEL_CLEARANCE = 0.30

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
OUT_FRAME = MODEL_DIR / "lampe-5-rahmen.3mf"
OUT_PANELS = MODEL_DIR / "lampe-5-leuchtflaechen.stl"

RAW_HEIGHT = 240.0
RAW_MIN_Y = 1.4861111119389534
SCALE = HEIGHT / (RAW_HEIGHT - RAW_MIN_Y)


@dataclass(frozen=True)
class Material:
    name: str
    color: str


TRANSPARENT = Material("Transparent", "#DCEFFFFF")
BLACK = Material("Black", "#171717FF")


def _cubic(p0, p1, p2, p3, count=10) -> np.ndarray:
    """Sample one cubic Bezier segment without repeating its first point."""
    t = np.linspace(0.0, 1.0, count + 1)[1:, None]
    p0, p1, p2, p3 = (np.asarray(p, dtype=float) for p in (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3


def _path(start, segments, count=10) -> np.ndarray:
    points = [np.asarray(start, dtype=float)]
    current = start
    for control1, control2, end in segments:
        points.extend(_cubic(current, control1, control2, end, count))
        current = end
    points = np.asarray(points)
    points[:, 1] -= RAW_MIN_Y
    return points * SCALE


def _outer_outline() -> manifold.CrossSection:
    # Clockwise photograph-derived outline. EvenOdd avoids relying on winding.
    points = _path(
        (36, 240),
        [
            ((75, 240), (140, 240), (160, 238)),
            ((168, 237), (172, 231), (172, 223)),
            ((172, 213), (171, 204), (166, 198)),
            ((145, 190), (103, 193), (78, 192)),
            ((69, 191), (62, 185), (64, 176)),
            ((65, 168), (70, 164), (78, 164)),
            ((91, 166), (104, 165), (114, 162)),
            ((140, 156), (156, 146), (165, 131)),
            ((175, 114), (180, 100), (177, 84)),
            ((176, 58), (168, 40), (154, 27)),
            ((141, 12), (123, 3), (104, 2)),
            ((80, 0), (58, 4), (42, 11)),
            ((20, 20), (8, 34), (7, 52)),
            ((6, 62), (7, 71), (12, 78)),
            ((21, 82), (34, 80), (43, 78)),
            ((47, 66), (57, 58), (70, 57)),
            ((84, 54), (97, 58), (103, 65)),
            ((112, 72), (112, 80), (105, 87)),
            ((99, 94), (90, 97), (82, 97)),
            ((67, 95), (53, 95), (45, 97)),
            ((32, 99), (24, 106), (22, 117)),
            ((15, 134), (14, 151), (17, 165)),
            ((18, 183), (17, 202), (22, 213)),
            ((25, 225), (29, 235), (36, 240)),
        ],
        count=12,
    )
    return manifold.CrossSection([points], manifold.FillRule.EvenOdd).simplify(0.05)


def _stroke(start, segments, width) -> manifold.CrossSection:
    points = _path(start, segments, count=8)
    circles = [
        manifold.CrossSection.circle(width / 2.0, 16).translate(tuple(point))
        for point in points
    ]
    capsules = [
        manifold.CrossSection.batch_hull([a, b])
        for a, b in zip(circles[:-1], circles[1:])
    ]
    return manifold.CrossSection.compose(capsules).simplify(0.05)


def _layout():
    outer = _outer_outline()
    interior = outer.offset(-FRAME_WIDTH).simplify(0.05)
    frame = outer - interior

    upper = _stroke(
        (14, 190),
        [((32, 193), (51, 187), (66, 176))],
        DIVIDER_WIDTH,
    )
    middle = _stroke(
        (16, 111),
        [
            ((42, 108), (60, 126), (79, 141)),
            ((98, 156), (130, 155), (163, 135)),
        ],
        DIVIDER_WIDTH,
    )
    lower = _stroke(
        (50, 96),
        [
            ((69, 119), (91, 116), (108, 101)),
            ((123, 88), (140, 93), (166, 126)),
        ],
        DIVIDER_WIDTH,
    )
    dividers = manifold.CrossSection.compose([upper, middle, lower]) ^ outer
    structure = (frame + dividers).simplify(0.05)
    ledge = (structure.offset(LEDGE_WIDTH) ^ outer).simplify(0.05)
    panels = (
        interior.offset(-PANEL_CLEARANCE)
        - dividers.offset(PANEL_CLEARANCE)
    ).simplify(0.05)
    panel_sections = sorted(
        panels.decompose(),
        key=lambda section: (-section.bounds()[3], section.bounds()[0]),
    )
    if len(panel_sections) != 4:
        raise RuntimeError(f"Expected 4 light panels, got {len(panel_sections)}")
    return outer, structure, ledge, panel_sections


def _trimesh(solid: manifold.Manifold) -> trimesh.Trimesh:
    raw = solid.to_mesh()
    mesh = trimesh.Trimesh(
        vertices=np.asarray(raw.vert_properties[:, :3]),
        faces=np.asarray(raw.tri_verts),
        process=False,
    )
    mesh.vertices = np.round(mesh.vertices, 3)
    mesh.merge_vertices()
    mesh.update_faces(mesh.unique_faces())
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals()
    return mesh


def _mesh(section: manifold.CrossSection, height: float, z: float = 0.0) -> trimesh.Trimesh:
    return _trimesh(section.extrude(height).translate((0.0, 0.0, z)))


def build_parts():
    outer, structure, ledge, panel_sections = _layout()
    center_x = (outer.bounds()[0] + outer.bounds()[2]) / 2.0
    shift = (-center_x, -HEIGHT / 2.0)
    structure = structure.translate(shift)
    ledge = ledge.translate(shift)
    panel_sections = [section.translate(shift) for section in panel_sections]

    transparent = _mesh(structure, LAYER_DEPTH)
    black_solid = (
        structure.extrude(LAYER_DEPTH).translate((0.0, 0.0, LAYER_DEPTH))
        + ledge.extrude(LEDGE_TOP_Z - LEDGE_BOTTOM_Z).translate(
            (0.0, 0.0, LEDGE_BOTTOM_Z)
        )
    )
    black = _trimesh(black_solid)
    panels = [
        _mesh(section, PANEL_THICKNESS, DEPTH - PANEL_THICKNESS)
        for section in panel_sections
    ]
    return transparent, black, panels


def _local_print_copy(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    result = mesh.copy()
    center_xy = result.bounds[:, :2].mean(axis=0)
    result.apply_translation([-center_xy[0], -center_xy[1], -result.bounds[0, 2]])
    return result


def arrange_panels(panels: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    """Pack all four panels flat on the 250 mm bed with at least 5 mm gaps."""
    placements = (
        (3, 0.0, (-120.0, -120.0)),
        (0, 90.0, (45.0, -120.0)),
        (1, 0.0, (-120.0, 27.0)),
        (2, 0.0, (-12.0, 27.0)),
    )
    arranged = []
    for index, angle, lower_left in placements:
        panel = _local_print_copy(panels[index])
        if angle:
            panel.apply_transform(
                trimesh.transformations.rotation_matrix(
                    np.radians(angle),
                    [0.0, 0.0, 1.0],
                )
            )
        panel.apply_translation(
            [
                lower_left[0] - panel.bounds[0, 0],
                lower_left[1] - panel.bounds[0, 1],
                0.0,
            ]
        )
        arranged.append(panel)
    layout = trimesh.util.concatenate(arranged)
    center_xy = layout.bounds[:, :2].mean(axis=0)
    layout.apply_translation([-center_xy[0], -center_xy[1], 0.0])
    return layout


def _write_ascii(mesh: trimesh.Trimesh, path: Path) -> None:
    path.write_text(trimesh.exchange.stl.export_stl_ascii(mesh), encoding="ascii")


def _write_3mf(path: Path, objects) -> None:
    core = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    ET.register_namespace("", core)
    model = ET.Element(
        f"{{{core}}}model",
        unit="millimeter",
        **{"{http://www.w3.org/XML/1998/namespace}lang": "en-US"},
    )
    resources = ET.SubElement(model, f"{{{core}}}resources")
    materials = ET.SubElement(resources, f"{{{core}}}basematerials", id="1")
    material_indices = {}
    used_materials = []
    for _name, _mesh_value, material in objects:
        if material not in used_materials:
            used_materials.append(material)
    for index, material in enumerate(used_materials):
        material_indices[material.name] = index
        ET.SubElement(
            materials,
            f"{{{core}}}base",
            name=material.name,
            displaycolor=material.color,
        )

    build = ET.SubElement(model, f"{{{core}}}build")
    for object_id, (name, mesh, material) in enumerate(objects, start=2):
        obj = ET.SubElement(
            resources,
            f"{{{core}}}object",
            id=str(object_id),
            name=name,
            type="model",
            pid="1",
            pindex=str(material_indices[material.name]),
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

    def write_member(archive: ZipFile, name: str, data) -> None:
        info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        archive.writestr(info, data)

    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        write_member(archive, "[Content_Types].xml", content_types)
        write_member(archive, "_rels/.rels", relationships)
        write_member(
            archive,
            "3D/3dmodel.model",
            ET.tostring(model, encoding="utf-8", xml_declaration=True),
        )


def _validate(name: str, mesh: trimesh.Trimesh) -> None:
    degenerate = int(np.count_nonzero(mesh.area_faces <= 1e-12))
    if not mesh.is_watertight or not mesh.is_winding_consistent or degenerate:
        raise RuntimeError(
            f"{name} invalid: watertight={mesh.is_watertight}, "
            f"winding={mesh.is_winding_consistent}, degenerate={degenerate}"
        )
    print(
        f"{name}: facets={len(mesh.faces)}, "
        f"bounds={np.round(mesh.bounds, 3).tolist()}, "
        f"watertight={mesh.is_watertight}, volume_mm3={mesh.volume:.3f}"
    )


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    transparent, black, panels = build_parts()
    frame_objects = [
        ("transparent_rear", transparent, TRANSPARENT),
        ("black_front", black, BLACK),
    ]

    for name, mesh, _material in frame_objects:
        _validate(name, mesh)
    for index, panel in enumerate(panels, start=1):
        _validate(f"light_panel_{index}", panel)

    panel_layout = arrange_panels(panels)
    if panel_layout.bounds[0, :2].min() < -125.0 or panel_layout.bounds[1, :2].max() > 125.0:
        raise RuntimeError(f"Panel layout exceeds bed: {panel_layout.bounds.tolist()}")
    _write_3mf(OUT_FRAME, frame_objects)
    _write_ascii(panel_layout, OUT_PANELS)

    frame_bounds = np.vstack([transparent.bounds, black.bounds])
    print("frame_extents:", np.round(np.ptp(frame_bounds, axis=0), 3).tolist())
    print("panel_layout_bounds:", np.round(panel_layout.bounds, 3).tolist())
    print("files:", OUT_FRAME, OUT_PANELS)


if __name__ == "__main__":
    main()
