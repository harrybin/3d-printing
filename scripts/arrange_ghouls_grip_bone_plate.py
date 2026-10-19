"""Compactly arrange Ghoul's Grip bone parts on print plate 2."""

from __future__ import annotations

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
BED_SIZE = 250.0
EDGE_MARGIN = 10.0
PART_CLEARANCE = 10.0
PLATE_X_OFFSET = 300.0

# Target XY bounding-box minima in millimeters. The palm and forearm share
# the upper row; the five fingers sit below them with a uniform gap.
UPPER_ROW = ("forearm", "hand-palm")
FINGER_ROW = (
    "hand-finger-thumb",
    "hand-finger-index",
    "hand-finger-middle",
    "hand-finger-ring",
    "hand-finger-little",
)
PART_NAMES = UPPER_ROW + FINGER_ROW
START_X = 69.0
START_Y = 72.0


def _build_id_by_name(settings: ET.Element) -> dict[str, str]:
    return {
        name.get("value"): item.get("id")
        for item in settings.findall("object")
        if (name := item.find("metadata[@key='name']")) is not None
    }


def _plate_ids(plate: ET.Element) -> set[str]:
    return {
        item.get("value")
        for instance in plate.findall("model_instance")
        if (item := instance.find("metadata[@key='object_id']")) is not None
    }


def _xy_bounds(
    entries: dict[str, bytes],
    model: ET.Element,
    object_id: str,
) -> tuple[float, float, float, float]:
    obj = model.find(f"c:resources/c:object[@id='{object_id}']", NS)
    if obj is None:
        raise ValueError(f"3MF model has no object {object_id}")
    component = obj.find("c:components/c:component", NS)
    if component is None:
        raise ValueError(f"3MF object {object_id} is not a component")
    entry = component.get(f"{{{PRODUCTION}}}path", "").lstrip("/")
    if not entry:
        raise ValueError(f"3MF object {object_id} has no mesh path")
    mesh = ET.fromstring(entries[entry])
    vertices = mesh.findall(".//c:vertices/c:vertex", NS)
    if not vertices:
        raise ValueError(f"3MF mesh {entry} has no vertices")
    build_item = next(
        (item for item in model.findall("c:build/c:item", NS)
         if item.get("objectid") == object_id),
        None,
    )
    if build_item is None:
        raise ValueError(f"3MF build has no item for object {object_id}")
    transform = [float(value) for value in
                 build_item.get("transform", "").split()]
    if len(transform) != 12:
        raise ValueError(f"Invalid 3MF transform for object {object_id}")

    xs, ys = [], []
    for vertex in vertices:
        x, y, z = (float(vertex.get(axis)) for axis in ("x", "y", "z"))
        xs.append(transform[0] * x + transform[1] * y
                  + transform[2] * z + transform[9])
        ys.append(transform[3] * x + transform[4] * y
                  + transform[5] * z + transform[10])
    return min(xs), min(ys), max(xs), max(ys)


def arrange(project: Path = PROJECT) -> None:
    with ZipFile(project) as archive:
        infos = archive.infolist()
        entries = {info.filename: archive.read(info.filename) for info in infos}

    model = ET.fromstring(entries["3D/3dmodel.model"])
    settings = ET.fromstring(entries["Metadata/model_settings.config"])
    names_to_ids = _build_id_by_name(settings)
    if not set(PART_NAMES).issubset(names_to_ids):
        raise ValueError("The saved project is missing one or more bone parts")
    plates = settings.findall("plate")
    if len(plates) < 2:
        raise ValueError("The saved project has no plate 2")
    bone_ids = {names_to_ids[name] for name in PART_NAMES}
    if not bone_ids.issubset(_plate_ids(plates[1])):
        raise ValueError("All bone parts must remain assigned to plate 2")

    items = {
        item.get("objectid"): item
        for item in model.findall("c:build/c:item", NS)
    }
    current_bounds = {
        name: _xy_bounds(entries, model, names_to_ids[name])
        for name in PART_NAMES
    }
    targets = {
        "forearm": (START_X, START_Y),
        "hand-palm": (
            current_bounds["forearm"][2] - current_bounds["forearm"][0]
            + START_X + PART_CLEARANCE,
            START_Y,
        ),
    }
    finger_x = START_X
    finger_y = max(
        current_bounds[name][3] - current_bounds[name][1]
        for name in UPPER_ROW
    ) + START_Y + PART_CLEARANCE
    for name in FINGER_ROW:
        targets[name] = (finger_x, finger_y)
        finger_x += (current_bounds[name][2] - current_bounds[name][0]
                     + PART_CLEARANCE)

    original_z = {}
    for name in PART_NAMES:
        target = targets[name]
        object_id = names_to_ids[name]
        item = items.get(object_id)
        if item is None:
            raise ValueError(f"3MF build has no item for {name}")
        serialized = item.get("transform", "").split()
        values = [float(value) for value in serialized]
        bounds = _xy_bounds(entries, model, object_id)
        dx = target[0] + PLATE_X_OFFSET - bounds[0]
        dy = target[1] - bounds[1]
        values[9] += dx
        values[10] += dy
        original_z[name] = values[11]
        serialized[9] = f"{values[9]:.6f}"
        serialized[10] = f"{values[10]:.6f}"
        item.set("transform", " ".join(serialized))

    # Re-open the changed model with the archive's mesh entries to verify the
    # saved plate positions before replacing the deliverable.
    bounds_by_name = {
        name: _xy_bounds(entries, model, names_to_ids[name])
        for name in PART_NAMES
    }
    for name, (plate_xmin, ymin, plate_xmax, ymax) in bounds_by_name.items():
        xmin, xmax = plate_xmin - PLATE_X_OFFSET, plate_xmax - PLATE_X_OFFSET
        if (xmin < EDGE_MARGIN - 0.01 or ymin < EDGE_MARGIN - 0.01
                or xmax > BED_SIZE - EDGE_MARGIN + 0.01
                or ymax > BED_SIZE - EDGE_MARGIN + 0.01):
            raise ValueError(f"{name} is too close to the plate edge: "
                             f"{(xmin, ymin, xmax, ymax)}")
        transform = [float(value) for
                     value in items[names_to_ids[name]].get(
                         "transform", "").split()]
        if abs(transform[11] - original_z[name]) > 1e-9:
            raise ValueError(f"{name} Z position unexpectedly changed")

    boxes = list(bounds_by_name.items())
    for index, (first_name, first) in enumerate(boxes):
        for second_name, second in boxes[index + 1:]:
            gap_x = max(second[0] - first[2], first[0] - second[2], 0.0)
            gap_y = max(second[1] - first[3], first[1] - second[3], 0.0)
            if gap_x < PART_CLEARANCE - 0.01 and \
                    gap_y < PART_CLEARANCE - 0.01:
                raise ValueError(
                    f"{first_name} and {second_name} are less than "
                    f"{PART_CLEARANCE:g} mm apart")

    entries["3D/3dmodel.model"] = ET.tostring(
        model, encoding="utf-8", xml_declaration=True)
    temporary = project.with_suffix(".layout.3mf")
    with ZipFile(temporary, "w") as archive:
        for info in infos:
            archive.writestr(info, entries[info.filename])
    os.replace(temporary, project)
    for name, bounds in bounds_by_name.items():
        print(f"{name}: {tuple(round(value, 2) for value in bounds)}")

if __name__ == "__main__":
    arrange()
