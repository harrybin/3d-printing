"""Measured support audit for the print orientation of any single part.

The orientation that "looks" support free is routinely wrong, so every print
transform in this project has to be backed by a real slice.  This script builds
one part, slices it in a set of competing orientations inside one cloned project
template and reports the support extrusion of each candidate.  Only the build
item orientation differs between runs, so the numbers are directly comparable.

    .\\.venv\\Scripts\\python.exe scripts\\audit_part_orientation.py drive-skull-knob
    .\\.venv\\Scripts\\python.exe scripts\\audit_part_orientation.py hand-palm forearm
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_chest_support import _project, _slice, _support_stats  # noqa: E402
import ghouls_grip  # noqa: E402

# Axis-aligned candidates. Anything else would need a part specific rule.
CANDIDATES = {
    "as-built": (0.0, (1.0, 0.0, 0.0)),
    "flip-x-180": (np.pi, (1.0, 0.0, 0.0)),
    "tilt-x-+90": (np.pi / 2.0, (1.0, 0.0, 0.0)),
    "tilt-x--90": (-np.pi / 2.0, (1.0, 0.0, 0.0)),
    "tilt-y-+90": (np.pi / 2.0, (0.0, 1.0, 0.0)),
    "tilt-y--90": (-np.pi / 2.0, (0.0, 1.0, 0.0)),
}

BED = 250.0
MAX_Z = 250.0


def _oriented(mesh: trimesh.Trimesh, angle: float, axis) -> trimesh.Trimesh:
    out = mesh.copy()
    if angle:
        out.apply_transform(
            trimesh.transformations.rotation_matrix(angle, axis))
    out.apply_translation([0.0, 0.0, -out.bounds[0, 2]])
    return out


def audit(part: str, parts: dict) -> str:
    base = parts[part]
    results = {}
    for name, (angle, axis) in CANDIDATES.items():
        mesh = _oriented(base, angle, axis)
        extents = mesh.extents
        if extents[0] > BED or extents[1] > BED or extents[2] > MAX_Z:
            print(f"{part}/{name:12s} skipped, does not fit the bed")
            continue
        if not mesh.is_volume:
            raise RuntimeError(f"{part}/{name} is not a closed volume")
        slug = f"{part}-{name}"
        stats = _support_stats(_slice(_project(mesh, slug), slug))
        stats["height_mm"] = round(float(extents[2]), 2)
        results[name] = stats
        print(f"{part}/{name:12s} {stats}")

    best = min(results, key=lambda key: results[key]["support_e"])
    worst = max(results, key=lambda key: results[key]["support_e"])
    print(f"{part}: best={best} ({results[best]['support_e']:.1f} E), "
          f"worst={worst} ({results[worst]['support_e']:.1f} E)\n")
    return best


def main() -> None:
    wanted = sys.argv[1:]
    if not wanted:
        raise SystemExit(__doc__)
    parts = ghouls_grip.build_parts()
    missing = [name for name in wanted if name not in parts]
    if missing:
        raise SystemExit(f"unknown part(s): {', '.join(missing)}")
    for part in wanted:
        audit(part, parts)


if __name__ == "__main__":
    main()
