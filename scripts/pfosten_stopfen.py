"""Snap-fit plug for the round hole in the steel post.

Measured: hole diameter 11.52 mm (caliper photo), post wall thickness 1.5 mm.

Design
------
* flat outer face (printed directly on the bed -> best surface + strongest
  layer bonding for the visible disc, no supports needed)
* 4 spring legs with a 45 deg retaining barb that snaps behind the sheet
* annular crush lip on the flange underside so the plug seats without rattle
* hollow shaft so the legs can actually flex inwards

Print orientation: flange flat on the bed, legs pointing up (+Z).
"""

from pathlib import Path

import numpy as np
import trimesh

# --- measured / user supplied (mm) ------------------------------------------
HOLE_DIA = 11.52        # caliper reading
WALL_T = 1.5            # steel post material thickness

# --- fit parameters ---------------------------------------------------------
SLIDE_CLEAR = 0.24      # shaft vs. hole, 0.4 mm nozzle profile
SHAFT_R = (HOLE_DIA - SLIDE_CLEAR) / 2.0        # 5.64
BARB_OVER = 0.55        # radial barb projection beyond the shaft
BARB_R = SHAFT_R + BARB_OVER                    # 6.19
PRELOAD = 0.10          # barb ledge sits slightly inside the sheet -> no play

# --- flange ------------------------------------------------------------------
FLANGE_R = 7.5
FLANGE_T = 1.8
FACE_T = 1.2            # solid outer skin below the hollow shaft
RIM_CHAMFER = 0.5

LIP_RI = 6.0            # crush lip footprint (outside the hole edge at 5.76)
LIP_RO = 6.9
LIP_H = 0.4

# --- shaft ------------------------------------------------------------------
SEAT_Z = FLANGE_T + LIP_H                       # sheet outer face
LEDGE_Z = SEAT_Z + WALL_T - PRELOAD             # start of the retaining ledge
BARB_Z = LEDGE_Z + BARB_OVER                    # 45 deg ledge -> printable
RAMP_TOP_Z = BARB_Z + 2.7                       # gentle insertion ramp
SHAFT_TOP_Z = RAMP_TOP_Z + 2.8
TIP_Z = SHAFT_TOP_Z + 0.5
TIP_R = SHAFT_R - 0.6

LEG_WALL = 1.8
BORE_R = SHAFT_R - LEG_WALL
BORE_Z0 = FACE_T

SLOT_W = 1.6
SLOT_R = BARB_R + 0.3   # radial reach of the compliance slots
SLOT_Z0 = FACE_T + 0.2

SEGMENTS = 96


def body() -> trimesh.Trimesh:
    profile = np.array(
        [
            [0.0, 0.0],
            [FLANGE_R - RIM_CHAMFER, 0.0],
            [FLANGE_R, RIM_CHAMFER],
            [FLANGE_R, FLANGE_T - 0.4],
            [FLANGE_R - 0.4, FLANGE_T],
            [SHAFT_R, FLANGE_T],
            [SHAFT_R, LEDGE_Z],
            [BARB_R, BARB_Z],
            [SHAFT_R, RAMP_TOP_Z],
            [SHAFT_R, SHAFT_TOP_Z],
            [TIP_R, TIP_Z],
            [0.0, TIP_Z],
        ]
    )
    return trimesh.creation.revolve(profile, sections=SEGMENTS)


def lip() -> trimesh.Trimesh:
    profile = np.array(
        [
            [LIP_RI, FLANGE_T],
            [LIP_RO, FLANGE_T],
            [LIP_RO - 0.25, FLANGE_T + LIP_H],
            [LIP_RI + 0.25, FLANGE_T + LIP_H],
            [LIP_RI, FLANGE_T],
        ]
    )
    return trimesh.creation.revolve(profile, sections=SEGMENTS)


def cutters() -> list[trimesh.Trimesh]:
    top = TIP_Z + 1.0

    bore = trimesh.creation.cylinder(radius=BORE_R, height=top - BORE_Z0, sections=SEGMENTS)
    bore.apply_translation([0.0, 0.0, (BORE_Z0 + top) / 2.0])

    cuts = [bore]
    for angle in (0.0, np.pi / 2.0):
        box = trimesh.creation.box(extents=[SLOT_W, 2 * SLOT_R, top - SLOT_Z0])
        box.apply_transform(trimesh.transformations.rotation_matrix(angle, [0, 0, 1]))
        box.apply_translation([0.0, 0.0, (SLOT_Z0 + top) / 2.0])
        cuts.append(box)
    return cuts


def build() -> trimesh.Trimesh:
    solid = trimesh.boolean.union([body(), lip()], engine="manifold")
    solid = trimesh.boolean.difference([solid] + cutters(), engine="manifold")
    solid.process(validate=True)
    solid.fix_normals()
    return solid


def main() -> None:
    mesh = build()
    out = Path(__file__).resolve().parents[1] / "models" / "pfosten-stopfen-11-5.stl"
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
    print("shaft_dia:", round(2 * SHAFT_R, 3), "barb_dia:", round(2 * BARB_R, 3))
    print("seat_z:", SEAT_Z, "ledge_z:", LEDGE_Z, "total_h:", TIP_Z)


if __name__ == "__main__":
    main()
