"""Render material-colored plate previews from the delivered Orca 3MF files."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import trimesh
import vedo
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
OUT = ROOT / "docs" / "images"
BED = 250.0
PLATE_X_PITCH = 300.0
PLATE_GRID_COLUMNS = 3
PROJECT = MODELS / "ghouls-grip-print.3mf"
PLATES = (
    ("Black PLA - chest", "#202124",
     "ghouls-grip-slice-black-plate-1.png"),
    ("Black PLA - lid", "#202124",
     "ghouls-grip-slice-black-plate-2.png"),
    ("Bone-beige PLA", "#D8C6A5", "ghouls-grip-slice-bone.png"),
    ("Natural-white PLA - mechanism", "#F1EBDD",
     "ghouls-grip-slice-mechanism-plate-1.png"),
    ("Natural-white PLA - connectors", "#F1EBDD",
     "ghouls-grip-slice-mechanism-plate-2.png"),
    ("Gray PLA", "#777777", "ghouls-grip-slice-accent.png"),
)


def _plate_meshes(path: Path) -> dict[int, list[trimesh.Trimesh]]:
    scene = trimesh.load(path, force="scene")
    core = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    with ZipFile(path) as archive:
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
        settings = ET.fromstring(archive.read("Metadata/model_settings.config"))

    component_by_object = {}
    for obj in model.findall(f".//{{{core}}}resources/{{{core}}}object"):
        component = obj.find(f"{{{core}}}components/{{{core}}}component")
        if component is not None:
            component_by_object[obj.get("id", "")] = component.get(
                "objectid", "")
    object_by_component = {
        component_id: object_id
        for object_id, component_id in component_by_object.items()
    }

    object_plate = {}
    for plate_index, plate in enumerate(settings.findall("plate")):
        for instance in plate.findall("model_instance"):
            object_id = next(
                (node.get("value") for node in instance.findall("metadata")
                 if node.get("key") == "object_id"),
                None,
            )
            if object_id is not None:
                if object_id in object_plate:
                    raise RuntimeError(
                        f"{path.name}: object {object_id} is on multiple plates")
                object_plate[object_id] = plate_index

    plates: dict[int, list[trimesh.Trimesh]] = {}
    for node in scene.graph.nodes_geometry:
        object_id = object_by_component.get(str(node))
        if object_id is None or object_id not in object_plate:
            raise RuntimeError(
                f"{path.name}: no plate assignment for mesh node {node}")
        transform, geometry_name = scene.graph.get(node)
        mesh = scene.geometry[geometry_name].copy()
        mesh.apply_transform(transform)
        plate = object_plate[object_id]
        plate_column = plate % PLATE_GRID_COLUMNS
        plate_row = plate // PLATE_GRID_COLUMNS
        mesh.apply_translation([
            -plate_column * PLATE_X_PITCH,
            plate_row * PLATE_X_PITCH,
            0.0,
        ])
        if (mesh.bounds[0, 0] < -0.01 or mesh.bounds[0, 1] < -0.01
                or mesh.bounds[1, 0] > BED + 0.01
                or mesh.bounds[1, 1] > BED + 0.01):
            raise RuntimeError(
                f"{path.name}: mesh node {node} is outside its plate: "
                f"{mesh.bounds.tolist()}")
        local = mesh.copy()
        plates.setdefault(plate, []).append(local)
    if len(object_plate) != sum(map(len, plates.values())):
        raise RuntimeError(
            f"{path.name}: plate metadata and mesh node counts differ")
    return plates


def _render_plate(meshes: list[trimesh.Trimesh], color: str,
                  output: Path) -> None:
    is_black = color.upper() == "#202124"
    bed = vedo.Box(
        pos=(BED / 2.0, BED / 2.0, -0.6),
        length=BED,
        width=BED,
        height=1.0,
    ).color("#555b66" if is_black else "#343840").alpha(1.0)
    actors = [bed]
    actors.extend(
        vedo.Mesh(mesh).color(color).lighting("plastic")
        for mesh in meshes
    )
    plotter = vedo.Plotter(
        offscreen=True,
        size=(900, 900),
        bg="#aeb3bc" if is_black else "#17191f",
    )
    plotter.show(
        *actors,
        axes=0,
        camera={
            "pos": (BED / 2.0, -310.0, 400.0),
            "focal_point": (BED / 2.0, BED / 2.0, 45.0),
            "viewup": (0.0, 0.0, 1.0),
        },
    )
    plotter.screenshot(str(output))
    plotter.close()


def _overview(paths: list[tuple[str, Path]]) -> None:
    thumb_size = (520, 520)
    margin = 24
    label_h = 34
    canvas = Image.new(
        "RGB",
        (3 * thumb_size[0] + 4 * margin,
         2 * (thumb_size[1] + label_h) + 3 * margin),
        "#111318",
    )
    draw = ImageDraw.Draw(canvas)
    for index, (label, path) in enumerate(paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail(thumb_size)
        column = index % 3
        row = index // 3
        x = margin + column * (thumb_size[0] + margin)
        y = margin + row * (thumb_size[1] + label_h + margin)
        canvas.paste(image, (x, y))
        draw.text((x, y + thumb_size[1] + 7), label, fill="#f3f4f6")
    canvas.save(OUT / "ghouls-grip-slice-overview.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    plates = _plate_meshes(PROJECT)
    if sorted(plates) != list(range(len(PLATES))):
        raise RuntimeError(
            f"{PROJECT.name}: expected {len(PLATES)} plates, "
            f"found {sorted(plates)}"
        )
    rendered: list[tuple[str, Path]] = []
    for plate, (label, color, filename) in enumerate(PLATES):
        output = OUT / filename
        _render_plate(plates[plate], color, output)
        rendered.append((label, output))
        print(output)
    _overview(rendered)
    print(OUT / "ghouls-grip-slice-overview.png")


if __name__ == "__main__":
    main()
