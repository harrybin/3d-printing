"""Generate the rounded-bottom body (torso) of the Egg-Cup Man.

The torso is shaped like a rounded teardrop / pear:
- Lower half: an oblate ellipsoid, flattened at the bottom to give a stable flat
  stand (cut at z = FLATTEN_Z from the ellipsoid centre).
- Upper half: a cylinder/cone transitioning into the egg-cup cavity.
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

# Overall body proportions
BODY_HEIGHT = 65.0          # total height of the torso
MAX_RADIUS   = 25.0         # max XY radius at the equator of the ellipsoid

# Lower rounded section
ELLIPSE_A = MAX_RADIUS      # XY semi-axis of lower ellipsoid
ELLIPSE_C = 35.0            # Z  semi-axis of lower ellipsoid
FLATTEN_Z = -8.0            # Z where we cut the bottom flat (relative to ellipsoid centre)
                            # ESTIMATE – adjust for desired stand height

# Upper cylindrical/cup section
CUP_INNER_R  = 19.0         # inner radius of egg cavity  (ESTIMATE)
CUP_DEPTH    = 22.0         # depth of egg cavity          (ESTIMATE)
WALL_T       = 3.0          # wall thickness
CUP_OUTER_R  = CUP_INNER_R + WALL_T

# Arm sockets (horizontal, pointing ±X)
ARM_DIAM     = 6.0          # socket diameter (ESTIMATE)
ARM_DEPTH    = 6.0          # socket depth into body (ESTIMATE)
ARM_Z        = 42.0         # height above body bottom (ESTIMATE)
PRESS_CLEAR  = 0.20         # press-fit clearance for 0.4 mm nozzle profile

# Leg sockets (pointing downward, angled outward)
LEG_DIAM     = 8.0          # socket diameter (ESTIMATE)
LEG_DEPTH    = 8.0          # socket depth (ESTIMATE)
LEG_SPREAD_X = 11.0         # ±X centre-of-socket from body axis (ESTIMATE)
LEG_Z        = 10.0         # socket centre height above body bottom (ESTIMATE)
LEG_ANGLE_DEG = 20.0        # downward tilt of leg socket axis (ESTIMATE)

SEGMENTS = 80               # angular resolution for revolve/cylinders

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ellipsoid(rx: float, rz: float, sections: int) -> trimesh.Trimesh:
    """Return an oblate ellipsoid centred at the origin, rx=ry, different rz."""
    # build a unit sphere and scale
    sphere = tc.icosphere(subdivisions=4)
    sphere.apply_scale([rx, rx, rz])
    return sphere


def _cylinder(radius: float, height: float, sections: int = SEGMENTS) -> trimesh.Trimesh:
    cyl = tc.cylinder(radius=radius, height=height, sections=sections)
    return cyl


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build() -> trimesh.Trimesh:
    # ------------------------------------------------------------------
    # 1. Lower rounded base: oblate ellipsoid, cut flat at bottom
    # ------------------------------------------------------------------
    ellipsoid = _ellipsoid(ELLIPSE_A, ELLIPSE_C, SEGMENTS)

    # The ellipsoid centre sits at z=0; the flat cut is at z=FLATTEN_Z.
    # Remove everything below FLATTEN_Z with a large cutting box.
    cut_z = FLATTEN_Z
    cut_box_half = MAX_RADIUS * 3
    cutter = tc.box(extents=[cut_box_half * 2, cut_box_half * 2, abs(cut_z) * 2])
    cutter.apply_translation([0.0, 0.0, cut_z - abs(cut_z)])  # box top face at cut_z

    lower_body = tb.difference([ellipsoid, cutter], engine="manifold")

    # Translate so that the flat bottom sits at z=0
    shift_z = -cut_z   # cut_z is negative, so shift_z is positive
    lower_body.apply_translation([0.0, 0.0, shift_z])

    # ------------------------------------------------------------------
    # 2. Upper cylindrical cup section
    # ------------------------------------------------------------------
    # The equator of the ellipsoid (max XY) is at its centre, now at z=shift_z.
    # We extend with a cylinder from the equator height up to BODY_HEIGHT.
    equator_z = shift_z   # ellipsoid XY maximum is at the original z=0 plane

    upper_height = BODY_HEIGHT - equator_z
    upper_cyl = _cylinder(CUP_OUTER_R, upper_height)
    upper_cyl.apply_translation([0.0, 0.0, equator_z + upper_height / 2.0])

    # Union lower rounded base + upper cylinder
    solid = tb.union([lower_body, upper_cyl], engine="manifold")

    # ------------------------------------------------------------------
    # 3. Hollow out egg cavity from the top
    # ------------------------------------------------------------------
    cavity = _cylinder(CUP_INNER_R, CUP_DEPTH + 1.0)   # +1 to ensure clean top cut
    cavity.apply_translation([0.0, 0.0, BODY_HEIGHT - CUP_DEPTH / 2.0])
    solid = tb.difference([solid, cavity], engine="manifold")

    # ------------------------------------------------------------------
    # 4. Arm sockets (horizontal holes on ±X sides)
    # ------------------------------------------------------------------
    arm_r = (ARM_DIAM - PRESS_CLEAR) / 2.0
    arm_cyl_len = ARM_DEPTH + 2.0   # slight over-depth for clean boolean

    for sign in (+1, -1):
        arm_sock = _cylinder(arm_r, arm_cyl_len, sections=SEGMENTS)
        # rotate to point along X
        rot = trimesh.transformations.rotation_matrix(
            np.pi / 2, [0, 1, 0], [0, 0, 0]
        )
        arm_sock.apply_transform(rot)
        arm_sock.apply_translation([sign * (MAX_RADIUS - ARM_DEPTH / 2.0 + 1.0),
                                    0.0,
                                    ARM_Z])
        solid = tb.difference([solid, arm_sock], engine="manifold")

    # ------------------------------------------------------------------
    # 5. Leg sockets (downward-angled holes near the base)
    # ------------------------------------------------------------------
    leg_r = (LEG_DIAM - PRESS_CLEAR) / 2.0
    leg_cyl_len = LEG_DEPTH + 2.0
    tilt = np.radians(LEG_ANGLE_DEG)  # downward tilt angle

    for sign in (+1, -1):
        leg_sock = _cylinder(leg_r, leg_cyl_len, sections=SEGMENTS)
        # Default cylinder axis is along Z; tilt downward in XZ-plane
        rot_axis = [0, 1, 0] if sign > 0 else [0, -1, 0]
        rot = trimesh.transformations.rotation_matrix(
            tilt, rot_axis, [0, 0, 0]
        )
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
