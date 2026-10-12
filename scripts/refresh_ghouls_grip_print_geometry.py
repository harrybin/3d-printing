"""Replace source meshes without resetting an approved Orca plate arrangement."""

from __future__ import annotations

import copy
import os
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


def surface(vertices, faces) -> bytes:
    triangles = np.round(np.asarray(vertices)[np.asarray(faces)], 3)
    triangles[triangles == 0] = 0
    order = np.lexsort((triangles[:, :, 2], triangles[:, :, 1],
                       triangles[:, :, 0]), axis=1)
    triangles = np.take_along_axis(triangles, order[:, :, None], axis=1)
    flat = triangles.reshape((-1, 9))
    return flat[np.lexsort(flat.T[::-1])].astype(np.float64).tobytes()


def refresh(project: Path, print_parts: dict, changed: set[str]) -> None:
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

    for name in changed:
        if name not in configs or name not in print_parts:
            raise ValueError(f"Missing saved/source part: {name}")
        obj = objects[configs[name].get("id")]
        component = obj.find("c:components/c:component", NS)
        item = next(node for node in build
                    if node.get("objectid") == obj.get("id"))
        replace_mesh(component.get(f"{{{PRODUCTION}}}path").lstrip("/"),
                     print_parts[name],
                     item.get("transform", "1 0 0 0 1 0 0 0 1 0 0 0"))

    # Add only the new transfer gears to free space on the existing connector
    # plate. Every original build transform and process override stays intact.
    connector = next(
        plate for plate in settings.findall("plate")
        if any(instance.find("metadata[@key='object_id']").get("value")
               == configs["idler-gear-01"].get("id")
               for instance in plate.findall("model_instance"))
    )
    template_config = configs["lid-crank"]
    template_obj = objects[template_config.get("id")]
    template_component = template_obj.find("c:components/c:component", NS)
    template_entry = template_component.get(f"{{{PRODUCTION}}}path").lstrip("/")
    template_data = entries[template_entry]
    rels = ET.fromstring(entries["3D/_rels/3dmodel.model.rels"])
    next_id = max(int(key) for key in objects) + 2
    # Keep the new objects consistent with Orca's ID-encoded production UUIDs.
    for index, name in enumerate(("lid-transfer-gear-01", "lid-transfer-gear-02")):
        if name in configs:
            obj = objects[configs[name].get("id")]
            component = obj.find("c:components/c:component", NS)
            object_id = int(obj.get("id"))
            number = object_id // 2
            entry = component.get(f"{{{PRODUCTION}}}path").lstrip("/")
            obj.set(f"{{{PRODUCTION}}}UUID",
                    f"{number:08x}-61cb-4c03-9d28-80fed5dfa1dc")
            component.set(f"{{{PRODUCTION}}}UUID",
                          f"{number:04x}0000-b206-40ff-9872-83e8017abed1")
            item = next(node for node in build
                        if node.get("objectid") == str(object_id))
            item.set(f"{{{PRODUCTION}}}UUID",
                     f"{object_id:08x}-b1ec-4553-aec9-835e5b724bb4")
            mesh_root = ET.fromstring(entries[entry])
            mesh_root.find("c:resources/c:object", NS).set(
                f"{{{PRODUCTION}}}UUID",
                f"{number:04x}0000-81cb-4c03-9d28-80fed5dfa1dc")
            entries[entry] = ET.tostring(mesh_root, encoding="utf-8",
                                         xml_declaration=True)
            replace_mesh(entry, print_parts[name])
            continue
        mesh_id, object_id = next_id - 1, next_id
        next_id += 2
        entry = f"3D/Objects/{name}_{mesh_id}.model"
        mesh_root = ET.fromstring(template_data)
        mesh_object = mesh_root.find("c:resources/c:object", NS)
        mesh_object.set("id", str(mesh_id))
        number = object_id // 2
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
        # Connector plate has its approved global origin at (0,-300).
        x, y = 45.0 + index * 24.0, -225.0
        z = float(print_parts[name].extents[2] / 2.0)
        ET.SubElement(build, f"{{{CORE}}}item", {
            "objectid": str(object_id),
            "transform": f"1 0 0 0 1 0 0 0 1 {x} {y} {z}",
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
        settings.insert(0, config)
        instance = ET.SubElement(connector, "model_instance")
        for key, value in (("object_id", str(object_id)), ("instance_id", "0"),
                           ("identify_id", str(object_id))):
            ET.SubElement(instance, "metadata", key=key, value=value)
        ET.SubElement(rels, f"{{{REL}}}Relationship", Target="/" + entry,
                      Id=f"rel-transfer-{index + 1}",
                      Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel")

    for plate in settings.findall("plate"):
        for metadata in plate.findall("metadata"):
            if metadata.get("key") in {"gcode_file", "thumbnail_file",
                                       "thumbnail_no_light_file", "top_file",
                                       "pick_file"}:
                metadata.set("value", "")
    metadata_entry = "Metadata/ghouls_grip_print_metadata.xml"
    metadata = ET.fromstring(entries[metadata_entry])
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
        elif name and (name.startswith("estimatedPrintTime")
                       or name.startswith("filamentUsage")
                       or name.startswith("supportFilament")):
            element.set("value", "unknown")
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
