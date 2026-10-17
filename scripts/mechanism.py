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

import fdm_joints
from mesh_kit import (box, clean, cylinder, difference, intersection,
                      rounded_box, sphere, union, fuse)
from sdf_bones import bone, segment_mesh, sphere as sdf_sphere

ARM_L = 72.0
ARM_W = 12.0
ARM_T = 4.0
# Snap pivot pins: printed Ø4 split pins in Ø4.6 bores (0.3 mm radial running
# clearance absorbs FDM hole shrink).  A Ø4 steel dowel with the same bores is
# the documented alternative.  Barbs land in Ø6 x 1.6 counterbores so nothing
# protrudes into the neighbouring arm plane.
PIVOT_D = 4.6
PIN_D = 4.0
PIN_HEAD_D = 7.5
PIN_HEAD_T = 1.6
PIN_BARB_R = 2.55       # relaxed barb reach in the flex direction
PIN_BARB_ARC_R = 2.2    # barb arc radius: 0.1 mm clearance once closed
PIN_BARB_OFFSET = PIN_BARB_R - PIN_BARB_ARC_R   # 0.35 mm closure per half
PIN_CRUSH_R = 2.45      # follower-pin crush ribs: 0.15 mm interference
PIN_BARB_LAND = 0.4
PIN_BARB_CONE = 1.0
PIN_AXIAL_PLAY = 0.2
PIN_SLOT_W = 1.4
PIN_SLOT_REACH = 7.0    # split length behind the catch face (strain ~1 %)
PIN_FLAT_Y = -1.6       # 0.4 mm print flat on the shank
PIN_CBORE_D = 6.0
PIN_CBORE_DEPTH = 1.6
# Grip = head underside to the face the barb catches on (stack thickness).
PIN_GRIPS = {
    "floor": 18.4,      # wange 30..34, False arm 35..39, wange 46..50 (cbore)
    "slider": 11.2,     # lug 36.6..40.6, True arm 41..45, lug 45.4..49.4
    "centre": 8.4,      # False arm 35..39, True arm 41..45 (cbore)
    "gear": 16.4,       # +plane top: lug, True arm, scissor-drive gear 47..53
    "short": 6.8,       # -plane top (lug + True cbore) and both slot pins
    "idler": 11.4,      # idler 47..52 (head sunk 1 mm) plus rail 40.6..46.6
    "follower": 4.0,    # follower bar 46..50: crush-rib press pin, no barb
}
PIN_TAILS = {"follower": 6.2}   # plain tail to u 56.2 in the cam slot
PIN_QUANTITIES = {
    "floor": 2, "slider": 2, "centre": 2, "gear": 1,
    "short": 3, "idler": 3, "follower": 1,
}
THETA_MIN = 18.0
THETA_MAX = 78.0

RAIL_W = 4.0
RAIL_D = 3.0
RAIL_Z = 8.0
CHEST_W = 120.0
WALL = 3.0

SCISSOR_Y = 40.0        # twin scissor planes flank the folded hand
# Floor yoke estimates, not measured fits: keep the unchanged arm planes
# (y +/-3, thickness 4) inside an open 12 mm channel. Confirm in PLA.
FLOOR_BEARING_OFFSET = 8.0
FLOOR_BEARING_T = 4.0
FLOOR_BEARING_R = 4.6  # 3 mm radial ligament; cap clears rack underside by 0.4
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
LID_SECTOR_R = LID_OPEN_TRAVEL / np.deg2rad(LID_OPEN_ANGLE)
LID_TRANSFER_STEP = 2.0 * LID_SECTOR_R
LID_TRANSFER_Y = LID_HINGE_Y - 2.0 * LID_TRANSFER_STEP
LID_IDLER_Y = LID_HINGE_Y - LID_TRANSFER_STEP
LID_RACK_Y = LID_TRANSFER_Y - LID_SECTOR_R
LID_TRANSFER_BEARING_X = -DRIVE_PITCH_R - 8.0
LID_TRANSFER_BLOCK_W = 4.0
# Transfer-gear journal: local z = world x + DRIVE_PITCH_R (gear face at 0).
_TRANSFER_INNER_Z = LID_TRANSFER_BEARING_X + LID_TRANSFER_BLOCK_W / 2.0 \
    + DRIVE_PITCH_R
_TRANSFER_OUTER_Z = _TRANSFER_INNER_Z - LID_TRANSFER_BLOCK_W
TRANSFER_HUB_R = 2.2
TRANSFER_HUB_LEN = -_TRANSFER_INNER_Z - 0.2
TRANSFER_CROSS_Z = _TRANSFER_OUTER_Z - 0.33 - 1.75 / 2.0
# Hinge-filament spacer between the lid crank (-x face at -DRIVE_PITCH_R) and
# the lid knuckle in the service channel (x = -43): keeps the crank coupling
# engaged in the lid socket (crank axial play ~0.2 + 0.2 mm).
CRANK_SPACER_LEN = 43.0 - DRIVE_PITCH_R - 0.2
CRANK_SPACER_R = 2.5
CRANK_SPACER_BORE_R = 1.0
LID_TOOTH_PHASE = 15.0
# Slider cam: the follower pin climbs 7 mm during the first 6 mm of slider
# travel (lid fully open), then dwells on a level track for the rest. The
# ramp must be this short: the rising hand/forearm sweeps the closed-lid
# envelope from theta ~20 deg, so the lid has to out-run it (audit sweep).
LID_CAM_TRAVEL = 6.0
FOLLOWER_X = -25.0              # world x of the vertical lid follower
FOLLOWER_PIN_Z = 10.0           # closed follower pin height
FOLLOWER_RACK_PHASE_Z = 2.9     # tuned by audit_ghouls_grip_assembly
DRIVE_RACK_PHASE_X = 0.0        # tuned by audit_ghouls_grip_assembly

SLIDER_SKID_Z = 2.2             # 0.2 mm above the floor top (z 2)
SLIDER_SIDE_U = 56.8            # cavity wall at u 58
SLIDER_FINGER_U = (55.0, 56.6)
SLIDER_NOSE_U = 59.4            # groove bottom u 60, groove z 8..12
DRIVE_GEAR_Y = (-46.0, -54.0)

IDLER_HEAD_CBORE_D = PIN_HEAD_D + 0.4
IDLER_HEAD_CBORE_DEPTH = 1.0
GEAR_RAIL_START = 14.0          # along the gear line from the fixed pin
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


def lid_cam_fraction(theta: float) -> float:
    """Fraction of the cam rise reached at scissor angle ``theta``."""
    travel = RETRACTED_SLIDER_X - slider_x(theta)
    return float(np.clip(travel / LID_CAM_TRAVEL, 0.0, 1.0))


def lid_follower_rise(theta: float) -> float:
    """Vertical lift of the cam-driven lid follower rack."""
    return LID_OPEN_TRAVEL * lid_cam_fraction(theta)


def lid_angle_from_travel(rise: float) -> float:
    """Lid sector angle for a given follower-rack rise."""
    used = np.clip(rise, 0.0, LID_OPEN_TRAVEL)
    return -float(np.rad2deg(used / LID_SECTOR_R))


def lid_angle(theta: float) -> float:
    """Fast cam opening followed by a captured level dwell."""
    return lid_angle_from_travel(lid_follower_rise(theta))


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
    # Snap-pin barbs sit flush in these top-face counterbores.  The assembly
    # lays every arm with this face outboard.
    counterbores = [
        cylinder(PIN_CBORE_D / 2.0, PIN_CBORE_DEPTH + 1.0,
                 (x, 0.0, ARM_T - PIN_CBORE_DEPTH / 2.0 + 0.5))
        for x in (-ARM_L / 2.0, 0.0, ARM_L / 2.0)
    ]
    # Key holes 8 mm from each end bore take the scissor-drive gear peg.
    key_holes = [cylinder(3.4 / 2.0, ARM_T + 4.0, (x, 0.0, ARM_T / 2.0))
                 for x in (-ARM_L / 2.0 + 8.0, ARM_L / 2.0 - 8.0)]
    lightening = [
        rounded_box((18.0, 5.6, ARM_T + 2.0), 2.4,
                    (sx * 14.0, 0.0, ARM_T / 2.0))
        for sx in (-1.0, 1.0)
    ]
    body = difference(body, [*bores, *counterbores, *key_holes, *lightening])
    return clean(body)


def _prism_yz(points, x0: float, x1: float) -> trimesh.Trimesh:
    """Extrude a convex (y, z) outline along X between ``x0`` and ``x1``."""
    pts = np.asarray(points, dtype=float)
    cloud = np.vstack([
        np.column_stack([np.full(len(pts), x), pts[:, 0], pts[:, 1]])
        for x in (x0, x1)
    ])
    return clean(trimesh.convex.convex_hull(cloud))


def _slot_xz(p0, p1, width: float, y_centre: float,
             y_len: float) -> trimesh.Trimesh:
    """Rounded slot cutter in the XZ plane, cut through along Y."""
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    delta = p1 - p0
    length = float(np.hypot(*delta))
    bar = box((length, y_len, width), (0.0, 0.0, 0.0))
    bar.apply_transform(trimesh.transformations.rotation_matrix(
        -np.arctan2(delta[1], delta[0]), (0.0, 1.0, 0.0)))
    mid = (p0 + p1) / 2.0
    bar.apply_translation((mid[0], y_centre, mid[1]))
    ends = [cylinder(width / 2.0, y_len, (p[0], y_centre, p[1]),
                     (0.0, 1.0, 0.0)) for p in (p0, p1)]
    return union([bar, *ends])


def _box_span(x0, x1, y0, y1, z0, z1) -> trimesh.Trimesh:
    return box((x1 - x0, y1 - y0, z1 - z0),
               ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0))


def _u_span(sign: float, u0: float, u1: float):
    lo, hi = sorted((sign * u0, sign * u1))
    return lo, hi


def slider_cam_path() -> list[tuple[float, float]]:
    """Follower-pin centreline in slider-local (x, z)."""
    start = FOLLOWER_X - RETRACTED_SLIDER_X
    end = FOLLOWER_X - slider_x(THETA_MAX)
    # 1 mm level over-travel at both ends keeps the pin off the slot caps.
    return [
        (start - 1.0, FOLLOWER_PIN_Z),
        (start, FOLLOWER_PIN_Z),
        (start + LID_CAM_TRAVEL, FOLLOWER_PIN_Z + LID_OPEN_TRAVEL),
        (end + 1.0, FOLLOWER_PIN_Z + LID_OPEN_TRAVEL),
    ]


def drive_rack_tooth_x() -> np.ndarray:
    """Slider-local x of the drive rack teeth (tooth centres)."""
    pitch = 2.0 * np.pi * DRIVE_PITCH_R / DRIVE_TEETH
    first = -RETRACTED_SLIDER_X + DRIVE_RACK_PHASE_X
    ks = np.arange(-30, 30)
    xs = first + ks * pitch
    return xs[(xs > -71.0) & (xs < 7.0)]


def build_slider() -> trimesh.Trimesh:
    """Rack-driven carriage held in the wall grooves by snap fingers.

    Slider-local x = world x - slider_x(theta).  The carriage rests on skids
    0.2 mm above the floor.  Two spring fingers per side carry 45-degree
    lead-in noses that click into the full-length wall grooves when the
    slider is pressed down; their flat catch faces sit 0.5 mm below the
    groove top flank and stop the carriage from lifting.  The open lug pair
    on each side carries the slider pivot of the True arm at z = RAIL_Z.
    """
    z0 = SLIDER_SKID_Z
    parts = []
    cuts = []
    for sy in (-1.0, 1.0):
        for u0, u1 in ((36.6, 40.6), (45.4, 49.4)):
            y0, y1 = _u_span(sy, u0, u1)
            parts.append(cylinder(4.6, u1 - u0, (0.0, (y0 + y1) / 2.0, RAIL_Z),
                                  (0.0, 1.0, 0.0)))
            parts.append(_box_span(0.0, 11.5, y0, y1, z0, 16.0))
        parts.append(_box_span(7.5, 11.5, *_u_span(sy, 36.6, SLIDER_SIDE_U),
                               z0, 16.0))
        parts.append(_box_span(0.0, 22.0, *_u_span(sy, 52.8, SLIDER_SIDE_U),
                               z0, 16.0))
        # Snap finger: horizontal cantilever anchored in the side wall.
        parts.append(_box_span(-26.0, 0.5, *_u_span(sy, *SLIDER_FINGER_U),
                               z0, 11.7))
        nose = [(56.6, 7.4), (SLIDER_NOSE_U, 10.2),
                (SLIDER_NOSE_U, 11.5), (56.6, 11.5)]
        parts.append(_prism_yz([(sy * u, z) for u, z in nose], -26.0, -20.0))
        cuts.append(cylinder(PIVOT_D / 2.0, 16.0, (0.0, sy * 42.4, RAIL_Z),
                             (0.0, 1.0, 0.0)))
        cuts.append(cylinder(PIN_CBORE_D / 2.0, 2.2,
                             (0.0, sy * 48.9, RAIL_Z), (0.0, 1.0, 0.0)))
    parts.append(_box_span(18.0, 22.0, -SLIDER_SIDE_U, SLIDER_SIDE_U,
                           z0, 16.0))

    # -Y: drive rack on a floor-skid web (stiff against pinion tooth load).
    parts.append(_box_span(-72.0, 8.0, -54.0, -46.0, 13.0, 17.5))
    parts.append(_box_span(-72.0, 11.5, -53.0, -50.6, z0, 13.2))
    parts.extend(
        _box_span(x - 1.05, x + 1.05, -53.5, -46.5, 17.4, 19.9)
        for x in drive_rack_tooth_x()
    )

    # +Y: lid cam plate.  The follower pin rides the slot: 7 mm rise over the
    # first 10 mm of travel, then a level dwell.
    parts.append(_box_span(-98.3, -33.0, 53.4, 56.6, z0, 23.0))
    parts.append(_box_span(-35.0, 11.5, 50.6, 53.0, z0, 23.0))
    parts.append(_box_span(-35.0, -33.0, 50.6, 56.6, z0, 23.0))
    path = slider_cam_path()
    for p0, p1 in zip(path[:-1], path[1:]):
        cuts.append(_slot_xz(p0, p1, PIVOT_D, 55.0, 8.0))

    body = difference(union(parts), cuts)
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
    hinge_bridge = union([
        box((4.0, 86.0, PLATFORM_T),
            (ARM_HINGE_X + sx * 7.0, 0.0, PLATFORM_T / 2.0))
        for sx in (-1.0, 1.0)
    ] + [
        box((18.0, 5.0, PLATFORM_T),
            (ARM_HINGE_X, y, PLATFORM_T / 2.0))
        for y in (-40.5, -14.0, 0.0, 14.0, 40.5)
    ])

    # Fixed top pivot: one inboard lug per side (u 36.6..40.6) beside the
    # True arm (u 41..45).  A round lug keeps 2.5+ mm from the False arm.
    fixed_lugs = []
    for sy in (-1.0, 1.0):
        y0, y1 = _u_span(sy, 36.6, 40.6)
        yc = (y0 + y1) / 2.0
        fixed_lugs.append(cylinder(5.5, 4.0, (PLATFORM_PIN_X, yc, -8.0),
                                   (0.0, 1.0, 0.0)))
        fixed_lugs.append(_box_span(PLATFORM_PIN_X - 5.5, PLATFORM_PIN_X + 5.5,
                                    y0, y1, -8.0, 0.5))

    # Slot pivot: inboard slot beams (u 30.6..34.6) guide the False arm's top
    # pin over the full slider stroke.
    slot_beams = []
    slot_cuts = []
    slot_x = (slider_x(THETA_MAX) + PLATFORM_PIN_X,
              slider_x(THETA_MIN) + PLATFORM_PIN_X)
    for sy in (-1.0, 1.0):
        y0, y1 = _u_span(sy, 30.6, 34.6)
        slot_beams.append(_box_span(-24.0, 47.5, y0, y1, -13.3, PLATFORM_T))
        slot_cuts.append(_slot_xz(
            (slot_x[0] - 1.0, -8.0), (slot_x[1] + 1.0, -8.0),
            PIVOT_D, sy * 32.6, 6.0))

    arm_ears = [_lug(FOREARM_BEARING_D, 26.0, 6.0,
                     (ARM_HINGE_X, sy * ARM_EAR_Y, ARM_HINGE_Z))
                for sy in (-1.0, 1.0)]

    gear_start, idler_centres, gear_end = forearm_gear_centres()
    gear_vector = gear_end - gear_start
    gear_distance = float(np.linalg.norm(gear_vector[[0, 2]]))
    gear_unit = gear_vector / gear_distance
    rail_from, rail_to = GEAR_RAIL_START, gear_distance - 4.0
    gear_rail = box((rail_to - rail_from, 6.0, 6.0), (0.0, 0.0, 0.0))
    gear_rail.apply_transform(trimesh.transformations.rotation_matrix(
        -np.arctan2(gear_vector[2], gear_vector[0]),
        (0.0, 1.0, 0.0),
    ))
    # The rail runs inboard of the gear plane (u 40.6..46.6) and starts clear
    # of the True arm's swept band; idlers turn on snap pins through it.
    gear_rail.apply_translation(
        gear_start + gear_unit * (rail_from + rail_to) / 2.0
        + np.array([0.0, -(FOREARM_GEAR_Y - 43.6), 0.0]))

    hinge_gussets = [
        box((3.2, 8.0, ARM_HINGE_Z - 13.0),
            (ARM_HINGE_X + dx, sy * ARM_EAR_Y,
             (ARM_HINGE_Z - 13.0) / 2.0))
        for sy in (-1.0, 1.0)
        for dx in (-6.4, 0.0, 6.4)
    ]
    body = union([*side_rails, *pivot_links, hinge_bridge, *fixed_lugs,
                  *slot_beams, *arm_ears, gear_rail, *hinge_gussets])
    idler_bores = [
        cylinder(PIVOT_D / 2.0, 14.0, centre + np.array([0.0, -6.4, 0.0]),
                 (0.0, 1.0, 0.0))
        for centre in idler_centres
    ]
    fixed_bores = [
        cylinder(PIVOT_D / 2.0, 6.0,
                 (PLATFORM_PIN_X, sy * 38.6, -8.0), (0.0, 1.0, 0.0))
        for sy in (-1.0, 1.0)
    ]
    body = difference(body, [
        cylinder(
            FOREARM_BEARING_D / 2.0,
            86.0,
            (ARM_HINGE_X, 20.0, ARM_HINGE_Z),
            (0.0, 1.0, 0.0),
        ),
        *idler_bores, *fixed_bores, *slot_cuts,
    ])
    # The long coaxial cut can leave sub-mm boolean crumbs at tangent edges.
    # They are not part of the platform and must not become loose print bodies.
    components = body.split(only_watertight=False)
    return clean(max(components, key=lambda component: abs(component.volume)))


DRIVE_SHAFT_FLAT = 1.0          # D-flat depth on the knob end of the shaft
DRIVE_SHAFT_END_Z = 28.0        # pinion-local; world y = -46 - z
DRIVE_CROSS_PIN_Z = 23.0        # 1.75 mm filament cross pin through the knob


def build_drive_pinion() -> trimesh.Trimesh:
    """Main pinion with an integral bearing shaft through the front wall.

    Gear face z 0..8 (world y -46..-54), round bearing journal through the
    Ø8.8 chest bore, then a D-flat end that keys the skull knob.  A 1.75 mm
    filament cross pin through knob stem and shaft retains the knob axially.
    """
    gear = _spur_gear(
        DRIVE_ROOT_R, GEAR_TOOTH_H, DRIVE_TEETH, 8.0,
        hub_r=7.2, rim=3.0,
    )
    journal = cylinder(DRIVE_SHAFT_D / 2.0, 17.5, (0.0, 0.0, 8.75))
    d_len = DRIVE_SHAFT_END_Z - 17.0
    d_end = fdm_joints.d_shaft(
        DRIVE_SHAFT_D, d_len, DRIVE_SHAFT_FLAT,
        center=(0.0, 0.0, 17.0 + d_len / 2.0),
    )
    body = union([gear, journal, d_end])
    cross = fdm_joints.cross_pin_hole(
        DRIVE_SHAFT_D, axis=(0.0, 1.0, 0.0),
        center=(0.0, 0.0, DRIVE_CROSS_PIN_Z))
    return clean(difference(body, [cross]))


FOLLOWER_X_SPAN = (FOLLOWER_X - 3.0, FOLLOWER_X + 3.0)
FOLLOWER_SPINE_X = (FOLLOWER_X - 2.0, FOLLOWER_X + 2.0)
FOLLOWER_BAR_U = (46.0, 50.0)
FOLLOWER_SPINE_U = (37.4, 41.0)
FOLLOWER_TOOTH_U = (41.0, 43.4)
FOLLOWER_TOP_Z = 97.0


def follower_rack_tooth_z() -> np.ndarray:
    """Closed-pose world z of the follower rack tooth centres."""
    teeth = max(6, int(round(2.0 * np.pi * LID_SECTOR_R / GEAR_PITCH)))
    pitch = 2.0 * np.pi * LID_SECTOR_R / teeth
    zs = LID_HINGE_Z + FOLLOWER_RACK_PHASE_Z + np.arange(-6, 6) * pitch
    return zs[(zs > 83.0) & (zs < FOLLOWER_TOP_Z - 0.8)]


def lid_follower_world() -> trimesh.Trimesh:
    """Cam-driven lid follower rack in closed world pose (+Y side).

    A vertical bar (u 46..50) rides the chest guide channel; its cross pin
    at z 10 runs in the slider cam slot.  Above the guide it jogs inboard to
    a spine whose rack teeth (u 41..43.4) drive the lid transfer gear.
    """
    x0, x1 = FOLLOWER_X_SPAN
    s0, s1 = FOLLOWER_SPINE_X
    bar = _box_span(x0, x1, *FOLLOWER_BAR_U, 6.0, 80.0)
    jog = _box_span(s0, s1, FOLLOWER_SPINE_U[0], FOLLOWER_BAR_U[1],
                    72.0, 80.0)
    spine = _box_span(s0, s1, *FOLLOWER_SPINE_U, 72.0, FOLLOWER_TOP_Z)
    teeth = [_box_span(s0, s1, FOLLOWER_SPINE_U[1] - 0.1, FOLLOWER_TOOTH_U[1],
                       z - 0.8, z + 0.8)
             for z in follower_rack_tooth_z()]
    body = union([bar, jog, spine, *teeth])
    hole = cylinder(PIVOT_D / 2.0, 8.0,
                    (FOLLOWER_X, 48.0, FOLLOWER_PIN_Z), (0.0, 1.0, 0.0))
    return clean(difference(body, [hole]))


# Print the follower lying on its -X face: world X becomes print Z.
FOLLOWER_PRINT_MATRIX = trimesh.transformations.rotation_matrix(
    -np.pi / 2.0, (0.0, 1.0, 0.0))


def build_lid_follower_rack() -> trimesh.Trimesh:
    """Lid follower rack in print orientation (see ``lid_follower_world``)."""
    body = lid_follower_world()
    body.apply_transform(FOLLOWER_PRINT_MATRIX)
    return clean(body)


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


def build_crank_spacer() -> trimesh.Trimesh:
    """Loose tube on the hinge filament that pins the crank into the socket."""
    return clean(difference(
        cylinder(CRANK_SPACER_R, CRANK_SPACER_LEN,
                 (0.0, 0.0, CRANK_SPACER_LEN / 2.0)),
        [cylinder(CRANK_SPACER_BORE_R, CRANK_SPACER_LEN + 2.0,
                  (0.0, 0.0, CRANK_SPACER_LEN / 2.0))]))


def build_lid_transfer_gear() -> trimesh.Trimesh:
    """Equal-ratio transfer gear with an integral, axially inserted journal."""
    teeth = max(6, int(round(2.0 * np.pi * LID_SECTOR_R / GEAR_PITCH)))
    gear = _spur_gear(LID_SECTOR_R - 1.5, GEAR_TOOTH_H,
                      teeth, 4.0)
    gear.apply_transform(trimesh.transformations.rotation_matrix(
        np.deg2rad(LID_TOOTH_PHASE), (0.0, 0.0, 1.0)))
    journal = cylinder(1.4, 18.0, (0.0, 0.0, -5.0))
    # Shoulder hub: stops 0.2 mm before the bearing block's inner face so the
    # gear cannot drift off its 4 mm rack/crank mesh; the cross pin sits
    # 0.33 mm outside the outer face.  Axial play totals ~0.5 mm.
    hub = cylinder(TRANSFER_HUB_R, TRANSFER_HUB_LEN,
                   (0.0, 0.0, -TRANSFER_HUB_LEN / 2.0 + 0.01))
    return clean(difference(union([gear, journal, hub]), [
        cylinder(0.95, 6.0, (0.0, 0.0, TRANSFER_CROSS_Z), (1.0, 0.0, 0.0)),
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
    # Peg reaches local z 11.5 (world u 41.5) into the True arm key hole.
    key_peg = cylinder(1.4, 11.5, (8.0, 0.0, 5.75))
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
    # The snap-pin head sinks 1 mm into the outboard face (local z 0) so it
    # clears the opened lid's rear rim at full lift.
    return clean(difference(gear, [
        cylinder(PIVOT_D / 2.0, 10.0, (0.0, 0.0, 3.0)),
        cylinder(IDLER_HEAD_CBORE_D / 2.0, 2.0,
                 (0.0, 0.0, IDLER_HEAD_CBORE_DEPTH - 1.0)),
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


def _barb_half(side: float, catch: float) -> trimesh.Trimesh:
    """One barb half: an r 2.2 arc offset outward by ``PIN_BARB_OFFSET``.

    A revolved barb cannot work in a split pin: closing the halves only moves
    them in the flex direction, so its width in the slot plane would stay
    above the bore.  The offset arc instead becomes a centred r 2.2 circle
    (0.1 mm radial clearance in the Ø4.6 bore) once each half has closed by
    the offset, while overhanging the bore edge by 0.25 mm when relaxed.
    """
    land_end = catch + PIN_BARB_LAND
    cone_end = land_end + PIN_BARB_CONE
    angles = np.linspace(0.0, 2.0 * np.pi, 48, endpoint=False)
    ring = np.column_stack([np.cos(angles), np.sin(angles)])
    points = []
    for z in (catch, land_end):
        xy = ring * PIN_BARB_ARC_R + [side * PIN_BARB_OFFSET, 0.0]
        points.append(np.column_stack([xy, np.full(len(xy), z)]))
    xy = ring * (PIN_D / 2.0 - 0.1)
    points.append(np.column_stack([xy, np.full(len(xy), cone_end)]))
    barb = trimesh.convex.convex_hull(np.vstack(points))
    keep = box((4.0, 8.0, cone_end - catch + 0.2),
               (side * 2.0, 0.0, (catch + cone_end) / 2.0))
    return intersection([barb, keep])


def build_pin(grip: float, tail: float = 0.0) -> trimesh.Trimesh:
    """Split snap pivot pin along +Z, head underside at z = 0.

    ``grip`` is the stack thickness from the head underside to the face the
    barb catches on; the catch face sits ``PIN_AXIAL_PLAY`` beyond it.  The
    two halves, separated by a 1.4 mm slot, each carry an offset barb arc
    (see ``_barb_half``) that overhangs the Ø4.6 bore by 0.25 mm; they flex
    0.35 mm inward on insertion and spring out in the Ø6 counterbore.  The
    0.4 mm flat at y = -1.6 is the print bed face; the slot plane is
    perpendicular to it so the halves flex in the print plane.
    """
    r = PIN_D / 2.0
    catch = grip + PIN_AXIAL_PLAY
    cone_end = catch + PIN_BARB_LAND + PIN_BARB_CONE
    tip = cone_end + tail
    profile = [
        (0.0, -PIN_HEAD_T),
        (PIN_HEAD_D / 2.0, -PIN_HEAD_T),
        (PIN_HEAD_D / 2.0, 0.0),
        (r, 0.0),
        (r, tip - 0.3),
        (r - 0.3, tip),
        (0.0, tip),
    ]
    body = clean(trimesh.creation.revolve(np.asarray(profile), sections=64))
    body = union([body, _barb_half(1.0, catch), _barb_half(-1.0, catch)])
    slot_from = max(catch - PIN_SLOT_REACH, 0.8)
    cuts = [
        box((PIN_SLOT_W, 10.0, tip - slot_from + 1.0),
            (0.0, 0.0, (slot_from + tip + 1.0) / 2.0)),
        box((10.0, 4.0, tip + PIN_HEAD_T + 2.0),
            (0.0, PIN_FLAT_Y - 2.0, (tip - PIN_HEAD_T) / 2.0)),
    ]
    return clean(difference(body, cuts))


def build_press_pin(grip: float, tail: float) -> trimesh.Trimesh:
    """Solid pin held by crush ribs in its first ``grip`` mm (follower pin).

    The 4 mm follower bar leaves too short a split for PLA (bending strain
    > 5 %), and a split tail would run as a non-round journal of single
    cantilever halves in the slider cam slot.  The pin carries no axial load,
    so three 0.8 mm crush ribs reaching r 2.45 (0.15 mm interference in the
    Ø4.6 bar bore, stopping 0.3 mm short of its far face) hold it; the plain
    Ø4 tail runs with 0.3 mm clearance in the cam slot.
    """
    r = PIN_D / 2.0
    tip = grip + tail
    profile = [
        (0.0, -PIN_HEAD_T),
        (PIN_HEAD_D / 2.0, -PIN_HEAD_T),
        (PIN_HEAD_D / 2.0, 0.0),
        (r, 0.0),
        (r, tip - 0.3),
        (r - 0.3, tip),
        (0.0, tip),
    ]
    body = clean(trimesh.creation.revolve(np.asarray(profile), sections=64))
    ribs = []
    rib_end = grip - 0.3
    for angle in (0.0, 90.0, 180.0):
        c, s = np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))
        pts = []
        for z, reach in ((0.0, PIN_CRUSH_R), (rib_end - 1.0, PIN_CRUSH_R),
                         (rib_end, r)):
            for t in (-0.4, 0.4):
                for depth in (r - 0.6, np.sqrt(reach ** 2 - t ** 2)):
                    pts.append((depth * c - t * s, depth * s + t * c, z))
        ribs.append(trimesh.convex.convex_hull(np.asarray(pts)))
    body = union([body, *ribs])
    flat = box((10.0, 4.0, tip + PIN_HEAD_T + 2.0),
               (0.0, PIN_FLAT_Y - 2.0, (tip - PIN_HEAD_T) / 2.0))
    return clean(difference(body, [flat]))


def pin_print_pose(pin: trimesh.Trimesh) -> trimesh.Trimesh:
    """Lay a pin from ``build_pin`` on its 0.4 mm flat for printing."""
    result = pin.copy()
    result.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2.0, (1.0, 0.0, 0.0)))
    return clean(result)


def build_pin_variant(variant: str) -> trimesh.Trimesh:
    if variant == "follower":
        return build_press_pin(PIN_GRIPS[variant], PIN_TAILS[variant])
    return build_pin(PIN_GRIPS[variant], PIN_TAILS.get(variant, 0.0))


PARTS = {
    "scissor-arm": build_scissor_arm,
    "slider": build_slider,
    # Pack the tall follower beside the slider, not in the final plate row.
    "lid-follower-rack": build_lid_follower_rack,
    "platform": build_platform,
    "drive-pinion": build_drive_pinion,
    "lid-crank": build_lid_crank,
    "crank-spacer": build_crank_spacer,
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
