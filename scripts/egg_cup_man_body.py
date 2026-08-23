"""Generate the sitting Egg-Cup Man as one watertight solid.

The torso (egg cup) is rebuilt **parametrically** from the measured geometry of
the original model plate `model-sources/egg-cup-man-original.stl`, with the
lower half rounded inwards so it reads as a ball bottom.  The upper cup region
- rim, wall and egg cavity - stays dimensionally identical to the original.

Arms and legs are generated as humanoid sphere sweeps with real ball joints
(shoulder / elbow / wrist and hip / knee / ankle) instead of the straight stubs
of the original plate.

Pose: the figure sits.  The cup stands on the table, both legs reach forward
(-Y) with a bent knee and the feet standing upright, and the arms hang down at
the sides with a bent elbow.

Measured reference values (see docs/egg-cup-man-measurements.md):
    outer cup radius        23.24 mm   (diameter 46.48)
    total cup height        21.98 mm
    egg cavity              ellipsoid a=21.10, b=23.30, centre z=21.60
    cavity floor            z = 2.60
    rim round-over          R = 1.07 centred at (r=22.17, z=21.00)
    original bottom fillet  R = 3.00, wall becomes vertical at z = 3.00

Print orientation: as generated - the figure already sits flat on the bed.
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

SEGMENTS = 128
ARC_STEPS = 48

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


CAVITY_CLEAR_H = 5.0  # how far the cavity cutter reaches above the rim
CAVITY_MARGIN = 0.20  # cutter oversize, keeps limbs clear of the cavity wall


def cavity_profile(margin: float = CAVITY_MARGIN) -> np.ndarray:
    """Closed (r, z) profile of the egg cavity as a *solid* cutter.

    The cutter is used on the limbs only, never on the body, and is grown by
    ``margin`` so no limb surface ends up coplanar with the cavity wall.
    """
    pts: list[tuple[float, float]] = [(0.0, CAV_FLOOR_Z - margin)]
    for z in np.linspace(CAV_FLOOR_Z - margin, RIM_Z, ARC_STEPS):
        pts.append((float(cavity_radius(z)) + margin, float(z)))
    pts.append((CAV_A + margin, RIM_Z + CAVITY_CLEAR_H))
    pts.append((0.0, RIM_Z + CAVITY_CLEAR_H))
    return np.asarray(pts, dtype=float)


def build_cavity(margin: float = CAVITY_MARGIN) -> trimesh.Trimesh:
    cav = trimesh.creation.revolve(cavity_profile(margin), sections=SEGMENTS)
    cav.merge_vertices()
    cav.fix_normals()
    return cav


# ---------------------------------------------------------------------------
# Humanoid limbs - parametric sphere sweeps with real joints
# ---------------------------------------------------------------------------
# Each limb is a chain of nodes (x, y, z, radius) in body coordinates:
# the body axis is at the origin, the table is z = 0 and the figure looks
# towards -Y.  The chain is resampled with a Catmull-Rom spline (positions and
# radii) and then swept with spheres, so joints read as smooth bends instead of
# faceted hinges.
#
# The first node of every limb is a *root flare*: it sits deep inside the body
# and is noticeably fatter than the joint that follows.  Where that fat sphere
# breaks through the body wall it widens the limb into a collar, which is what
# makes the transition to the body look faired instead of glued on.

ARM_NODES = [
    (20.6, 0.0, 16.0, 5.0),    # root flare - buried in the cup wall
    (23.6, -0.2, 15.4, 4.4),   # collar - breaks through the wall
    (26.6, -1.0, 13.6, 3.8),   # shoulder
    (30.4, -3.0, 9.8, 3.4),    # elbow
    (30.2, -5.5, 6.0, 3.0),    # forearm - drops almost vertically
    (29.6, -7.0, 3.6, 2.8),    # wrist
    (29.2, -8.5, 3.2, 3.2),    # hand - props on the table
]

LEG_NODES = [
    (7.2, -10.2, 6.2, 6.0),    # root flare - buried in the rounded lower body
    (8.4, -12.4, 6.0, 5.8),    # inner collar
    (9.6, -15.0, 5.9, 5.45),   # outer collar - breaks through the wall
    (10.6, -18.4, 5.9, 5.0),   # hip
    (11.0, -24.0, 6.6, 4.8),   # thigh rising towards the knee
    (11.4, -30.5, 7.4, 4.6),   # knee - the bend of the sitting pose
    (11.5, -37.0, 5.3, 4.1),   # shin dropping back to the table
    (11.5, -42.5, 3.8, 3.6),   # ankle
    (11.5, -44.0, 8.0, 4.2),   # instep - the foot stands upright
    (11.5, -44.3, 12.5, 4.4),  # toe cap
]

SPHERE_SUBDIV = 3  # icosphere subdivisions used for the limb sweeps
SPLINE_SAMPLES = 8  # spline samples per node interval


def _sphere(centre, radius: float) -> trimesh.Trimesh:
    s = trimesh.creation.icosphere(subdivisions=SPHERE_SUBDIV, radius=radius)
    s.apply_translation(np.asarray(centre, dtype=float))
    return s


def spline_nodes(nodes, samples: int = SPLINE_SAMPLES) -> np.ndarray:
    """Catmull-Rom resampling of a limb chain, radii included.

    Radii are clipped to the input range so the spline cannot overshoot into a
    negative or ballooning radius at a sharp bend (the ankle in particular).
    """
    P = np.asarray(nodes, dtype=float)
    ext = np.vstack([2.0 * P[0] - P[1], P, 2.0 * P[-1] - P[-2]])

    out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for t in np.linspace(0.0, 1.0, samples, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * (2.0 * p1
                              + (-p0 + p2) * t
                              + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
                              + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3))
    out.append(P[-1])

    res = np.asarray(out, dtype=float)
    res[:, 3] = np.clip(res[:, 3], P[:, 3].min(), P[:, 3].max())
    return res


def limb_segments(nodes, sign: int) -> list:
    """Convex-hull segments of one splined limb, mirrored to the given side."""
    pts = spline_nodes(nodes).copy()
    pts[:, 0] *= sign
    segments = []
    for a, b in zip(pts[:-1], pts[1:]):
        pair = trimesh.util.concatenate([_sphere(a[:3], a[3]), _sphere(b[:3], b[3])])
        segments.append(pair.convex_hull)
    return segments


def limb_check(nodes, name: str) -> None:
    """Warn if the splined limb dips below the table or misses the body."""
    pts = spline_nodes(nodes)
    worst = float(np.min(pts[:, 2] - pts[:, 3]))
    if worst < -0.01:
        print(f"  WARNING {name}: spline sinks {-worst:.2f} mm below the table")

    intrusion = 0.0
    for x, y, z, r in pts:
        if CAV_FLOOR_Z <= z <= RIM_Z:
            gap = float(cavity_radius(z)) - (float(np.hypot(x, y)) - r)
            intrusion = max(intrusion, gap)
    if intrusion > 0.0:
        print(f"  note {name}: reaches {intrusion:.2f} mm into the cavity "
              f"- trimmed by the cavity cut")

    root = nodes[0]
    protrusion = -np.inf
    for x, y, z, r in pts:
        z_cap = min(float(z), BELLY_TOP_Z)
        wall = float(belly_radius(z_cap)) if z < BELLY_TOP_Z else CUP_R
        if float(np.hypot(x, y)) > wall:
            break  # past the wall - this is the free limb, not the collar
        protrusion = max(protrusion, float(np.hypot(x, y)) + r - wall)
    print(f"  {name} root: flare R={root[3]:.2f}, "
          f"collar sticks out {protrusion:+.2f} mm past the body wall")


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def assemble(body, limbs) -> trimesh.Trimesh:
    """Trim the limbs against the egg cavity, then union everything."""
    limb_solid = tb.union(limbs, engine="manifold")
    limb_solid = tb.difference([limb_solid, build_cavity()], engine="manifold")

    figure = tb.union([body, limb_solid], engine="manifold")
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
    body = build_body()

    limb_check(ARM_NODES, "arm")
    limb_check(LEG_NODES, "leg")

    limbs = []
    for sign in (+1, -1):
        limbs += limb_segments(ARM_NODES, sign)
        limbs += limb_segments(LEG_NODES, sign)

    figure = assemble(body, limbs)

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
