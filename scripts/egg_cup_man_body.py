"""Generate the rounded-bottom body (torso) of the Egg-Cup Man.

The torso is shaped like a rounded pear / egg:
- The body is built as a revolution profile:
    * Bottom: a hemisphere-like rounded cap (flattened ellipse) cut flat for stand
    * Middle: gently bulging waist up to the shoulder radius
    * Top: straight cylinder for the egg-cup
- Arm sockets: two horizontal cylindrical holes on the sides at ARM_Z.
- Leg sockets: two downward-angled cylindrical holes at the base.

All key dimensions are declared as module-level constants and cross-referenced in
docs/egg-cup-man-measurements.md.  Every fit-critical number is flagged as an
estimate until confirmed by a test print.

Print orientation: flat bottom on the bed, egg-cup cavity pointing up.
"""

from pathlib import Path

import numpy as np
import trimesh
import trimesh.creation as tc
import trimesh.boolean as tb

# ---------------------------------------------------------------------------
# Parameters (all mm) – see docs/egg-cup-man-measurements.md
# ---------------------------------------------------------------------------

# Cup section
CUP_INNER_R   = 19.0    # inner radius of egg cavity (ESTIMATE)
CUP_DEPTH     = 22.0    # depth of egg cavity (ESTIMATE)
WALL_T        = 3.0     # wall thickness

# Overall body proportions
BODY_HEIGHT   = 65.0                    # total height of the torso (ESTIMATE)
BODY_R_MAX    = 25.0                    # max outer radius (at the equator/waist)  (ESTIMATE)
BODY_R_TOP    = CUP_INNER_R + WALL_T    # outer radius at the top of the cup section

# Lower rounded belly: ellipsoidal cap
# The belly occupies the bottom BELLY_H mm of the body.
# It is formed by scaling a hemisphere to have XY-radius=BODY_R_MAX and height=BELLY_H.
BELLY_H       = 30.0    # height of the rounded belly section (ESTIMATE)
FLAT_BOTTOM   = 5.0     # mm to cut off the very bottom → flat stand ring

# Arm sockets (horizontal, pointing ±X)
ARM_DIAM      = 6.0     # socket diameter (ESTIMATE)
ARM_DEPTH     = 6.0     # socket depth into body (ESTIMATE)
ARM_Z         = 40.0    # height above body bottom (ESTIMATE)
PRESS_CLEAR   = 0.20    # press-fit clearance for 0.4 mm nozzle profile

# Leg sockets (pointing downward, angled outward)
LEG_DIAM      = 8.0     # socket diameter (ESTIMATE)
LEG_DEPTH     = 8.0     # socket depth (ESTIMATE)
LEG_SPREAD_X  = 11.0    # ±X centre-of-socket from body axis (ESTIMATE)
LEG_Z         = 8.0     # socket centre height above body bottom (ESTIMATE)
LEG_ANGLE_DEG = 25.0    # downward tilt of leg socket axis (ESTIMATE)

SEGMENTS = 80

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cylinder(radius: float, height: float, sections: int = SEGMENTS) -> trimesh.Trimesh:
    cyl = tc.cylinder(radius=radius, height=height, sections=sections)
    return cyl


def _revolve_profile(profile: np.ndarray) -> trimesh.Trimesh:
    """Revolve a 2-D profile [[r,z], ...] 360° around the Z axis."""
    return trimesh.creation.revolve(profile, sections=SEGMENTS)


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build() -> trimesh.Trimesh:
    # ------------------------------------------------------------------
    # 1. Build outer shell as a revolved profile (r, z) – origin at bottom
    # ------------------------------------------------------------------
    # Profile points (r, z) going counter-clockwise from bottom-centre outward:
    #   bottom flat ring  →  belly curve  →  shoulder  →  cup top
    # The belly uses a quarter-ellipse arc parameterised in t ∈ [0, π/2].

    n_arc = 24  # arc sample points

    # Quarter-ellipse belly: XY radius 0→BODY_R_MAX over the full belly height.
    # The belly profile starts at the bottom centre (r=0, z=0) and arcs outward.
    t = np.linspace(0, np.pi / 2, n_arc)
    belly_r = BODY_R_MAX * np.sin(t)
    belly_z = BELLY_H    * (1 - np.cos(t))   # 0 at t=0, BELLY_H at t=π/2
    assert np.isclose(belly_r[0], 0.0) and np.isclose(belly_z[0], 0.0)

    # Straight cylinder section from top of belly to BODY_HEIGHT
    cup_r = np.array([BODY_R_MAX, BODY_R_TOP])
    cup_z = np.array([BELLY_H,     BODY_HEIGHT])

    # Full outer profile – closed loop including axis (r=0) so revolve produces
    # a watertight solid: axis-bottom → belly arc → shoulder → cup top → axis-top
    outer_r = np.concatenate([[0.0], belly_r[1:], cup_r[1:], [0.0]])
    outer_z = np.concatenate([[0.0],  belly_z[1:], cup_z[1:], [BODY_HEIGHT]])
    outer_profile = np.column_stack([outer_r, outer_z])

    outer_shell = _revolve_profile(outer_profile)

    # ------------------------------------------------------------------
    # 2. Cut flat bottom: slice at z=FLAT_BOTTOM so the stand ring is flat
    # ------------------------------------------------------------------
    big = BODY_R_MAX * 4
    # cutter box: from z=-big to z=FLAT_BOTTOM  → top face at FLAT_BOTTOM
    floor_cutter = tc.box(extents=[big * 2, big * 2, big + FLAT_BOTTOM])
    floor_cutter.apply_translation([0.0, 0.0, FLAT_BOTTOM / 2.0 - big / 2.0])

    solid = tb.difference([outer_shell, floor_cutter], engine="manifold")

    # Shift so the flat stand face sits exactly at z=0
    solid.apply_translation([0.0, 0.0, -FLAT_BOTTOM])

    # After the shift: body spans z=0 … BODY_TOP
    body_top = BODY_HEIGHT - FLAT_BOTTOM

    # ------------------------------------------------------------------
    # 3. Hollow out egg cavity from the top
    # ------------------------------------------------------------------
    cavity_h = CUP_DEPTH + 2.0   # slight over-depth for clean boolean
    cavity = _cylinder(CUP_INNER_R, cavity_h)
    cavity_cz = body_top - CUP_DEPTH / 2.0 + 1.0   # cavity centre
    cavity.apply_translation([0.0, 0.0, cavity_cz])
    solid = tb.difference([solid, cavity], engine="manifold")

    # ------------------------------------------------------------------
    # 4. Arm sockets (horizontal holes on ±X sides)
    # ------------------------------------------------------------------
    arm_r = (ARM_DIAM + PRESS_CLEAR) / 2.0
    arm_len = ARM_DEPTH + 4.0

    for sign in (+1, -1):
        arm_sock = _cylinder(arm_r, arm_len)
        rot = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
        arm_sock.apply_transform(rot)
        arm_sock.apply_translation([sign * (BODY_R_MAX - ARM_DEPTH / 2.0 + 2.0),
                                    0.0, ARM_Z])
        solid = tb.difference([solid, arm_sock], engine="manifold")

    # ------------------------------------------------------------------
    # 5. Leg sockets (downward-angled holes near the base)
    # ------------------------------------------------------------------
    leg_r = (LEG_DIAM + PRESS_CLEAR) / 2.0
    leg_len = LEG_DEPTH + 4.0
    tilt = np.radians(LEG_ANGLE_DEG)

    for sign in (+1, -1):
        leg_sock = _cylinder(leg_r, leg_len)
        rot_axis = [0, 1, 0]
        rot = trimesh.transformations.rotation_matrix(tilt * sign, rot_axis)
        leg_sock.apply_transform(rot)
        leg_sock.apply_translation([sign * LEG_SPREAD_X, 0.0, LEG_Z])
        solid = tb.difference([solid, leg_sock], engine="manifold")

    solid.process(validate=True)
    solid.fix_normals()
    return solid


# ---------------------------------------------------------------------------
# Validation stats
# ---------------------------------------------------------------------------

def print_stats(mesh: trimesh.Trimesh, path: Path) -> None:
    print("file:    ", path)
    print("facets:  ", len(mesh.faces))
    print("bounds:  ", mesh.bounds.tolist())
    print("extents: ", mesh.extents.tolist())
    print("watertight:", mesh.is_watertight)
    print("winding_consistent:", mesh.is_winding_consistent)
    print("volume_mm3:", round(mesh.volume, 3))
    print("euler:   ", mesh.euler_number)
    print("degenerate:", int(np.count_nonzero(mesh.area_faces <= 1e-12)))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    mesh = build()
    out = Path(__file__).resolve().parents[1] / "models" / "egg-cup-man-body.stl"
    out.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(out, file_type="stl_ascii")
    print_stats(mesh, out)


if __name__ == "__main__":
    main()
