"""Render actual support extrusion paths from the final OrcaSlicer G-code."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import vedo
from PIL import Image, ImageDraw
from vtkmodules.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData

from render_ghouls_grip_print_projects import (
    BED, OUT, PROJECT, _plate_meshes, plate_filament,
)


def support_segments(path: Path) -> np.ndarray:
    position = np.zeros(3)
    absolute_xyz = True
    absolute_e = True
    extruder = 0.0
    support = False
    segments = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.startswith(";TYPE:"):
            support = raw.partition(":")[2].strip() in (
                "Support", "Support interface")
        command = raw.partition(";")[0].strip().split()
        if not command:
            continue
        verb = command[0]
        if verb in ("G90", "G91"):
            absolute_xyz = verb == "G90"
        elif verb in ("M82", "M83"):
            absolute_e = verb == "M82"
        elif verb in ("G0", "G1", "G92"):
            values = {
                key: float(value)
                for key, value in re.findall(
                    r"([XYZE])(-?(?:\d+(?:\.\d*)?|\.\d+))",
                    " ".join(command[1:]))
            }
            previous = position.copy()
            for axis, key in enumerate("XYZ"):
                if key in values:
                    position[axis] = (
                        values[key] if absolute_xyz or verb == "G92"
                        else position[axis] + values[key])
            delta = 0.0
            if "E" in values:
                delta = values["E"] - extruder if absolute_e else values["E"]
                extruder = (
                    values["E"] if absolute_e or verb == "G92"
                    else extruder + values["E"])
            if (verb != "G92" and support and delta > 0
                    and np.linalg.norm(position - previous) > 0.00001):
                segments.append((previous, position.copy()))
    return np.asarray(segments, dtype=float).reshape((-1, 2, 3))


def support_actor(segments: np.ndarray):
    points = vtkPoints()
    points.SetData(numpy_to_vtk(segments.reshape((-1, 3)), deep=True))
    connectivity = np.column_stack((
        np.full(len(segments), 2, dtype=np.int64),
        np.arange(2 * len(segments), dtype=np.int64).reshape((-1, 2)),
    )).ravel()
    lines = vtkCellArray()
    lines.ImportLegacyFormat(numpy_to_vtkIdTypeArray(connectivity, deep=True))
    data = vtkPolyData()
    data.SetPoints(points)
    data.SetLines(lines)
    return vedo.Lines(data, c="#ec6500", lw=2)




def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slices", type=Path,
                        help="Directory containing plate_1.gcode through plate_N.gcode")
    parser.add_argument("--project", type=Path, default=PROJECT)
    args = parser.parse_args()
    meshes = _plate_meshes(args.project)
    plate_indices = sorted(meshes)
    if plate_indices != list(range(len(plate_indices))):
        raise RuntimeError(f"Non-contiguous plate assignments: {plate_indices}")
    OUT.mkdir(parents=True, exist_ok=True)
    thumbnails = []
    labels = []
    for index in plate_indices:
        source = args.slices / f"plate_{index + 1}.gcode"
        if not source.exists():
            raise FileNotFoundError(source)
        segments = support_segments(source)
        label, material_color = plate_filament(source)
        title = f"Plate {index + 1} - {label}"
        actors = [
            vedo.Box(pos=(125, 125, -0.6), length=BED, width=BED,
                     height=1).color("#e1e5eb"),
            *[vedo.Mesh(mesh).color(material_color).alpha(0.24)
              for mesh in meshes[index]],
            vedo.Text2D(f"{title}\n" + (
                "Orange: actual support / interface paths" if len(segments)
                else "No support / interface extrusion in this slice"),
                        pos="top-left", c="#202124", s=0.7),
        ]
        if len(segments):
            actors.append(support_actor(segments))
        output = OUT / f"{args.project.stem}-plate-{index + 1}-supports.png"
        plotter = vedo.Plotter(offscreen=True, size=(1000, 1000), bg="#f5f6f8")
        plotter.show(*actors, axes=0, camera={
            "pos": (125, -310, 400), "focal_point": (125, 125, 45),
            "viewup": (0, 0, 1)})
        plotter.screenshot(str(output))
        plotter.close()
        thumbnails.append(output)
        labels.append(title)
        print(f"{output}: {label}, {len(segments)} support segments")
    columns = 3
    rows = (len(thumbnails) + columns - 1) // columns
    overview = Image.new("RGB", (columns * 600, rows * 620), "#f5f6f8")
    draw = ImageDraw.Draw(overview)
    for index, output in enumerate(thumbnails):
        with Image.open(output) as image:
            image.thumbnail((600, 600))
            x, y = (index % columns) * 600, (index // columns) * 620
            overview.paste(image, (x, y))
            draw.text((x + 12, y + 600), labels[index], fill="#202124")
    overview.save(OUT / f"{args.project.stem}-support-overview.png")


if __name__ == "__main__":
    main()
