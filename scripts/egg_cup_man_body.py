"""Generate the Egg-Cup Man print plate (body + 2 arms + 2 legs).

The body (torso / egg cup) is rebuilt **parametrically** from the measured
geometry of the original model plate `model-sources/egg-cup-man-original.stl`
and then reshaped so the lower half becomes noticeably more spherical
("kugeliger") while the upper cup region - where the arms attach - stays
dimensionally identical to the original.

Arms are taken over unchanged from the original plate.  Legs are taken over
from the original plate but their flat mating face is re-cut against the new
bulged belly so they still sit flush on the rounder body.

Measured reference values (see docs/egg-cup-man-measurements.md):
    outer cup radius        23.24 mm   (diameter 46.48)
    total height            21.98 mm
    egg cavity              ellipsoid a=21.10, b=23.30, centre z=21.60
    cavity floor            z = 2.60
    rim round-over          R = 1.07 centred at (r=22.17, z=21.00)
    original bottom fillet  R = 3.00, wall becomes vertical at z = 3.00

Print orientation: flat foot on the bed, egg cavity pointing up.
"""

from pathlib import Path

import numpy as np
import trimesh
import trimesh.boolean as tb

# ---------------------------------------------------------------------------
# Measured original dimensions (all mm) - high confidence, read from the STL
# ---------------------------------------------------------------------------

CUP_R = 23.24  # outer radius of the cup wall
CAV_A = 21.10  # egg cavity ellipsoid: radial semi-axis
CAV_B = 23.30  # egg cavity ellipsoid: vertical semi-axis
CAV_ZC = 21.60  # egg cavity ellipsoid: centre height
CAV_FLOOR_Z = 2.60  # flat floor of the egg cavity
RIM_Z = 21.00  # height where the rim round-over starts
RIM_R = (CUP_R - CAV_A) / 2.0  # 1.07 - radius of the rim round-over
RIM_RC = (CUP_R + CAV_A) / 2.0  # 22.17 - centre radius of the round-over

# ---------------------------------------------------------------------------
# New lower body shape - the only intentional change to the original body
# ---------------------------------------------------------------------------
# The body never gets wider than the original cup wall.  Below BELLY_TOP_Z the
# outer wall rounds *inwards* along an ellipse that is tangent to the straight
# wall at BELLY_TOP_Z, so the torso reads as the lower half of a ball with no
# outward bulge and no crease:
#     r(z) = CUP_R * sqrt(1 - ((BELLY_TOP_Z - z) / BELLY_B) ** 2)
BELLY_TOP_Z = 14.00  # height where the round-off starts (vertical tangent)
FOOT_R = 17.00  # radius of the flat stand face at z = 0 - keeps overhang < 50 deg

# ---------------------------------------------------------------------------
# Leg fitting
# ---------------------------------------------------------------------------
LEG_SPREAD_X = 9.46  # +/-X centre distance of the two legs (from original plate)
LEG_CONTACT_Z = 3.00  # height where the flat leg meets the rounded lower body
LEG_BITE = 2.50  # how deep the leg is pushed into the body before the union
ARM_Z = 1.00  # height of the arm's lowest point above the table
ARM_BITE = 1.50  # how deep the arm shoulder is pushed into the cup wall

SEGMENTS = 128
ARC_STEPS = 48

SRC_PLATE = Path(__file__).resolve().parents[1] / "model-sources" / "egg-cup-man-original.stl"
OUT_STL = Path(__file__).resolve().parents[1] / "models" / "egg-cup-man-body.stl"


# ---------------------------------------------------------------------------
# Profile helpers
# ---------------------------------------------------------------------------

def _belly_b() -> float:
    """Vertical semi-axis so the round-off reaches FOOT_R at z = 0."""
    inner = 1.0 - (FOOT_R / CUP_R) ** 2
    if inner <= 0.0:
        raise ValueError("FOOT_R must be smaller than CUP_R")
    return BELLY_TOP_Z / float(np.sqrt(inner))


BELLY_B = _belly_b()


def belly_radius(z):
    """Outer radius of the rounded lower body at height z.

    Tangent to the straight cup wall at BELLY_TOP_Z, curving inwards below it.
    """
    t = (BELLY_TOP_Z - np.asarray(z, dtype=float)) / BELLY_B
    return CUP_R * np.sqrt(np.clip(1.0 - t * t, 0.0, None))


def cavity_radius(z):
    """Radius of the egg cavity ellipsoid at height z."""
    t = (np.asarray(z, dtype=float) - CAV_ZC) / CAV_B
    return CAV_A * np.sqrt(np.clip(1.0 - t * t, 0.0, None))


# ---------------------------------------------------------------------------
# Body construction
# ---------------------------------------------------------------------------

def body_profile() -> np.ndarray:
    """Closed (r, z) profile of the hollow body, both ends on the Z axis."""
    pts: list[tuple[float, float]] = []

    # 1. flat foot, from the axis outwards
    pts.append((0.0, 0.0))
    pts.append((FOOT_R, 0.0))

    # 2. rounded lower body, tangent to the straight wall at BELLY_TOP_Z
    for z in np.linspace(0.0, BELLY_TOP_Z, ARC_STEPS)[1:]:
        pts.append((float(belly_radius(z)), float(z)))

    # 3. straight original cup wall up to the rim round-over
    pts.append((CUP_R, RIM_Z))

    # 4. rim round-over (outer -> top -> inner), unchanged from the original
    for ang in np.linspace(0.0, np.pi, ARC_STEPS)[1:]:
        pts.append((RIM_RC + RIM_R * float(np.cos(ang)),
                    RIM_Z + RIM_R * float(np.sin(ang))))

    # 5. egg cavity ellipsoid downwards to the cavity floor
    for z in np.linspace(RIM_Z, CAV_FLOOR_Z, ARC_STEPS)[1:]:
        pts.append((float(cavity_radius(z)), float(z)))

    # 6. flat cavity floor back to the axis
    pts.append((0.0, CAV_FLOOR_Z))

    return np.asarray(pts, dtype=float)


def build_body() -> trimesh.Trimesh:
    body = trimesh.creation.revolve(body_profile(), sections=SEGMENTS)
    body.merge_vertices()
    body.fix_normals()
    return body


# ---------------------------------------------------------------------------
# Original plate parts
# ---------------------------------------------------------------------------

def load_original_parts() -> dict:
    """Split the original plate into body / arms / legs by their footprint."""
    plate = trimesh.load(SRC_PLATE, force="mesh")
    parts = list(plate.split(only_watertight=False))

    body_idx = int(np.argmax([p.volume for p in parts]))
    rest = [p for i, p in enumerate(parts) if i != body_idx]

    # arms are the slim ones (Y extent ~6 mm), legs have a long foot (~23 mm)
    arms = [p for p in rest if p.extents[1] < 12.0]
    legs = [p for p in rest if p.extents[1] >= 12.0]
    if len(arms) != 2 or len(legs) != 2:
        raise RuntimeError(f"unexpected plate layout: {len(arms)} arms, {len(legs)} legs")

    return {"body": parts[body_idx], "arms": arms, "legs": legs}


def _to_origin(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Copy with min-corner at the origin."""
    out = mesh.copy()
    out.apply_translation(-out.bounds[0])
    return out


def place_leg(leg: trimesh.Trimesh, sign: int) -> trimesh.Trimesh:
    """Move a leg into its sitting assembly position.

    The egg-cup man sits: the cup stands on the table, both legs lie flat on
    the table pointing forward (-Y) and the foot rises vertically at the far
    end.  On the source plate the leg already has that pose, but pointing +Y,
    so it is mirrored and pushed LEG_BITE into the rounded lower body.
    """
    work = leg.copy()
    work.apply_scale([sign, -1.0, 1.0])  # face forward, mirror left/right
    work.fix_normals()
    work = _to_origin(work)

    # after mirroring the hip end is the max-Y end, the foot sits at y = 0
    hip_y = float(work.bounds[1][1])
    x_off = sign * LEG_SPREAD_X - work.extents[0] / 2.0

    # contact radius halfway up the flat part of the leg
    r_contact = float(belly_radius(LEG_CONTACT_Z))
    y_body = float(np.sqrt(max(r_contact ** 2 - (sign * LEG_SPREAD_X) ** 2, 0.0)))

    work.apply_translation([x_off, -(y_body - LEG_BITE) - hip_y, 0.0])
    return work


def place_arm(arm: trimesh.Trimesh, sign: int) -> trimesh.Trimesh:
    """Move an arm into its assembly position on the upper cup wall.

    The arm's flat shoulder face (its min-X face, at shoulder height 15-20 mm)
    is pushed ARM_BITE into the straight cup wall.  ``sign`` mirrors the arm
    onto the opposite side.
    """
    work = _to_origin(arm)
    work.apply_translation([CUP_R - ARM_BITE, -work.extents[1] / 2.0, ARM_Z])

    if sign < 0:
        work.apply_scale([-1.0, 1.0, 1.0])
        work.fix_normals()

    return work


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def assemble(body, arms, legs) -> trimesh.Trimesh:
    """Union body, arms and legs into one watertight figure."""
    figure = tb.union([body, *legs, *arms], engine="manifold")
    figure.merge_vertices()
    figure.fix_normals()

    # drop the whole figure onto the bed and centre it in XY
    figure.apply_translation([0.0, 0.0, -float(figure.bounds[0][2])])
    centre = figure.bounds.mean(axis=0)
    figure.apply_translation([-centre[0], -centre[1], 0.0])
    return figure


# ---------------------------------------------------------------------------
# Validation stats
# ---------------------------------------------------------------------------

def print_stats(mesh: trimesh.Trimesh, path: Path) -> None:
    print("file:              ", path)
    print("facets:            ", len(mesh.faces))
    print("bounds:            ", np.round(mesh.bounds, 3).tolist())
    print("extents:           ", np.round(mesh.extents, 3).tolist())
    print("watertight:        ", mesh.is_watertight)
    print("winding_consistent:", mesh.is_winding_consistent)
    print("volume_mm3:        ", round(mesh.volume, 3))
    print("euler:             ", mesh.euler_number)
    print("degenerate:        ", int(np.count_nonzero(mesh.area_faces <= 1e-12)))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def max_overhang_deg() -> float:
    """Steepest wall angle from vertical on the rounded lower body."""
    z = np.linspace(0.0, BELLY_TOP_Z, 400)
    r = belly_radius(z)
    slope = np.abs(np.gradient(r, z))
    return float(np.degrees(np.arctan(slope.max())))


def main() -> None:
    original = load_original_parts()
    body = build_body()

    legs = [place_leg(original["legs"][0], +1),
            place_leg(original["legs"][0], -1)]
    arms = [place_arm(original["arms"][0], +1),
            place_arm(original["arms"][0], -1)]

    figure = assemble(body, arms, legs)

    OUT_STL.parent.mkdir(parents=True, exist_ok=True)
    figure.export(OUT_STL, file_type="stl_ascii")

    print(f"round-off starts:   z = {BELLY_TOP_Z:.2f} mm (tangent to the wall)")
    print(f"ellipse semi-axis:  b = {BELLY_B:.3f} mm")
    print(f"foot radius:        {FOOT_R:.3f} mm (diameter {2 * FOOT_R:.1f})")
    print(f"max outer radius:   {CUP_R:.3f} mm (unchanged)")
    print(f"max wall overhang:  {max_overhang_deg():.1f} deg from vertical")
    print_stats(figure, OUT_STL)


if __name__ == "__main__":
    main()
