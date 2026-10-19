"""Replace source meshes without resetting an approved Orca plate arrangement."""

from __future__ import annotations

import copy
import math
import os
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np

CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PRODUCTION = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"c": CORE}
ET.register_namespace("", CORE)
ET.register_namespace("p", PRODUCTION)
BED = 250.0
PLATE_PITCH = 300.0
PACK_GAP = 14.0


def surface(vertices, faces) -> bytes:
    triangles = np.round(np.asarray(vertices)[np.asarray(faces)], 3)
    triangles[triangles == 0] = 0
    order = np.lexsort((triangles[:, :, 2], triangles[:, :, 1],
                       triangles[:, :, 0]), axis=1)
    triangles = np.take_along_axis(triangles, order[:, :, None], axis=1)
    flat = triangles.reshape((-1, 9))
    return flat[np.lexsort(flat.T[::-1])].astype(np.float64).tobytes()


def pack(sizes: dict) -> dict:
    """Shelf-pack XY footprints on one bed; raise when they cannot fit."""
    for gap, margin in ((PACK_GAP, 15.0), (5.0, 0.0)):
        placements, x, y, row = {}, margin, margin, 0.0
        overflow = False
        for key in sorted(sizes, key=lambda k: (-sizes[k][1], -sizes[k][0], k)):
            width, depth = (float(value) for value in sizes[key])
            if x > margin and x + width > BED - margin:
                x, y, row = margin, y + row + gap, 0.0
            if x + width > BED - margin or y + depth > BED - margin:
                overflow = True
                break
            placements[key] = (x, y)
            x += width + gap
            row = max(row, depth)
        if not overflow:
            return placements
    raise ValueError(f"plate overflow while packing {key}")


def refresh(project: Path, print_parts: dict, changed: set[str],
            prune: bool = False) -> None:
    """Refresh saved meshes, add new BOM parts and optionally prune old ones.

    Only ``changed`` meshes are replaced. Parts absent from the project are
    added beside a template of the same kind; with ``prune`` saved objects
    that left the source BOM are removed. Plates are re-packed only when
    their membership changed or a resized part overlaps or leaves the bed.
    """
    with ZipFile(project) as archive:
        infos = archive.infolist()
        entries = {info.filename: archive.read(info.filename) for info in infos}
    model = ET.fromstring(entries["3D/3dmodel.model"])
    settings = ET.fromstring(entries["Metadata/model_settings.config"])
    resources = model.find("c:resources", NS)
    build = model.find("c:build", NS)
    if resources is None or build is None:
        raise ValueError("Saved project has no resources/build")
    configs = {
        obj.find("metadata[@key='name']").get("value"): obj
        for obj in settings.findall("object")
    }
    objects = {obj.get("id"): obj for obj in resources.findall("c:object", NS)}

    def replace_mesh(entry: str, mesh, build_transform: str | None = None) -> None:
        root = ET.fromstring(entries[entry])
        target = root.find("c:resources/c:object/c:mesh", NS)
        if target is None:
            raise ValueError(f"{entry}: expected a mesh object")
        centered = mesh.vertices - np.mean(mesh.bounds, axis=0)
        old_vertices = [
            [float(node.get(axis)) for axis in ("x", "y", "z")]
            for node in target.findall("c:vertices/c:vertex", NS)
        ]
        old_faces = [
            [int(node.get(axis)) for axis in ("v1", "v2", "v3")]
            for node in target.findall("c:triangles/c:triangle", NS)
        ]
        if build_transform is not None:
            matrix = np.asarray([float(value) for value in build_transform.split()])
            up = matrix[:9].reshape((3, 3)).T[2]
            if np.dot(up, up) <= 1e-12:
                raise ValueError(f"{entry}: singular print transform")
            # Preserve the saved bed-contact plane even when the part height
            # changes; bounds-centering alone would sink the taller crank.
            offset = (np.min(np.asarray(old_vertices) @ up)
                      - np.min(centered @ up))
            centered = centered + up * offset / np.dot(up, up)
        if surface(old_vertices, old_faces) == surface(centered, mesh.faces):
            return
        # Same topology within export rounding noise is not a geometry change;
        # keeping the saved payload avoids churn in untouched parts.
        if (len(old_faces) == len(mesh.faces)
                and len(old_vertices) == len(centered)
                and np.array_equal(np.asarray(old_faces), mesh.faces)
                and np.max(np.abs(np.asarray(old_vertices) - centered)) <= 0.002):
            return
        target.clear()
        vertices = ET.SubElement(target, f"{{{CORE}}}vertices")
        for x, y, z in centered:
            ET.SubElement(vertices, f"{{{CORE}}}vertex",
                          x=f"{x:.3f}", y=f"{y:.3f}", z=f"{z:.3f}")
        triangles = ET.SubElement(target, f"{{{CORE}}}triangles")
        for a, b, c in mesh.faces:
            ET.SubElement(triangles, f"{{{CORE}}}triangle",
                          v1=str(a), v2=str(b), v3=str(c))
        entries[entry] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    rels = ET.fromstring(entries["3D/_rels/3dmodel.model.rels"])
    plates = settings.findall("plate")
    columns = max(1, math.ceil(math.sqrt(len(plates))))

    def mesh_entry(obj) -> str:
        component = obj.find("c:components/c:component", NS)
        return component.get(f"{{{PRODUCTION}}}path").lstrip("/")

    def footprint(object_id: str):
        item = next(node for node in build if node.get("objectid") == object_id)
        matrix = np.asarray([float(v) for v in item.get("transform").split()])
        rotation = matrix[:9].reshape((3, 3))
        root = ET.fromstring(entries[mesh_entry(objects[object_id])])
        vertices = np.asarray([
            [float(node.get(axis)) for axis in ("x", "y", "z")]
            for node in root.findall(".//c:vertex", NS)
        ]) @ rotation
        return item, matrix, vertices.min(axis=0), vertices.max(axis=0)

    def overlap(a, b) -> float:
        size = np.minimum(a[1], b[1]) - np.maximum(a[0], b[0])
        return float(np.prod(np.clip(size, 0.0, None)))

    old_xy = {}
    for object_id in objects:
        _item, matrix, low, high = footprint(object_id)
        old_xy[object_id] = (low[:2] + matrix[9:11], high[:2] + matrix[9:11])
    changed_ids = set()

    for name in changed:
        if name not in print_parts:
            raise ValueError(f"Missing source part: {name}")
        if name not in configs:
            continue
        changed_ids.add(configs[name].get("id"))
        obj = objects[configs[name].get("id")]
        component = obj.find("c:components/c:component", NS)
        item = next(node for node in build
                    if node.get("objectid") == obj.get("id"))
        replace_mesh(component.get(f"{{{PRODUCTION}}}path").lstrip("/"),
                     print_parts[name],
                     item.get("transform", "1 0 0 0 1 0 0 0 1 0 0 0"))

    def plate_of(object_id: str):
        return next((plate for plate in plates
                     if any(instance.find("metadata[@key='object_id']")
                            .get("value") == object_id
                            for instance in plate.findall("model_instance"))),
                    None)

    touched_plates: set[int] = set()

    # Add source parts missing from the project. Each new object clones the
    # Orca object config of the closest saved part of the same kind so its
    # filament mapping and per-object process overrides stay consistent.
    # Adding runs before pruning so replaced variants (old pin names) can
    # still serve as templates for their successors.
    def template_for(name: str) -> str:
        if name == "candy-dish":
            return "drive-skull-knob"
        base = re.sub(r"-\d{2}$", "", name)
        candidates = [key for key in configs if key.startswith(base)]
        if not candidates:
            kind = name.split("-")[0]
            candidates = [key for key in configs if key.startswith(kind)]
        if not candidates:
            candidates = ["lid-crank"] if "lid-crank" in configs else sorted(configs)
        return sorted(candidates)[0]

    next_id = max(int(key) for key in objects) + 2
    for name in [key for key in print_parts if key not in configs]:
        template_config = configs[template_for(name)]
        template_obj = objects[template_config.get("id")]
        template_data = entries[mesh_entry(template_obj)]
        plate = plate_of(template_config.get("id"))
        mesh_id, object_id = next_id - 1, next_id
        next_id += 2
        number = object_id // 2
        entry = f"3D/Objects/{name}_{mesh_id}.model"
        mesh_root = ET.fromstring(template_data)
        mesh_object = mesh_root.find("c:resources/c:object", NS)
        mesh_object.set("id", str(mesh_id))
        mesh_object.set(f"{{{PRODUCTION}}}UUID",
                        f"{number:04x}0000-81cb-4c03-9d28-80fed5dfa1dc")
        entries[entry] = ET.tostring(mesh_root, encoding="utf-8")
        replace_mesh(entry, print_parts[name])
        obj = copy.deepcopy(template_obj)
        obj.set("id", str(object_id))
        obj.set(f"{{{PRODUCTION}}}UUID",
                f"{number:08x}-61cb-4c03-9d28-80fed5dfa1dc")
        component = obj.find("c:components/c:component", NS)
        component.set("objectid", str(mesh_id))
        component.set(f"{{{PRODUCTION}}}path", "/" + entry)
        component.set(f"{{{PRODUCTION}}}UUID",
                      f"{number:04x}0000-b206-40ff-9872-83e8017abed1")
        resources.append(obj)
        objects[str(object_id)] = obj
        z = float(print_parts[name].extents[2] / 2.0)
        ET.SubElement(build, f"{{{CORE}}}item", {
            "objectid": str(object_id),
            "transform": f"1 0 0 0 1 0 0 0 1 0 0 {z}",
            "printable": "1", "auto_drop": "1",
            f"{{{PRODUCTION}}}UUID":
                f"{object_id:08x}-b1ec-4553-aec9-835e5b724bb4",
        })
        config = copy.deepcopy(template_config)
        config.set("id", str(object_id))
        part = config.find("part")
        part.set("id", str(mesh_id))
        for element in config.iter("metadata"):
            key = element.get("key")
            if key == "name":
                element.set("value", name)
            elif key in {"source_object_id", "source_volume_id"}:
                element.set("value", "0")
            elif key.startswith("source_offset_"):
                element.set("value", "0")
        if name == "candy-dish":
            from export_ghouls_grip_orca_projects import OBJECT_OVERRIDES
            for key, value in OBJECT_OVERRIDES[name].items():
                metadata = config.find(f"metadata[@key='{key}']")
                if metadata is None:
                    metadata = ET.SubElement(config, "metadata", key=key)
                metadata.set("value", value)
        settings.insert(0, config)
        configs[name] = config
        if plate is not None:
            touched_plates.add(plates.index(plate))
            instance = ET.SubElement(plate, "model_instance")
            for key, value in (("object_id", str(object_id)),
                               ("instance_id", "0"),
                               ("identify_id", str(object_id))):
                ET.SubElement(instance, "metadata", key=key, value=value)
        ET.SubElement(rels, f"{{{REL}}}Relationship", Target="/" + entry,
                      Id=f"rel-{object_id}",
                      Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel")

    # Remove saved objects whose part no longer exists in the source BOM.
    if prune:
        for name in sorted(set(configs) - set(print_parts)):
            config = configs.pop(name)
            object_id = config.get("id")
            obj = objects.pop(object_id)
            entry = mesh_entry(obj)
            plate = plate_of(object_id)
            if plate is not None:
                touched_plates.add(plates.index(plate))
                for instance in list(plate.findall("model_instance")):
                    if (instance.find("metadata[@key='object_id']").get("value")
                            == object_id):
                        plate.remove(instance)
            resources.remove(obj)
            for item in [node for node in build
                         if node.get("objectid") == object_id]:
                build.remove(item)
            settings.remove(config)
            for relation in list(rels):
                if relation.get("Target", "").lstrip("/") == entry:
                    rels.remove(relation)
            entries.pop(entry, None)

    # Orca aborts loading when an assemble_item names a deleted object, and
    # objects without an entry lose their assembly-view pose.
    assemble = settings.find("assemble")
    if assemble is not None:
        for item in list(assemble):
            if item.get("object_id") not in objects:
                assemble.remove(item)
        listed = {item.get("object_id") for item in assemble}
        for node in build:
            object_id = node.get("objectid")
            if object_id in objects and object_id not in listed:
                ET.SubElement(assemble, "assemble_item", {
                    "object_id": object_id, "instance_id": "0",
                    "transform": node.get(
                        "transform", "1 0 0 0 1 0 0 0 1 0 0 0"),
                    "offset": "0 0 0",
                })

    # Plates whose membership changed, or whose resized parts now overlap
    # neighbours more than before or leave the bed, are re-packed. Untouched
    # plates keep the user's arrangement.
    for index, plate in enumerate(plates):
        origin = np.asarray([(index % columns) * PLATE_PITCH,
                             -(index // columns) * PLATE_PITCH])
        ids = [instance.find("metadata[@key='object_id']").get("value")
               for instance in plate.findall("model_instance")]
        boxes = {}
        for object_id in ids:
            item, matrix, low, high = footprint(object_id)
            boxes[object_id] = (item, matrix, low, high,
                                low[:2] + matrix[9:11], high[:2] + matrix[9:11])
        valid = True
        for object_id in changed_ids & set(boxes):
            lo, hi = boxes[object_id][4], boxes[object_id][5]
            if np.any(lo - origin < -1e-3) or np.any(hi - origin > BED + 1e-3):
                valid = False
            for other in boxes:
                if other == object_id:
                    continue
                before = (overlap(old_xy[object_id], old_xy[other])
                          if other in old_xy else 0.0)
                after = overlap((lo, hi), (boxes[other][4], boxes[other][5]))
                if after > before + 1.0:
                    valid = False
        if valid and index not in touched_plates:
            continue
        placements = pack(
            {key: boxes[key][3][:2] - boxes[key][2][:2] for key in boxes})
        for object_id, (x, y) in placements.items():
            item, matrix, low, _high, *_ = boxes[object_id]
            matrix[9] = origin[0] + x - low[0]
            matrix[10] = origin[1] + y - low[1]
            matrix[11] = -low[2]
            item.set("transform", " ".join(f"{value:.6f}" for value in matrix))

    for plate in settings.findall("plate"):
        for metadata in plate.findall("metadata"):
            if metadata.get("key") in {"gcode_file", "thumbnail_file",
                                       "thumbnail_no_light_file", "top_file",
                                       "pick_file"}:
                metadata.set("value", "")
    metadata_entry = "Metadata/ghouls_grip_print_metadata.xml"
    if metadata_entry in entries:
        metadata = ET.fromstring(entries[metadata_entry])
    else:
        metadata = ET.Element("ghouls-grip-print-metadata", version="1")
        for k, v in (
            ("status", "not-verified"),
            ("plateCount", str(len(settings.findall("plate")))),
            ("objectCount", str(len(build))),
            ("plateDetails", "[]"),
            ("filamentUsageByColor", "{}"),
        ):
            ET.SubElement(metadata, "metadata", name=k, value=v)
    for element in metadata.iter("metadata"):
        name = element.get("name")
        if name == "status":
            element.set("value", "not-verified")
        elif name == "plateDetails":
            element.set("value", "[]")
        elif name == "filamentUsageByColor":
            element.set("value", "{}")
        elif name == "objectCount":
            element.set("value", str(len(build)))
        elif name == "materialColorName":
            element.set("value", element.get("value", "").replace("Gray PLA", "Gold PLA"))
        elif name == "materialColorHex":
            element.set("value", element.get("value", "").replace("#777777", "#D4AF37"))
        elif name and (name.startswith("estimatedPrintTime")
                       or name.startswith("filamentUsage")
                       or name.startswith("supportFilament")):
            element.set("value", "unknown")
    if "Metadata/project_settings.config" in entries:
        entries["Metadata/project_settings.config"] = (
            entries["Metadata/project_settings.config"]
            .replace(b"#777777", b"#D4AF37")
            .replace(b"#777777ff", b"#D4AF37ff")
            .replace(b"#009CBD", b"#D4AF37")
            .replace(b"#009CBDff", b"#D4AF37ff")
        )
    for key, root in (("3D/3dmodel.model", model),
                      ("Metadata/model_settings.config", settings),
                      (metadata_entry, metadata)):
        entries[key] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    # Orca's relationship reader compares unprefixed XML names. A valid but
    # prefixed Relationship element makes every external mesh appear empty.
    ET.register_namespace("", REL)
    entries["3D/_rels/3dmodel.model.rels"] = ET.tostring(
        rels, encoding="utf-8", xml_declaration=True)
    ET.register_namespace("", CORE)
    entries["Metadata/slice_info.config"] = b"<config/>"
    stale = {name for name in entries if name.startswith(
        ("Metadata/plate_", "Metadata/plate_no_light_", "Metadata/top_",
         "Metadata/pick_"))}
    temporary = project.with_suffix(".refresh.3mf")
    existing = {info.filename: info for info in infos}
    with ZipFile(temporary, "w") as archive:
        for name, data in entries.items():
            if name not in stale:
                archive.writestr(existing.get(name, name), data)
    os.replace(temporary, project)
