"""Render material-colored plate previews from the delivered Orca 3MF files."""

from __future__ import annotations

from pathlib import Path

import trimesh
import vedo
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
OUT = ROOT / "docs" / "images"
BED = 250.0
PLATE_PITCH = 300.0

PROJECTS = {
    "black": (
        MODELS / "ghouls-grip-print-black-pla.3mf",
        "#202124",
        ("ghouls-grip-slice-black-plate-1.png",),
    ),
    "bone": (
        MODELS / "ghouls-grip-print-bone-pla.3mf",
        "#D8C6A5",
        ("ghouls-grip-slice-bone.png",),
    ),
    "mechanism": (
        MODELS / "ghouls-grip-print-mechanism-pla.3mf",
        "#F1EBDD",
        ("ghouls-grip-slice-mechanism-plate-1.png",
         "ghouls-grip-slice-mechanism-plate-2.png"),
    ),
    "accent": (
        MODELS / "ghouls-grip-print-accent-pla.3mf",
        "#777777",
        ("ghouls-grip-slice-accent.png",),
    ),
}


def _plate_meshes(path: Path) -> dict[int, list[trimesh.Trimesh]]:
    scene = trimesh.load(path, force="scene")
    plates: dict[int, list[trimesh.Trimesh]] = {}
    for mesh in scene.dump(concatenate=False):
        plate = int(mesh.centroid[0] // PLATE_PITCH)
        local = mesh.copy()
        local.apply_translation([-plate * PLATE_PITCH, 0.0, 0.0])
        plates.setdefault(plate, []).append(local)
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
    rendered: list[tuple[str, Path]] = []
    for material, (project, color, filenames) in PROJECTS.items():
        plates = _plate_meshes(project)
        if len(plates) != len(filenames):
            raise RuntimeError(
                f"{project.name}: expected {len(filenames)} plates, "
                f"found {len(plates)}"
            )
        for plate, filename in zip(sorted(plates), filenames):
            output = OUT / filename
            _render_plate(plates[plate], color, output)
            rendered.append((f"{material} - plate {plate + 1}", output))
            print(output)
    _overview(rendered)
    print(OUT / "ghouls-grip-slice-overview.png")


if __name__ == "__main__":
    main()
