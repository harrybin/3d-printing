"""Working mechanism for the Ghoul's Grip automaton box.

Single stage scissor, rubber band drive, rocker latch, winding crank and the
skeletal forearm that carries the hand.  All numbers come from the kinematic
chain documented in docs/ghouls-grip-masse-und-bauanleitung.md:

    arm length           L = 72 mm (pivot to pivot)
    retracted            theta = 18 deg  ->  h =  22.2 mm
    deployed             theta = 78 deg  ->  h =  70.4 mm
    slider travel        x = +40.5 -> -13.0 mm  (53.5 mm)

The lid has its own opening bands and is released by the same rocker as the
slider.  A control cord with deliberate slack keeps the hand folded during the
first part of the lift; once taut, it unwraps from a sector drum on the
forearm hinge and rotates the hand into its presentation angle.

Every part is modelled in its print orientation: flat parts lie in XY with
their thickness along Z, so nothing needs support.
"""

from __future__ import annotations

import numpy as np
import trimesh

from mesh_kit import (box, clean, cylinder, difference, rounded_box, sphere,
                      union, fuse)
from sdf_bones import bone, segment_mesh, sphere as sdf_sphere

ARM_L = 72.0
ARM_W = 12.0
ARM_T = 4.0
PIVOT_D = 3.2
PIN_D = 3.0
THETA_MIN = 18.0
THETA_MAX = 78.0

RAIL_W = 4.0
RAIL_D = 3.0
RAIL_Z = 8.0
CHEST_W = 120.0
WALL = 3.0

SCISSOR_Y = 40.0        # twin scissor planes flank the folded hand
FLOOR_PIVOT_X = 0.0
PLATFORM_PIN_X = -28.0
PLATFORM_L = 78.0
PLATFORM_W = 90.0
PLATFORM_T = 6.0
ARM_HINGE_X = 33.0
ARM_HINGE_Z = 22.0
STOW_ANGLE = -105.0
DEPLOYED_FOREARM_ANGLE = -45.0
HAND_PALM_ROLL = -75.0

FOREARM_ENGAGE_THETA = 45.0
FOREARM_CORD_Y = 34.0
FOREARM_ANCHOR_X = 70.0
FOREARM_ANCHOR_Y = 52.0
FOREARM_ANCHOR_Z = 72.0
FOREARM_CORD_ANCHOR = np.array([
    FOREARM_ANCHOR_X, FOREARM_ANCHOR_Y, FOREARM_ANCHOR_Z,
])
FOREARM_GUIDE_LOCAL = np.array([25.0, 48.0, 10.0])

FIT = 0.4               # running clearance on printed sliding fits


def slider_x(theta: float) -> float:
    return FLOOR_PIVOT_X + ARM_L * np.cos(np.deg2rad(theta))


def platform_origin(theta: float) -> np.ndarray:
    lift = ARM_L * np.sin(np.deg2rad(theta))
    return np.array([
        FLOOR_PIVOT_X - PLATFORM_PIN_X,
        0.0,
        RAIL_Z + lift + 8.0,
    ])


def forearm_hinge(theta: float) -> np.ndarray:
    return platform_origin(theta) + np.array(
        [ARM_HINGE_X, 0.0, ARM_HINGE_Z]
    )


def forearm_cord_guide(theta: float) -> np.ndarray:
    return platform_origin(theta) + FOREARM_GUIDE_LOCAL


def forearm_cord_distance(theta: float) -> float:
    return float(np.linalg.norm(
        forearm_cord_guide(theta) - FOREARM_CORD_ANCHOR
    ))


FOREARM_CORD_TRAVEL = (
    forearm_cord_distance(THETA_MAX)
    - forearm_cord_distance(FOREARM_ENGAGE_THETA)
)
FOREARM_SECTOR_R = FOREARM_CORD_TRAVEL / np.deg2rad(
    DEPLOYED_FOREARM_ANGLE - STOW_ANGLE
)
FOREARM_CORD_X = float(forearm_hinge(THETA_MIN)[0] + FOREARM_SECTOR_R)
RETRACTED_SLIDER_X = slider_x(THETA_MIN)
LATCH_SUPPORT_XS = (-8.0, RETRACTED_SLIDER_X + 8.0)
LATCH_AXIS_Y = -50.0
LATCH_AXIS_Z = 24.0
LATCH_TRIGGER_Y = -53.0
LATCH_RETURN_Y = -49.0
LATCH_RELEASE_TRAVEL = 12.0
CRANK_SPOOL_X = 82.0


def forearm_angle(theta: float) -> float:
    """Angle produced when the taut control cord unwraps from its sector."""
    if theta <= FOREARM_ENGAGE_THETA:
        return STOW_ANGLE
    used = forearm_cord_distance(theta) - forearm_cord_distance(
        FOREARM_ENGAGE_THETA
    )
    return float(min(DEPLOYED_FOREARM_ANGLE, STOW_ANGLE + np.rad2deg(
        used / FOREARM_SECTOR_R
    )))


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
    # The carriage is asymmetric around its pivot. Its short rear overhang and
    # forward band hooks preserve positive clearance to the fixed posts at the
    # compact 78 degree deployed stop.
    body = box((30.0, span, 10.0), (7.0, 0.0, RAIL_Z + 3.0))

    tongues = [box((30.0, 2.0 * (RAIL_D - 0.4), RAIL_W - 0.4),
                   (7.0, sy * inner, RAIL_Z + RAIL_W / 2.0))
               for sy in (-1.0, 1.0)]

    lugs = [_lug(PIVOT_D, 16.0, ARM_T + 2.0 * FIT + 2.0,
                 (0.0, sy * SCISSOR_Y, RAIL_Z + 8.0 + 8.0))
            for sy in (-1.0, 1.0)]

    hooks = []
    for sy in (-1.0, 1.0):
        hooks.append(box((8.0, 8.0, 12.0), (8.0, sy * 50.0, RAIL_Z + 4.0)))
        hooks.append(cylinder(4.0, 8.0, (8.0, sy * 50.0, RAIL_Z + 12.0),
                              (0.0, 1.0, 0.0)))

    body = union([body, *tongues, *lugs, *hooks])
    # The pawl enters this notch only at the fully retracted slider position.
    # The axial bore is the reset-cord tie point for the right-wall crank.
    body = difference(body, [
        box((10.0, 22.0, 24.0), (0.0, -50.0, 17.0)),
        cylinder(4.0 / 2.0, 12.0, (8.0, 40.0, RAIL_Z + 12.0), (0.0, 1.0, 0.0)),
        cylinder(4.0 / 2.0, 12.0, (8.0, -40.0, RAIL_Z + 12.0), (0.0, 1.0, 0.0)),
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
        box((76.0, 4.0, PLATFORM_T), (2.0, sy * 43.0, PLATFORM_T / 2.0))
        for sy in (-1.0, 1.0)
    ]
    # Short links tie the fixed top pivots to the side rails without crossing
    # the volume occupied by the folded palm and fingers.
    pivot_links = [
        box((12.0, 12.0, PLATFORM_T),
            (PLATFORM_PIN_X, sy * SCISSOR_Y, PLATFORM_T / 2.0))
        for sy in (-1.0, 1.0)
    ]
    # The forearm hinge is at the free end, outside the stowed palm envelope.
    hinge_bridge = box((18.0, 86.0, PLATFORM_T),
                       (ARM_HINGE_X, 0.0, PLATFORM_T / 2.0))

    pins = [_lug(PIVOT_D, 16.0, ARM_T + 2.0 * FIT + 2.0,
                 (PLATFORM_PIN_X, sy * SCISSOR_Y, -8.0))
            for sy in (-1.0, 1.0)]

    slots = []
    for sy in (-1.0, 1.0):
        rail = box((68.0, ARM_T + 2.0 * FIT + 4.0, 12.0),
                   (8.0, sy * SCISSOR_Y, -6.0))
        rail = difference(rail, [box((68.0, ARM_T + 2.0 * FIT, 6.0),
                                     (8.0, sy * SCISSOR_Y, -7.0))])
        slots.append(rail)

    arm_ears = [_lug(PIN_D + 0.4, 26.0, 6.0,
                     (ARM_HINGE_X, sy * 11.0, ARM_HINGE_Z))
                for sy in (-1.0, 1.0)]

    # The finger tendon bundle terminates at the rear eye.
    eyes = []
    for x, y in ((ARM_HINGE_X - 14.0, 36.0),):
        post = cylinder(4.0, 10.0, (x, y, PLATFORM_T + 5.0))
        post = difference(post, [cylinder(1.5, 12.0,
                                          (x, y, PLATFORM_T + 6.0),
                                          (0.0, 1.0, 0.0))])
        eyes.append(post)

    hinge_gussets = [
        box((18.0, 8.0, ARM_HINGE_Z - 13.0),
            (ARM_HINGE_X, sy * 11.0, (ARM_HINGE_Z - 13.0) / 2.0))
        for sy in (-1.0, 1.0)
    ]
    eye_gusset = box((8.0, 12.0, PLATFORM_T),
                     (ARM_HINGE_X - 14.0, 40.0, PLATFORM_T / 2.0))
    cord_guide_support = box((10.0, 8.0, 10.0), (25.0, 47.0, 5.0))
    cord_guide = cylinder(4.0, 14.0, FOREARM_GUIDE_LOCAL,
                          (0.0, 0.0, 1.0))
    return clean(union([*side_rails, *pivot_links, hinge_bridge,
                        *pins, *slots, *arm_ears, *eyes,
                        *hinge_gussets, eye_gusset,
                        cord_guide_support, cord_guide]))

def build_latch() -> trimesh.Trimesh:
    """Vertical internal latch raised by the skull plunger's cam face.

    The overhead bridge and pawl translate together.  Twelve millimetres of
    lift clears the complete slider envelope without any rocker arm crossing
    the carriage path.
    """
    bridge = rounded_box(
        (80.0, 6.0, 6.0), 2.0, (34.0, -49.0, 46.0)
    )
    pawl_drop = rounded_box(
        (6.0, 4.0, 34.0), 1.5,
        (RETRACTED_SLIDER_X, -51.0, 31.0)
    )
    pawl_tab = rounded_box(
        (4.0, 6.0, 4.0), 1.0,
        (RETRACTED_SLIDER_X, -51.0, 15.0)
    )
    cam_points = np.array([
        [-53.0, 38.0],
        [-51.0, 50.0],
        [-43.0, 50.0],
        [-39.0, 38.0],
    ])
    cam_yz = np.column_stack([
        np.zeros(len(cam_points)),
        cam_points[:, 0],
        cam_points[:, 1],
    ])
    cam = trimesh.Trimesh(
        vertices=np.vstack([
            cam_yz - [4.0, 0.0, 0.0],
            cam_yz + [4.0, 0.0, 0.0],
        ])
    ).convex_hull
    return_eye = cylinder(5.0, 6.0, (-4.0, LATCH_RETURN_Y, 52.0),
                          (1.0, 0.0, 0.0))
    body = union([bridge, pawl_drop, pawl_tab, cam, return_eye])
    return clean(difference(body, [
        cylinder(2.0, 10.0, (-4.0, LATCH_RETURN_Y, 52.0),
                 (1.0, 0.0, 0.0)),
    ]))


def build_latch_bracket() -> trimesh.Trimesh:
    """Internal guide cage for the vertically sliding latch."""
    x_mid = sum(LATCH_SUPPORT_XS) / 2.0
    span = LATCH_SUPPORT_XS[1] - LATCH_SUPPORT_XS[0]
    # The frame clears the inward-projecting front scrollwork. Two local pads
    # leave a 0.1 mm adhesive gap to the plain inner wall outside that relief.
    outer = box((span + 18.0, 22.1, 34.0), (x_mid, -45.05, 51.0))
    channel = box((span + 10.0, 19.0, 38.0), (x_mid, -45.0, 51.0))
    frame = difference(outer, [channel])
    mounting_pads = [
        box((8.0, 1.8, 20.0), (x, -56.0, 51.0))
        for x in (-12.0, 80.0)
    ]
    return clean(union([frame, *mounting_pads]))


def build_crank_spool() -> trimesh.Trimesh:
    """Internal reset spool with a keyed shaft through the right wall."""
    shaft = cylinder(6.0 / 2.0 - 0.2, 25.0, (0.0, 0.0, -11.5))
    spool = difference(cylinder(12.0, 10.0, (0.0, 0.0, -18.0)),
                       [difference(cylinder(12.1, 6.0, (0.0, 0.0, -18.0)),
                                   [cylinder(9.0, 7.0, (0.0, 0.0, -18.0))])])
    collar = cylinder(6.0, 3.0, (0.0, 0.0, -1.5))
    key_tongue = rounded_box((4.0, 4.0, 4.0), 0.8, (0.0, 0.0, 3.0))
    body = union([shaft, spool, collar, key_tongue])
    body = difference(body, [cylinder(1.3, 20.0, (0.0, 0.0, -18.0),
                                      (1.0, 0.0, 0.0))])
    return clean(body)


def build_crank_key() -> trimesh.Trimesh:
    """Removable low-profile bone key for the reset-spool square drive."""
    collar = cylinder(7.0, 4.0, (0.0, 0.0, 5.0))
    handle = segment_mesh(
        [*bone((-13.0, 0.0, 6.2), (13.0, 0.0, 6.2), 2.3, 3.2),
         sdf_sphere((0.0, 0.0, 6.2), 3.4)], pitch=0.5, blend=1.1)
    body = union([collar, handle])
    socket = rounded_box((4.5, 4.5, 7.0), 0.9, (0.0, 0.0, 4.5))
    return clean(difference(body, [socket]))


def build_band_anchor() -> trimesh.Trimesh:
    """Two band hooks that peg into the chest floor behind the slider."""
    base = box((14.0, 108.0, 5.0), (0.0, 0.0, 2.5))
    posts, hooks = [], []
    for sy in (-1.0, 1.0):
        posts.append(box((10.0, 10.0, 18.0), (0.0, sy * 50.0, 9.0)))
        hooks.append(cylinder(4.0, 10.0, (0.0, sy * 50.0, 17.0),
                              (0.0, 1.0, 0.0)))
    pegs = [cylinder(4.0 / 2.0 - 0.15, 5.0, (0.0, sy * 44.0, -2.0))
            for sy in (-1.0, 1.0)]
    body = union([base, *posts, *hooks, *pegs])
    body = difference(body, [cylinder(2.0, 14.0, (0.0, sy * 50.0, 17.0),
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
    control_shaft = cylinder(
        4.0, FOREARM_CORD_Y + 4.0,
        (0.0, (FOREARM_CORD_Y + 4.0) / 2.0, 4.0),
        (0.0, 1.0, 0.0),
    )
    sector = cylinder(
        FOREARM_SECTOR_R + 2.5, 6.0,
        (0.0, FOREARM_CORD_Y, 4.0),
        (0.0, 1.0, 0.0),
    )
    body = union([body, spigot, ear, control_shaft, sector])
    wrist_pin_angle = HAND_PALM_ROLL + 0.5
    wrist_pin_axis = (
        np.cos(np.deg2rad(wrist_pin_angle)),
        np.sin(np.deg2rad(wrist_pin_angle)),
        0.0,
    )
    body = difference(body, [
        cylinder(1.9 / 2.0, 20.0, (0.0, 0.0, length + 9.0), wrist_pin_axis),
        cylinder((PIN_D + 0.4) / 2.0, 30.0, (0.0, 0.0, 4.0), (0.0, 1.0, 0.0)),
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
    "latch-slider": build_latch,
    "latch-bracket": build_latch_bracket,
    "crank-spool": build_crank_spool,
    "crank-key": build_crank_key,
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
