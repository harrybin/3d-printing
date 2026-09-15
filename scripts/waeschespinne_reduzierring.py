"""Generate an ASA reducer ring for a 43 mm laundry-line pole in a 60 mm sleeve.

Print orientation: place the collar flat on the bed. The vertical walls require no
support; use at least five perimeters and 50 % rectilinear infill for the selected
load-bearing ASA use case.
"""

from pathlib import Path

import numpy as np
import trimesh

# --- user-confirmed dimensions and fit policy (mm) --------------------------
SLEEVE_ID = 60.0
POLE_OD = 43.0
GENERAL_CLEARANCE = 0.30
INSERTION_HEIGHT = 50.0
COLLAR_OUTER_DIA = 70.0
COLLAR_HEIGHT = 3.0

# Clearance is diametral: both mating diameters retain 0.30 mm total clearance.
OUTER_DIA = SLEEVE_ID - GENERAL_CLEARANCE
INNER_DIA = POLE_OD + GENERAL_CLEARANCE

# The collar rests on the sleeve rim and prevents the reducer ring from sinking in.
# A 1 mm chamfer at the pole-entry end eases assembly.
CHAMFER = 1.0
SEGMENTS = 128


def build() -> trimesh.Trimesh:
    outer_r = OUTER_DIA / 2.0
    inner_r = INNER_DIA / 2.0
    collar_r = COLLAR_OUTER_DIA / 2.0
    total_height = INSERTION_HEIGHT + COLLAR_HEIGHT
    profile = np.array(
        [
            [inner_r, 0.0],
            [collar_r, 0.0],
            [collar_r, COLLAR_HEIGHT],
            [outer_r, COLLAR_HEIGHT],
            [outer_r, total_height - CHAMFER],
            [outer_r - CHAMFER, total_height],
            [inner_r + CHAMFER, total_height],
            [inner_r, total_height - CHAMFER],
            [inner_r, 0.0],
        ]
    )
    ring = trimesh.creation.revolve(profile, sections=SEGMENTS)
    ring.vertices = np.round(ring.vertices, 3)
    ring.merge_vertices()
    ring.update_faces(ring.unique_faces())
    ring.update_faces(ring.nondegenerate_faces())
    ring.remove_unreferenced_vertices()
    ring.fix_normals()
    return ring


def main() -> None:
    mesh = build()
    if not mesh.is_watertight or not mesh.is_winding_consistent:
        raise RuntimeError("Generated reducer ring is not a valid watertight mesh.")

    out = Path(__file__).resolve().parents[1] / "models" / "waeschespinne-reduzierring-60-43.stl"
    out.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(out, file_type="stl_ascii")

    print("file:", out)
    print("facets:", len(mesh.faces))
    print("bounds:", np.round(mesh.bounds, 3).tolist())
    print("extents:", np.round(mesh.extents, 3).tolist())
    print("watertight:", mesh.is_watertight)
    print("winding_consistent:", mesh.is_winding_consistent)
    print("volume_mm3:", round(mesh.volume, 3))
    print("euler:", mesh.euler_number)
    print("degenerate:", int(np.count_nonzero(mesh.area_faces <= 1e-12)))
    print(
        "outer_dia:", OUTER_DIA,
        "inner_dia:", INNER_DIA,
        "insertion_height:", INSERTION_HEIGHT,
        "collar_dia:", COLLAR_OUTER_DIA,
        "total_height:", INSERTION_HEIGHT + COLLAR_HEIGHT,
    )


if __name__ == "__main__":
    main()
