"""Generate the replacement drive-coupling insert for a pepper mill grinding
mechanism ("Mahlwerk", CrushGrind-style ceramic grinder).

Function: the pentagon ("Fuenfkant") drive shaft of the mill is pushed
centrically all the way through the insert. The lower cylindrical shaft body
registers/guides inside the Mahlwerk cavity; the thicker head at the top
carries four half-round lobes (90 degrees apart) that key into the Mahlwerk's
scalloped socket (visible as a 4-lobed recess around the centre bore, stamped
"CRUSHGRIND CO") and prevent the insert from spinning freely inside the
housing. Turning the pentagon shaft therefore turns the insert, and the
insert's lobes carry that torque into the Mahlwerk housing/burr.

Print orientation: insert axis vertical (+Z), head up, as modeled here.

Measurements (see model-sources/pfeffermuehle-mahlwerk/):
- overall Mahlwerk height:            17.01 mm measured (tile 04) -> user-specified 17 mm
- Fuenfkant shaft, across flats:       5.75 mm measured (tile 00)
- old insert max outer diameter:      12.59 mm measured (tile 05)
- old insert broken-fragment bore:     7.06 mm measured (tile 01) -- this is the
  ENLARGED/damaged bore after the wall fractured, not a design target; the
  user confirmed the original insert kept >= 1 mm wall everywhere, so the new
  pentagon bore is sized from the shaft measurement + clearance instead.
- broken fragment wall thickness:      2.12 mm measured (tile 06)
- 4-lobe scalloped socket, 90 degrees apart: seen on tile 02 ("CRUSHGRIND CO")

Fit-critical dimensions that are DESIGN CHOICES (not directly measured), see
docs/pfeffermuehle-mahlwerk-einsatz-messungen.md for the full writeup:
- shaft/head diameters and the height split are sized to keep >= 1 mm wall
  around the pentagon bore everywhere (user requirement), not measured off a
  photo.
"""

import tempfile
from math import cos, radians
from pathlib import Path

import numpy as np
import trimesh
from build123d import BuildPart, BuildSketch, Plane, RegularPolygon, export_stl, extrude

# --- measured parameters (mm) ------------------------------------------------
FUENFKANT_SW = 5.75          # Fuenfkant across-flats, measured (tile 00)
OLD_INSERT_OD = 12.59        # old insert max outer diameter, measured (tile 05)
H_TOTAL = 17.0               # Mahlwerk / insert overall height, user-specified

# --- design choices (mm) -----------------------------------------------------
CLEARANCE_SLIDING = 0.30     # general/sliding clearance baseline (0.4 mm nozzle)
MIN_WALL = 1.0               # user requirement: >= 1 mm wall everywhere

PENT_SW = FUENFKANT_SW + 0.25            # 6.00 mm pentagon bore, across flats
PENT_R = PENT_SW / (1.0 + cos(radians(36.0)))   # circumradius for RegularPolygon
PENT_DIAGONAL = 2.0 * PENT_R * cos(radians(18.0))  # widest vertex-vertex span

SHAFT_D = 9.0                 # lower cylindrical shaft, majority of height
SHAFT_H = 12.0
HEAD_H = H_TOTAL - SHAFT_H    # 5.0 mm

# Head is built as 4 overlapping cylinders ("Nasen"), 90 degrees apart, with
# NO separate smaller core cylinder. Overlapping lobes keep the outer contour
# a continuous run of arcs (a "quatrefoil"): the tip radius (through a lobe
# centre) and the waist radius (on the 45-degree bisector between two lobes)
# are both defined by lobe-circle geometry, so the rim connecting the
# roundings is smooth everywhere instead of dropping to a plain cylindrical
# core between lobes.
LOBE_TIP_D = 12.30             # tip-to-tip envelope, ~0.29 mm clearance under the
                                # 12.59 mm measured socket (general-fit baseline)
LOBE_COUNT = 4
LOBE_CENTER_R = 2.7            # lobe-centre offset from axis, chosen so adjacent
                                # lobes overlap (continuous rim) while keeping
                                # >= 1 mm wall at the 45-degree waist
LOBE_R = LOBE_TIP_D / 2.0 - LOBE_CENTER_R   # radius of each half-round lobe


def _quatrefoil_waist_radius() -> float:
    """Distance from the axis to the head outline on the 45-degree bisector
    between two adjacent lobe centres (the narrowest point of the connected
    rim)."""
    c45 = cos(radians(45.0))
    return LOBE_CENTER_R * c45 + (LOBE_R ** 2 - 0.5 * LOBE_CENTER_R ** 2) ** 0.5

SEGMENTS = 96


def _wall_mm(outer_radius: float) -> float:
    return outer_radius - PENT_DIAGONAL / 2.0


def _pentagon_solid_mesh() -> trimesh.Trimesh:
    """Pentagon prism (the Fuenfkant through-bore) via build123d, full height."""
    margin = 1.0
    with BuildPart() as bp:
        with BuildSketch(Plane.XY.offset(-margin)):
            RegularPolygon(radius=PENT_R, side_count=5)
        extrude(amount=H_TOTAL + 2 * margin)

    with tempfile.TemporaryDirectory() as td:
        stl_path = Path(td) / "pentagon.stl"
        export_stl(bp.part, str(stl_path))
        mesh = trimesh.load_mesh(stl_path)
    return mesh


def _body_mesh() -> trimesh.Trimesh:
    shaft = trimesh.creation.cylinder(radius=SHAFT_D / 2.0, height=SHAFT_H, sections=SEGMENTS)
    shaft.apply_translation([0.0, 0.0, SHAFT_H / 2.0])

    lobes = []
    for k in range(LOBE_COUNT):
        angle = radians(360.0 / LOBE_COUNT * k)
        cx = LOBE_CENTER_R * np.cos(angle)
        cy = LOBE_CENTER_R * np.sin(angle)
        lobe = trimesh.creation.cylinder(radius=LOBE_R, height=HEAD_H, sections=SEGMENTS)
        lobe.apply_translation([cx, cy, SHAFT_H + HEAD_H / 2.0])
        lobes.append(lobe)

    body = trimesh.boolean.union([shaft] + lobes, engine="manifold")
    return body


def build() -> trimesh.Trimesh:
    body = _body_mesh()
    pentagon = _pentagon_solid_mesh()
    solid = trimesh.boolean.difference([body, pentagon], engine="manifold")

    solid.vertices = np.round(solid.vertices, 3)
    solid.merge_vertices()
    solid.update_faces(solid.unique_faces())
    solid.update_faces(solid.nondegenerate_faces())
    solid.process(validate=True)
    solid.fix_normals()
    return solid


def main() -> None:
    waist_r = _quatrefoil_waist_radius()
    print("pentagon bore across-flats (target):", round(PENT_SW, 3), "mm")
    print("pentagon widest diagonal:", round(PENT_DIAGONAL, 3), "mm")
    print("wall at shaft (r=%.2f mm):" % (SHAFT_D / 2.0), round(_wall_mm(SHAFT_D / 2.0), 3), "mm")
    print("head lobe tip radius:", round(LOBE_TIP_D / 2.0, 3), "mm")
    print("head quatrefoil waist radius (45deg, connecting rim):", round(waist_r, 3), "mm")
    print("wall at head waist:", round(_wall_mm(waist_r), 3), "mm")
    assert _wall_mm(SHAFT_D / 2.0) >= MIN_WALL, "shaft wall below required minimum"
    assert _wall_mm(waist_r) >= MIN_WALL, "head waist wall below required minimum"
    assert waist_r > SHAFT_D / 2.0, "lobes do not overlap enough to stay outside the shaft radius"
    assert LOBE_TIP_D < OLD_INSERT_OD, "lobe tip envelope exceeds measured socket size"

    mesh = build()
    out = Path(__file__).resolve().parents[1] / "models" / "pfeffermuehle-mahlwerk-einsatz.stl"
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
