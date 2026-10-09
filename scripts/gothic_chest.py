"""Gothic chest and lid for the Ghoul's Grip automaton.

Everything decorative is modelled as real geometry rather than a texture: the
chest is a shell with a stepped plinth and cornice, corner pilasters, sunken
panels and lancet tracery built from annulus sectors, because a pointed arch
cannot be hulled from two circles. Every relief stands at least 1.2 mm proud,
well above the 0.4 mm a 0.4 mm nozzle can resolve.

The chest prints upright and the lid prints face down, so no decorated surface
is ever a bridge.
"""

from __future__ import annotations

import numpy as np
import trimesh

import mechanism
from mesh_kit import (arc_band, box, clean, cylinder, difference,
                      intersection, rounded_box, sphere, union)
from skull import skull_relief

CHEST_L = 200.0
CHEST_W = 120.0
BODY_H = 86.0
LID_H = 24.0
WALL = 3.0
FLOOR = 3.0

PLINTH_H = 10.0
CORNICE_H = 8.0
PROUD = 3.0            # how far plinth, cornice and pilasters stand out
PILASTER = 19.0
PANEL_DEPTH = 2.5
RELIEF = 2.6
ECONOMY_SKIN = 1.6    # visual shell retained behind internal lightening pockets

RAIL_W = 4.0           # slider rail groove, as specified in the brief
RAIL_D = 3.0
LID_DROP = 74.0         # chest z of the lid local origin when closed
RAIL_Z = 8.0
HINGE_Z = 93.0          # lid pin axis, shared by chest and lid knuckles
HINGE_Y = CHEST_W / 2.0 + PROUD - 2.0  # rear long edge; axis runs along X


def _stepped_skirt(z0: float, height: float, flip: bool) -> trimesh.Trimesh:
    """Plinth or cornice as two steps, so no face overhangs by the full 3 mm.

    ``flip`` builds the cornice, which grows downwards instead of upwards.
    """
    grows = [PROUD, PROUD * 0.5] if flip else [PROUD * 0.5, PROUD]
    steps = []
    lo = z0
    for grow, frac in zip(grows, (0.5, 0.5)):
        thick = height * frac
        steps.append(box((CHEST_L + 2 * grow, CHEST_W + 2 * grow, thick),
                         (0.0, 0.0, lo + thick / 2.0)))
        lo += thick
    return union(steps)


def _lancet(width: float, height: float, depth: float,
            centre, normal_x: bool) -> list[trimesh.Trimesh]:
    """One pointed arch: two jambs, a sill and two struck arcs."""
    half = width / 2.0
    radius = width          # equilateral arch: struck from the opposite jamb
    spring = height - np.sqrt(radius ** 2 - half ** 2)
    band = 5.0

    # The jambs run past the springing line and the arcs run past the apex,
    # so every joint is a real overlap rather than a tangential knife edge.
    jamb = spring + band
    parts = [
        box((band, jamb, depth), (-half + band / 2.0, jamb / 2.0, 0.0)),
        box((band, jamb, depth), (half - band / 2.0, jamb / 2.0, 0.0)),
        box((width, band, depth), (0.0, band / 2.0, 0.0)),
    ]
    # Equilateral arch: each flank arc is struck from the opposite springing
    # point, so both meet in a true point at the apex.
    for side, a0, a1 in ((-1.0, 0.0, 64.0), (1.0, 116.0, 180.0)):
        parts.append(arc_band(radius, band, depth,
                              np.deg2rad(a0), np.deg2rad(a1),
                              (side * half, spring, 0.0)))

    arch = union(parts)
    arch.apply_translation([0.0, 0.0, -depth / 2.0])
    arch.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2.0, [1.0, 0.0, 0.0]))
    if normal_x:
        arch.apply_transform(trimesh.transformations.rotation_matrix(
            np.pi / 2.0, [0.0, 0.0, 1.0]))
    arch.apply_translation(np.asarray(centre, dtype=float))
    return [arch]


def _frame(size, centre, normal_x: bool, proud: float,
           band: float = 6.0) -> trimesh.Trimesh:
    """Raised border around a field, so the field reads as a sunken panel.

    The chest wall is only 3 mm thick, so decoration is added outwards instead
    of cut inwards - a 2.5 mm recess would leave a 0.5 mm wall.
    """
    w, h = size
    if normal_x:
        outer = rounded_box((proud, w + 2 * band, h + 2 * band),
                            min(3.0, proud * 0.4), centre)
        inner = box((proud + 4.0, w, h), centre)
    else:
        outer = rounded_box((w + 2 * band, proud, h + 2 * band),
                            min(3.0, proud * 0.4), centre)
        inner = box((w, proud + 4.0, h), centre)
    return difference(outer, [inner])


def _leaf(length: float, width: float, depth: float,
          centre, angle: float) -> trimesh.Trimesh:
    """Convex almond leaf used in the baroque-gothic scrollwork."""
    leaf = sphere(1.0, subdivisions=2)
    leaf.apply_scale([length / 2.0, width / 2.0, depth / 2.0])
    leaf.apply_transform(trimesh.transformations.rotation_matrix(
        angle, (0.0, 0.0, 1.0)))
    leaf.apply_translation(np.asarray(centre, dtype=float))
    return clean(leaf)


def _scroll_pair(depth: float) -> trimesh.Trimesh:
    """Symmetrical acanthus curls in the local XY plane, extruded in Z."""
    parts = []
    for side in (-1.0, 1.0):
        group = [
            arc_band(19.0, 3.2, depth, np.deg2rad(-105),
                     np.deg2rad(145), (38.0, 0.0, 0.0)),
            arc_band(10.5, 2.6, depth, np.deg2rad(35),
                     np.deg2rad(305), (34.0, 3.0, 0.0)),
            _leaf(17.0, 7.0, depth, (17.0, 7.0, 0.0),
                  np.deg2rad(22.0)),
            _leaf(14.0, 6.0, depth, (52.0, -12.0, 0.0),
                  np.deg2rad(-35.0)),
            _leaf(11.0, 5.0, depth, (61.0, 10.0, 0.0),
                  np.deg2rad(58.0)),
        ]
        if side < 0:
            for part in group:
                part.apply_scale([-1.0, 1.0, 1.0])
        parts.extend(group)
    parts.append(_leaf(18.0, 8.0, depth, (0.0, 15.0, 0.0), np.pi / 2.0))
    return union(parts)

def _front_scrollwork(z: float) -> trimesh.Trimesh:
    depth = RELIEF + 1.5
    motif = _scroll_pair(depth)
    # Local Y becomes world Z and local Z becomes -world Y.
    motif.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2.0, (1.0, 0.0, 0.0)))
    motif.apply_translation([0.0,
                             -CHEST_W / 2.0 - (RELIEF - 1.5) / 2.0,
                             z])
    return clean(motif)


def _wall_decoration(length: float, x_sign: float, y_sign: float,
                     normal_x: bool, arch_count: int,
                     skip_middle: bool = False):
    """Raised frame plus tracery for one wall."""
    face = (CHEST_L / 2.0) if normal_x else (CHEST_W / 2.0)
    sign = x_sign if normal_x else y_sign
    panel_h = BODY_H - PLINTH_H - CORNICE_H - 16.0
    panel_z = PLINTH_H + 8.0 + panel_h / 2.0
    field = length - 2 * PILASTER - 10.0

    adds = []
    # Decoration is sunk 1.5 mm into the wall so the union has real overlap
    # instead of a tangential knife edge.
    frame_plane = face + (PANEL_DEPTH - 1.5) / 2.0
    centre = ((sign * frame_plane, 0.0, panel_z) if normal_x
              else (0.0, sign * frame_plane, panel_z))
    adds.append(_frame((field, panel_h), centre, normal_x, PANEL_DEPTH + 1.5))

    pitch = field / arch_count
    arch_w = min(pitch - 10.0, 36.0)
    arch_h = panel_h - 10.0
    plane = face + (RELIEF - 1.5) / 2.0
    for i in range(arch_count):
        if skip_middle and i == arch_count // 2:
            continue      # the skull trigger sits in the middle bay
        offset = (i - (arch_count - 1) / 2.0) * pitch
        base = panel_z - arch_h / 2.0
        if normal_x:
            spot = (sign * plane, offset, base)
        else:
            spot = (offset, sign * plane, base)
        adds += _lancet(arch_w, arch_h, RELIEF + 1.5, spot, normal_x)
    return [], adds


def _wall_lightening_pockets() -> list[trimesh.Trimesh]:
    """Thin broad non-functional wall fields from the inside.

    The exterior relief, corner pilasters, lower rail zone and upper hinge/
    anchor zone stay untouched.  Opening the pockets into the main cavity avoids
    enclosed support traps while retaining a 1.6 mm outer skin.
    """
    pocket_z0 = 18.0
    pocket_z1 = 70.0
    pocket_h = pocket_z1 - pocket_z0
    overlap = 0.2
    depth = WALL - ECONOMY_SKIN + overlap
    wall_offset = WALL - depth / 2.0 + overlap
    pockets = []

    # Front is split around the skull trigger; the rear can use one broad bay.
    for x in (-50.0, 50.0):
        pockets.append(box(
            (56.0, depth, pocket_h),
            (x, -CHEST_W / 2.0 + wall_offset, (pocket_z0 + pocket_z1) / 2.0),
        ))
    pockets.append(box(
        (164.0, depth, pocket_h),
        (0.0, CHEST_W / 2.0 - wall_offset, (pocket_z0 + pocket_z1) / 2.0),
    ))

    # Side pockets stop well before the corner pilasters.
    for sign in (-1.0, 1.0):
        pockets.append(box(
            (depth, 84.0, pocket_h),
            (sign * (CHEST_L / 2.0 - wall_offset), 0.0,
             (pocket_z0 + pocket_z1) / 2.0),
        ))
    return pockets


def build_chest() -> trimesh.Trimesh:
    """Open-topped gothic chest with internal rails and control bores."""
    shell = box((CHEST_L, CHEST_W, BODY_H), (0.0, 0.0, BODY_H / 2.0))
    cavity = box((CHEST_L - 2 * WALL, CHEST_W - 2 * WALL, BODY_H),
                 (0.0, 0.0, FLOOR + BODY_H / 2.0))

    pilasters = []
    shaft_h = BODY_H - PLINTH_H - CORNICE_H
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            cx = sx * (CHEST_L / 2.0 - PILASTER / 2.0 + PROUD)
            cy = sy * (CHEST_W / 2.0 - PILASTER / 2.0 + PROUD)
            pilasters.append(box((PILASTER, PILASTER, shaft_h),
                                 (cx, cy, PLINTH_H + shaft_h / 2.0)))
            # Base and capital blocks, so the pilaster reads as a column.
            for z in (PLINTH_H + 3.0, BODY_H - CORNICE_H - 3.0):
                pilasters.append(box((PILASTER + 3.0, PILASTER + 3.0, 6.0),
                                     (cx, cy, z)))

    cuts, adds = _wall_lightening_pockets(), []
    for normal_x, sign, length, count, skip in ((False, -1.0, CHEST_L, 3, True),
                                                (False, 1.0, CHEST_L, 3, False),
                                                (True, -1.0, CHEST_W, 2, False),
                                                (True, 1.0, CHEST_W, 2, False)):
        c, a = _wall_decoration(length, sign, sign, normal_x, count, skip)
        cuts += c
        adds += a

    # The concept art is dominated by raised acanthus scrolls.  Lancet arches
    # alone read as plain architecture, so a deep paired curl frames the skull
    # trigger on the front while preserving the 3 mm structural wall.
    adds.append(_front_scrollwork(48.0))

    rivets = []
    for sign in (-1.0, 1.0):
        for x in np.arange(-CHEST_L / 2.0 + 16.0, CHEST_L / 2.0 - 10.0, 24.0):
            for z in (PLINTH_H - 4.0, BODY_H - CORNICE_H + 4.0):
                rivets.append(sphere(2.4, (x, sign * (CHEST_W / 2.0 + PROUD), z),
                                     subdivisions=2))

    body = union([shell,
                  _stepped_skirt(0.0, PLINTH_H, flip=False),
                  _stepped_skirt(BODY_H - CORNICE_H, CORNICE_H, flip=True),
                  *pilasters])
    body = difference(body, [cavity, *cuts])
    body = union([body, *adds, *rivets])

    # Collar around the skull trigger: the button flange drops into the ring.
    collar = difference(
        cylinder(38.0 / 2.0, 6.0, (0.0, -CHEST_W / 2.0 - 1.5, 46.0),
                 (0.0, 1.0, 0.0)),
        [cylinder(31.0 / 2.0, 10.0, (0.0, -CHEST_W / 2.0 - 1.5, 46.0),
                  (0.0, 1.0, 0.0))])
    body = union([body, collar])

    # Function cuts: slider rails, the skull trigger bore and the crank bore.
    service = [
        box((CHEST_L, RAIL_D * 2.0, RAIL_W),
            (0.0, -(CHEST_W / 2.0 - WALL), RAIL_Z + RAIL_W / 2.0)),
        box((CHEST_L, RAIL_D * 2.0, RAIL_W),
            (0.0, CHEST_W / 2.0 - WALL, RAIL_Z + RAIL_W / 2.0)),
        cylinder(4.4 / 2.0, 40.0, (0.0, -CHEST_W / 2.0, 46.0), (0.0, 1.0, 0.0)),

        cylinder(6.4 / 2.0, 40.0, (CHEST_L / 2.0, 0.0, 30.0), (1.0, 0.0, 0.0)),
    ]
    body = difference(body, service)

    # Fixed scissor pivots and the peg sockets for latch bracket and band
    # anchor. The scissor pivot sits at x = 0 so the compact platform stays inside
    # the chest over the whole stroke (see docs, kinematics table).
    posts = []
    for sy in (-1.0, 1.0):
        posts.append(box((12.0, 6.0, 14.0),
                         (mechanism.FLOOR_PIVOT_X,
                          sy * mechanism.SCISSOR_Y, FLOOR + 7.0)))
        posts.append(cylinder(6.0, 6.0,
                              (mechanism.FLOOR_PIVOT_X,
                               sy * mechanism.SCISSOR_Y, RAIL_Z),
                              (0.0, 1.0, 0.0)))
    body = union([body, *posts])
    sockets = [cylinder(4.2 / 2.0, 6.0, (x, y, FLOOR), (0.0, 0.0, 1.0))
               for x, y in ((-76.0, 44.0), (-76.0, -44.0))]
    sockets.append(cylinder(3.2 / 2.0, 80.0,
                            (mechanism.FLOOR_PIVOT_X, 0.0, RAIL_Z),
                            (0.0, 1.0, 0.0)))
    body = difference(body, sockets)

    # High side-wall eye for the forearm control cord. Routing above the
    # carriage keeps the entire cord clear of slider, arms and lifting yoke.
    cord_boss = rounded_box(
        (14.0, 12.0, 14.0), 2.0,
        (mechanism.FOREARM_ANCHOR_X, 54.0, mechanism.FOREARM_ANCHOR_Z),
    )
    cord_eye = cylinder(
        5.0, 8.0, mechanism.FOREARM_CORD_ANCHOR, (0.0, 1.0, 0.0)
    )
    cord_eye = difference(cord_eye, [
        cylinder(2.0, 12.0, mechanism.FOREARM_CORD_ANCHOR,
                 (0.0, 1.0, 0.0))
    ])
    body = union([body, cord_boss, cord_eye])

    # Two low rear eyes anchor rubber bands that bias the lid open.  The same
    # latch rocker that holds the slider also retains the lid catch cord, so
    # both motions start from one skull-button press.
    lid_band_anchors = []
    for x in (-70.0, 70.0):
        boss = rounded_box((12.0, 12.0, 12.0), 2.0,
                           (x, 55.0, 65.0))
        eye = cylinder(5.0, 8.0, (x, 50.0, 65.0), (1.0, 0.0, 0.0))
        eye = difference(eye, [
            cylinder(2.0, 12.0, (x, 50.0, 65.0), (1.0, 0.0, 0.0))
        ])
        lid_band_anchors.extend([boss, eye])
    body = union([body, *lid_band_anchors])

    # Hinge on the long rear edge.  Three chest knuckles alternate with four
    # lid knuckles; 1 mm axial gaps stop elephant-foot swelling from binding.
    knuckles = []
    for x in (-66.0, 0.0, 66.0):
        knuckles.append(box((28.0, 10.0, 10.0), (x, HINGE_Y, BODY_H + 2.0)))
        knuckles.append(cylinder(5.0, 28.0, (x, HINGE_Y, HINGE_Z),
                                  (1.0, 0.0, 0.0)))
    body = union([body, *knuckles])
    body = difference(body, [cylinder(1.9 / 2.0, CHEST_L + 20.0,
                                      (0.0, HINGE_Y, HINGE_Z),
                                      (1.0, 0.0, 0.0))])
    return clean(body)


def build_lid() -> trimesh.Trimesh:
    """Flat-topped gothic lid with a skull cartouche, printed face down."""
    top = box((CHEST_L, CHEST_W, 6.0), (0.0, 0.0, LID_H - 3.0))
    frame = box((CHEST_L + 2 * PROUD, CHEST_W + 2 * PROUD, 6.0),
                (0.0, 0.0, LID_H - 9.0))
    step = box((CHEST_L + PROUD, CHEST_W + PROUD, 3.0),
               (0.0, 0.0, LID_H - 10.5))
    # A full rectangular plug cannot rotate out of the chest: its front edge
    # sweeps into the front wall during the first opening degrees.  A rear-and-
    # side U-guide seats the lid just as accurately while leaving that sweep
    # volume open.
    spigot_outer_x = CHEST_L - 2 * WALL - 0.6
    spigot_outer_y = CHEST_W - 2 * WALL - 0.6
    spigot_wall = 3.3
    side_length = spigot_outer_y - 18.0
    spigot = union([
        box((spigot_outer_x, spigot_wall, 12.0),
            (0.0, (spigot_outer_y - spigot_wall) / 2.0, 6.0)),
        box((spigot_wall, side_length, 12.0),
            (-(spigot_outer_x - spigot_wall) / 2.0, 9.0, 6.0)),
        box((spigot_wall, side_length, 12.0),
            ((spigot_outer_x - spigot_wall) / 2.0, 9.0, 6.0)),
    ])

    body = union([top, frame, step, spigot])

    # Narrow underside channels replace the former mostly solid 12 mm slab with
    # a 2.0 mm face skin, a wide perimeter and a rib grid.  Each ceiling bridges
    # only 10 mm, matching the repository's support-free bridge limit.  The
    # seating guide, hinge, catch and opening-band interfaces are added outside
    # these channels and retain their original dimensions.
    pocket_z0 = 11.0
    pocket_z1 = 19.5
    lid_pockets = [
        rounded_box(
            (80.0, 10.0, pocket_z1 - pocket_z0),
            2.0,
            (x, y, (pocket_z0 + pocket_z1) / 2.0),
        )
        for x in (-50.0, 50.0)
        for y in (-39.0, -25.0, -11.0, 11.0, 25.0, 39.0)
    ]
    body = difference(body, lid_pockets)

    # Sunken field on the lid face.
    floor_z = LID_H - PANEL_DEPTH
    field = rounded_box((CHEST_L - 38.0, CHEST_W - 38.0, PANEL_DEPTH * 2.0),
                        4.0, (0.0, 0.0, LID_H))
    body = difference(body, [field])

    # Skull cartouche, sunk 1.5 mm into the field so the union really overlaps.
    cartouche = skull_relief(1.5, depth=RELIEF + PANEL_DEPTH)
    cartouche.apply_translation([0.0, 0.0, floor_z - 1.5])

    # Raised bead frame around the field plus corner bosses.
    bead = difference(
        box((CHEST_L - 30.0, CHEST_W - 30.0, PANEL_DEPTH + 1.5),
            (0.0, 0.0, floor_z + (PANEL_DEPTH - 1.5) / 2.0)),
        [box((CHEST_L - 42.0, CHEST_W - 42.0, PANEL_DEPTH + 6.0),
             (0.0, 0.0, floor_z))])
    beads = []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            beads.append(sphere(5.0, (sx * (CHEST_L / 2.0 - 11.0),
                                      sy * (CHEST_W / 2.0 - 11.0),
                                      LID_H - 1.5), subdivisions=3))
    # Raised bands flanking the cartouche.
    wings = [box((10.0, CHEST_W - 46.0, RELIEF + 1.5),
                 (sx * 62.0, 0.0, floor_z + (RELIEF - 1.5) / 2.0))
             for sx in (-1.0, 1.0)]
    wings += [box((6.0, CHEST_W - 46.0, RELIEF + 1.5),
                  (sx * 74.0, 0.0, floor_z + (RELIEF - 1.5) / 2.0))
              for sx in (-1.0, 1.0)]

    lid_scrolls = _scroll_pair(RELIEF + 1.5)
    lid_scrolls.apply_scale([0.92, 0.72, 1.0])
    lid_scrolls.apply_translation([0.0, -8.0,
                                   floor_z + (RELIEF - 1.5) / 2.0])

    body = union([body, cartouche, bead, lid_scrolls, *beads, *wings])

    # The decorative rear frame stops at the hinge axis. Material extending
    # behind that axis would dip into the chest rim during the first degrees
    # of opening; only the cylindrical knuckles may project farther rearward.
    body = difference(body, [
        box((CHEST_L + 8.0, 3.0, 18.0), (0.0, 62.5, 9.0))
    ])

    # Four lid knuckles fill the gaps between the three chest knuckles.
    lid_segments = ((-90.0, 18.0), (-33.0, 36.0),
                    (33.0, 36.0), (90.0, 18.0))
    knuckles = [cylinder(5.0, length, (x, HINGE_Y, LID_H - 5.0),
                         (1.0, 0.0, 0.0)) for x, length in lid_segments]
    body = union([body, *knuckles])
    body = difference(body, [cylinder(2.0 / 2.0, CHEST_L + 24.0,
                                      (0.0, HINGE_Y, LID_H - 5.0),
                                      (1.0, 0.0, 0.0))])

    # The opening-band eyes must sit on the front side of the hinge axis.
    # Eyes behind the axis sweep down through the chest while the lid opens.
    band_tabs = []
    for x in (-70.0, 70.0):
        band_tabs.append(box((12.0, 10.0, 10.0),
                             (x, 55.0, LID_H - 5.0)))
        tab = cylinder(5.0, 8.0, (x, 50.0, LID_H - 5.0),
                       (1.0, 0.0, 0.0))
        tab = difference(tab, [
            cylinder(2.0, 12.0, (x, 50.0, LID_H - 5.0),
                     (1.0, 0.0, 0.0))
        ])
        band_tabs.append(tab)

    catch_y = -45.0
    catch = rounded_box((12.0, 10.0, 12.0), 2.0,
                        (0.0, catch_y, 7.0))
    catch = difference(catch, [
        cylinder(2.0, 18.0, (0.0, catch_y, 7.0),
                 (1.0, 0.0, 0.0))
    ])
    body = union([body, *band_tabs, catch])

    # Rebuild only the rear seating region around frozen chest-side hardware.
    # Alternating pockets clear the three chest hinge supports; the small
    # right-hand notch clears the existing forearm-cord boss below the rim.
    clearance_pockets = [
        box((30.0, 12.0, 18.0), (x, HINGE_Y, 16.5))
        for x in (-66.0, 0.0, 66.0)
    ]
    clearance_pockets.append(box((16.0, 9.0, 9.0), (70.0, 54.5, 4.0)))
    return clean(difference(body, clearance_pockets))


if __name__ == "__main__":
    for name, mesh in (("chest", build_chest()), ("lid", build_lid())):
        print(f"{name:6s} faces {len(mesh.faces):6d} watertight {mesh.is_watertight} "
              f"bodies {len(mesh.split(only_watertight=False))} "
              f"euler {mesh.euler_number} extents {np.round(mesh.extents, 1).tolist()}")
        mesh.export(f"model-sources/ghouls-grip/reference/_{name}.stl")
    _ = intersection
