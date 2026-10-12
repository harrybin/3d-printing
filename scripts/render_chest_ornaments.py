"""Offscreen evaluation renders of the sculpted gothic chest ornaments.

Four close views - front wall, rear wall, side wall, lid - plus one overview,
rendered with a raking light so the relief reads as relief.  These are the
images used to judge whether the ornaments look organic rather than like flat
stamped strokes.

    .\\.venv\\Scripts\\python.exe scripts\\render_chest_ornaments.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import trimesh
import vedo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "build" / "ornament-audit"

import gothic_chest  # noqa: E402

VIEWS = {
    "front": dict(pos=(0.0, -330.0, 70.0), focal_point=(0.0, 0.0, 46.0),
                  size=(1500, 950)),
    "rear": dict(pos=(0.0, 330.0, 70.0), focal_point=(0.0, 0.0, 46.0),
                 size=(1500, 950)),
    "side": dict(pos=(-300.0, -40.0, 60.0), focal_point=(0.0, 0.0, 46.0),
                 size=(1200, 1000)),
    "hero": dict(pos=(-280.0, -300.0, 210.0), focal_point=(0.0, 0.0, 44.0),
                 size=(1500, 1150)),
}


def _render(mesh: trimesh.Trimesh, view: dict, out: Path) -> Path:
    vedo.settings.default_backend = "vtk"
    actor = vedo.Mesh([mesh.vertices, mesh.faces]).c("#9aa0a8")
    actor.lighting("glossy").phong()
    cam = dict(pos=view["pos"], focal_point=view["focal_point"],
               viewup=(0, 0, 1))
    pl = vedo.Plotter(offscreen=True, size=view["size"], bg="#15151a")
    pl.show(actor, axes=0, camera=cam)
    pl.screenshot(str(out))
    pl.close()
    print(f"-> {out}")
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    chest = gothic_chest.build_chest()
    for name, view in VIEWS.items():
        _render(chest, view, OUT / f"render-chest-{name}.png")

    lid = gothic_chest.build_lid()
    lid_view = dict(pos=(0.0, -120.0, 300.0), focal_point=(0.0, -6.0, 12.0),
                    size=(1500, 1050))
    _render(lid, lid_view, OUT / "render-lid-top.png")
    raking = dict(pos=(-150.0, -190.0, 130.0), focal_point=(0.0, -6.0, 12.0),
                  size=(1500, 1050))
    _render(lid, raking, OUT / "render-lid-raking.png")


if __name__ == "__main__":
    main()
