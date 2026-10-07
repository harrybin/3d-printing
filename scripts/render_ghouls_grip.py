"""Assembly views of the Ghoul's Grip, built from the real kinematic chain.

Every part is placed by the same numbers the generator uses, so a collision or
a mismatched pivot shows up here instead of on the printer.

    python scripts/render_ghouls_grip.py            # both views
    python scripts/render_ghouls_grip.py deployed   # hero view only
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import trimesh
import vedo

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mechanism
from gothic_chest import HINGE_Z, LID_DROP, build_chest, build_lid
from skeleton_hand import GRIP_POSE, assemble, load_skeleton
from skull import build_trigger

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images"

ARM_L = 90.0
FLOOR_PIVOT = np.array([-22.0, 8.0])     # x, z of the fixed scissor pivot
PLATFORM_PIN = -42.0                     # pin lug, local x on the platform
SCISSOR_Y = 26.0

POSES = {"retracted": 16.0, "deployed": 76.0}


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


def build_scene(pose: str):
    theta = POSES[pose]
    rad = np.deg2rad(theta)
    lift = ARM_L * np.sin(rad)
    slider_x = FLOOR_PIVOT[0] + ARM_L * np.cos(rad)
    plate_z = FLOOR_PIVOT[1] + lift
    plat_origin = np.array([FLOOR_PIVOT[0] - PLATFORM_PIN, 0.0, plate_z + 8.0])

    items = []
    items.append(("chest", build_chest(), "#43434e"))

    lid = build_lid()
    lid.apply_translation([0.0, 0.0, LID_DROP])
    if pose == "deployed":
        lid.apply_transform(rot(-108.0, [0, 1, 0],
                                [-100.0 + 3.0 - 4.0, 0.0, HINGE_Z]))
    items.append(("lid", lid, "#43434e"))

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

    hinge = plat_origin + np.array([14.0, 0.0, 16.0])
    tilt = 0.0 if pose == "deployed" else -104.0

    forearm = mechanism.build_forearm()
    forearm.apply_translation([0.0, 0.0, -4.0])
    forearm.apply_transform(rot(tilt, [0, 1, 0]))
    forearm.apply_translation(hinge)
    items.append(("forearm", forearm, "#d8c6a5"))

    skeleton = load_skeleton()
    # Stowed the tendon holds the fingers curled, which is also the
    # most compact shape - the flat print pose would not fit the chest.
    hand = assemble(skeleton, GRIP_POSE)
    stack = trimesh.util.concatenate(list(hand.values()))
    wrist_y = stack.bounds[0][1]
    for name, mesh in hand.items():
        part = mesh.copy()
        part.apply_transform(rot(90.0, [1, 0, 0]))
        part.apply_translation([0.0, 0.0, -wrist_y + 38.0])
        part.apply_transform(rot(tilt, [0, 1, 0]))
        part.apply_translation(hinge)
        colour = "#efe2c4" if name.startswith("hand-finger") else "#d8c6a5"
        items.append((name, part, colour))

    trigger = build_trigger()
    trigger.apply_transform(rot(90.0, [1, 0, 0]))
    trigger.apply_translation([0.0, -60.0 - 1.5, 46.0])
    items.append(("trigger", trigger, "#8d8d96"))

    latch = mechanism.build_latch()
    items.append(("latch", latch, "#8d8d96"))
    items.append(("latch-bracket", mechanism.build_latch_bracket(), "#8d8d96"))

    anchor = mechanism.build_band_anchor()
    anchor.apply_translation([-76.0, 0.0, 3.0])
    items.append(("band-anchor", anchor, "#d8c6a5"))

    crank = mechanism.build_crank()
    crank.apply_transform(rot(90.0, [0, 1, 0]))
    crank.apply_translation([-100.0, 0.0, 30.0])
    items.append(("crank", crank, "#8d8d96"))
    return items


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
