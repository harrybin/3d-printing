"""Assembly views of the Ghoul's Grip, built from the real kinematic chain.

Every part is placed by the same numbers the generator uses, so a collision or
a mismatched pivot shows up here instead of on the printer.

    python scripts/render_ghouls_grip.py            # both views
    python scripts/render_ghouls_grip.py deployed   # hero view only
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import trimesh
import vedo

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mechanism
from gothic_chest import HINGE_Y, HINGE_Z, LID_DROP, build_chest, build_lid
from skeleton_hand import (GRIP_POSE, assemble, load_skeleton,
                           palm_to_forearm_transform)
from skull import build_drive_knob

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images"

ARM_L = mechanism.ARM_L
ARM_HINGE_X = mechanism.ARM_HINGE_X
ARM_HINGE_Z = mechanism.ARM_HINGE_Z
STOW_ANGLE = mechanism.STOW_ANGLE
FLOOR_PIVOT = np.array([mechanism.FLOOR_PIVOT_X, 8.0])
PLATFORM_PIN = mechanism.PLATFORM_PIN_X
SCISSOR_Y = mechanism.SCISSOR_Y

POSES = {
    "retracted": mechanism.THETA_MIN,
    "intermediate": 48.0,
    "deployed": mechanism.THETA_MAX,
}
BLACK_COLOR = "#202124"
BONE_COLOR = "#D8C6A5"
MECHANISM_COLOR = "#F1EBDD"
FINGER_COLOR = BONE_COLOR
ACCENT_COLOR = "#777777"


def rot(angle_deg: float, axis, point=(0.0, 0.0, 0.0)):
    return trimesh.transformations.rotation_matrix(
        np.deg2rad(angle_deg), axis, point)


def lay_arm(mesh: trimesh.Trimesh, theta: float, y: float,
            mirrored: bool, flip: bool = False) -> trimesh.Trimesh:
    """Stand a flat printed arm up in the XZ plane at the given angle.

    The printed top face (pin counterbores) ends up facing +Y; ``flip``
    turns the arm over about its long axis first so that face looks -Y.
    """
    arm = mesh.copy()
    arm.apply_translation([0.0, 0.0, -mesh.extents[2] / 2.0])
    if flip:
        arm.apply_transform(rot(180.0, [1, 0, 0]))
    arm.apply_transform(rot(-90.0, [1, 0, 0]))
    arm.apply_transform(rot(-(180.0 - theta) if mirrored else -theta, [0, 1, 0]))
    mid_x = FLOOR_PIVOT[0] + ARM_L * np.cos(np.deg2rad(theta)) / 2.0
    mid_z = FLOOR_PIVOT[1] + ARM_L * np.sin(np.deg2rad(theta)) / 2.0
    arm.apply_translation([mid_x, y, mid_z])
    return arm


# The forearm D-socket sits 4 mm down the output-gear shaft (forearm-local z).
FOREARM_SEAT_Z = -4.0

# Skull knob: the stem face stops 0.4 mm short of the chest bearing boss.
KNOB_STEM_LEN = 12.0
KNOB_STEM_FACE_Y = -64.4

PIN_ROLE_VARIANT = {
    "floor": "floor", "slider": "slider", "centre": "centre",
    "fixed": "gear", "slot": "short",
}


def place_pin(variant: str, x: float, y_head: float, z: float,
              direction: float) -> trimesh.Trimesh:
    """Snap pin with its head underside at ``y_head`` pointing along +-Y."""
    pin = source_mesh(mechanism.build_pin_variant, variant=variant)
    pin.apply_transform(rot(-90.0 if direction > 0 else 90.0, [1, 0, 0]))
    pin.apply_translation([x, y_head, z])
    return pin


def tube_between(start, end, radius: float) -> trimesh.Trimesh:
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    vector = end - start
    return trimesh.creation.cylinder(
        radius=radius,
        height=float(np.linalg.norm(vector)),
        sections=16,
        segment=np.vstack([start, end]),
    )


def lid_angle(theta: float) -> float:
    """Compatibility wrapper for the physical rack-and-crank solution."""
    return mechanism.lid_angle(theta)



@lru_cache(maxsize=1)
def grip_hand():
    """Build the expensive voxel-fused anatomical hand once per process."""
    return assemble(load_skeleton(), GRIP_POSE)


@lru_cache(maxsize=None)
def _source_mesh(builder, **kwargs):
    return builder(**kwargs)


def source_mesh(builder, **kwargs):
    return _source_mesh(builder, **kwargs).copy()


def build_scene_at(theta: float):
    rad = np.deg2rad(theta)
    lift = ARM_L * np.sin(rad)
    slider_x = FLOOR_PIVOT[0] + ARM_L * np.cos(rad)
    plate_z = FLOOR_PIVOT[1] + lift
    plat_origin = np.array([FLOOR_PIVOT[0] - PLATFORM_PIN, 0.0, plate_z + 8.0])

    items = []
    items.append(("chest", source_mesh(build_chest), BLACK_COLOR))

    lid = source_mesh(build_lid)
    lid.apply_translation([0.0, 0.0, LID_DROP])
    opening = lid_angle(theta)
    lid_transform = np.eye(4)
    if opening:
        lid_transform = rot(opening, [1, 0, 0],
                            [0.0, HINGE_Y, HINGE_Z])
        lid.apply_transform(lid_transform)
    items.append(("lid", lid, BLACK_COLOR))

    lid_crank = source_mesh(mechanism.build_lid_crank)
    lid_crank.apply_transform(rot(90.0, [0, 1, 0]))
    lid_crank.apply_transform(rot(opening, [1, 0, 0]))
    lid_crank.apply_translation([
        -mechanism.DRIVE_PITCH_R, HINGE_Y, HINGE_Z
    ])
    items.append(("lid-crank", lid_crank, MECHANISM_COLOR))

    spacer = source_mesh(mechanism.build_crank_spacer)
    spacer.apply_transform(rot(90.0, [0, 1, 0]))
    spacer.apply_translation([
        -mechanism.DRIVE_PITCH_R - 0.1 - mechanism.CRANK_SPACER_LEN,
        HINGE_Y, HINGE_Z,
    ])
    items.append(("crank-spacer", spacer, MECHANISM_COLOR))

    for name, y, angle in (
        ("lid-transfer-input", mechanism.LID_TRANSFER_Y, opening),
        ("lid-transfer-idler", mechanism.LID_IDLER_Y, -opening),
    ):
        gear = source_mesh(mechanism.build_lid_transfer_gear)
        gear.apply_transform(rot(90.0, [0, 1, 0]))
        gear.apply_transform(rot(angle, [1, 0, 0]))
        gear.apply_translation([-mechanism.DRIVE_PITCH_R, y, HINGE_Z])
        items.append((name, gear, MECHANISM_COLOR))

    slider = source_mesh(mechanism.build_slider)
    slider.apply_translation([slider_x, 0.0, 0.0])
    items.append(("slider", slider, MECHANISM_COLOR))

    drive_rotation = mechanism.drive_angle(theta)
    pinion = source_mesh(mechanism.build_drive_pinion)
    pinion.apply_transform(rot(-drive_rotation, [0, 0, 1]))
    pinion.apply_transform(rot(90.0, [1, 0, 0]))
    pinion.apply_translation(
        mechanism.DRIVE_AXIS
        + np.array([0.0, mechanism.DRIVE_GEAR_Y[0]
                    - mechanism.DRIVE_AXIS[1], 0.0]))
    items.append(("drive-pinion", pinion, MECHANISM_COLOR))

    knob_angle = mechanism.KNOB_STOW_ANGLE + drive_rotation
    knob = source_mesh(build_drive_knob, shaft_d=mechanism.DRIVE_SHAFT_D)
    knob.apply_transform(rot(90.0, [1, 0, 0]))
    knob.apply_transform(rot(knob_angle, [0, 1, 0]))
    knob.apply_translation(mechanism.DRIVE_AXIS + np.array(
        [0.0, KNOB_STEM_FACE_Y - KNOB_STEM_LEN - mechanism.DRIVE_AXIS[1],
         0.0]))
    items.append(("drive-skull-knob", knob, ACCENT_COLOR))

    rise = mechanism.lid_follower_rise(theta)
    follower = source_mesh(mechanism.build_lid_follower_rack)
    follower.apply_transform(np.linalg.inv(mechanism.FOLLOWER_PRINT_MATRIX))
    follower.apply_translation([0.0, 0.0, rise])
    items.append(("lid-follower-rack", follower, MECHANISM_COLOR))

    arm = source_mesh(mechanism.build_scissor_arm)
    for i, y in enumerate((-SCISSOR_Y, SCISSOR_Y)):
        side = np.sign(y)
        for mirrored in (False, True):
            # True arms (slider -> fixed pin) run outboard (u 41..45), False
            # arms (floor -> slot) inboard (u 35..39) on both planes.  The
            # -Y arms are flipped so every counterbore faces outboard.
            off = side * 3.0 if mirrored else -side * 3.0
            items.append((f"arm-{i}-{mirrored}",
                          lay_arm(arm, theta, y + off, mirrored,
                                  flip=side < 0), MECHANISM_COLOR))

    top = FLOOR_PIVOT[1] + lift
    gear_start_local, idler_local, gear_end_local = (
        mechanism.forearm_gear_centres()
    )
    # (variant, x, z, head-underside |y|, direction in |y|, planes)
    pin_specs = [
        ("floor", FLOOR_PIVOT[0], FLOOR_PIVOT[1], 30.0, 1.0),
        ("slider", slider_x, FLOOR_PIVOT[1], 36.6, 1.0),
        ("centre", slider_x / 2.0, FLOOR_PIVOT[1] + lift / 2.0, 35.0, 1.0),
        ("fixed", FLOOR_PIVOT[0], top, 36.6, 1.0),
        ("slot", slider_x, top, 30.6, 1.0),
    ]
    for plane, y in enumerate((-SCISSOR_Y, SCISSOR_Y)):
        side = np.sign(y)
        for role, x, z, u_head, direction in pin_specs:
            variant = PIN_ROLE_VARIANT[role]
            if role == "fixed":
                variant = "gear" if side > 0 else "short"
            items.append((
                f"pivot-pin-{role}-{plane}",
                place_pin(variant, x, side * u_head, z, side * direction),
                MECHANISM_COLOR,
            ))
    for index, centre in enumerate(idler_local):
        world = plat_origin + centre
        items.append((
            f"pivot-pin-idler-{index}",
            place_pin("idler", world[0],
                      53.0 - mechanism.IDLER_HEAD_CBORE_DEPTH, world[2],
                      -1.0),
            MECHANISM_COLOR,
        ))
    items.append((
        "pivot-pin-follower",
        place_pin("follower", mechanism.FOLLOWER_X, 46.0,
                  mechanism.FOLLOWER_PIN_Z + rise, 1.0),
        MECHANISM_COLOR,
    ))

    platform = source_mesh(mechanism.build_platform)
    platform.apply_translation(plat_origin)
    items.append(("platform", platform, MECHANISM_COLOR))

    hinge = plat_origin + np.array([ARM_HINGE_X, 0.0, ARM_HINGE_Z])
    tilt = mechanism.forearm_angle(theta)

    gear_start = plat_origin + gear_start_local
    idler_centres = [plat_origin + centre for centre in idler_local]
    gear_end = plat_origin + gear_end_local

    input_gear = source_mesh(mechanism.build_scissor_drive_gear)
    input_gear.apply_transform(rot(-theta, [0, 0, 1]))
    input_gear.apply_transform(rot(90.0, [1, 0, 0]))
    input_gear.apply_translation(gear_start + np.array([0.0, 3.0, 0.0]))
    items.append(("scissor-drive-gear", input_gear, MECHANISM_COLOR))

    for index, (centre, angle) in enumerate(zip(
            idler_centres, mechanism.forearm_idler_angles(theta))):
        idler = source_mesh(mechanism.build_idler_gear)
        idler.apply_transform(rot(angle, [0, 0, 1]))
        idler.apply_transform(rot(90.0, [1, 0, 0]))
        idler.apply_translation(centre + np.array([0.0, 3.0, 0.0]))
        items.append((f"idler-gear-{index}", idler, MECHANISM_COLOR))

    output_gear = source_mesh(mechanism.build_forearm_output_gear)
    output_gear.apply_transform(rot(tilt, [0, 1, 0]))
    output_gear.apply_translation(hinge)
    items.append(("forearm-output-gear", output_gear, MECHANISM_COLOR))

    forearm = source_mesh(mechanism.build_forearm)
    forearm.apply_translation([0.0, 0.0, FOREARM_SEAT_Z])
    forearm.apply_transform(rot(tilt, [0, 1, 0]))
    forearm.apply_translation(hinge)
    items.append(("forearm", forearm, BONE_COLOR))

    # The common finger flexures remain in their compact pre-curled pose.
    # The palm is located only by the wrist cross pin, so its pin datum must
    # follow the forearm seat shift; otherwise the pin holes miss by 4 mm.
    hand = grip_hand()
    wrist_transform = palm_to_forearm_transform(
        load_skeleton(),
        mechanism.FOREARM_LENGTH + 9.0 + FOREARM_SEAT_Z,
        mechanism.HAND_PALM_ROLL,
    )
    for name, mesh in hand.items():
        part = mesh.copy()
        part.apply_transform(wrist_transform)
        part.apply_transform(rot(tilt, [0, 1, 0]))
        part.apply_translation(hinge)
        colour = FINGER_COLOR if name.startswith("hand-finger") else BONE_COLOR
        items.append((name, part, colour))

    return items


def build_scene(pose: str):
    return build_scene_at(POSES[pose])


def render(pose: str) -> Path:
    vedo.settings.default_backend = "vtk"
    items = build_scene(pose)
    actors = [vedo.Mesh([m.vertices, m.faces]).c(c).lighting("glossy")
              for _, m, c in items]
    top = max(m.bounds[1][2] for _, m, _ in items)
    out = OUT / f"ghouls-grip-{pose}.png"
    if pose == "deployed":
        cam = dict(pos=(470.0, -620.0, top * 0.92),
                   focal_point=(-10.0, 0.0, top * 0.44), viewup=(0, 0, 1))
        size = (1150, 1450)
    elif pose == "intermediate":
        cam = dict(pos=(350.0, -560.0, top + 150.0),
                   focal_point=(-10.0, 0.0, top * 0.40), viewup=(0, 0, 1))
        size = (1150, 1250)
    else:
        cam = dict(pos=(300.0, -420.0, 300.0),
                   focal_point=(-10.0, 0.0, 55.0), viewup=(0, 0, 1))
        size = (1400, 1100)
    pl = vedo.Plotter(offscreen=True, size=size, bg="#121218")
    pl.show(*actors, axes=0, camera=cam)
    pl.screenshot(str(out))
    pl.close()
    print(f"{pose}: highest point {top:.1f} mm  ->  {out}")
    return out


if __name__ == "__main__":
    for which in (sys.argv[1:] or [
            "deployed", "intermediate", "retracted"]):
        render(which)
