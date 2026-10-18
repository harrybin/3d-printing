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
OUT_VIEW_3MF = ROOT / "models" / "ghouls-grip-view.3mf"
OUT_PRINT_3MF = ROOT / "models" / "ghouls-grip-print.3mf"
OUT_PREVIEW = ROOT / "models" / "ghouls-grip-preview.stl"

LEGACY_OUTPUTS = (
    ROOT / "models" / "ghouls-grip-master.3mf",
    ROOT / "models" / "ghouls-grip-master-retracted.3mf",
    ROOT / "models" / "ghouls-grip.3mf",
    ROOT / "models" / "ghouls-grip-retracted.3mf",
    ROOT / "models" / "ghouls-grip-black-pla.3mf",
    ROOT / "models" / "ghouls-grip-bone-pla.3mf",
    ROOT / "models" / "ghouls-grip-mechanism-pla.3mf",
    ROOT / "models" / "ghouls-grip-accent-pla.3mf",
    ROOT / "models" / "ghouls-grip-fingers-pla.3mf",
    ROOT / "models" / "ghouls-grip-print-black-pla.3mf",
    ROOT / "models" / "ghouls-grip-print-bone-pla.3mf",
    ROOT / "models" / "ghouls-grip-print-mechanism-pla.3mf",
    ROOT / "models" / "ghouls-grip-print-accent-pla.3mf",
)

BED = 250.0
VIEW_PLATE_PITCH = 300.0
VIEW_POSES = (
    ("deployed", mechanism.THETA_MAX, "Fully deployed"),
    ("intermediate", 48.0, "Intermediate - 48 degree scissor angle"),
    ("retracted", mechanism.THETA_MIN, "Retracted"),
)


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


def write_3mf(
    path: Path,
    objects,
    plate_names: list[str] | None = None,
    object_plates: dict[str, int] | None = None,
    material_slots: dict[Material, int] | None = None,
) -> None:
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
        "supportFilamentGrams": "unknown",
        "supportFilamentMillimeters": "unknown",
        "supportFilamentCubicMillimeters": "unknown",
        "printerProfile": "unknown",
        "nozzleDiameterMm": "unknown",
        "processProfile": "unknown",
        "layerHeightMm": "unknown",
        "filamentProfile": "unknown",
        "materialType": "unknown",
        "bedType": "unknown",
        "plateCount": str(len(plate_names) if plate_names else 1),
        "objectCount": str(len(objects)),
    }
    for name, value in neutral_values.items():
        ET.SubElement(metadata, "metadata", name=name, value=value)

    def member(archive: ZipFile, name: str, data) -> None:
        info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        archive.writestr(info, data)

    model_settings = None
    if plate_names is not None:
        if object_plates is None or material_slots is None:
            raise ValueError("Multi-plate 3MF needs object plate and material maps")
        model_settings = ET.Element("config")
        plate_objects: dict[int, list[str]] = {}
        for object_id, (name, _mesh, material, _transform) in enumerate(
                objects, start=2):
            if name not in object_plates:
                raise ValueError(f"Missing plate assignment for {name}")
            object_id_text = str(object_id)
            config_object = ET.SubElement(
                model_settings, "object", id=object_id_text)
            ET.SubElement(config_object, "metadata", key="name", value=name)
            ET.SubElement(
                config_object, "metadata", key="extruder",
                value=str(material_slots[material] + 1),
            )
            part = ET.SubElement(
                config_object, "part", id=str(object_id + 1),
                subtype="normal_part",
            )
            ET.SubElement(part, "metadata", key="name", value=name)
            ET.SubElement(
                part, "metadata", key="matrix",
                value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1",
            )
            ET.SubElement(part, "metadata", key="source_file", value=path.name)
            ET.SubElement(part, "metadata", key="source_object_id",
                          value=object_id_text)
            ET.SubElement(part, "metadata", key="source_volume_id", value="0")
            for key in ("source_offset_x", "source_offset_y", "source_offset_z"):
                ET.SubElement(part, "metadata", key=key, value="0")
            plate_objects.setdefault(object_plates[name], []).append(
                object_id_text)
        for index, plate_name in enumerate(plate_names):
            plate = ET.SubElement(model_settings, "plate")
            for key, value in (
                ("plater_id", str(index + 1)),
                ("plater_name", plate_name),
                ("locked", "false"),
                ("filament_map_mode", "Auto For Flush"),
                ("gcode_file", ""),
            ):
                ET.SubElement(plate, "metadata", key=key, value=value)
            for object_id in plate_objects.get(index, []):
                instance = ET.SubElement(plate, "model_instance")
                for key, value in (
                    ("object_id", object_id),
                    ("instance_id", "0"),
                    ("identify_id", object_id),
                ):
                    ET.SubElement(instance, "metadata", key=key, value=value)

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
        if model_settings is not None:
            member(
                archive,
                "Metadata/model_settings.config",
                ET.tostring(model_settings, encoding="utf-8",
                            xml_declaration=True),
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
    "drive-pinion": MECH,
    "lid-follower-rack": MECH, "lid-crank": MECH, "crank-spacer": MECH,
    "lid-transfer-gear": MECH,
    "scissor-drive-gear": MECH, "idler-gear": MECH,
    "forearm-output-gear": MECH,
    **{f"pivot-pin-{variant}": MECH for variant in mechanism.PIN_GRIPS},
    "drive-skull-knob": ACCENT,
    "forearm": BONE, "hand-palm": BONE,
}

PRINT_QUANTITIES = {
    "scissor-arm": 4,
    "idler-gear": 3,
    **{f"pivot-pin-{variant}": count
       for variant, count in mechanism.PIN_QUANTITIES.items() if count > 1},
    "lid-transfer-gear": 2,
}


def build_parts() -> dict:
    parts = {"chest": build_chest(), "lid": build_lid()}
    for name, fn in mechanism.PARTS.items():
        parts[name] = fn()
    for variant in mechanism.PIN_GRIPS:
        parts[f"pivot-pin-{variant}"] = mechanism.pin_print_pose(
            mechanism.build_pin_variant(variant))
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
        printable = mesh.copy()
        if name == "lid":
            # Print the lid standing on its rear (hinge) edge. Measured against
            # the upright, upside-down and front-edge candidates by
            # scripts/audit_lid_orientation.py this is the only orientation in
            # which neither the hollow inner ceiling nor the sculpted cartouche
            # becomes a large overhang: 4598.9 support E versus 20336.1 upright,
            # 20553.3 upside down and 14840.6 on the front edge. This
            # print-only transform does not alter the assembled master or any
            # hinge datum.
            printable.apply_transform(trimesh.transformations.rotation_matrix(
                -np.pi / 2.0, (1.0, 0.0, 0.0)))
            printable.apply_translation(
                [0.0, 0.0, -printable.bounds[0, 2]])
        elif name == "hand-palm":
            # Stand the palm on its wrist cut. Measured by
            # scripts/audit_part_orientation.py: 290.0 support E versus 2958.9
            # as built and 1970.5 flipped, because the finger sockets and the
            # thenar undercut then run vertically instead of roofing over.
            printable.apply_transform(trimesh.transformations.rotation_matrix(
                np.pi / 2.0, (1.0, 0.0, 0.0)))
            printable.apply_translation(
                [0.0, 0.0, -printable.bounds[0, 2]])
        elif name == "drive-skull-knob":
            # Print the skull knob face up on its flat shaft boss. Measured by
            # scripts/audit_part_orientation.py: 968.7 support E versus 3266.5
            # as built. The two side-laid candidates reach 655-732 E but would
            # drag support across the sculpted face, so the flat footprint with
            # the clean face wins.
            printable.apply_transform(trimesh.transformations.rotation_matrix(
                np.pi, (1.0, 0.0, 0.0)))
            printable.apply_translation(
                [0.0, 0.0, -printable.bounds[0, 2]])
        quantity = PRINT_QUANTITIES.get(name, 1)
        for index in range(quantity):
            instance = name if quantity == 1 else f"{name}-{index + 1:02d}"
            expanded[instance] = printable.copy()
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


def view_assembly_objects() -> tuple[list, list[str], dict[str, int], dict[Material, int]]:
    import render_ghouls_grip

    materials = (BLACK, BONE, MECH, ACCENT)
    material_slots = {material: index for index, material in enumerate(materials)}
    objects = []
    plate_names = []
    object_plates = {}
    for plate_index, (pose, theta, plate_name) in enumerate(VIEW_POSES):
        scene = render_ghouls_grip.build_scene_at(theta)
        minimum = np.min(
            [mesh.bounds[0][:2] for _, mesh, _ in scene], axis=0)
        maximum = np.max(
            [mesh.bounds[1][:2] for _, mesh, _ in scene], axis=0)
        footprint = maximum - minimum
        if np.any(footprint > BED):
            raise RuntimeError(
                f"{pose} assembly footprint does not fit the view plate: "
                f"{footprint.tolist()}"
            )
        offset = np.array([20.0, 20.0]) - minimum
        for name, mesh, _colour in scene:
            placed = mesh.copy()
            placed.apply_translation([
                offset[0] + plate_index * VIEW_PLATE_PITCH,
                offset[1],
                0.0,
            ])
            object_name = f"{pose}-{name}"
            objects.append((
                object_name,
                placed,
                assembly_material(name),
                None,
            ))
            object_plates[object_name] = plate_index
        plate_names.append(plate_name)
    return objects, plate_names, object_plates, material_slots


def render_view_3mf(path: Path) -> Path:
    from PIL import Image, ImageDraw
    import vedo

    scene = trimesh.load(path, force="scene")
    by_plate: dict[int, list[tuple[str, trimesh.Trimesh]]] = {}
    for node in scene.graph.nodes_geometry:
        transform, geometry_name = scene.graph.get(node)
        mesh = scene.geometry[geometry_name].copy()
        mesh.apply_transform(transform)
        plate_index = int(mesh.centroid[0] // VIEW_PLATE_PITCH)
        mesh.apply_translation([-plate_index * VIEW_PLATE_PITCH, 0.0, 0.0])
        by_plate.setdefault(plate_index, []).append((node, mesh))
    if sorted(by_plate) != [0, 1, 2]:
        raise RuntimeError(f"{path.name}: expected three view plates")

    def material_color(name: str) -> str:
        part_name = name.split("-", 1)[1]
        if part_name in {"chest", "lid"}:
            return "#202124"
        if (part_name in {"forearm", "hand-palm"}
                or part_name.startswith("hand-finger")):
            return "#D8C6A5"
        if part_name == "drive-skull-knob":
            return "#777777"
        return "#F1EBDD"

    thumbnails = []
    for plate_index, plate_name in enumerate(VIEW_POSES):
        entries = by_plate[plate_index]
        meshes = [mesh for _, mesh in entries]
        actors = [
            vedo.Box(
                pos=(BED / 2.0, BED / 2.0, -0.6),
                length=BED,
                width=BED,
                height=1.0,
            ).color("#343840"),
        ]
        actors.extend(
            vedo.Mesh([mesh.vertices, mesh.faces])
            .c(material_color(name))
            .lighting("glossy")
            for name, mesh in entries
        )
        upper = max(mesh.bounds[1, 2] for mesh in meshes)
        plotter = vedo.Plotter(
            offscreen=True,
            size=(760, 720),
            bg="#17191f",
        )
        plotter.show(
            *actors,
            axes=0,
            camera={
                "pos": (365.0, -440.0, upper + 230.0),
                "focal_point": (125.0, 125.0, upper * 0.42),
                "viewup": (0.0, 0.0, 1.0),
            },
        )
        thumbnail = ROOT / "build" / f"ghouls-grip-view-plate-{plate_index + 1}.png"
        thumbnail.parent.mkdir(parents=True, exist_ok=True)
        plotter.screenshot(str(thumbnail))
        plotter.close()
        thumbnails.append((plate_name[2], Image.open(thumbnail).convert("RGB")))

    margin, label_height, width, height = 24, 42, 760, 720
    output = ROOT / "docs" / "images" / "ghouls-grip-view.png"
    canvas = Image.new(
        "RGB",
        (3 * width + 4 * margin, height + label_height + 2 * margin),
        "#111318",
    )
    draw = ImageDraw.Draw(canvas)
    for index, (label, image) in enumerate(thumbnails):
        x = margin + index * (width + margin)
        y = margin
        canvas.paste(image, (x, y))
        draw.text((x, y + height + 10), label, fill="#f3f4f6")
    canvas.save(output)
    return output


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
    parts = build_parts()
    for name, mesh in parts.items():
        validate(name, mesh)

    print_parts = expand_print_parts(parts)
    if OUT_PRINT_3MF.exists():
        from refresh_ghouls_grip_print_geometry import refresh
        # Every BOM part is offered; identical meshes are no-ops, new pin
        # variants are added and superseded parts (lid-rack, old Ø3 pins)
        # are pruned while the user's Orca settings stay untouched.
        refresh(OUT_PRINT_3MF, print_parts, set(print_parts), prune=True)
        print_projects = [OUT_PRINT_3MF]
    else:
        from export_ghouls_grip_orca_projects import export_print_project
        print_projects = export_print_project(
            print_parts, write_3mf, arrange, material_for)

    view_objects, view_plates, object_plates, material_slots = (
        view_assembly_objects()
    )
    write_3mf(
        OUT_VIEW_3MF,
        view_objects,
        plate_names=view_plates,
        object_plates=object_plates,
        material_slots=material_slots,
    )
    presentation = render_view_3mf(OUT_VIEW_3MF)
    deployed = assembly_objects("deployed")
    preview = trimesh.util.concatenate([m for _, m, _, _ in deployed])
    write_ascii(clean(preview), OUT_PREVIEW)
    for path in LEGACY_OUTPUTS:
        path.unlink(missing_ok=True)
    print(f"files: {len(parts)} validated part types, {OUT_VIEW_3MF}, "
          f"{OUT_PREVIEW}, render={presentation}, print projects={print_projects}")


if __name__ == "__main__":
    main()
