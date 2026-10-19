"""Gravity-seated candy dish and a cupped derivative of the licensed bone rig.

The existing wrist, forearm and box drive stay unchanged. The dish opening is
level at mid-travel, limiting its tilt to 30 degrees over the full 60-degree
forearm stroke. Three asymmetric blind sockets sit flush in the metacarpal
bones so the palm has no protruding struts when used without the dish, while
the nested dish plugs directly into the palm on three short underside pins.
"""

from __future__ import annotations

import numpy as np
import trimesh
from build123d import (
    Align,
    BuildLine,
    BuildPart,
    BuildSketch,
    Cone,
    Mode,
    Plane,
    Spline,
    loft,
    make_face,
)

import mechanism
from mesh_kit import clean, cylinder, difference, union
from skeleton_hand import GRIP_POSE, Skeleton, assemble, palm_to_forearm_transform

DISH_BOTTOM_RADII = np.array([18.2, 16.0])
DISH_TOP_RADII = np.array([24.4, 28.8])
DISH_BOTTOM_CONTOUR = dict(bump_thumb=5.0, notch_thumb=1.5, bump_fingers=0.6, bump_wrist=0.0)
DISH_TOP_CONTOUR = dict(bump_thumb=5.8, notch_thumb=3.6, bump_fingers=4.8, bump_wrist=6.0)
DISH_HEIGHT = 30.8
DISH_FLOOR = 1.6
DISH_WALL = 1.5
DISH_CENTRE = np.array([-4.0, 24.0, -8.0])
DISH_OFFSET = np.array([-1.5, -2.5, -3.5])
LOCATOR_D = 3.0
LOCATOR_CLEAR = 0.4
LOCATOR_HEIGHT = 3.2
SOCKET_DEPTH = 3.6
SOCKET_BOSS_RADIUS = 2.6
SUPPORT_ROOTS = (("middle", 0.35), ("ring", 0.60), ("little", 0.35))
ROOT_Z_RIMS = (-4.76, -1.90, -5.77)


def dish_polar_radii(
    angles: np.ndarray,
    base_radii: np.ndarray,
    bump_thumb: float = 0.0,
    notch_thumb: float = 0.0,
    bump_fingers: float = 0.0,
    bump_wrist: float = 0.0,
) -> np.ndarray:
    """Contoured polar radii reaching into fingers (-Y), thumb (+X), and wrist (+Y)."""
    rx, ry = float(base_radii[0]), float(base_radii[1])
    r0 = 1.0 / np.hypot(np.cos(angles) / rx, np.sin(angles) / ry)

    def _lobe(center_deg: float, width_deg: float) -> np.ndarray:
        delta = np.arctan2(
            np.sin(angles - np.deg2rad(center_deg)),
            np.cos(angles - np.deg2rad(center_deg)),
        )
        return np.exp(-0.5 * (delta / np.deg2rad(width_deg)) ** 2)

    return (
        r0
        + bump_thumb * _lobe(-2.0, 22.0)
        - notch_thumb * _lobe(-54.0, 15.0)
        + bump_fingers * _lobe(-102.0, 26.0)
        + bump_wrist * _lobe(105.0, 32.0)
    )


def dish_rim_points(n: int = 721, inner: bool = True) -> np.ndarray:
    """3D points on the top rim of the dish in dish_frame coordinates."""
    angles = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    r_top = dish_polar_radii(angles, DISH_TOP_RADII, **DISH_TOP_CONTOUR)
    if inner:
        r_top = r_top - DISH_WALL
    return np.column_stack([
        r_top * np.cos(angles),
        r_top * np.sin(angles),
        np.full(len(angles), DISH_HEIGHT),
    ])


def _cad_mesh(shape) -> trimesh.Trimesh:
    vertices, faces = shape.tessellate(0.04)
    return clean(trimesh.Trimesh(
        vertices=[tuple(vertex) for vertex in vertices], faces=faces))


def dish_frame(skeleton: Skeleton) -> np.ndarray:
    mid = (mechanism.THETA_MIN + mechanism.THETA_MAX) / 2.0
    wrist = palm_to_forearm_transform(skeleton, 0.0, mechanism.HAND_PALM_ROLL)
    forearm = trimesh.transformations.rotation_matrix(
        np.deg2rad(mechanism.forearm_angle(mid)), [0.0, 1.0, 0.0])
    normal = (forearm @ wrist)[:3, :3].T @ [0.0, 0.0, 1.0]
    x = np.array([1.0, 0.0, 0.0]) - normal * normal[0]
    x /= np.linalg.norm(x)
    frame = np.eye(4)
    frame[:3, :3] = np.column_stack([x, np.cross(normal, x), normal])
    frame[:3, 3] = DISH_CENTRE
    shift = np.eye(4)
    shift[:3, 3] = DISH_OFFSET
    return frame @ shift


def mount_datums(skeleton: Skeleton) -> list[tuple[np.ndarray, np.ndarray]]:
    inverse = np.linalg.inv(dish_frame(skeleton))
    datums = []
    for (ray, fraction), z_rim in zip(SUPPORT_ROOTS, ROOT_Z_RIMS):
        a, b = skeleton.axes[f"metacarpal-{ray}"]
        xy = trimesh.transform_points([a + (b - a) * fraction], inverse)[0][:2]
        root = np.r_[xy, z_rim]
        seat = np.r_[xy, 0.0]
        datums.append((root, seat))
    return datums


def build_dish(skeleton: Skeleton) -> trimesh.Trimesh:
    angles = np.linspace(0.0, 2.0 * np.pi, 72, endpoint=False)
    r_bot = dish_polar_radii(angles, DISH_BOTTOM_RADII, **DISH_BOTTOM_CONTOUR)
    r_top = dish_polar_radii(angles, DISH_TOP_RADII, **DISH_TOP_CONTOUR)
    lower_inner = r_bot + (r_top - r_bot) * DISH_FLOOR / DISH_HEIGHT - DISH_WALL
    upper_inner = r_top - DISH_WALL + (r_top - r_bot) / DISH_HEIGHT
    with BuildPart() as bowl:
        with BuildSketch(Plane.XY):
            with BuildLine():
                Spline(
                    [(float(r * np.cos(a)), float(r * np.sin(a))) for r, a in zip(r_bot, angles)],
                    periodic=True,
                )
            make_face()
        with BuildSketch(Plane.XY.offset(DISH_HEIGHT)):
            with BuildLine():
                Spline(
                    [(float(r * np.cos(a)), float(r * np.sin(a))) for r, a in zip(r_top, angles)],
                    periodic=True,
                )
            make_face()
        loft()
        with BuildSketch(Plane.XY.offset(DISH_FLOOR)):
            with BuildLine():
                Spline(
                    [(float(r * np.cos(a)), float(r * np.sin(a))) for r, a in zip(lower_inner, angles)],
                    periodic=True,
                )
            make_face()
        with BuildSketch(Plane.XY.offset(DISH_HEIGHT + 1.0)):
            with BuildLine():
                Spline(
                    [(float(r * np.cos(a)), float(r * np.sin(a))) for r, a in zip(upper_inner, angles)],
                    periodic=True,
                )
            make_face()
        loft(mode=Mode.SUBTRACT)
    body = _cad_mesh(bowl.part)
    legs = []
    for root, _seat in mount_datums(skeleton):
        x, y, z_rim = root
        shoulder_bottom = z_rim + 0.25
        shoulder_height = 1.5 - shoulder_bottom
        legs.append(cylinder(
            2.4, shoulder_height,
            [x, y, shoulder_bottom + shoulder_height / 2.0]))
        peg_height = LOCATOR_HEIGHT + 0.5
        legs.append(cylinder(
            LOCATOR_D / 2.0, peg_height,
            [x, y, z_rim - LOCATOR_HEIGHT + peg_height / 2.0]))
    return union([body, *legs])


def build_cavity(_skeleton: Skeleton) -> trimesh.Trimesh:
    angles = np.linspace(0.0, 2.0 * np.pi, 72, endpoint=False)
    r_bot = dish_polar_radii(angles, DISH_BOTTOM_RADII, **DISH_BOTTOM_CONTOUR)
    r_top = dish_polar_radii(angles, DISH_TOP_RADII, **DISH_TOP_CONTOUR)
    lower = r_bot + (r_top - r_bot) * DISH_FLOOR / DISH_HEIGHT - DISH_WALL
    with BuildPart() as cavity:
        with BuildSketch(Plane.XY.offset(DISH_FLOOR)):
            with BuildLine():
                Spline(
                    [(float(r * np.cos(a)), float(r * np.sin(a))) for r, a in zip(lower, angles)],
                    periodic=True,
                )
            make_face()
        with BuildSketch(Plane.XY.offset(DISH_HEIGHT)):
            with BuildLine():
                Spline(
                    [(float(r * np.cos(a)), float(r * np.sin(a))) for r, a in zip(r_top - DISH_WALL, angles)],
                    periodic=True,
                )
            make_face()
        loft()
    return _cad_mesh(cavity.part)


def build_hand(skeleton: Skeleton) -> dict[str, trimesh.Trimesh]:
    parts = assemble(skeleton, GRIP_POSE)
    frame = dish_frame(skeleton)
    palm_in_dish = clean(parts["hand-palm"].copy().apply_transform(np.linalg.inv(frame)))
    bosses, holes = [], []
    bore_radius = (LOCATOR_D + LOCATOR_CLEAR) / 2.0
    for root, _seat in mount_datums(skeleton):
        x, y, z_rim = root
        boss_height = SOCKET_DEPTH + 1.8
        bosses.append(cylinder(
            SOCKET_BOSS_RADIUS, boss_height,
            [x, y, z_rim - boss_height / 2.0]))
        hole_height = 8.0 - (z_rim - SOCKET_DEPTH)
        holes.append(cylinder(
            bore_radius, hole_height,
            [x, y, z_rim - SOCKET_DEPTH + hole_height / 2.0]))
        chamfer = _cad_mesh(Cone(
            bore_radius - 0.1, bore_radius + 0.4, 0.6,
            align=(Align.CENTER, Align.CENTER, Align.MAX)))
        chamfer.apply_translation([x, y, z_rim + 0.1])
        holes.append(chamfer)
    palm_with_sockets = difference(union([palm_in_dish, *bosses]), holes)
    parts["hand-palm"] = clean(palm_with_sockets.apply_transform(frame))
    return parts


def assembled_hand(skeleton: Skeleton) -> dict[str, trimesh.Trimesh]:
    parts = build_hand(skeleton)
    dish = build_dish(skeleton)
    dish.apply_transform(dish_frame(skeleton))
    parts["candy-dish"] = dish
    return parts
