"""Close-up of actual delivered floor yokes; chest ghosted for visibility."""

from pathlib import Path

import numpy as np
import trimesh
import vedo
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "models/ghouls-grip-view.3mf"
OUTPUT = ROOT / "docs/images/ghouls-grip-floor-bearings.png"


def render():
    scene = trimesh.load(PROJECT, force="scene")
    canvas = Image.new("RGB", (1800, 830), "#e3e5e8")
    draw = ImageDraw.Draw(canvas)
    for index, pose in enumerate(("retracted", "deployed")):
        def part(name):
            transform, geometry = scene.graph.get(pose + "-" + name)
            mesh = scene.geometry[geometry].copy()
            mesh.apply_transform(transform)
            return mesh

        chest = part("chest")
        origin = np.array([chest.bounds[:, 0].mean(),
                           chest.bounds[1, 1] - 66, 0])
        names = ("arm-0-False", "arm-0-True", "pivot-pin-3-0-0", "slider")
        actors = [vedo.Mesh(chest).color("#202124").alpha(0.25)]
        actors.extend(vedo.Mesh(part(name)).color("#F1EBDD").lighting("plastic")
                      for name in names)
        plotter = vedo.Plotter(offscreen=True, size=(900, 780), bg="#d6d9de")
        plotter.show(*actors, axes=0, camera={
            "pos": origin + (-27, -8, 35),
            "focal_point": origin + (0, -40, 8),
            "viewup": (0, 0, 1),
            "parallel_scale": 20,
        })
        image = plotter.screenshot(asarray=True)
        plotter.close()
        canvas.paste(Image.fromarray(image[:, :, :3]), (index * 900, 0))
        draw.text((index * 900 + 18, 792),
                  f"{pose}: actual 3MF / chest ghosted / unchanged arms",
                  fill="#202124")
        draw.text((index * 900 + 18, 810),
                  "Open double cheeks, floor roots, inboard pin head",
                  fill="#202124")
    canvas.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    render()
