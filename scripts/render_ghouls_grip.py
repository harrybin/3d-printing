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
from skull import build_trigger

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
LID_OPEN_ANGLE = 92.0


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
    """Fast spring opening released by the same rocker as the slider."""
    travel = (
        mechanism.RETRACTED_SLIDER_X
        - mechanism.slider_x(mechanism.THETA_MAX)
    )
    released = (
        mechanism.RETRACTED_SLIDER_X - mechanism.slider_x(theta)
    ) / travel
    return -LID_OPEN_ANGLE * min(max(released / 0.28, 0.0), 1.0)



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
    items.append(("chest", build_chest(), "#43434e"))

    lid = build_lid()
    lid.apply_translation([0.0, 0.0, LID_DROP])
    opening = lid_angle(theta)
    lid_transform = np.eye(4)
    if opening:
        lid_transform = rot(opening, [1, 0, 0],
                            [0.0, HINGE_Y, HINGE_Z])
        lid.apply_transform(lid_transform)
    items.append(("lid", lid, "#43434e"))

    for index, x in enumerate((-70.0, 70.0)):
        moving = trimesh.transform_points(
            [[x, 70.0, LID_DROP + 19.0]], lid_transform
        )[0]
        items.append((
            f"lid-opening-band-{index}",
            tube_between((x, 50.0, 65.0), moving, 1.1),
            "#6f4a2d",
        ))

    slider = mechanism.build_slider()
    slider.apply_translation([slider_x, 0.0, 0.0])
    items.append(("slider", slider, "#c9b48e"))

    arm = mechanism.build_scissor_arm()
    for i, y in enumerate((-SCISSOR_Y, SCISSOR_Y)):
        for mirrored in (False, True):
            off = 3.0 if mirrored else -3.0
            items.append((f"arm-{i}-{mirrored}",
                          lay_arm(arm, theta, y + off, mirrored), "#d8c6a5"))

    platform = mechanism.build_platform()
    platform.apply_translation(plat_origin)
    items.append(("platform", platform, "#d8c6a5"))

    hinge = plat_origin + np.array([ARM_HINGE_X, 0.0, ARM_HINGE_Z])
    tilt = mechanism.forearm_angle(theta)

    forearm = mechanism.build_forearm()
    forearm.apply_translation([0.0, 0.0, -4.0])
    forearm.apply_transform(rot(tilt, [0, 1, 0]))
    forearm.apply_translation(hinge)
    items.append(("forearm", forearm, "#d8c6a5"))

    radians = np.deg2rad(tilt)
    sector_point = hinge + np.array([
        mechanism.FOREARM_SECTOR_R * np.cos(radians),
        mechanism.FOREARM_CORD_Y,
        -mechanism.FOREARM_SECTOR_R * np.sin(radians),
    ])
    cord_anchor = mechanism.FOREARM_CORD_ANCHOR.copy()
    cord_guide = mechanism.forearm_cord_guide(theta)
    items.append((
        "forearm-control-cord-fixed",
        tube_between(cord_anchor, cord_guide, 0.7),
        "#dedede",
    ))
    if theta <= mechanism.FOREARM_ENGAGE_THETA:
        slack = (cord_guide + sector_point) / 2.0 + np.array([-8.0, 0.0, 8.0])
        items.append((
            "forearm-control-cord-a",
            tube_between(cord_guide, slack, 0.7),
            "#dedede",
        ))
        items.append((
            "forearm-control-cord-b",
            tube_between(slack, sector_point, 0.7),
            "#dedede",
        ))
    else:
        items.append((
            "forearm-control-cord",
            tube_between(cord_guide, sector_point, 0.7),
            "#dedede",
        ))

    # Stowed the tendon holds the fingers curled, which is also the
    # most compact shape - the flat print pose would not fit the chest.
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
        colour = "#efe2c4" if name.startswith("hand-finger") else "#d8c6a5"
        items.append((name, part, colour))

    trigger = build_trigger()
    trigger.apply_transform(rot(90.0, [1, 0, 0]))
    trigger.apply_translation([0.0, -60.0 - 1.5, 46.0])
    items.append(("trigger", trigger, "#8d8d96"))

    latch = mechanism.build_latch()
    release = min(max(
        (mechanism.RETRACTED_SLIDER_X - slider_x) / 1.0, 0.0
    ), 1.0)
    latch_transform = trimesh.transformations.translation_matrix(
        [0.0, 0.0, mechanism.LATCH_RELEASE_TRAVEL * release]
    )
    latch.apply_transform(latch_transform)
    items.append(("latch", latch, "#8d8d96"))
    items.append(("latch-bracket", mechanism.build_latch_bracket(), "#8d8d96"))
    return_eye = trimesh.transform_points(
        [[-4.0, mechanism.LATCH_RETURN_Y, 52.0]], latch_transform
    )[0]
    items.append((
        "latch-return-band",
        tube_between((-4.0, mechanism.LATCH_RETURN_Y, 34.0),
                     return_eye, 0.9),
        "#6f4a2d",
    ))

    lid_catch = trimesh.transform_points(
        [[0.0, -52.0, LID_DROP + 7.0]], lid_transform
    )[0]
    if theta <= mechanism.THETA_MIN + 0.01:
        items.append((
            "lid-release-loop",
            tube_between(
                lid_catch,
                trimesh.transform_points(
                    [[0.0, mechanism.LATCH_RETURN_Y, 46.0]],
                    latch_transform
                )[0],
                0.7,
            ),
            "#dedede",
        ))
    else:
        items.append((
            "lid-release-loop",
            tube_between(lid_catch, lid_catch + [0.0, 0.0, -28.0], 0.7),
            "#dedede",
        ))

    anchor = mechanism.build_band_anchor()
    anchor.apply_translation([-76.0, 0.0, 4.5])
    items.append(("band-anchor", anchor, "#d8c6a5"))

    for sy in (-1.0, 1.0):
        items.append((
            f"drive-band-{int(sy):+d}",
            tube_between(
                (-76.0, sy * 50.0, 20.0),
                (slider_x + 8.0, sy * 50.0, mechanism.RAIL_Z + 12.0),
                1.2,
            ),
            "#6f4a2d",
        ))

    for name, builder in (
        ("crank-spool", mechanism.build_crank_spool),
        ("crank-key", mechanism.build_crank_key),
    ):
        crank = builder()
        crank.apply_transform(rot(90.0, [0, 1, 0]))
        crank.apply_translation([100.0, 0.0, 30.0])
        items.append((name, crank, "#8d8d96"))
    items.append((
        "reset-cord",
        tube_between(
            (slider_x + 20.0, 0.0, mechanism.RAIL_Z + 6.0),
            (mechanism.CRANK_SPOOL_X, 0.0, 30.0),
            0.7,
        ),
        "#dedede",
    ))
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
