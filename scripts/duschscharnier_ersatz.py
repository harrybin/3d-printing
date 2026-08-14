"""Generate the shower-door pivot replacement with the build123d CAD kernel.

Geometry follows the reference video/photos: circular bearing head with a
teardrop insert pocket (two intersecting circles), hollow chambered mounting
arm, screw bosses whose conical countersinks blend directly into the bores,
cross ribs and cast pads in the dish, and the full-height guide block at the
pocket outlet. All dimensions in millimetres.
"""

from pathlib import Path

from build123d import (
    BuildPart,
    BuildSketch,
    Circle,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Plane,
    Rectangle,
    export_stl,
    extrude,
    make_hull,
)

BASE_T = 2.4
WALL_T = 2.0
TOTAL_T = 12.5
HEAD_R = 19.0
TIP_Y = -40.165
HEAD_C_Y = TIP_Y + HEAD_R
HEAD_END_Y = TIP_Y + 43.0
ARM_W = 20.0
ARM_END_Y = 40.165
# Fuse the arm 5 mm into the circular head instead of a near-tangent joint.
ARM_HEAD_OVERLAP = 5.0
ARM_START_Y = HEAD_C_Y + HEAD_R - ARM_HEAD_OVERLAP
ARM_C_Y = (ARM_START_Y + ARM_END_Y) / 2.0
ARM_L = ARM_END_Y - ARM_START_Y

INSERT_W = 33.9
INSERT_L = 38.3
FIT = 0.20
POCKET_R = (INSERT_W + 2 * FIT) / 2.0
POCKET_LEN = INSERT_L + 2 * FIT
HEAD_WALL = HEAD_R - POCKET_R
POCKET_HEAD_C_Y = HEAD_C_Y + 2.0
POCKET_TIP_R = 3.0
POCKET_TIP_C_Y = TIP_Y + HEAD_WALL + POCKET_TIP_R
OUTER_HEAD_C_Y = POCKET_HEAD_C_Y
OUTER_TIP_R = POCKET_TIP_R + HEAD_WALL
OUTER_TIP_C_Y = POCKET_TIP_C_Y

RIB_H = 2.0
RIB_W = 2.0
PAD_R = 3.5
GUIDE_W = 8.0
GUIDE_L = 6.0
GUIDE_TOP = 2.5

HOLE_D = 4.0
CSK_D = 8.5
CSK_DEPTH = 5.0
# Measured from the outer arm end, towards the teardrop/head.
MOUNT_FROM_ARM_END = (12.4, 31.7)
MOUNT_Y = tuple(ARM_END_Y - distance for distance in MOUNT_FROM_ARM_END)

INNER_W = ARM_W - 2 * WALL_T
INNER_H = TOTAL_T - BASE_T
ARM_INNER_END_Y = ARM_END_Y - WALL_T
MID_WALL_HALF = 1.0
OUTER_BOSS_WEB_HALF = 1.5
BOSS_SIDE_RIB_W = 3.0
BOSS_SIDE_RIB_Y = 3.0
MOUNT_BOSS_R = 4.25
BETWEEN_BOSS_RIB_W = 3.0
BETWEEN_BOSS_RIB_OVERLAP = 0.25
BETWEEN_BOSS_RIB_Y0 = MOUNT_Y[1] + MOUNT_BOSS_R - BETWEEN_BOSS_RIB_OVERLAP
BETWEEN_BOSS_RIB_Y1 = MOUNT_Y[0] - MOUNT_BOSS_R + BETWEEN_BOSS_RIB_OVERLAP
BETWEEN_BOSS_RIB_C_Y = (BETWEEN_BOSS_RIB_Y0 + BETWEEN_BOSS_RIB_Y1) / 2.0
BETWEEN_BOSS_RIB_L = BETWEEN_BOSS_RIB_Y1 - BETWEEN_BOSS_RIB_Y0
ARM_END_RIB_W = 3.0
ARM_END_RIB_Y0 = MOUNT_Y[0] + MOUNT_BOSS_R - BETWEEN_BOSS_RIB_OVERLAP
ARM_END_RIB_Y1 = ARM_END_Y
ARM_END_RIB_C_Y = (ARM_END_RIB_Y0 + ARM_END_RIB_Y1) / 2.0
ARM_END_RIB_L = ARM_END_RIB_Y1 - ARM_END_RIB_Y0
HEAD_ARM_RIB_W = 3.0
HEAD_ARM_RIB_L = 12.0
# Overlap the head-side mounting boss, with clearance to the arm side walls.
HEAD_ARM_RIB_X = 4.50
HEAD_ARM_RIB_C_Y = HEAD_C_Y + POCKET_R + WALL_T + HEAD_ARM_RIB_L / 2.0


def build():
    with BuildPart() as part:
        # Outer body: pointed teardrop head, rectangular arm, raised guide.
        with BuildSketch(Plane.XY):
            with Locations((0.0, OUTER_HEAD_C_Y)):
                Circle(HEAD_R)
            with Locations((0.0, OUTER_TIP_C_Y)):
                Circle(OUTER_TIP_R)
            make_hull(mode=Mode.REPLACE)
            with Locations((0.0, ARM_C_Y)):
                Rectangle(ARM_W, ARM_L)
        extrude(amount=TOTAL_T)
        with BuildSketch(Plane.XY):
            with Locations((0.0, POCKET_TIP_C_Y + 3.0)):
                Rectangle(GUIDE_W, GUIDE_L + 2.0)
        extrude(amount=TOTAL_T + GUIDE_TOP)

        # Teardrop pocket: hull of two intersecting circles, cut to depth.
        with BuildSketch(Plane.XY.offset(BASE_T)):
            with Locations((0.0, POCKET_HEAD_C_Y)):
                Circle(POCKET_R)
            with Locations((0.0, POCKET_TIP_C_Y)):
                Circle(POCKET_TIP_R)
            make_hull(mode=Mode.REPLACE)
        extrude(amount=INNER_H + GUIDE_TOP + 1.0, mode=Mode.SUBTRACT)

        # Arm chambers left and right of the continuous middle wall.
        # Start the arm cavity only after the arm-facing end of the pocket so
        # the teardrop remains closed at both ends.
        chamber_a_y0 = POCKET_HEAD_C_Y + POCKET_R + WALL_T
        chamber_a_y1 = MOUNT_Y[0] - OUTER_BOSS_WEB_HALF
        chamber_b_y0 = MOUNT_Y[0] + OUTER_BOSS_WEB_HALF
        chamber_b_y1 = ARM_INNER_END_Y
        with BuildSketch(Plane.XY.offset(BASE_T)):
            with Locations((0.0, (chamber_a_y0 + chamber_a_y1) / 2.0)):
                Rectangle(INNER_W, chamber_a_y1 - chamber_a_y0)
            with Locations((0.0, (chamber_b_y0 + chamber_b_y1) / 2.0)):
                Rectangle(INNER_W, chamber_b_y1 - chamber_b_y0)
            with Locations((-6.0, 3.5), (6.0, 3.5)):
                Rectangle(4.0, 4.5)
        extrude(amount=INNER_H + 1.0, mode=Mode.SUBTRACT)

        # Reconnect the head-side screw boss to both arm walls with ribs.
        with BuildSketch(Plane.XY.offset(BASE_T)):
            with Locations((-7.0, MOUNT_Y[1]), (7.0, MOUNT_Y[1])):
                Rectangle(BOSS_SIDE_RIB_W, BOSS_SIDE_RIB_Y)
        extrude(amount=INNER_H)

        # Center rib transfers load directly between the two mounting bosses.
        with BuildSketch(Plane.XY.offset(BASE_T)):
            with Locations((0.0, BETWEEN_BOSS_RIB_C_Y)):
                Rectangle(BETWEEN_BOSS_RIB_W, BETWEEN_BOSS_RIB_L)
        extrude(amount=INNER_H)

        # Join the outer mounting boss directly to the short arm end wall.
        with BuildSketch(Plane.XY.offset(BASE_T)):
            with Locations((0.0, ARM_END_RIB_C_Y)):
                Rectangle(ARM_END_RIB_W, ARM_END_RIB_L)
        extrude(amount=INNER_H)

        # Two longitudinal ribs carry load from the closed pocket edge into
        # the head-side mounting boss without protruding into the pocket.
        with BuildSketch(Plane.XY.offset(BASE_T)):
            with Locations((-HEAD_ARM_RIB_X, HEAD_ARM_RIB_C_Y), (HEAD_ARM_RIB_X, HEAD_ARM_RIB_C_Y)):
                Rectangle(HEAD_ARM_RIB_W, HEAD_ARM_RIB_L)
        extrude(amount=INNER_H)

        # Cross ribs and four cast pads on the dish floor.
        with BuildSketch(Plane.XY.offset(BASE_T)):
            with Locations((0.0, POCKET_HEAD_C_Y)):
                Rectangle(INSERT_W, RIB_W)
            with Locations((0.0, POCKET_HEAD_C_Y - POCKET_R + POCKET_LEN / 2.0 - 0.5)):
                Rectangle(RIB_W, POCKET_LEN - 1.0)
            with Locations(*[(sx * 8.0, POCKET_HEAD_C_Y + sy * 8.0) for sx in (-1, 1) for sy in (-1, 1)]):
                Circle(PAD_R)
        extrude(amount=RIB_H)

        # Screw bosses re-fused over the chambers.
        with Locations((0.0, MOUNT_Y[0], BASE_T + INNER_H / 2.0), (0.0, MOUNT_Y[1], BASE_T + INNER_H / 2.0)):
            Cylinder(MOUNT_BOSS_R, INNER_H)

        # Through bores, then countersink cones opening at the outer face
        # (z=0) and narrowing exactly to the bore: no ledge, no gap.
        with Locations((0.0, MOUNT_Y[0], TOTAL_T / 2.0), (0.0, MOUNT_Y[1], TOTAL_T / 2.0)):
            Cylinder(HOLE_D / 2.0, TOTAL_T + 4.0, mode=Mode.SUBTRACT)
        with Locations((0.0, MOUNT_Y[0], CSK_DEPTH / 2.0), (0.0, MOUNT_Y[1], CSK_DEPTH / 2.0)):
            Cone(bottom_radius=CSK_D / 2.0, top_radius=HOLE_D / 2.0, height=CSK_DEPTH, mode=Mode.SUBTRACT)
    return part


def main():
    part = build()
    out = Path(__file__).resolve().parents[1] / "models" / "duschscharnier_ersatz.stl"
    export_stl(part.part, str(out))
    print("file:", out)
    bb = part.part.bounding_box()
    print("bounds:", [[round(v, 3) for v in (bb.min.X, bb.min.Y, bb.min.Z)], [round(v, 3) for v in (bb.max.X, bb.max.Y, bb.max.Z)]])
    print("volume_mm3:", round(part.part.volume, 3))


if __name__ == "__main__":
    main()
