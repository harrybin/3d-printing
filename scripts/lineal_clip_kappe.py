"""Generate the snap-fit clip cap for the two holes at the end of the steel ruler.

Print orientation: plate flat on the bed, snap pegs pointing up (+Z).
In use the part is flipped so the plate lies on top of the ruler.
"""

from pathlib import Path

import numpy as np
import trimesh

# --- measured / derived parameters (mm) -------------------------------------
RULER_WIDTH = 14.5      # from image scaling
HOLE_DIA = 2.5          # from image scaling
HOLE_SPACING = 9.1      # centre-to-centre, from image scaling
MATERIAL_T = 2.0        # user supplied

PLATE_X = RULER_WIDTH   # across the ruler width
PLATE_Y = 7.0           # along the ruler (narrow strip)
PLATE_Z = 2.0

PRESS_CLEAR = 0.20      # press-fit baseline for the 0.4 mm nozzle profile
PEG_R = (HOLE_DIA - PRESS_CLEAR) / 2.0    # 1.15
BARB_R = PEG_R + 0.35                     # retaining lip
TIP_R = 0.55
LEAD_IN = 1.4           # axial length of the insertion cone

SLOT_W = 0.6            # compliance slot -> two spring legs per peg
SLOT_INTO_PLATE = 0.6

SEGMENTS = 64


def peg(cx: float) -> trimesh.Trimesh:
    z_ledge = PLATE_Z + MATERIAL_T
    z_tip = z_ledge + LEAD_IN

    profile = np.array(
        [
            [0.0, 0.0],
            [PEG_R, 0.0],
            [PEG_R, z_ledge],
            [BARB_R, z_ledge],
            [TIP_R, z_tip],
            [0.0, z_tip],
        ]
    )
    body = trimesh.creation.revolve(profile, sections=SEGMENTS)
    body.apply_translation([cx, 0.0, 0.0])
    return body


def slot(cx: float) -> trimesh.Trimesh:
    z0 = PLATE_Z - SLOT_INTO_PLATE
    z1 = PLATE_Z + MATERIAL_T + LEAD_IN + 0.5
    box = trimesh.creation.box(extents=[2 * BARB_R + 1.0, SLOT_W, z1 - z0])
    box.apply_translation([cx, 0.0, (z0 + z1) / 2.0])
    return box


def build() -> trimesh.Trimesh:
    plate = trimesh.creation.box(extents=[PLATE_X, PLATE_Y, PLATE_Z])
    plate.apply_translation([0.0, 0.0, PLATE_Z / 2.0])

    xs = (-HOLE_SPACING / 2.0, HOLE_SPACING / 2.0)
    solid = trimesh.boolean.union([plate] + [peg(x) for x in xs], engine="manifold")
    solid = trimesh.boolean.difference([solid] + [slot(x) for x in xs], engine="manifold")

    solid.process(validate=True)
    solid.fix_normals()
    return solid


def main() -> None:
    mesh = build()
    out = Path(__file__).resolve().parents[1] / "models" / "lineal-clip-kappe.stl"
    out.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(out, file_type="stl_ascii")

    print("file:", out)
    print("facets:", len(mesh.faces))
    print("bounds:", mesh.bounds.tolist())
    print("extents:", mesh.extents.tolist())
    print("watertight:", mesh.is_watertight)
    print("winding_consistent:", mesh.is_winding_consistent)
    print("volume_mm3:", round(mesh.volume, 3))
    print("euler:", mesh.euler_number)
    print("degenerate:", int(np.count_nonzero(mesh.area_faces <= 1e-12)))


if __name__ == "__main__":
    main()
