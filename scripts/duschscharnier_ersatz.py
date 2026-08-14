"""Generate the shower-door pivot replacement with the build123d CAD kernel.

Geometry follows the reference video/photos: circular bearing head with a
teardrop insert pocket (head and tip radius joined by tangent flank arcs, so
the outline has no straight sections), hollow chambered mounting
arm, screw bosses whose conical countersinks blend directly into the bores,
cross ribs and cast pads in the dish, and a pair of longitudinal guide rails on
the inner arm walls that stand proud of the wall rim. All dimensions in
millimetres.
"""

import math
from pathlib import Path

from build123d import (
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Circle,
    Cone,
    Cylinder,
    Locations,
    Mode,
    Plane,
    Polygon,
    Rectangle,
    add,
    export_stl,
    extrude,
    fillet,
    make_face,
    mirror,
)

BASE_T = 2.0
WALL_T = 2.0
TOTAL_T = 12.5
HEAD_R = 19.0
TIP_Y = -40.165
HEAD_C_Y = TIP_Y + HEAD_R
HEAD_END_Y = TIP_Y + 43.0
ARM_W = 20.0
ARM_END_Y = 40.165
ARM_L = 43.0
ARM_START_Y = ARM_END_Y - ARM_L
ARM_HEAD_OVERLAP = HEAD_END_Y - ARM_START_Y
ARM_C_Y = (ARM_START_Y + ARM_END_Y) / 2.0

INSERT_W = 33.9
INSERT_L = 38.3
FIT = 0.20
POCKET_R = (INSERT_W + 2 * FIT) / 2.0
POCKET_LEN = INSERT_L + 2 * FIT
HEAD_WALL = HEAD_R - POCKET_R
POCKET_TIP_R = 9.0
POCKET_TIP_C_Y = TIP_Y + HEAD_WALL + POCKET_TIP_R
POCKET_HEAD_C_Y = POCKET_TIP_C_Y - POCKET_TIP_R + POCKET_LEN - POCKET_R
OUTER_HEAD_C_Y = POCKET_HEAD_C_Y
OUTER_TIP_R = POCKET_TIP_R + HEAD_WALL
OUTER_TIP_C_Y = POCKET_TIP_C_Y

# Cross ribs and cast pads stand 2.4 mm proud of the 2.0 mm dish floor, so
# their top face sits 4.4 mm above the outer (closed) face.
RIB_H = 2.4
RIB_TOP_Z = BASE_T + RIB_H
RIB_W = 2.0
PAD_R = 3.5
# Slight cast radius along the lower outside edges of the walls (the z = 0
# perimeter of the closed face). Kept below the 2.0 mm floor and wall so the
# closed face stays full size, and large enough to be visible after slicing.
OUTER_EDGE_R = 0.8
FLOOR_TIP_RIB_Y0 = TIP_Y + 0.25
FLOOR_TIP_RIB_Y1 = POCKET_HEAD_C_Y + POCKET_R - 0.5
FLOOR_TIP_RIB_C_Y = (FLOOR_TIP_RIB_Y0 + FLOOR_TIP_RIB_Y1) / 2.0
FLOOR_TIP_RIB_L = FLOOR_TIP_RIB_Y1 - FLOOR_TIP_RIB_Y0
# Internal guide: a pair of longitudinal rails, one on each inner side wall of
# the arm, forming a slot that guides the mating part.
#
# Top-down photos 201653 and 202910 both show the pair: measured against the
# 20 mm arm width the sequence across the arm is
# wall 2.0 | rail 2.0 | slot 12.0 | rail 2.0 | wall 2.0, and each rail casts a
# hard shadow line along its inner face, so the rails are clearly raised.
#
# The side view 202902 (part lying edge-on, open face towards the camera) shows
# how far they are raised: the rails stand proud of the wall rim by roughly
# 6 mm over about 28 mm of the arm. That is the "ragt oben heraus" note in the
# measurement doc, and it matches the user-measured guide height of 5.3 mm when
# 5.3 mm is read as the exposed height above the rim -- which is exactly what a
# caliper on the side view returns. The rails therefore run from the chamber
# floor all the way up and continue GUIDE_PROUD past the rim.
#
# They span roughly y 9.5 .. 29.5, i.e. from the head-side screw boss to just
# past the outer one.
GUIDE_PROUD = 5.3
GUIDE_T = 2.0
GUIDE_L = 20.0
GUIDE_WALL_BITE = 0.6
GUIDE_C_Y = 19.5
GUIDE_INNER_X = ARM_W / 2.0 - WALL_T
GUIDE_X0 = GUIDE_INNER_X - GUIDE_T
GUIDE_X1 = GUIDE_INNER_X + GUIDE_WALL_BITE
GUIDE_C_X = (GUIDE_X0 + GUIDE_X1) / 2.0
GUIDE_SKETCH_W = GUIDE_X1 - GUIDE_X0
GUIDE_SLOT_W = 2 * GUIDE_INNER_X - 2 * GUIDE_T
GUIDE_TOP_Z = TOTAL_T + GUIDE_PROUD
GUIDE_H = GUIDE_TOP_Z - BASE_T

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
HEAD_ARM_RIB_L = 9.5
HEAD_ARM_RIB_POCKET_CLEAR = 0.5
# Overlap the head-side mounting boss, with clearance to the arm side walls.
HEAD_ARM_RIB_X = 4.50
HEAD_ARM_RIB_C_Y = POCKET_HEAD_C_Y + POCKET_R + HEAD_ARM_RIB_POCKET_CLEAR + HEAD_ARM_RIB_L / 2.0

# Teardrop flank radius. The original casting has no straight section between
# the head and the tip radius: the two are joined by a large concave-side arc
# that is internally tangent to both. A hull of the two circles would insert a
# ~9.5 mm straight tangent line instead, which is clearly visible on the part.
# 34 mm was picked by overlaying candidate outlines on PXL_20260813_201713762.
FLANK_R = 34.0
EGG_SEGMENTS = (90, 40, 60)


def egg_arcs(head_r, tip_r, flank_r):
    """Add the +X half of the three-arc teardrop to the active BuildLine.

    Head arc, flank arc and tip arc are mutually tangent, so the outline has no
    straight section. Offsetting all three radii by the same wall thickness
    keeps every arc centre unchanged, so the pocket reuses this construction.
    The caller mirrors the half about Plane.YZ and closes it into a face.
    """
    d = OUTER_HEAD_C_Y - OUTER_TIP_C_Y
    oy = (d * d + (tip_r - head_r) * (2 * flank_r - head_r - tip_r)) / (2 * d)
    ox = -math.sqrt((flank_r - head_r) ** 2 - oy * oy)

    a1 = math.degrees(math.atan2(-oy, -ox))
    a2 = math.degrees(math.atan2(d - oy, -ox))

    # The construction above works in a frame whose +t axis points from the
    # head centre towards the tip. Sketch Y runs the other way, so every angle
    # flips sign and every centre is mirrored through OUTER_HEAD_C_Y.
    CenterArc((0.0, OUTER_HEAD_C_Y), head_r, 90.0, -a1 - 90.0)
    CenterArc((ox, OUTER_HEAD_C_Y - oy), flank_r, -a1, a1 - a2)
    CenterArc((0.0, OUTER_TIP_C_Y), tip_r, -a2, a2 - 90.0)


def egg_outline(head_r, tip_r, flank_r, segments=EGG_SEGMENTS):
    """Polyline sampling of the same outline, kept for numeric verification."""
    d = OUTER_HEAD_C_Y - OUTER_TIP_C_Y
    oy = (d * d + (tip_r - head_r) * (2 * flank_r - head_r - tip_r)) / (2 * d)
    ox = -math.sqrt((flank_r - head_r) ** 2 - oy * oy)

    a1 = math.atan2(-oy, -ox)
    a2 = math.atan2(d - oy, -ox)

    def arc(cx, cy, radius, start, end, count):
        step = (end - start) / count
        return [
            (cx + radius * math.cos(start + i * step), cy + radius * math.sin(start + i * step))
            for i in range(count + 1)
        ]

    n_head, n_flank, n_tip = segments
    half = arc(0.0, 0.0, head_r, -math.pi / 2, a1, n_head)
    half += arc(ox, oy, flank_r, a1, a2, n_flank)[1:]
    half += arc(0.0, d, tip_r, a2, math.pi / 2, n_tip)[1:]
    mirrored = [(-x, t) for x, t in reversed(half[1:-1])]
    return [(x, OUTER_HEAD_C_Y - t) for x, t in half + mirrored]


def build():
    def _cavity_tool(sketch_fn, height):
        """Plain prism cutter for a cavity, built outside the main part."""
        with BuildPart() as tool:
            with BuildSketch(Plane.XY.offset(BASE_T)):
                sketch_fn()
            extrude(amount=height)
        return tool.part

    def _pocket_sketch():
        with BuildLine() as pocket_ln:
            egg_arcs(POCKET_R, POCKET_TIP_R, FLANK_R - HEAD_WALL)
            mirror(pocket_ln.line, about=Plane.YZ)
        # Pass the edges explicitly: build123d resolves the implicit builder
        # context from the calling frame, which is not the sketch frame here.
        make_face(pocket_ln.line.edges())

    # Arm chambers left and right of the continuous middle wall.
    # Start the arm cavity only after the arm-facing end of the pocket so
    # the teardrop remains closed at both ends.
    chamber_a_y0 = POCKET_HEAD_C_Y + POCKET_R + WALL_T
    chamber_a_y1 = MOUNT_Y[0] - OUTER_BOSS_WEB_HALF
    chamber_b_y0 = MOUNT_Y[0] + OUTER_BOSS_WEB_HALF
    chamber_b_y1 = ARM_INNER_END_Y

    def _chamber_sketch():
        with Locations((0.0, (chamber_a_y0 + chamber_a_y1) / 2.0)):
            Rectangle(INNER_W, chamber_a_y1 - chamber_a_y0)
        with Locations((0.0, (chamber_b_y0 + chamber_b_y1) / 2.0)):
            Rectangle(INNER_W, chamber_b_y1 - chamber_b_y0)
        with Locations((-6.0, 3.5), (6.0, 3.5)):
            Rectangle(4.0, 4.5)

    # Cavity cutters are built outside the main part context.
    pocket_tool = _cavity_tool(_pocket_sketch, INNER_H + 1.0)
    chamber_tool = _cavity_tool(_chamber_sketch, INNER_H + 1.0)

    with BuildPart() as part:
        # Outer body: pointed teardrop head, rectangular arm, raised guide.
        with BuildSketch(Plane.XY):
            with BuildLine() as head_ln:
                egg_arcs(HEAD_R, OUTER_TIP_R, FLANK_R)
                mirror(head_ln.line, about=Plane.YZ)
            make_face()
            with Locations((0.0, ARM_C_Y)):
                Rectangle(ARM_W, ARM_L)
        extrude(amount=TOTAL_T)

        # Slight cast radius along the lower outside edges of the walls, i.e.
        # the whole z = 0 perimeter of the closed face. Done immediately after
        # the outer prism: OCCT refuses to fillet the finished assembly, and no
        # later feature reaches down to z = 0, so the radius survives.
        for r in (OUTER_EDGE_R, 0.6, 0.4, 0.25):
            try:
                fillet(part.edges().filter_by_position(Axis.Z, -0.01, 0.01), radius=r)
            except Exception:
                continue
            if r != OUTER_EDGE_R:
                print(f"note: outer bottom radius reduced to {r} mm")
            break
        else:
            print("warning: outer bottom radius skipped")

        # Teardrop pocket: same three-arc outline, offset inwards by the wall.
        add(pocket_tool, mode=Mode.SUBTRACT)
        add(chamber_tool, mode=Mode.SUBTRACT)

        # Internal guide: one rail per inner arm wall, together forming the
        # guide slot. The rails start at the chamber floor and stand
        # GUIDE_PROUD proud of the wall rim, matching the side view.
        with BuildSketch(Plane.XY.offset(BASE_T)):
            with Locations((GUIDE_C_X, GUIDE_C_Y), (-GUIDE_C_X, GUIDE_C_Y)):
                Rectangle(GUIDE_SKETCH_W, GUIDE_L)
        extrude(amount=GUIDE_H)

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
            with Locations((0.0, FLOOR_TIP_RIB_C_Y)):
                Rectangle(RIB_W, FLOOR_TIP_RIB_L)
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
    export_stl(part.part, str(out), ascii_format=True)
    print("file:", out)
    bb = part.part.bounding_box()
    print("bounds:", [[round(v, 3) for v in (bb.min.X, bb.min.Y, bb.min.Z)], [round(v, 3) for v in (bb.max.X, bb.max.Y, bb.max.Z)]])
    print("volume_mm3:", round(part.part.volume, 3))


if __name__ == "__main__":
    main()
