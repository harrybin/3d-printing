"""Generate the replacement drive-coupling insert for a pepper mill grinding
mechanism ("Mahlwerk", CrushGrind-style ceramic grinder).

Function: the pentagon ("Fuenfkant") drive shaft of the mill is pushed
centrically all the way through the insert. The lower/most of the shaft is a
plain cylinder that registers/guides inside the Mahlwerk cavity. Near the top,
four rounded lobes (90 degrees apart) run a measured 7.08 mm up the shaft,
including the collar, and key into the Mahlwerk's scalloped socket
(visible as a 4-lobed recess around the centre bore, stamped "CRUSHGRIND CO"),
preventing the insert from spinning freely inside the housing. A round
flange/disc caps the very top, above the ribs. Turning the pentagon shaft
therefore turns the insert, and the insert's ribs carry that torque into the
Mahlwerk housing/burr.

This geometry was corrected after 2 additional fragment photos showed the
actual broken insert: a round top collar/disc plus four long ribs. The user
confirmed that the rib ends must be rounded like the original scalloped
socket, rather than flat-faced.

Print orientation: insert axis vertical (+Z), flange up, as modeled here.

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
- rib ("Nasen") length/height:          7.08 mm, user-measured on the fragment

Fit-critical dimensions that are DESIGN CHOICES (not directly measured), see
docs/pfeffermuehle-mahlwerk-einsatz-messungen.md for the full writeup:
- shaft/rib/flange diameters and the height split are sized to keep >= 1 mm
  wall around the pentagon bore everywhere (user requirement), not measured
  off a photo.
- flange thickness (2.0 mm): user-confirmed default assumption, not measured.
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

SHAFT_D = 9.0                  # plain cylindrical shaft diameter, full height
                                # under the collar (registers/guides in the
                                # Mahlwerk's round bore)

NASEN_LENGTH_MEASURED = 7.08     # user-measured "Nasen" length INCLUDING the
                                  # collar (Kragen) it measured up to
COLLAR_H = 2.0                   # collar ("Kragen") thickness, user-confirmed
                                  # default assumption (not separately measured)
RIB_H = NASEN_LENGTH_MEASURED - COLLAR_H   # 5.08 mm lobe height, excluding
                                            # the collar itself
COLLAR_D = 12.30                # collar outer diameter, ~0.29 mm clearance
                                 # under the 12.59 mm measured old-insert OD
                                 # (general-fit baseline)

LOBE_COUNT = 4
LOBE_TIP_R = COLLAR_D / 2.0       # lobe tips are flush with the collar edge
# Each circular pocket in the Mahlwerk is discrete. Therefore the four lobe
# circles must remain separate; only each individual lobe overlaps the shaft
# core to transmit torque. Centres lie on the shaft radius, leaving clear
# cylindrical arcs between the lobes.
LOBE_CENTER_R = SHAFT_D / 2.0
LOBE_R = LOBE_TIP_R - LOBE_CENTER_R

# Height split, bottom (z=0) to top (z=H_TOTAL):
#   [0, SHAFT_PLAIN_H)                 -> plain shaft, Ø SHAFT_D
#   [SHAFT_PLAIN_H, SHAFT_PLAIN_H+RIB_H) -> lobe zone: shaft core + 4 lobes
#   [H_TOTAL-COLLAR_H, H_TOTAL)         -> collar ("Kragen"), Ø COLLAR_D
SHAFT_PLAIN_H = H_TOTAL - COLLAR_H - RIB_H   # 9.92 mm


def _wall_mm(outer_radius: float) -> float:
    return outer_radius - PENT_DIAGONAL / 2.0


SEGMENTS = 96


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


def _lobe(angle_deg: float) -> trimesh.Trimesh:
    """One rounded torque-transmitting lobe ("Nase") below the collar."""
    angle = radians(angle_deg)
    lobe = trimesh.creation.cylinder(radius=LOBE_R, height=RIB_H, sections=SEGMENTS)
    lobe.apply_translation([
        LOBE_CENTER_R * np.cos(angle),
        LOBE_CENTER_R * np.sin(angle),
        SHAFT_PLAIN_H + RIB_H / 2.0,
    ])
    return lobe


def _body_mesh() -> trimesh.Trimesh:
    # Full-height shaft core: plain cylindrical shaft plus the rib-zone core,
    # all at the same diameter, so the ribs simply add material on top of a
    # continuous core instead of needing a separate join.
    core_h = SHAFT_PLAIN_H + RIB_H
    core = trimesh.creation.cylinder(radius=SHAFT_D / 2.0, height=core_h, sections=SEGMENTS)
    core.apply_translation([0.0, 0.0, core_h / 2.0])

    lobes = [_lobe(360.0 / LOBE_COUNT * k) for k in range(LOBE_COUNT)]

    collar = trimesh.creation.cylinder(radius=COLLAR_D / 2.0, height=COLLAR_H, sections=SEGMENTS)
    collar.apply_translation([0.0, 0.0, H_TOTAL - COLLAR_H / 2.0])

    body = trimesh.boolean.union([core] + lobes + [collar], engine="manifold")
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
    rib_inner_r = SHAFT_D / 2.0
    print("pentagon bore across-flats (target):", round(PENT_SW, 3), "mm")
    print("pentagon widest diagonal:", round(PENT_DIAGONAL, 3), "mm")
    print("wall at plain shaft (r=%.2f mm):" % rib_inner_r, round(_wall_mm(rib_inner_r), 3), "mm")
    print("lobe tip radius (= collar radius):", round(LOBE_TIP_R, 3), "mm")
    print("wall at lobe tip / collar (r=%.2f mm):" % LOBE_TIP_R, round(_wall_mm(LOBE_TIP_R), 3), "mm")
    print("lobe centre radius / lobe radius:", LOBE_CENTER_R, "/", LOBE_R, "mm")
    print("shaft_plain_h / lobe_h / collar_h:", round(SHAFT_PLAIN_H, 3), "/", RIB_H, "/", COLLAR_H, "mm  (sum=%.2f)" % (SHAFT_PLAIN_H + RIB_H + COLLAR_H))
    assert _wall_mm(rib_inner_r) >= MIN_WALL, "plain shaft wall below required minimum"
    assert _wall_mm(LOBE_TIP_R) >= MIN_WALL, "lobe/collar wall below required minimum"
    assert COLLAR_D < OLD_INSERT_OD, "collar envelope exceeds measured socket size"
    assert SHAFT_PLAIN_H > 0, "rib_h + collar_h exceed the overall height"

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
