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

RAIL_W = 4.0           # slider rail groove, as specified in the brief
RAIL_D = 3.0
LID_DROP = 74.0         # chest z of the lid local origin when closed
RAIL_Z = 8.0
HINGE_Z = 93.0          # lid pin axis, shared by chest and lid knuckles


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


def build_chest() -> trimesh.Trimesh:
    """Open-topped gothic chest with rails, latch window and trigger bore."""
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

    cuts, adds = [], []
    for normal_x, sign, length, count, skip in ((False, -1.0, CHEST_L, 3, True),
                                                (False, 1.0, CHEST_L, 3, False),
                                                (True, -1.0, CHEST_W, 2, False),
                                                (True, 1.0, CHEST_W, 2, False)):
        c, a = _wall_decoration(length, sign, sign, normal_x, count, skip)
        cuts += c
        adds += a

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

        cylinder(6.4 / 2.0, 40.0, (-CHEST_L / 2.0, 0.0, 30.0), (1.0, 0.0, 0.0)),
    ]
    body = difference(body, service)

    # Fixed scissor pivots and the peg sockets for latch bracket and band
    # anchor. The scissor pivot sits at x = -22 so the platform stays inside
    # the chest over the whole stroke (see docs, kinematics table).
    posts = []
    for sy in (-1.0, 1.0):
        posts.append(box((12.0, 6.0, 14.0), (-22.0, sy * 26.0, FLOOR + 7.0)))
        posts.append(cylinder(6.0, 6.0, (-22.0, sy * 26.0, RAIL_Z),
                              (0.0, 1.0, 0.0)))
    body = union([body, *posts])
    sockets = [cylinder(4.2 / 2.0, 6.0, (x, y, FLOOR), (0.0, 0.0, 1.0))
               for x, y in ((14.0, -40.0), (-14.0, -40.0),
                            (-76.0, 34.0), (-76.0, -34.0))]
    sockets.append(cylinder(3.2 / 2.0, 80.0, (-22.0, 0.0, RAIL_Z),
                            (0.0, 1.0, 0.0)))
    body = difference(body, sockets)

    # Hinge knuckles for the lid, at the back wall.
    # Hinge knuckles on short columns that rise off the cornice, so the pin
    # axis matches the lid knuckles at z = 93 and the lid can swing clear.
    hx = -CHEST_L / 2.0 + PROUD - 4.0
    knuckles = []
    for y in (-34.0, 34.0):
        knuckles.append(box((10.0, 14.0, 10.0), (hx, y, BODY_H + 2.0)))
        knuckles.append(cylinder(5.0, 14.0, (hx, y, HINGE_Z), (0.0, 1.0, 0.0)))
    body = union([body, *knuckles])
    body = difference(body, [cylinder(1.9 / 2.0, CHEST_W + 20.0,
                                      (hx, 0.0, HINGE_Z), (0.0, 1.0, 0.0))])
    return clean(body)


def build_lid() -> trimesh.Trimesh:
    """Flat-topped gothic lid with a skull cartouche, printed face down."""
    top = box((CHEST_L, CHEST_W, 6.0), (0.0, 0.0, LID_H - 3.0))
    frame = box((CHEST_L + 2 * PROUD, CHEST_W + 2 * PROUD, 6.0),
                (0.0, 0.0, LID_H - 9.0))
    step = box((CHEST_L + PROUD, CHEST_W + PROUD, 3.0),
               (0.0, 0.0, LID_H - 10.5))
    spigot = box((CHEST_L - 2 * WALL - 0.6, CHEST_W - 2 * WALL - 0.6, 12.0),
                 (0.0, 0.0, 6.0))
    spigot = difference(spigot, [box((CHEST_L - 2 * WALL - 2 * 3.6,
                                      CHEST_W - 2 * WALL - 2 * 3.6, 16.0),
                                     (0.0, 0.0, 6.0))])

    body = union([top, frame, step, spigot])

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

    body = union([body, cartouche, bead, *beads, *wings])

    # Lid sits with its local z = 0 at chest z = LID_DROP, so the knuckle at
    # local z = 19 lands on the shared hinge axis z = 93.
    knuckles = [cylinder(5.0, 13.0, (-CHEST_L / 2.0 + PROUD - 4.0, y, LID_H - 5.0),
                         (0.0, 1.0, 0.0)) for y in (-50.0, -18.0, 18.0, 50.0)]
    body = union([body, *knuckles])
    body = difference(body, [cylinder(2.0 / 2.0, CHEST_W + 24.0,
                                      (-CHEST_L / 2.0 + PROUD - 4.0, 0.0,
                                       LID_H - 5.0), (0.0, 1.0, 0.0))])
    return clean(body)


if __name__ == "__main__":
    for name, mesh in (("chest", build_chest()), ("lid", build_lid())):
        print(f"{name:6s} faces {len(mesh.faces):6d} watertight {mesh.is_watertight} "
              f"bodies {len(mesh.split(only_watertight=False))} "
              f"euler {mesh.euler_number} extents {np.round(mesh.extents, 1).tolist()}")
        mesh.export(f"model-sources/ghouls-grip/reference/_{name}.stl")
    _ = intersection
