"""Move every natural-white mechanism part onto one collision-free print plate."""

from __future__ import annotations

import math
import os
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "models" / "ghouls-grip-print.3mf"
CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PRODUCTION = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
NS = {"c": CORE}
ET.register_namespace("", CORE)
ET.register_namespace("p", PRODUCTION)

BED = 250.0
BED_MARGIN = 10.0
PART_GAP = 6.0
MECHANISM_PLATE_ORIGIN = (0.0, -300.0)


def _metadata(parent: ET.Element, key: str) -> ET.Element | None:
    return next(
        (node for node in parent.findall("metadata") if node.get("key") == key),
        None,
    )


def _metadata_value(parent: ET.Element, key: str) -> str | None:
    node = _metadata(parent, key)
    return node.get("value") if node is not None else None


def _mesh_bounds(archive: ZipFile, outer: ET.Element) -> tuple[float, ...]:
    component = outer.find("c:components/c:component", NS)
    if component is None:
        raise ValueError(f"Object {outer.get('id')} has no mesh component")
    entry = component.get(f"{{{PRODUCTION}}}path")
    if not entry:
        raise ValueError(f"Object {outer.get('id')} has no component path")
    mesh_root = ET.fromstring(archive.read(entry.lstrip("/")))
    vertices = mesh_root.findall(".//c:vertices/c:vertex", NS)
    if not vertices:
        raise ValueError(f"{entry}: mesh has no vertices")
    points = [
        tuple(float(vertex.get(axis)) for axis in ("x", "y", "z"))
        for vertex in vertices
    ]
    return tuple(
        value
        for axis in range(3)
        for value in (min(point[axis] for point in points),
                      max(point[axis] for point in points))
    )


def _transformed_xy_bounds(
    bounds: tuple[float, ...], transform: list[float]
) -> tuple[float, float, float, float]:
    corners = [
        (x, y, z)
        for x in (bounds[0], bounds[1])
        for y in (bounds[2], bounds[3])
        for z in (bounds[4], bounds[5])
    ]
    points = [
        (
            transform[0] * x + transform[1] * y + transform[2] * z
            + transform[9],
            transform[3] * x + transform[4] * y + transform[5] * z
            + transform[10],
        )
        for x, y, z in corners
    ]
    xs, ys = zip(*points)
    return min(xs), min(ys), max(xs), max(ys)


def _pack_rectangles(
    rectangles: list[tuple[str, float, float]],
) -> dict[str, tuple[float, float]]:
    usable = BED - 2.0 * BED_MARGIN
    free = [(0.0, 0.0, usable, usable)]
    placed: dict[str, tuple[float, float, float, float]] = {}
    ordered = sorted(
        rectangles,
        key=lambda item: (-item[1] * item[2], -max(item[1], item[2]), item[0]),
    )
    for name, width, height in ordered:
        packed_width = width + PART_GAP
        packed_height = height + PART_GAP
        choices = []
        for index, (x, y, free_width, free_height) in enumerate(free):
            if packed_width <= free_width and packed_height <= free_height:
                choices.append((
                    min(free_width - packed_width,
                        free_height - packed_height),
                    max(free_width - packed_width,
                        free_height - packed_height),
                    y, x, index,
                ))
        if not choices:
            raise RuntimeError(
                f"Cannot pack {name} ({width:.3f} x {height:.3f} mm) "
                "onto one plate without changing its orientation"
            )
        _, _, y, x, _ = min(choices)
        placed[name] = (
            x + PART_GAP / 2.0,
            y + PART_GAP / 2.0,
            width,
            height,
        )

        split: list[tuple[float, float, float, float]] = []
        for free_x, free_y, free_width, free_height in free:
            if (x >= free_x + free_width or x + packed_width <= free_x
                    or y >= free_y + free_height
                    or y + packed_height <= free_y):
                split.append((free_x, free_y, free_width, free_height))
                continue
            if x > free_x:
                split.append((free_x, free_y, x - free_x, free_height))
            if x + packed_width < free_x + free_width:
                split.append((
                    x + packed_width, free_y,
                    free_x + free_width - x - packed_width, free_height,
                ))
            if y > free_y:
                split.append((free_x, free_y, free_width, y - free_y))
            if y + packed_height < free_y + free_height:
                split.append((
                    free_x, y + packed_height, free_width,
                    free_y + free_height - y - packed_height,
                ))
        free = [
            rect for index, rect in enumerate(split)
            if not any(
                index != other_index
                and rect[0] >= other[0] - 1e-8
                and rect[1] >= other[1] - 1e-8
                and rect[0] + rect[2] <= other[0] + other[2] + 1e-8
                and rect[1] + rect[3] <= other[1] + other[3] + 1e-8
                for other_index, other in enumerate(split)
            )
        ]
    return {name: (x, y) for name, (x, y, _, _) in placed.items()}


def consolidate(project: Path = PROJECT) -> None:
    with ZipFile(project) as source:
        infos = source.infolist()
        entries = {info.filename: source.read(info.filename) for info in infos}
        settings = ET.fromstring(entries["Metadata/model_settings.config"])
        model = ET.fromstring(entries["3D/3dmodel.model"])

        names = {
            obj.get("id"): _metadata_value(obj, "name")
            for obj in settings.findall("object")
        }
        plates = settings.findall("plate")
        main_plate = next(
            (plate for plate in plates
             if all(term in (_metadata_value(plate, "plater_name") or "")
                    for term in ("Mechanik", "Hauptteile"))),
            None,
        )
        connector_plate = next(
            (plate for plate in plates
             if "Zahnraeder und Verbinder" in
             (_metadata_value(plate, "plater_name") or "")),
            None,
        )
        if main_plate is None:
            raise ValueError(
                "Expected a mechanism main-parts plate"
            )
        main_index = plates.index(main_plate)
        main_instances = main_plate.findall("model_instance")
        connector_instances = (
            connector_plate.findall("model_instance")
            if connector_plate is not None else []
        )
        if connector_plate is not None and plates.index(connector_plate) != main_index + 1:
            raise ValueError("Mechanism plates are not consecutive")
        expected_counts = (
            (11, 16) if connector_plate is not None else (27, 0)
        )
        if (len(main_instances), len(connector_instances)) != expected_counts:
            raise ValueError(
                f"Expected {expected_counts[0]} main parts and "
                f"{expected_counts[1]} connector parts; "
                f"found {len(main_instances)} and {len(connector_instances)}"
            )

        instances = main_instances + connector_instances
        object_ids = [
            _metadata_value(instance, "object_id") for instance in instances
        ]
        if any(object_id is None for object_id in object_ids):
            raise ValueError("A mechanism plate has an instance without object_id")
        if len(set(object_ids)) != len(object_ids):
            raise ValueError("Mechanism plates contain duplicate object IDs")

        resources = {
            obj.get("id"): obj
            for obj in model.findall("c:resources/c:object", NS)
        }
        build = {
            item.get("objectid"): item
            for item in model.findall("c:build/c:item", NS)
        }
        extents = {}
        positions = {}
        current_bounds = {}
        for object_id in object_ids:
            name = names.get(object_id)
            config = next(
                (obj for obj in settings.findall("object")
                 if obj.get("id") == object_id),
                None,
            )
            if not name or config is None:
                raise ValueError(f"Missing object settings for {object_id}")
            if _metadata_value(config, "extruder") != "3":
                raise ValueError(
                    f"{name} is not assigned to the natural-white filament slot"
                )
            item = build.get(object_id)
            outer = resources.get(object_id)
            if item is None or outer is None:
                raise ValueError(f"{name} is missing its model/build entry")
            transform = [
                float(value) for value in item.get(
                    "transform", "1 0 0 0 1 0 0 0 1 0 0 0"
                ).split()
            ]
            if len(transform) != 12:
                raise ValueError(f"{name} has an invalid build transform")
            bounds = _mesh_bounds(source, outer)
            xy = _transformed_xy_bounds(bounds, transform)
            extents[name] = (
                math.ceil((xy[2] - xy[0]) * 1000.0) / 1000.0,
                math.ceil((xy[3] - xy[1]) * 1000.0) / 1000.0,
            )
            current_bounds[name] = xy
            positions[name] = (item, transform)

        x_origin, y_origin = MECHANISM_PLATE_ORIGIN
        packed = _pack_rectangles([
            (name, width, height)
            for name, (width, height) in extents.items()
        ])

        for name, (target_x, target_y) in packed.items():
            item, transform = positions[name]
            old_x, old_y, _, _ = current_bounds[name]
            transform[9] += x_origin + BED_MARGIN + target_x - old_x
            transform[10] += y_origin + BED_MARGIN + target_y - old_y
            item.set("transform", " ".join(f"{value:.6f}" for value in transform))

        final_bounds = {}
        for name, (target_x, target_y) in packed.items():
            width, height = extents[name]
            final_bounds[name] = (
                BED_MARGIN + target_x,
                BED_MARGIN + target_y,
                BED_MARGIN + target_x + width,
                BED_MARGIN + target_y + height,
            )
        for name, (min_x, min_y, max_x, max_y) in final_bounds.items():
            if (min_x < BED_MARGIN - 1e-5 or min_y < BED_MARGIN - 1e-5
                    or max_x > BED - BED_MARGIN + 1e-5
                    or max_y > BED - BED_MARGIN + 1e-5):
                raise RuntimeError(f"{name} exceeds the reserved bed area")
        for index, first in enumerate(object_ids):
            name = names[first]
            a = final_bounds[name]
            for second in object_ids[index + 1:]:
                other_name = names[second]
                b = final_bounds[other_name]
                if (a[0] < b[2] and b[0] < a[2]
                        and a[1] < b[3] and b[1] < a[3]):
                    raise RuntimeError(
                        f"Packed bounding boxes overlap: {name}, {other_name}"
                    )

        main_name = _metadata(main_plate, "plater_name")
        if main_name is None:
            raise ValueError("Main mechanism plate has no name metadata")
        main_name.set("value", "Mechanik - Hauptteile und Verbinder")
        if connector_plate is not None:
            for instance in connector_instances:
                main_plate.append(instance)
            settings.remove(connector_plate)
        for index, plate in enumerate(settings.findall("plate"), start=1):
            plate_id = _metadata(plate, "plater_id")
            if plate_id is None:
                raise ValueError("A plate has no plater_id metadata")
            plate_id.set("value", str(index))
            for key in (
                "gcode_file", "thumbnail_file", "thumbnail_no_light_file",
                "top_file", "pick_file",
            ):
                value = _metadata(plate, key)
                if value is not None:
                    value.set("value", "")

        metadata_path = "Metadata/ghouls_grip_print_metadata.xml"
        metadata = ET.fromstring(entries[metadata_path])
        for element in metadata.iter("metadata"):
            key = element.get("name")
            if key == "status":
                element.set("value", "not-verified")
            elif key == "plateCount":
                element.set("value", str(len(settings.findall("plate"))))
            elif key == "objectCount":
                element.set("value", str(len(names)))
            elif key == "plateDetails":
                element.set("value", "[]")
            elif key == "filamentUsageByColor":
                element.set("value", "{}")
            elif key and (
                key.startswith("estimatedPrintTime")
                or key.startswith("filamentUsage")
                or key.startswith("supportFilament")
            ):
                element.set("value", "unknown")

        entries["Metadata/model_settings.config"] = ET.tostring(
            settings, encoding="utf-8", xml_declaration=True
        )
        entries["3D/3dmodel.model"] = ET.tostring(
            model, encoding="utf-8", xml_declaration=True
        )
        entries[metadata_path] = ET.tostring(
            metadata, encoding="utf-8", xml_declaration=True
        )
        entries["Metadata/slice_info.config"] = b"<config/>"

    stale = {
        name for name in entries
        if name.startswith((
            "Metadata/plate_", "Metadata/plate_no_light_", "Metadata/top_",
            "Metadata/pick_",
        ))
    }
    temporary = project.with_suffix(".consolidated.3mf")
    original_infos = {info.filename: info for info in infos}
    with ZipFile(temporary, "w") as output:
        for name, data in entries.items():
            if name not in stale:
                output.writestr(original_infos.get(name, name), data)
    os.replace(temporary, project)
    print(
        f"{project}: consolidated 27 natural-white parts onto one plate; "
        f"{len(settings.findall('plate'))} plates, {len(names)} objects"
    )


if __name__ == "__main__":
    consolidate()
