"""Working mechanism for the Ghoul's Grip automaton box.

A manually reversible skull knob turns one pinion.  The pinion drives a
horizontal rack on the proven scissor slider and a rigid lost-motion linkage
that opens and closes the lid.  A five-gear train with three idlers carried by
the platform positively unfolds the forearm; reverse knob rotation folds it
again.

There are no cords, rubber bands, springs or winding spools.  All numbers come
from the kinematic chain documented in docs/ghouls-grip-masse-und-bauanleitung.md:

    arm length           L = 72 mm (pivot to pivot)
    retracted            theta = 18 deg  ->  h =  22.2 mm
    deployed             theta = 78 deg  ->  h =  70.4 mm
    slider travel        x = +40.5 -> -13.0 mm  (53.5 mm)

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
ARM_EAR_Y = 14.0
STOW_ANGLE = -105.0
DEPLOYED_FOREARM_ANGLE = -45.0
HAND_PALM_ROLL = -75.0

FOREARM_ENGAGE_THETA = THETA_MIN
FOREARM_GEAR_Y = 50.0
FOREARM_INPUT_R = 12.0
FOREARM_GEAR_R = 12.0
FOREARM_SHAFT_D = 6.0
FOREARM_BEARING_D = 7.2
FOREARM_SOCKET_D = 6.6
FOREARM_SHAFT_FLAT_X = 1.7
FOREARM_SOCKET_FLAT_X = 1.9
FOREARM_SHAFT_Y_MIN = -22.0
FOREARM_SHAFT_Y_MAX = 53.0
FOREARM_RETAINER_Y = -19.5
FOREARM_LENGTH = 34.0
GEAR_TRAIN_DISTANCE = float(np.hypot(
    ARM_HINGE_X - PLATFORM_PIN_X, ARM_HINGE_Z - (-8.0)
))
FOREARM_IDLER_R = (
    GEAR_TRAIN_DISTANCE - FOREARM_INPUT_R - FOREARM_GEAR_R
) / 6.0
GEAR_PITCH = 4.0
GEAR_TOOTH_H = 2.2
FOREARM_INPUT_TEETH = max(
    8, int(round(2.0 * np.pi * FOREARM_INPUT_R / GEAR_PITCH))
)
FOREARM_IDLER_TEETH = max(
    8, int(round(2.0 * np.pi * FOREARM_IDLER_R / GEAR_PITCH))
)
FOREARM_OUTPUT_TEETH = max(
    8, int(round(2.0 * np.pi * FOREARM_GEAR_R / GEAR_PITCH))
)
FOREARM_GEAR_LINE_ANGLE = float(np.rad2deg(np.arctan2(
    ARM_HINGE_Z - (-8.0),
    ARM_HINGE_X - PLATFORM_PIN_X,
)))
FOREARM_INPUT_TOOTH_PHASE = FOREARM_GEAR_LINE_ANGLE + THETA_MIN
FOREARM_IDLER_TOOTH_PHASE = (
    FOREARM_GEAR_LINE_ANGLE
    + 180.0
    - 180.0 / FOREARM_IDLER_TEETH
)
# The output tooth ring faces the opposite side of the gear plane. Its phase is
# independent of the keyed D-shaft so the shaft can preserve the forearm datum.
FOREARM_OUTPUT_TOOTH_PHASE = 12.5
DRIVE_PITCH_R = 27.0
DRIVE_ROOT_R = DRIVE_PITCH_R - 1.5
DRIVE_OUTER_R = DRIVE_PITCH_R + GEAR_TOOTH_H
DRIVE_TEETH = 42
DRIVE_AXIS = np.array([0.0, -50.0, 46.0])
DRIVE_SHAFT_D = 8.0
KNOB_STOW_ANGLE = 32.0
LID_OPEN_ANGLE = 108.0
LID_OPEN_TRAVEL = 7.0
LID_HINGE_Y = 61.0
LID_HINGE_Z = 93.0
LID_LINK_PIN_Z = 70.0
LID_SECTOR_R = LID_OPEN_TRAVEL / np.deg2rad(LID_OPEN_ANGLE)
LID_TRANSFER_STEP = 2.0 * LID_SECTOR_R
LID_TRANSFER_Y = LID_HINGE_Y - 2.0 * LID_TRANSFER_STEP
LID_IDLER_Y = LID_HINGE_Y - LID_TRANSFER_STEP
LID_RACK_Y = LID_TRANSFER_Y - LID_SECTOR_R
LID_TRANSFER_BEARING_X = -DRIVE_PITCH_R - 8.0
LID_TOOTH_PHASE = 15.0
LID_LINK_FRONT_Y = -38.0
LID_YOKE_SPAN = LID_RACK_Y - LID_LINK_FRONT_Y

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


SLIDER_TRAVEL = slider_x(THETA_MIN) - slider_x(THETA_MAX)
RETRACTED_SLIDER_X = slider_x(THETA_MIN)


def forearm_angle(theta: float) -> float:
    """Angle imposed by the continuous four-mesh scissor gear train."""
    input_rotation = np.clip(
        theta - FOREARM_ENGAGE_THETA,
        0.0, THETA_MAX - FOREARM_ENGAGE_THETA,
    )
    return float(STOW_ANGLE + input_rotation * (
        FOREARM_INPUT_R / FOREARM_GEAR_R
    ))


def forearm_gear_centres() -> tuple[np.ndarray, list[np.ndarray], np.ndarray]:
    """Local platform-space centres for input, three idlers and output."""
    start = np.array([PLATFORM_PIN_X, FOREARM_GEAR_Y, -8.0])
    end = np.array([ARM_HINGE_X, FOREARM_GEAR_Y, ARM_HINGE_Z])
    vector = end - start
    distance = float(np.linalg.norm(vector[[0, 2]]))
    unit = vector / distance
    first = FOREARM_INPUT_R + FOREARM_IDLER_R
    step = 2.0 * FOREARM_IDLER_R
    idlers = [start + unit * (first + index * step) for index in range(3)]
    return start, idlers, end


def forearm_idler_angles(theta: float) -> tuple[float, float, float]:
    """Tooth phases for the three freely rotating intermediate gears."""
    delta = max(0.0, theta - FOREARM_ENGAGE_THETA)
    ratio = FOREARM_INPUT_TEETH / FOREARM_IDLER_TEETH
    tooth_phase = FOREARM_GEAR_LINE_ANGLE
    gap_phase = FOREARM_IDLER_TOOTH_PHASE
    return (
        gap_phase + delta * ratio,
        tooth_phase - delta * ratio,
        gap_phase + delta * ratio,
    )


def drive_angle(theta: float) -> float:
    """Clockwise pinion travel from the retracted skull-knob stop."""
    return np.rad2deg(
        (RETRACTED_SLIDER_X - slider_x(theta)) / DRIVE_PITCH_R
    )


def lid_angle_from_travel(rise: float) -> float:
    """Lid sector angle after the lost-motion rack has taken up."""
    used = np.clip(rise, 0.0, LID_OPEN_TRAVEL)
    return -float(np.rad2deg(used / LID_SECTOR_R))


def lid_angle(theta: float) -> float:
    """Fast cam opening followed by a captured vertical dwell."""
    rise = min(RETRACTED_SLIDER_X - slider_x(theta), SLIDER_TRAVEL)
    return lid_angle_from_travel(rise)


def _spur_gear(root_r: float, tooth_h: float, teeth: int,
               width: float, hub_r: float | None = None,
               rim: float = 2.4, spokes: int = 6) -> trimesh.Trimesh:
    """Printable coarse spur gear with rectangular FDM-safe teeth."""
    blank = cylinder(root_r, width, (0.0, 0.0, width / 2.0))
    parts = []
    if hub_r is None:
        parts.append(blank)
    else:
        inner_r = root_r - rim
        parts.extend([
            difference(blank, [
                cylinder(inner_r, width + 2.0,
                         (0.0, 0.0, width / 2.0))
            ]),
            cylinder(hub_r, width, (0.0, 0.0, width / 2.0)),
        ])
        spoke_length = inner_r - hub_r + 0.8
        for index in range(spokes):
            spoke = box(
                (spoke_length, 2.4, width),
                ((inner_r + hub_r) / 2.0, 0.0, width / 2.0),
            )
            spoke.apply_transform(trimesh.transformations.rotation_matrix(
                2.0 * np.pi * index / spokes, (0.0, 0.0, 1.0)
            ))
            parts.append(spoke)
    tooth_w = 0.32 * 2.0 * np.pi * (root_r + tooth_h / 2.0) / teeth
    tooth_l = tooth_h + 0.4
    for index in range(teeth):
        angle = 2.0 * np.pi * index / teeth
        tooth = box(
            (tooth_l, tooth_w, width),
            (root_r + tooth_h / 2.0, 0.0, width / 2.0),
        )
        tooth.apply_transform(trimesh.transformations.rotation_matrix(
            angle, (0.0, 0.0, 1.0)
        ))
        parts.append(tooth)
    return clean(union(parts))


def _rack_teeth(x_positions, y: float, z0: float,
                tooth_w: float = 2.1) -> list[trimesh.Trimesh]:
    return [
        box((tooth_w, 7.0, GEAR_TOOTH_H), (x, y, z0 + GEAR_TOOTH_H / 2.0))
        for x in x_positions
    ]


def _d_prism(diameter: float, length: float, flat_x: float,
             centre=(0.0, 0.0, 0.0)) -> trimesh.Trimesh:
    """D-profile shaft or cutter with its axis along Y."""
    body = cylinder(diameter / 2.0, length, (0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0))
    cutter = box(
        (diameter * 2.0, length + 2.0, diameter * 2.0),
        (flat_x + diameter, 0.0, 0.0),
    )
    body = difference(body, [cutter])
    body.apply_translation(np.asarray(centre, dtype=float))
    return clean(body)


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
    lightening = [
        rounded_box((18.0, 5.6, ARM_T + 2.0), 2.4,
                    (sx * 14.0, 0.0, ARM_T / 2.0))
        for sx in (-1.0, 1.0)
    ]
    body = difference(body, [*bores, *lightening])
    return clean(body)


def build_slider() -> trimesh.Trimesh:
    """Rack-driven carriage running in the 4 x 3 mm wall grooves."""
    inner = CHEST_W / 2.0 - WALL           # 57.0
    span = 2.0 * inner - FIT               # between the walls
    # The carriage is asymmetric around its pivot. Its short rear overhang and
    # forward band hooks preserve positive clearance to the fixed posts at the
    # compact 78 degree deployed stop.
    frame_z = RAIL_Z + 3.0
    frame_wall = 4.0
    body = union([
        box((30.0, frame_wall, 10.0),
            (7.0, sy * (span - frame_wall) / 2.0, frame_z))
        for sy in (-1.0, 1.0)
    ] + [
        box((frame_wall, span - 2.0 * frame_wall, 10.0),
            (7.0 + sx * (30.0 - frame_wall) / 2.0, 0.0, frame_z))
        for sx in (-1.0, 1.0)
    ] + [
        box((5.0, span - 2.0 * frame_wall, 10.0),
            (0.0, 0.0, frame_z))
    ])

    tongues = [box((30.0, 2.0 * (RAIL_D - 0.4), RAIL_W - 0.4),
                   (7.0, sy * inner, RAIL_Z + RAIL_W / 2.0))
               for sy in (-1.0, 1.0)]

    lugs = [_lug(PIVOT_D, 16.0, ARM_T + 2.0 * FIT + 2.0,
                 (0.0, sy * SCISSOR_Y, RAIL_Z + 8.0 + 8.0))
            for sy in (-1.0, 1.0)]

    rack_bar = box((80.0, 8.0, 5.0), (-32.0, -50.0, 15.5))
    rack_bar = difference(rack_bar, [
        box((8.0, 4.8, 3.8), (x, -50.0, 14.4))
        for x in np.arange(-65.0, 2.0, 11.0)
    ])
    rack_teeth = _rack_teeth(
        np.arange(-70.0, 8.1, GEAR_PITCH), -50.0, 18.0
    )

    return clean(union([body, *tongues, *lugs, rack_bar, *rack_teeth]))


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
    hinge_bridge = union([
        box((4.0, 86.0, PLATFORM_T),
            (ARM_HINGE_X + sx * 7.0, 0.0, PLATFORM_T / 2.0))
        for sx in (-1.0, 1.0)
    ] + [
        box((18.0, 5.0, PLATFORM_T),
            (ARM_HINGE_X, y, PLATFORM_T / 2.0))
        for y in (-40.5, -14.0, 0.0, 14.0, 40.5)
    ])

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

    arm_ears = [_lug(FOREARM_BEARING_D, 26.0, 6.0,
                     (ARM_HINGE_X, sy * ARM_EAR_Y, ARM_HINGE_Z))
                for sy in (-1.0, 1.0)]

    gear_start, idler_centres, gear_end = forearm_gear_centres()
    gear_vector = gear_end - gear_start
    gear_distance = float(np.linalg.norm(gear_vector[[0, 2]]))
    gear_rail = box(
        (gear_distance - 8.0, 6.0, 6.0),
        (0.0, 0.0, 0.0),
    )
    gear_rail.apply_transform(trimesh.transformations.rotation_matrix(
        -np.arctan2(gear_vector[2], gear_vector[0]),
        (0.0, 1.0, 0.0),
    ))
    # Keep the support on the inboard side of the gear plane. The original rail
    # occupied the same Y volume as all five gears, making the rendered assembly
    # impossible. Inboard placement also leaves the outboard side open so the
    # output gear and its long D-shaft can be inserted axially.
    gear_rail.apply_translation((gear_start + gear_end) / 2.0
                                + np.array([0.0, -6.0, 0.0]))
    idler_posts = [
        cylinder(1.4, 12.0, centre + np.array([0.0, -3.0, 0.0]),
                 (0.0, 1.0, 0.0))
        for centre in idler_centres
    ]

    hinge_gussets = [
        box((3.2, 8.0, ARM_HINGE_Z - 13.0),
            (ARM_HINGE_X + dx, sy * ARM_EAR_Y,
             (ARM_HINGE_Z - 13.0) / 2.0))
        for sy in (-1.0, 1.0)
        for dx in (-6.4, 0.0, 6.4)
    ]
    body = union([*side_rails, *pivot_links, hinge_bridge,
                  *pins, *slots, *arm_ears, *idler_posts,
                  gear_rail, *hinge_gussets])
    # Axial installation tunnel for the removable D-shaft/output gear.
    input_key_slot = [
        cylinder(
            1.8,
            12.0,
            (
                PLATFORM_PIN_X + 8.0 * np.cos(np.deg2rad(theta)),
                SCISSOR_Y,
                -8.0 - 8.0 * np.sin(np.deg2rad(theta)),
            ),
            (0.0, 1.0, 0.0),
        )
        for theta in np.linspace(THETA_MIN - 3.0, THETA_MAX + 3.0, 25)
    ]
    body = difference(body, [
        cylinder(
            FOREARM_BEARING_D / 2.0,
            86.0,
            (ARM_HINGE_X, 20.0, ARM_HINGE_Z),
            (0.0, 1.0, 0.0),
        ),
        *input_key_slot,
    ])
    # The long coaxial cut can leave sub-mm boolean crumbs at tangent edges.
    # They are not part of the platform and must not become loose print bodies.
    components = body.split(only_watertight=False)
    return clean(max(components, key=lambda component: abs(component.volume)))


def build_drive_pinion() -> trimesh.Trimesh:
    """Main pinion with an integral bearing shaft through the front wall."""
    gear = _spur_gear(
        DRIVE_ROOT_R, GEAR_TOOTH_H, DRIVE_TEETH, 8.0,
        hub_r=7.2, rim=3.0,
    )
    shaft = cylinder(DRIVE_SHAFT_D / 2.0, 24.0, (0.0, 0.0, 12.0))
    collar = cylinder(7.0, 3.0, (0.0, 0.0, 9.5))
    return clean(union([gear, shaft, collar]))


def build_lid_rack() -> trimesh.Trimesh:
    """Main vertical rack with a downward lost-motion slot for the lid."""
    spine = box((67.0, 8.0, 5.0), (6.5, 0.0, 0.0))
    spine = difference(spine, [
        box((8.4, 5.6, 7.0), (x, 0.0, 0.0))
        for x in np.arange(-20.0, 34.0, 10.0)
    ])
    teeth = [
        box((2.1, 7.0, GEAR_TOOTH_H),
            (x, 0.0, -(5.0 + GEAR_TOOTH_H) / 2.0))
        for x in np.arange(-24.0, 38.1, GEAR_PITCH)
    ]
    dwell = SLIDER_TRAVEL - LID_OPEN_TRAVEL
    flange = box(
        (dwell + 12.0, 18.0, 8.0),
        (40.0 - dwell / 2.0, 9.0, 0.0),
    )
    lost_slot = rounded_box(
        (dwell + 8.0, 7.2, 12.0), 3.0,
        (40.0 - dwell / 2.0, 12.0, 0.0),
    )
    return clean(difference(union([spine, flange, *teeth]), [lost_slot]))


def build_lid_follower_rack() -> trimesh.Trimesh:
    """Seven-millimetre yoke linking the front lost slot to the lid gear."""
    rear_spine = box((18.0, 2.4, 6.0),
                    (0.0, LID_YOKE_SPAN - 2.7, 0.0))
    teeth = [
        box((1.6, GEAR_TOOTH_H, 6.0),
            (x, LID_YOKE_SPAN - 0.4, 0.0))
        for x in np.arange(-6.0, 6.1, GEAR_PITCH)
    ]
    connector = box(
        (6.0, LID_YOKE_SPAN + 5.0, 6.0),
        (-20.0, LID_YOKE_SPAN / 2.0, 0.0),
    )
    connector = difference(connector, [
        box((2.8, 9.0, 8.0), (-20.0, y, 0.0))
        for y in np.arange(8.0, LID_YOKE_SPAN - 4.0, 12.0)
    ])
    rear_link = box((19.0, 5.0, 6.0),
                    (-12.5, LID_YOKE_SPAN - 3.7, 0.0))
    pin = cylinder(3.0, 14.0, (-20.0, 0.0, 0.0))
    return clean(union([rear_spine, connector, rear_link, pin, *teeth]))


def build_lid_crank() -> trimesh.Trimesh:
    """Small hinge sector gear driven by the secondary lid rack."""
    teeth = max(6, int(round(2.0 * np.pi * LID_SECTOR_R / GEAR_PITCH)))
    gear = _spur_gear(LID_SECTOR_R - 1.5, GEAR_TOOTH_H,
                      teeth, 8.0)
    gear.apply_transform(trimesh.transformations.rotation_matrix(
        np.deg2rad(LID_TOOTH_PHASE), (0.0, 0.0, 1.0)))
    # The key points inward, above the rim, rather than down through the rear
    # wall. Its longer axial tab enters the matching underside lid socket.
    coupling = box((5.0, 18.0, 2.6), (0.0, -7.0, 9.7))
    hub = cylinder(2.0, 11.0, (0.0, 0.0, 5.5))
    return clean(difference(union([gear, hub, coupling]), [
        cylinder(2.0 / 2.0, 15.0, (0.0, 0.0, 5.5))
    ]))


def build_lid_transfer_gear() -> trimesh.Trimesh:
    """Equal-ratio transfer gear with an integral, axially inserted journal."""
    teeth = max(6, int(round(2.0 * np.pi * LID_SECTOR_R / GEAR_PITCH)))
    gear = _spur_gear(LID_SECTOR_R - 1.5, GEAR_TOOTH_H,
                      teeth, 4.0)
    gear.apply_transform(trimesh.transformations.rotation_matrix(
        np.deg2rad(LID_TOOTH_PHASE), (0.0, 0.0, 1.0)))
    journal = cylinder(1.4, 18.0, (0.0, 0.0, -5.0))
    return clean(difference(union([gear, journal]), [
        cylinder(0.95, 6.0, (0.0, 0.0, -12.0), (1.0, 0.0, 0.0)),
    ]))


def build_scissor_drive_gear() -> trimesh.Trimesh:
    """Continuous input gear positively keyed to one scissor arm."""
    gear = _spur_gear(
        FOREARM_INPUT_R - 1.5,
        GEAR_TOOTH_H,
        FOREARM_INPUT_TEETH,
        6.0,
        hub_r=4.2,
    )
    gear.apply_transform(trimesh.transformations.rotation_matrix(
        np.deg2rad(FOREARM_INPUT_TOOTH_PHASE), (0.0, 0.0, 1.0)
    ))
    key_peg = cylinder(1.4, 10.0, (8.0, 0.0, 5.0))
    return clean(difference(union([gear, key_peg]), [
        cylinder(PIVOT_D / 2.0, 10.0, (0.0, 0.0, 3.0))
    ]))


def build_idler_gear() -> trimesh.Trimesh:
    """One of two equal intermediate gears reversing the input rotation."""
    gear = _spur_gear(
        FOREARM_IDLER_R - 1.5,
        GEAR_TOOTH_H,
        FOREARM_IDLER_TEETH,
        6.0,
    )
    return clean(difference(gear, [
        cylinder(3.2 / 2.0, 10.0, (0.0, 0.0, 3.0))
    ]))


def build_forearm_output_gear() -> trimesh.Trimesh:
    """Mechanism-color output gear with a removable keyed hinge shaft.

    The long D-shaft is inserted from the gear side after the bone-color
    forearm has been lowered between the platform ears. A 1.75 mm filament
    cross pin at the opposite end retains the assembly axially.
    """
    gear = _spur_gear(
        FOREARM_GEAR_R - 1.5,
        GEAR_TOOTH_H,
        FOREARM_OUTPUT_TEETH,
        6.0,
        hub_r=4.6,
    )
    gear.apply_transform(trimesh.transformations.rotation_matrix(
        np.deg2rad(FOREARM_OUTPUT_TOOTH_PHASE), (0.0, 0.0, 1.0)
    ))
    gear.apply_translation((0.0, 0.0, -3.0))
    gear.apply_transform(trimesh.transformations.rotation_matrix(
        -np.pi / 2.0, (1.0, 0.0, 0.0)
    ))
    gear.apply_translation((0.0, FOREARM_GEAR_Y, 0.0))

    shaft_length = FOREARM_SHAFT_Y_MAX - FOREARM_SHAFT_Y_MIN
    shaft = _d_prism(
        FOREARM_SHAFT_D,
        shaft_length,
        FOREARM_SHAFT_FLAT_X,
        (0.0, (FOREARM_SHAFT_Y_MIN + FOREARM_SHAFT_Y_MAX) / 2.0, 0.0),
    )
    body = union([gear, shaft])
    retainer_hole = cylinder(
        1.9 / 2.0, 10.0,
        (0.0, FOREARM_RETAINER_Y, 0.0),
        (1.0, 0.0, 0.0),
    )
    return clean(difference(body, [retainer_hole]))


def build_forearm(length: float = FOREARM_LENGTH) -> trimesh.Trimesh:
    """Bone-color radius and ulna with a keyed removable hinge socket."""
    shafts = [
        *bone((-7.0, 0.0, 6.0), (-4.5, 0.0, length - 6.0), 4.2, 6.2),
        *bone((7.0, 0.0, 6.0), (4.5, 0.0, length - 6.0), 4.6, 5.6),
        sdf_sphere((0.0, 0.0, length - 4.0), 8.4),
        sdf_sphere((0.0, 0.0, 8.0), 9.0),
    ]
    body = segment_mesh(shafts, pitch=0.6, blend=2.4)

    spigot = cylinder(12.0 / 2.0 - 0.2, 18.0, (0.0, 0.0, length + 4.0))
    ear = box((22.0, 8.0, 14.0), (0.0, 0.0, 4.0))
    body = union([body, spigot, ear])
    wrist_pin_angle = HAND_PALM_ROLL + 0.5
    wrist_pin_axis = (
        np.cos(np.deg2rad(wrist_pin_angle)),
        np.sin(np.deg2rad(wrist_pin_angle)),
        0.0,
    )
    body = difference(body, [
        cylinder(1.9 / 2.0, 20.0, (0.0, 0.0, length + 9.0), wrist_pin_axis),
        _d_prism(
            FOREARM_SOCKET_D,
            24.0,
            FOREARM_SOCKET_FLAT_X,
            (0.0, 0.0, 4.0),
        ),
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
    # Pack the tall follower beside the slider, not in the final plate row.
    "lid-follower-rack": build_lid_follower_rack,
    "platform": build_platform,
    "drive-pinion": build_drive_pinion,
    "lid-rack": build_lid_rack,
    "lid-crank": build_lid_crank,
    "lid-transfer-gear": build_lid_transfer_gear,
    "scissor-drive-gear": build_scissor_drive_gear,
    "idler-gear": build_idler_gear,
    "forearm-output-gear": build_forearm_output_gear,
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
