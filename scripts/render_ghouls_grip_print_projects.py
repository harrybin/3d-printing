"""Render material-colored plate previews from an OrcaSlicer 3MF and its slices."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import argparse
import re

import trimesh
import vedo
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
OUT = ROOT / "docs" / "images"
BED = 250.0
PLATE_X_PITCH = 300.0
PROJECT = MODELS / "ghouls-grip-print.3mf"
FILAMENTS = (
    ("Black PLA", "#202124"),
    ("Bone-beige PLA", "#D8C6A5"),
    ("Natural-white PLA", "#F1EBDD"),
    ("Gray PLA", "#777777"),
)


def plate_filament(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"; filament used \[g\] = ([0-9., ]+)", text)
    if not match:
        raise RuntimeError(f"Missing filament use metadata in {path}")
    values = [float(item.strip()) for item in match.group(1).split(",")]
    active = [index for index, value in enumerate(values) if value > 0]
    if len(active) != 1 or active[0] >= len(FILAMENTS):
        raise RuntimeError(f"Cannot identify one plate material in {path}")
    colour_match = re.search(r"; filament_colour = ([^\r\n]+)", text)
    if colour_match:
        colours = [c.strip() for c in colour_match.group(1).split(";") if c.strip()]
        if active[0] < len(colours):
            from update_ghouls_grip_slice_metadata import FILAMENT_NAMES
            hex_col = colours[active[0]]
            label = FILAMENT_NAMES.get(hex_col.lower(), hex_col)
            return label, hex_col
    return FILAMENTS[active[0]]


def _plate_meshes(path: Path) -> dict[int, list[trimesh.Trimesh]]:
    scene = trimesh.load(path, force="scene")
    core = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    with ZipFile(path) as archive:
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
        settings = ET.fromstring(archive.read("Metadata/model_settings.config"))
    grid_columns = 3 if len(settings.findall("plate")) >= 5 else 2

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
        object_id = (
            str(node)
            if str(node) in object_plate
            else object_by_component.get(str(node))
        )
        if object_id is None or object_id not in object_plate:
            raise RuntimeError(
                f"{path.name}: no plate assignment for mesh node {node}")
        transform, geometry_name = scene.graph.get(node)
        mesh = scene.geometry[geometry_name].copy()
        mesh.apply_transform(transform)
        plate = object_plate[object_id]
        plate_column = plate % grid_columns
        plate_row = plate // grid_columns
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


def _overview(paths: list[tuple[str, Path]], output: Path) -> None:
    thumb_size = (520, 520)
    margin = 24
    label_h = 34
    columns = 3
    rows = (len(paths) + columns - 1) // columns
    canvas = Image.new(
        "RGB",
        (columns * thumb_size[0] + (columns + 1) * margin,
         rows * (thumb_size[1] + label_h) + (rows + 1) * margin),
        "#111318",
    )
    draw = ImageDraw.Draw(canvas)
    for index, (label, path) in enumerate(paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail(thumb_size)
        column = index % columns
        row = index // columns
        x = margin + column * (thumb_size[0] + margin)
        y = margin + row * (thumb_size[1] + label_h + margin)
        canvas.paste(image, (x, y))
        draw.text((x, y + thumb_size[1] + 7), label, fill="#f3f4f6")
    canvas.save(output)
    if output.name == "ghouls-grip-print-preview.png":
        canvas.save(OUT / "ghouls-grip-slice-overview.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slices", type=Path,
                        help="Directory containing the successful plate_*.gcode slices")
    parser.add_argument("--project", type=Path, default=PROJECT)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    plates = _plate_meshes(args.project)
    if sorted(plates) != list(range(len(plates))):
        raise RuntimeError(f"{args.project.name}: non-contiguous plates")
    rendered: list[tuple[str, Path]] = []
    for plate in sorted(plates):
        slice_path = args.slices / f"plate_{plate + 1}.gcode"
        if not slice_path.exists():
            raise FileNotFoundError(slice_path)
        label, color = plate_filament(slice_path)
        label = f"Plate {plate + 1} - {label}"
        output = OUT / f"ghouls-grip-slice-plate-{plate + 1}.png"
        _render_plate(plates[plate], color, output)
        rendered.append((label, output))
        print(output)
    preview = OUT / f"{args.project.stem}-preview.png"
    _overview(rendered, preview)
    print(preview)


if __name__ == "__main__":
    main()
