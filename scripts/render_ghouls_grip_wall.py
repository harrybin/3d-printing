"""Render the repaired rear wall from the exact delivered view 3MF."""

from pathlib import Path

import numpy as np
import trimesh
import vedo
from PIL import Image, ImageDraw

from render_3mf_previews import _project_colors

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "models" / "ghouls-grip-view.3mf"
OUTPUT = ROOT / "docs" / "images" / "ghouls-grip-continuous-wall.png"


def render():
    scene = trimesh.load(PROJECT, force="scene")
    colors = _project_colors(PROJECT)
    parts = []
    for node in scene.graph.nodes_geometry:
        if not str(node).startswith("deployed-"):
            continue
        transform, geometry = scene.graph.get(node)
        mesh = scene.geometry[geometry].copy()
        mesh.apply_transform(transform)
        parts.append((node, mesh))
    chest = next(mesh for name, mesh in parts if name == "deployed-chest")
    origin = np.array([
        float(np.mean(chest.bounds[:, 0])),
        float(chest.bounds[1, 1] - 66.0),
        0.0,
    ])
    views = (
        ("Continuous rear wall / no mechanism window",
         (-60.0, 215.0, 133.0), (-27.0, 59.0, 79.0)),
        ("Inboard rack / transfer gears above the intact rim",
         (-140.0, -130.0, 235.0), (-27.0, 46.0, 85.0)),
    )
    canvas = Image.new("RGB", (1800, 820), "#e3e5e8")
    draw = ImageDraw.Draw(canvas)
    for index, (label, position, focal) in enumerate(views):
        actors = []
        for name, mesh in parts:
            color = colors.get(name, "#F1EBDD")
            black = color.lower().startswith("#202124")
            actors.append(vedo.Mesh(mesh).color(color).lighting(
                "plastic", ambient=0.4 if black else 0.2,
                diffuse=0.8 if black else 0.3, specular=0.05))
        actors.extend([
            vedo.Light(origin + position, origin + focal, intensity=2.0),
            vedo.Light(origin + (100, 160, 220), origin + focal, intensity=0.8),
        ])
        plotter = vedo.Plotter(offscreen=True, size=(900, 780), bg="#d6d9de")
        plotter.show(*actors, axes=0, camera={
            "pos": origin + position,
            "focal_point": origin + focal,
            "viewup": (0, 0, 1),
            "parallel_scale": 49.0,
        })
        image = plotter.screenshot(asarray=True)
        plotter.close()
        canvas.paste(Image.fromarray(image[:, :, :3]), (index * 900, 0))
        draw.text((index * 900 + 18, 795), label, fill="#202124")
    canvas.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    render()
