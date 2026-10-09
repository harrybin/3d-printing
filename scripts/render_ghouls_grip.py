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
from skeleton_hand import GRIP_POSE, assemble, load_skeleton
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
            mirrored: bool) -> trimesh.Trimesh:
    """Stand a flat printed arm up in the XZ plane at the given angle."""
    arm = mesh.copy()
    arm.apply_translation([0.0, 0.0, -mesh.extents[2] / 2.0])
    arm.apply_transform(rot(-90.0, [1, 0, 0]))
    arm.apply_transform(rot(-(180.0 - theta) if mirrored else -theta, [0, 1, 0]))
    mid_x = FLOOR_PIVOT[0] + ARM_L * np.cos(np.deg2rad(theta)) / 2.0
    mid_z = FLOOR_PIVOT[1] + ARM_L * np.sin(np.deg2rad(theta)) / 2.0
    arm.apply_translation([mid_x, y, mid_z])
    return arm


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

def build_scene_at(theta: float):
    rad = np.deg2rad(theta)
    lift = ARM_L * np.sin(rad)
    slider_x = FLOOR_PIVOT[0] + ARM_L * np.cos(rad)
    plate_z = FLOOR_PIVOT[1] + lift
    plat_origin = np.array([FLOOR_PIVOT[0] - PLATFORM_PIN, 0.0, plate_z + 8.0])

    items = []
    items.append(("chest", build_chest(), BLACK_COLOR))

    lid = build_lid()
    lid.apply_translation([0.0, 0.0, LID_DROP])
    opening = lid_angle(theta)
    lid_transform = np.eye(4)
    if opening:
        lid_transform = rot(opening, [1, 0, 0],
                            [0.0, HINGE_Y, HINGE_Z])
        lid.apply_transform(lid_transform)
    items.append(("lid", lid, BLACK_COLOR))

    lid_crank = mechanism.build_lid_crank()
    lid_crank.apply_transform(rot(90.0, [0, 1, 0]))
    lid_crank.apply_transform(rot(opening, [1, 0, 0]))
    lid_crank.apply_translation([
        -mechanism.DRIVE_PITCH_R, HINGE_Y, HINGE_Z
    ])
    items.append(("lid-crank", lid_crank, MECHANISM_COLOR))

    slider = mechanism.build_slider()
    slider.apply_translation([slider_x, 0.0, 0.0])
    items.append(("slider", slider, MECHANISM_COLOR))

    drive_rotation = mechanism.drive_angle(theta)
    pinion = mechanism.build_drive_pinion()
    pinion.apply_transform(rot(drive_rotation, [0, 0, 1]))
    pinion.apply_transform(rot(90.0, [1, 0, 0]))
    pinion.apply_translation(mechanism.DRIVE_AXIS)
    items.append(("drive-pinion", pinion, MECHANISM_COLOR))

    knob_angle = mechanism.KNOB_STOW_ANGLE - drive_rotation
    knob = build_drive_knob(shaft_d=mechanism.DRIVE_SHAFT_D)
    knob.apply_transform(rot(90.0, [1, 0, 0]))
    knob.apply_transform(rot(knob_angle, [0, 1, 0]))
    knob.apply_translation(mechanism.DRIVE_AXIS + np.array([0.0, -17.0, 0.0]))
    items.append(("drive-skull-knob", knob, ACCENT_COLOR))

    lid_rack = mechanism.build_lid_rack()
    lid_rack.apply_transform(rot(-90.0, [0, 1, 0]))
    drive_rise = mechanism.RETRACTED_SLIDER_X - slider_x
    lid_rack.apply_translation([
        -mechanism.DRIVE_PITCH_R,
        mechanism.DRIVE_AXIS[1],
        mechanism.LID_LINK_PIN_Z - 40.0 + drive_rise,
    ])
    items.append(("lid-rack", lid_rack, MECHANISM_COLOR))

    follower = mechanism.build_lid_follower_rack()
    follower.apply_transform(rot(-90.0, [0, 1, 0]))
    follower.apply_translation([
        -mechanism.DRIVE_PITCH_R,
        mechanism.LID_LINK_FRONT_Y,
        mechanism.LID_LINK_PIN_Z + 20.0
        + min(drive_rise, mechanism.LID_OPEN_TRAVEL),
    ])
    items.append(("lid-follower-rack", follower, MECHANISM_COLOR))

    arm = mechanism.build_scissor_arm()
    for i, y in enumerate((-SCISSOR_Y, SCISSOR_Y)):
        for mirrored in (False, True):
            off = 3.0 if mirrored else -3.0
            items.append((f"arm-{i}-{mirrored}",
                          lay_arm(arm, theta, y + off, mirrored), MECHANISM_COLOR))

    platform = mechanism.build_platform()
    platform.apply_translation(plat_origin)
    items.append(("platform", platform, MECHANISM_COLOR))

    hinge = plat_origin + np.array([ARM_HINGE_X, 0.0, ARM_HINGE_Z])
    tilt = mechanism.forearm_angle(theta)

    gear_start = np.array([
        FLOOR_PIVOT[0], mechanism.FOREARM_GEAR_Y, FLOOR_PIVOT[1] + lift
    ])
    gear_end = hinge + np.array([0.0, mechanism.FOREARM_GEAR_Y, 0.0])
    gear_vector = gear_end - gear_start
    gear_distance = float(np.linalg.norm(gear_vector[[0, 2]]))
    gear_unit = gear_vector / gear_distance
    idler_centres = [
        gear_start + gear_unit * (
            mechanism.FOREARM_INPUT_R + mechanism.FOREARM_IDLER_R
        ),
        gear_end - gear_unit * (
            mechanism.FOREARM_GEAR_R + mechanism.FOREARM_IDLER_R
        ),
    ]

    input_gear = mechanism.build_scissor_drive_gear()
    input_gear.apply_transform(rot(-theta, [0, 0, 1]))
    input_gear.apply_transform(rot(90.0, [1, 0, 0]))
    input_gear.apply_translation(gear_start)
    items.append(("scissor-drive-gear", input_gear, MECHANISM_COLOR))

    for index, centre in enumerate(idler_centres):
        idler = mechanism.build_idler_gear()
        idler.apply_transform(rot(
            ((-1.0) ** index) * theta, [0, 0, 1]
        ))
        idler.apply_transform(rot(90.0, [1, 0, 0]))
        idler.apply_translation(centre)
        items.append((f"idler-gear-{index}", idler, MECHANISM_COLOR))

    forearm = mechanism.build_forearm()
    forearm.apply_translation([0.0, 0.0, -4.0])
    forearm.apply_transform(rot(tilt, [0, 1, 0]))
    forearm.apply_translation(hinge)
    items.append(("forearm", forearm, BONE_COLOR))

    # The common finger flexures remain in their compact pre-curled pose.  The
    # The rigid redesign changes the box drive, lid and forearm linkage only.
    hand = grip_hand()
    stack = trimesh.util.concatenate(list(hand.values()))
    wrist_y = stack.bounds[0][1]
    for name, mesh in hand.items():
        part = mesh.copy()
        part.apply_transform(rot(90.0, [1, 0, 0]))
        part.apply_translation([0.0, 0.0, -wrist_y + 38.0])
        part.apply_transform(rot(mechanism.HAND_PALM_ROLL, [0, 0, 1]))
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
    for which in (sys.argv[1:] or ["deployed", "retracted"]):
        render(which)
