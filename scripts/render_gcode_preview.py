"""Render a top-down preview from sliced OrcaSlicer G-code extrusion paths."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

MOVE_RE = re.compile(r"([XYZE])(-?\d+(?:\.\d+)?)")


def extrusion_segments(path: Path):
    x = y = z = e = 0.0
    absolute_xyz = True
    absolute_e = True
    segments = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw in handle:
            line = raw.split(";", 1)[0].strip()
            if not line:
                continue
            if line == "G90":
                absolute_xyz = True
                continue
            if line == "G91":
                absolute_xyz = False
                continue
            if line == "M82":
                absolute_e = True
                continue
            if line == "M83":
                absolute_e = False
                continue
            if line.startswith("G92"):
                values = {key: float(value) for key, value in MOVE_RE.findall(line)}
                x = values.get("X", x)
                y = values.get("Y", y)
                z = values.get("Z", z)
                e = values.get("E", e)
                continue
            if not (line.startswith("G0 ") or line.startswith("G1 ")):
                continue
            values = {key: float(value) for key, value in MOVE_RE.findall(line)}
            nx = values.get("X", x)
            ny = values.get("Y", y)
            nz = values.get("Z", z)
            ne = values.get("E", e)
            if not absolute_xyz:
                nx += x if "X" in values else 0.0
                ny += y if "Y" in values else 0.0
                nz += z if "Z" in values else 0.0
            extrusion = 0.0
            if "E" in values:
                extrusion = ne - e if absolute_e else values["E"]
                if not absolute_e:
                    ne = e + values["E"]
            if extrusion > 1e-5 and (nx != x or ny != y):
                segments.append((x, y, nx, ny, nz))
            x, y, z, e = nx, ny, nz, ne
    return segments


def render(gcode: Path, output: Path, title: str, size: int = 1000) -> None:
    segments = extrusion_segments(gcode)
    if not segments:
        raise RuntimeError(f"No extrusion paths found in {gcode}")
    margin = 65
    bed = 250.0
    scale = (size - 2 * margin) / bed
    image = Image.new("RGB", (size, size), "#101116")
    draw = ImageDraw.Draw(image)
    draw.rectangle(
        (margin, margin, size - margin, size - margin),
        fill="#191c24", outline="#707784", width=3)
    for tick in range(0, 251, 50):
        p = margin + tick * scale
        draw.line((p, margin, p, size - margin), fill="#292d37", width=1)
        draw.line((margin, size - p, size - margin, size - p), fill="#292d37", width=1)
    zmax = max(segment[4] for segment in segments) or 1.0
    step = max(1, len(segments) // 350000)
    for x0, y0, x1, y1, z in segments[::step]:
        t = min(1.0, max(0.0, z / zmax))
        color = (int(90 + 150 * t), int(190 - 60 * t), int(245 - 80 * t))
        draw.line((margin + x0 * scale, size - margin - y0 * scale,
                   margin + x1 * scale, size - margin - y1 * scale),
                  fill=color, width=1)
    font = ImageFont.load_default(size=18)
    draw.text((margin, 22), title, fill="#f0f2f5", font=font)
    draw.text((margin, size - 42),
              f"OrcaSlicer G-code paths | {len(segments):,} extrusion moves | Z {zmax:.1f} mm",
              fill="#b9c0cc", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, quality=94)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("gcode", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--title")
    args = parser.parse_args()
    render(args.gcode, args.output, args.title or args.gcode.stem)


if __name__ == "__main__":
    main()
