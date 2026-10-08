"""Working mechanism for the Ghoul's Grip automaton box.

Single stage scissor, rubber band drive, rocker latch, winding crank and the
skeletal forearm that carries the hand.  All numbers come from the kinematic
chain documented in docs/ghouls-grip-masse-und-bauanleitung.md:

    arm length           L = 90 mm (pivot to pivot)
    retracted            theta = 16 deg  ->  h =  24.8 mm
    deployed             theta = 76 deg  ->  h =  87.3 mm
    slider travel        x = +64.5 ->  -0.2 mm  (64.7 mm)
    platform top         8 + 87.3 + 6 = 101.3 mm, i.e. 15 mm over the rim

Every part is modelled in its print orientation: flat parts lie in XY with
their thickness along Z, so nothing needs support.
"""

from __future__ import annotations

import numpy as np
import trimesh

from mesh_kit import (box, clean, cylinder, difference, rounded_box, sphere,
                      union, fuse)
from sdf_bones import bone, segment_mesh, sphere as sdf_sphere

ARM_L = 90.0
ARM_W = 12.0
ARM_T = 4.0
PIVOT_D = 3.2
PIN_D = 3.0

RAIL_W = 4.0
RAIL_D = 3.0
RAIL_Z = 8.0
CHEST_W = 120.0
WALL = 3.0

SCISSOR_Y = 26.0        # half spacing of the two scissor planes
FLOOR_PIVOT_X = -22.0
PLATFORM_L = 104.0
PLATFORM_W = 104.0
PLATFORM_T = 6.0
ARM_HINGE_X = 42.0
ARM_HINGE_Z = 19.0
STOW_ANGLE = -100.0

FIT = 0.4               # running clearance on printed sliding fits


def _lug(hole_d: float, height: float, thickness: float,
         centre, axis=(0.0, 1.0, 0.0)) -> trimesh.Trimesh:
    """Upstanding ear with a cross bore - the generic pin mount."""
    radius = min(height * 0.35, thickness * 0.45, height * 0.45)
    body = rounded_box((height, thickness, height), radius, (0, 0, 0))
    body = union([body, box((height, thickness, height / 2.0),
                            (0.0, 0.0, -height / 4.0))])
    body = difference(body, [cylinder(hole_d / 2.0, thickness + 4.0,
                                      (0.0, 0.0, 0.0), (0.0, 1.0, 0.0))])
    if tuple(axis) != (0.0, 1.0, 0.0):
        body.apply_transform(trimesh.geometry.align_vectors([0, 1, 0], axis))
    body.apply_translation(np.asarray(centre, dtype=float))
    return body


def build_scissor_arm() -> trimesh.Trimesh:
    """One of four identical scissor arms, printed flat."""
    shaft = box((ARM_L, ARM_W, ARM_T), (0.0, 0.0, ARM_T / 2.0))
    ends = [cylinder(ARM_W / 2.0, ARM_T, (sx * ARM_L / 2.0, 0.0, ARM_T / 2.0))
            for sx in (-1.0, 1.0)]
    # Waist relief keeps the arm light without weakening the pivot bosses.
    body = union([shaft, *ends])
    bores = [cylinder(PIVOT_D / 2.0, ARM_T + 4.0, (x, 0.0, ARM_T / 2.0))
             for x in (-ARM_L / 2.0, 0.0, ARM_L / 2.0)]
    body = difference(body, bores)
    return clean(body)


def build_slider() -> trimesh.Trimesh:
    """Rubber band driven carriage running in the 4 x 3 mm wall grooves."""
    inner = CHEST_W / 2.0 - WALL           # 57.0
    span = 2.0 * inner - FIT               # between the walls
    # The carriage is asymmetric around its pivot.  A symmetric 44 mm body
    # collides with the fixed floor pivots above 71 degrees; keeping only
    # 10 mm behind the moving pivot preserves a 5.8 mm hard clearance at the
    # 76 degree deployed stop while retaining 22 mm of structure ahead.
    body = box((32.0, span, 10.0), (6.0, 0.0, RAIL_Z + 3.0))

    tongues = [box((32.0, 2.0 * (RAIL_D - 0.4), RAIL_W - 0.4),
                   (0.0, sy * (inner + RAIL_D - 0.4 - 0.2 - (RAIL_D - 0.4)),
                    RAIL_Z + RAIL_W / 2.0))
               for sy in (-1.0, 1.0)]
    tongues = [box((32.0, 2.0 * (RAIL_D - 0.4), RAIL_W - 0.4),
                   (6.0, sy * inner, RAIL_Z + RAIL_W / 2.0))
               for sy in (-1.0, 1.0)]

    lugs = [_lug(PIVOT_D, 16.0, ARM_T + 2.0 * FIT + 2.0,
                 (0.0, sy * SCISSOR_Y, RAIL_Z + 8.0 + 8.0))
            for sy in (-1.0, 1.0)]

    hooks = []
    for sy in (-1.0, 1.0):
        hooks.append(box((8.0, 8.0, 12.0), (-8.0, sy * 40.0, RAIL_Z + 4.0)))
        hooks.append(cylinder(4.0, 8.0, (-8.0, sy * 40.0, RAIL_Z + 12.0),
                              (0.0, 1.0, 0.0)))

    body = union([body, *tongues, *lugs, *hooks])
    # Latch notch on the front edge and the cord eye for the crank.
    body = difference(body, [
        box((9.0, 10.0, 8.0), (16.0, -(inner - 3.0), RAIL_Z + 3.0)),
        cylinder(4.0 / 2.0, 12.0, (-8.0, 40.0, RAIL_Z + 12.0), (0.0, 1.0, 0.0)),
        cylinder(4.0 / 2.0, 12.0, (-8.0, -40.0, RAIL_Z + 12.0), (0.0, 1.0, 0.0)),
        cylinder(2.2 / 2.0, 60.0, (20.0, 0.0, RAIL_Z + 6.0), (1.0, 0.0, 0.0)),
    ])
    return clean(body)


def build_platform() -> trimesh.Trimesh:
    """Open lifting yoke carrying the scissor heads and skeletal forearm.

    The first prototype used a 104 x 104 mm solid candy tray.  In the stowed
    pose the real hand necessarily swept through that tray.  This yoke keeps
    the centre completely open: two rails sit against the chest side walls,
    while local bridges support only the scissor pivots and forearm hinge.
    Sweets are carried by the curled hand itself, matching the concept image.
    """
    side_rails = [
        box((94.0, 4.0, PLATFORM_T), (5.0, sy * 54.0, PLATFORM_T / 2.0))
        for sy in (-1.0, 1.0)
    ]
    # Short links tie the fixed top pivots to the side rails without crossing
    # the volume occupied by the folded palm and fingers.
    pivot_links = [
        box((12.0, 32.0, PLATFORM_T),
            (-PLATFORM_L / 2.0 + 10.0, sy * 40.0, PLATFORM_T / 2.0))
        for sy in (-1.0, 1.0)
    ]
    # The forearm hinge is at the free end, outside the stowed palm envelope.
    hinge_bridge = box((18.0, 108.0, PLATFORM_T),
                       (ARM_HINGE_X, 0.0, PLATFORM_T / 2.0))

    pins = [_lug(PIVOT_D, 16.0, ARM_T + 2.0 * FIT + 2.0,
                 (-PLATFORM_L / 2.0 + 10.0, sy * SCISSOR_Y, -8.0))
            for sy in (-1.0, 1.0)]

    slots = []
    for sy in (-1.0, 1.0):
        rail = box((70.0, ARM_T + 2.0 * FIT + 4.0, 12.0),
                   (10.0, sy * SCISSOR_Y, -6.0))
        rail = difference(rail, [box((70.0, ARM_T + 2.0 * FIT, 6.0),
                                     (10.0, sy * SCISSOR_Y, -7.0))])
        slots.append(rail)

    arm_ears = [_lug(PIN_D + 0.4, 26.0, 6.0,
                     (ARM_HINGE_X, sy * 11.0, ARM_HINGE_Z))
                for sy in (-1.0, 1.0)]

    # Two simple eyes terminate the lid cord and the five-finger tendon bundle.
    eyes = []
    for x, y in ((-PLATFORM_L / 2.0 + 30.0, -49.0),
                 (ARM_HINGE_X - 14.0, 49.0)):
        post = cylinder(4.0, 10.0, (x, y, PLATFORM_T + 5.0))
        post = difference(post, [cylinder(1.5, 12.0,
                                          (x, y, PLATFORM_T + 6.0),
                                          (0.0, 1.0, 0.0))])
        eyes.append(post)

    return clean(union([*side_rails, *pivot_links, hinge_bridge,
                        *pins, *slots, *arm_ears, *eyes]))

def build_latch() -> trimesh.Trimesh:
    """Rocker that holds the slider against the bands until the skull is pushed.

    Pivot bore runs along X at (0, -40, 24); the skull stem hits the upper arm
    at z = 46 and the hook drops out of the slider notch at z = 12.
    """
    plate = 5.0
    pts = np.array([
        [-2.0, 47.0], [6.0, 47.0], [6.0, 26.0],        # upper arm
        [4.0, 18.0], [16.0, 14.0], [16.0, 8.0],        # hook
        [-6.0, 8.0], [-6.0, 26.0], [-6.0, 42.0],
    ])
    poly = np.column_stack([np.zeros(len(pts)), pts[:, 0], pts[:, 1]])
    lever = trimesh.Trimesh(
        vertices=np.vstack([poly - [plate / 2.0, 0, 0],
                            poly + [plate / 2.0, 0, 0]])).convex_hull

    boss = cylinder(5.0, plate, (0.0, 0.0, 24.0), (1.0, 0.0, 0.0))
    body = union([lever, boss])
    body = difference(body, [cylinder((PIN_D + 0.4) / 2.0, plate + 6.0,
                                      (0.0, 0.0, 24.0), (1.0, 0.0, 0.0))])

    # Printed leaf spring pushing the hook back into the notch.
    leaf = box((plate, 1.2, 22.0), (0.0, -5.4, 13.0))
    foot = box((plate, 11.0, 3.0), (0.0, -10.0, 3.5))
    body = union([body, leaf, foot])
    body.apply_translation([0.0, -40.0, 0.0])
    return clean(body)


def build_latch_bracket() -> trimesh.Trimesh:
    """Floor bracket carrying the latch pin; pegs into the chest floor."""
    base = box((40.0, 16.0, 4.0), (0.0, -40.0, 2.0))
    posts = [box((5.0, 10.0, 26.0), (sx * 7.5, -40.0, 15.0))
             for sx in (-1.0, 1.0)]
    pegs = [cylinder(4.0 / 2.0 - 0.15, 5.0, (sx * 14.0, -40.0, -2.0))
            for sx in (-1.0, 1.0)]
    body = union([base, *posts, *pegs])
    body = difference(body, [cylinder((PIN_D + 0.3) / 2.0, 44.0,
                                      (0.0, -40.0, 24.0), (1.0, 0.0, 0.0))])
    return clean(body)


def build_crank() -> trimesh.Trimesh:
    """Skeleton key winder: shaft, cord spool and a bone shaped handle."""
    shaft = cylinder(6.0 / 2.0 - 0.2, 26.0, (0.0, 0.0, 13.0))
    spool = difference(cylinder(14.0, 10.0, (0.0, 0.0, 31.0)),
                       [difference(cylinder(14.1, 6.0, (0.0, 0.0, 31.0)),
                                   [cylinder(9.0, 7.0, (0.0, 0.0, 31.0))])])
    collar = cylinder(11.0, 3.0, (0.0, 0.0, -1.5))
    handle = segment_mesh(
        [*bone((0.0, 0.0, -6.0), (34.0, 0.0, -6.0), 3.0, 5.0),
         sdf_sphere((0.0, 0.0, -6.0), 5.5)], pitch=0.6, blend=1.6)
    body = union([shaft, spool, collar, handle])
    body = difference(body, [cylinder(1.3, 20.0, (0.0, 0.0, 31.0),
                                      (1.0, 0.0, 0.0))])
    return clean(body)


def build_band_anchor() -> trimesh.Trimesh:
    """Two band hooks that peg into the chest floor behind the slider."""
    base = box((14.0, 96.0, 5.0), (0.0, 0.0, 2.5))
    posts, hooks = [], []
    for sy in (-1.0, 1.0):
        posts.append(box((10.0, 10.0, 18.0), (0.0, sy * 40.0, 9.0)))
        hooks.append(cylinder(4.0, 10.0, (0.0, sy * 40.0, 17.0),
                              (0.0, 1.0, 0.0)))
    pegs = [cylinder(4.0 / 2.0 - 0.15, 5.0, (0.0, sy * 34.0, -2.0))
            for sy in (-1.0, 1.0)]
    body = union([base, *posts, *hooks, *pegs])
    body = difference(body, [cylinder(2.0, 14.0, (0.0, sy * 40.0, 17.0),
                                      (0.0, 1.0, 0.0)) for sy in (-1.0, 1.0)])
    return clean(body)


def build_forearm(length: float = 34.0) -> trimesh.Trimesh:
    """Radius and ulna carrying the hand, hinged to the platform."""
    shafts = [
        *bone((-7.0, 0.0, 6.0), (-4.5, 0.0, length - 6.0), 4.2, 6.2),
        *bone((7.0, 0.0, 6.0), (4.5, 0.0, length - 6.0), 4.6, 5.6),
        sdf_sphere((0.0, 0.0, length - 4.0), 8.4),
        sdf_sphere((0.0, 0.0, 8.0), 9.0),
    ]
    body = segment_mesh(shafts, pitch=0.6, blend=2.4)

    spigot = cylinder(12.0 / 2.0 - 0.2, 18.0, (0.0, 0.0, length + 4.0))
    ear = box((22.0, 6.0, 14.0), (0.0, 0.0, 4.0))
    body = union([body, spigot, ear])
    body = difference(body, [
        cylinder(1.9 / 2.0, 20.0, (0.0, 0.0, length + 9.0), (1.0, 0.0, 0.0)),
        cylinder((PIN_D + 0.4) / 2.0, 30.0, (0.0, 0.0, 4.0), (1.0, 0.0, 0.0)),
    ])
    return clean(body)


def build_pin(diameter: float, length: float) -> trimesh.Trimesh:
    """Printed pivot pin with a small head."""
    shank = cylinder(diameter / 2.0 - 0.15, length, (0.0, 0.0, length / 2.0))
    head = cylinder(diameter / 2.0 + 1.6, 1.6, (0.0, 0.0, 0.8))
    return clean(union([shank, head]))


PARTS = {
    "scissor-arm": build_scissor_arm,
    "slider": build_slider,
    "platform": build_platform,
    "latch-rocker": build_latch,
    "latch-bracket": build_latch_bracket,
    "crank": build_crank,
    "band-anchor": build_band_anchor,
    "forearm": build_forearm,
}


if __name__ == "__main__":
    for name, fn in PARTS.items():
        m = fn()
        print(f"{name:16s} faces {len(m.faces):6d} wt {m.is_watertight!s:5s} "
              f"bodies {len(m.split(only_watertight=False)):2d} "
              f"euler {m.euler_number:4d} ext {np.round(m.extents, 1).tolist()}")
        m.export(f"model-sources/ghouls-grip/reference/_{name}.stl")
    _ = (sphere, fuse)
