"""Replacement tyre for a toy car wheel, printed in rigid PLA (no glue).

Dimensions: docs/modellauto-reifen-masse.md

Rigid PLA cannot be stretched over the 33.74 mm rib ring like the original
rubber tyre, so the tyre is a sleeve with a front lip: slid on from the axle
side until the lip rests against the wheel face, held by a press fit.

Print orientation: lip (wheel face side) flat on the bed, open end up (+Z).
"""

from pathlib import Path

import numpy as np
import trimesh

# --- measured (mm) ------------------------------------------------------------
TYRE_OD = 37.20          # intact tyre, user
TYRE_W = 26.00           # intact tyre, user
RIB_RING_OD = 33.74      # rim rib ring = tyre seat
FRONT_RING_OD = 22.54    # front rim ring inside the lip opening

# --- fit / design --------------------------------------------------------------
FIT_CLEAR = 0.20         # press fit baseline (diameter)
LIP_CLEAR = 0.46
LIP_T = 1.40             # (26.0 - 23.2) / 2, like the original sidewall

R_OUT = TYRE_OD / 2.0
R_SEAT = (RIB_RING_OD + FIT_CLEAR) / 2.0
R_LIP = (FRONT_RING_OD + LIP_CLEAR) / 2.0

FACE_CHAMFER = 0.8       # outer edge on the bed (45 deg, also elephant foot)
BACK_CHAMFER = 0.8       # outer edge at the open end
LEAD_IN = 0.5            # inner insertion chamfer at the open end
LIP_EDGE = 0.4           # chamfer of the lip opening on the bed side

SEGMENTS = 192


def build() -> trimesh.Trimesh:
    profile = np.array(
        [
            [R_LIP + LIP_EDGE, 0.0],
            [R_OUT - FACE_CHAMFER, 0.0],
            [R_OUT, FACE_CHAMFER],
            [R_OUT, TYRE_W - BACK_CHAMFER],
            [R_OUT - BACK_CHAMFER, TYRE_W],
            [R_SEAT + LEAD_IN, TYRE_W],
            [R_SEAT, TYRE_W - LEAD_IN],
            [R_SEAT, LIP_T],
            [R_LIP, LIP_T],
            [R_LIP, LIP_EDGE],
            [R_LIP + LIP_EDGE, 0.0],
        ]
    )
    mesh = trimesh.creation.revolve(profile, sections=SEGMENTS)
    mesh.vertices = np.round(mesh.vertices, 3)
    mesh.merge_vertices()
    mesh.update_faces(mesh.unique_faces())
    mesh.process(validate=True)
    mesh.fix_normals()
    return mesh


def main() -> None:
    mesh = build()
    out = Path(__file__).resolve().parents[1] / "models" / "modellauto-reifen.stl"
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
    print("seat_dia:", round(2 * R_SEAT, 3), "lip_dia:", round(2 * R_LIP, 3),
          "tread_wall:", round(R_OUT - R_SEAT, 3))


if __name__ == "__main__":
    main()
