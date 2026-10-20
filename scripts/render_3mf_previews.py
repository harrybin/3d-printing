"""Render one complete-project preview image for every 3MF in models/."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import json
import trimesh
import vedo


ROOT = Path(os.environ.get("CATALOG_ROOT", Path.cwd())).resolve()
if "CATALOG_ROOT" in os.environ:
    from printforge.cli import catalog_root
    ROOT = catalog_root(ROOT)
MODELS = ROOT / "models"
OUTPUT = ROOT / "docs" / "images"
DEFAULT_COLOR = "#8b949e"


def _color(value: str | None) -> str | None:
    if not value or not value.startswith("#"):
        return None
    return value[:7] if len(value) >= 7 else None


def _project_colors(path: Path) -> dict[str, str]:
    with ZipFile(path) as archive:
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
        entries = set(archive.namelist())
        project_settings = (
            json.loads(archive.read("Metadata/project_settings.config"))
            if "Metadata/project_settings.config" in entries else {}
        )
        model_settings = (
            ET.fromstring(archive.read("Metadata/model_settings.config"))
            if "Metadata/model_settings.config" in entries else None
        )

    palettes: dict[str, list[str]] = {}
    for group in model.findall(".//{*}basematerials") + model.findall(".//{*}colorgroup"):
        palette = []
        for item in list(group):
            color = _color(item.get("displaycolor") or item.get("color"))
            palette.append(color or DEFAULT_COLOR)
        palettes[group.get("id", "")] = palette

    colors: dict[str, str] = {}
    model_objects = model.findall(".//{*}object")
    for obj in model_objects:
        palette = palettes.get(obj.get("pid", ""), [])
        index = obj.get("pindex")
        if index is not None and index.isdigit() and int(index) < len(palette):
            value = palette[int(index)]
        else:
            value = DEFAULT_COLOR
        colors[obj.get("id", "")] = value
        if obj.get("name"):
            colors[obj.get("name", "")] = value

    filament_colors = project_settings.get("filament_colour", [])
    if model_settings is not None and filament_colors:
        object_colors: dict[str, str] = {}
        for obj in model_settings.findall("object"):
            object_id = obj.get("id", "")
            slot = next(
                (node.get("value") for node in obj.findall("metadata")
                 if node.get("key") == "extruder"),
                None,
            )
            if slot and slot.isdigit() and 0 < int(slot) <= len(filament_colors):
                object_colors[object_id] = _color(filament_colors[int(slot) - 1]) or DEFAULT_COLOR
        component_colors = {
            component.get("objectid", ""): object_colors.get(obj.get("id", ""), DEFAULT_COLOR)
            for obj in model_objects
            for component in obj.findall("{*}components/{*}component")
        }
        colors.update(object_colors)
        colors.update(component_colors)
    return colors


def render_preview(path: Path, output: Path) -> None:
    scene = trimesh.load(path, force="scene")
    if not scene.graph.nodes_geometry:
        raise RuntimeError(f"No geometry in {path}")
    colors = _project_colors(path)
    actors = []
    for node in scene.graph.nodes_geometry:
        transform, geometry_name = scene.graph.get(node)
        mesh = scene.geometry[geometry_name].copy()
        mesh.apply_transform(transform)
        color = colors.get(str(node), colors.get(str(geometry_name), DEFAULT_COLOR))
        actors.append(vedo.Mesh(mesh).color(color).lighting("plastic"))

    bounds = scene.bounds
    minimum, maximum = bounds
    center = (minimum + maximum) / 2.0
    extent = max(float((maximum - minimum).max()), 1.0)
    plotter = vedo.Plotter(offscreen=True, size=(1400, 1000), bg="#111318")
    plotter.show(
        *actors,
        vedo.Text2D(path.name, pos="top-left", c="#f3f4f6", s=0.8),
        axes=0,
        camera={
            "pos": center + [extent * 1.45, -extent * 1.8, extent * 1.35],
            "focal_point": center,
            "viewup": (0.0, 0.0, 1.0),
        },
    )
    plotter.screenshot(str(output))
    plotter.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="*", type=Path,
                        help="Optional 3MF files; defaults to every models/*.3mf")
    args = parser.parse_args()
    paths = args.models or sorted(MODELS.glob("*.3mf"))
    if not paths:
        parser.error("No 3MF files found; set CATALOG_ROOT or pass explicit project paths")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for path in paths:
        output = OUTPUT / f"{path.stem}-preview.png"
        render_preview(path, output)
        print(output)


if __name__ == "__main__":
    main()
