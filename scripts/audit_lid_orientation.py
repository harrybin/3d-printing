"""Support audit for the lid print orientation.

The sculpted cartouche changed the trade-off: laying the lid on its decorated
face now rests the part on relief peaks instead of a flat surface.  This script
slices the same lid in competing orientations inside one project template, so
only the orientation differs.

    .\\.venv\\Scripts\\python.exe scripts\\audit_lid_orientation.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_chest_support import _project, _slice, _support_stats  # noqa: E402
import gothic_chest  # noqa: E402


def _oriented(angle: float, axis) -> trimesh.Trimesh:
    mesh = gothic_chest.build_lid()
    if angle:
        mesh.apply_transform(
            trimesh.transformations.rotation_matrix(angle, axis))
    mesh.apply_translation([0.0, 0.0, -mesh.bounds[0, 2]])
    return mesh


CANDIDATES = {
    "lid-upright": (0.0, (1.0, 0.0, 0.0)),
    "lid-upside-down": (np.pi, (1.0, 0.0, 0.0)),
    "lid-on-front-edge": (np.pi / 2.0, (1.0, 0.0, 0.0)),
    "lid-on-rear-edge": (-np.pi / 2.0, (1.0, 0.0, 0.0)),
}


def main() -> None:
    results = {}
    for name, (angle, axis) in CANDIDATES.items():
        mesh = _oriented(angle, axis)
        if not mesh.is_volume:
            raise RuntimeError(f"{name} is not a closed volume")
        gcode = _slice(_project(mesh, name), name)
        stats = _support_stats(gcode)
        stats["height_mm"] = round(float(mesh.extents[2]), 2)
        results[name] = stats
        print(f"{name:18s} {stats}")

    best = min(results, key=lambda key: results[key]["support_e"])
    print(f"\nlowest support: {best}")


if __name__ == "__main__":
    main()
