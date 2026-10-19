"""Build the Ghoul's Grip skeleton hand from real human bone geometry.

The bones come from the NIH 3D Print Exchange entry 3DPX-016815 (CC-BY, see
``extract_hand_bones.py``). They are delivered as 27 separate shells in a
relaxed scan pose, which is unsuitable as a printable assembly: the carpals
float apart and the fingers curl in the scanner's pose.

This module re-rigs them. Every finger ray is rebuilt as a chain - each bone
keeps its real length and shape but is re-aimed along a designed direction -
and the chain is fused into one rigid body with rounded, solid knuckles.
Each finger keeps its curved print pose without relief gaps, wire or tendons.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import trimesh

from extract_hand_bones import RAYS, load_bones
from mesh_kit import (clean, cylinder, difference, fuse, simplify,
                      simplify_tolerance, sphere, union)

# A life size hand is 190 mm long and simply does not fit into the 194 mm chest
# cavity together with its forearm, so the whole skeleton is scaled down.
HAND_SCALE = 0.72

DORSAL = np.array([0.0, 0.0, 1.0])

PEG_D = 4.0
PEG_LEN = 10.0
MCP_SOCKET_START = 2.4
MCP_RELIEF_D = 8.6
MCP_THUMB_RELIEF_D = 11.2
MCP_RELIEF_LEN = 7.0
MCP_RELIEF_START = 2.0
JOINT_END_INSET = 2.0
MCP_END_INSET = 2.4
SOCKET_CLEAR = 0.40
WRIST_D = 12.0
WRIST_SOCKET = 16.0
WRIST_SOCKET_LEAD_IN = 2.0
WRIST_PIN_FROM_MOUNT = WRIST_SOCKET * 0.6
# Flexion per joint. The MCP knuckle is a rigid peg joint, so its bend is built
# into the palm and the proximal phalanx follows that angle in the print pose.
MCP_DEG = {"thumb": 40.0, "index": 40.0, "middle": 40.0, "ring": 38.0, "little": 36.0}
MCP_YAW_DEG = {"thumb": 55.0}
FLAT_POSE = {
    "thumb": (0.0, 0.0),
    "index": (0.0, 0.0, 0.0),
    "middle": (0.0, 0.0, 0.0),
    "ring": (0.0, 0.0, 0.0),
    "little": (0.0, 0.0, 0.0),
}
GRIP_POSE = {
    "thumb": (MCP_DEG["thumb"], 35.0),
    "index": (MCP_DEG["index"], 57.0, 27.0),
    "middle": (MCP_DEG["middle"], 55.0, 25.0),
    "ring": (MCP_DEG["ring"], 57.0, 27.0),
    "little": (MCP_DEG["little"], 59.0, 29.0),
}

PHALANGES = {
    "thumb": ("proximal", "distal"),
    "index": ("proximal", "middle", "distal"),
    "middle": ("proximal", "middle", "distal"),
    "ring": ("proximal", "middle", "distal"),
    "little": ("proximal", "middle", "distal"),
}


@dataclass
class Skeleton:
    bones: dict[str, trimesh.Trimesh]
    axes: dict[str, np.ndarray]


def load_skeleton(scale: float = HAND_SCALE) -> Skeleton:
    bones, axes = load_bones()
    scaled_bones, scaled_axes = {}, {}
    for name, mesh in bones.items():
        copy = mesh.copy()
        copy.apply_scale(scale)
        copy.fix_normals()
        scaled_bones[name] = copy
        scaled_axes[name] = axes[name] * scale
    return Skeleton(scaled_bones, scaled_axes)


def _flex_axis(direction: np.ndarray) -> np.ndarray:
    """Hinge axis of a joint: perpendicular to the bone and to the palm normal."""
    axis = np.cross(DORSAL, direction)
    norm = np.linalg.norm(axis)
    if norm < 1e-6:
        axis = np.array([1.0, 0.0, 0.0])
        norm = 1.0
    return axis / norm


def _rotate(vector: np.ndarray, axis: np.ndarray, angle: float) -> np.ndarray:
    matrix = trimesh.transformations.rotation_matrix(angle, axis)[:3, :3]
    return matrix @ vector


def _local_radius(mesh: trimesh.Trimesh, point: np.ndarray,
                  direction: np.ndarray, window: float = 3.0) -> float:
    """Radius of the bone around ``point``, measured on a short slice."""
    offset = mesh.vertices - point
    along = offset @ direction
    near = offset[np.abs(along) <= window]
    if len(near) < 4:
        near = offset[np.argsort(np.abs(along))[:40]]
    radial = near - np.outer(near @ direction, direction)
    return float(np.linalg.norm(radial, axis=1).max())


@dataclass
class PosedRay:
    """One re-aimed finger ray plus the frames of its joints."""
    bones: list[trimesh.Trimesh]
    joints: list[np.ndarray]        # joint centres, proximal to distal
    directions: list[np.ndarray]    # unit direction of every bone
    base: np.ndarray                # MCP joint, where the finger meets the palm
    base_direction: np.ndarray


def pose_ray(skeleton: Skeleton, ray: str, angles) -> PosedRay:
    """Re-aim the phalanges of one ray along a designed chain of directions."""
    head_axis = skeleton.axes[f"metacarpal-{ray}"]
    base_direction = head_axis[1] - head_axis[0]
    base_direction = base_direction / np.linalg.norm(base_direction)
    base_direction = _rotate(
        base_direction, DORSAL, np.deg2rad(MCP_YAW_DEG.get(ray, 0.0)))
    flex_axis = _flex_axis(base_direction)
    cumulative_angle = 0.0
    joint = head_axis[1].copy()

    base = joint.copy()
    bones, joints, directions = [], [joint.copy()], []
    for name, angle in zip(PHALANGES[ray], angles):
        mesh = skeleton.bones[f"{ray}-{name}"].copy()
        a, b = skeleton.axes[f"{ray}-{name}"]
        length = float(np.linalg.norm(b - a))
        cumulative_angle += angle
        direction = _rotate(
            base_direction, flex_axis, np.deg2rad(cumulative_angle))
        direction = direction / np.linalg.norm(direction)

        rotation = trimesh.geometry.align_vectors((b - a) / length, direction)
        mesh.apply_transform(rotation)
        moved_a = (rotation[:3, :3] @ a) + rotation[:3, 3]
        mesh.apply_translation(joint - moved_a)

        # Real scan bones have bulbous articular ends. Rotating two complete
        # shells about the same joint centre makes those ends occupy the same
        # volume. Pull each end back to leave a real joint line; the explicit
        # solid knuckle below reconnects them without anatomical overlap.
        along = (mesh.vertices - joint) @ direction
        start_inset = MCP_END_INSET if not bones else JOINT_END_INSET
        usable = length - start_inset - JOINT_END_INSET
        remapped = start_inset + along * (usable / length)
        mesh.vertices += np.outer(remapped - along, direction)

        bones.append(mesh)
        directions.append(direction.copy())
        joint = joint + direction * length
        joints.append(joint.copy())
    # The MCP socket is always coaxial with the first phalanx, so a finger
    # printed flat and a finger shown in the grip pose share the same joint.
    return PosedRay(bones, joints, directions, base, directions[0])


def build_finger(skeleton: Skeleton, ray: str, pose: dict) -> trimesh.Trimesh:
    """One rigid printed finger: posed bones, solid knuckles and MCP socket."""
    posed = pose_ray(skeleton, ray, pose[ray])

    collars = []
    for index in range(1, len(posed.joints) - 1):
        point = posed.joints[index]
        d0, d1 = posed.directions[index - 1], posed.directions[index]
        b0, b1 = posed.bones[index - 1], posed.bones[index]
        v0 = b0.vertices[(b0.vertices - point) @ d0 >= -4.5]
        v1 = b1.vertices[(b1.vertices - point) @ d1 <= 4.5]
        collars.append(clean(trimesh.Trimesh(vertices=np.vstack([v0, v1])).convex_hull))
        radius = min(_local_radius(b0, point - d0 * JOINT_END_INSET, d0, window=2.0),
                     _local_radius(b1, point + d1 * JOINT_END_INSET, d1, window=2.0))
        collars.append(sphere(radius * 0.90, point, subdivisions=3))

    # Socket neck that slides onto the peg on the metacarpal head.
    neck_length = PEG_LEN - 2.0
    neck = cylinder(PEG_D / 2.0 + 1.6, neck_length,
                    posed.base + posed.base_direction * (
                        MCP_SOCKET_START + neck_length / 2.0),
                    posed.base_direction)

    # OrcaSlicer 2.3 rejects one pathological 0.35 mm index voxelization even
    # though it is manifold. A 0.34 mm reconstruction preserves the shape and
    # slices cleanly; the other rays retain the proven 0.35 mm pitch.
    fuse_pitch = 0.34 if ray == "index" else 0.35
    body = fuse([*posed.bones, *collars, neck], pitch=fuse_pitch,
                bridge=1.1, smooth=0.9)
    body = simplify(body, 9000)

    socket = cylinder(
        (PEG_D + SOCKET_CLEAR) / 2.0, PEG_LEN + 2.0,
        posed.base + posed.base_direction * (PEG_LEN / 2.0),
        posed.base_direction)

    result = simplify_tolerance(difference(body, [socket]), 0.01)
    if not result.is_volume or len(result.split(only_watertight=False)) != 1:
        raise RuntimeError(f"{ray}: solid-knuckle finger is not one closed body")
    return result


def wrist_frame(skeleton: Skeleton) -> tuple[np.ndarray, np.ndarray]:
    """Mount point and forearm direction at the proximal end of the carpals."""
    carpals = [skeleton.bones[f"carpal-{i}"] for i in range(1, 9)]
    verts = np.vstack([c.vertices for c in carpals])
    centre = verts.mean(axis=0)
    return np.array([centre[0], verts[:, 1].min(), centre[2]]), np.array([0.0, -1.0, 0.0])


def build_palm(skeleton: Skeleton) -> trimesh.Trimesh:
    """Carpals and metacarpals fused into one rigid part with knuckle pegs."""
    carpals = [skeleton.bones[f"carpal-{i}"] for i in range(1, 9)]
    metacarpals = [skeleton.bones[f"metacarpal-{ray}"] for ray in RAYS]

    # The carpals are eight loose pebbles in the scan. A shrunken hull of the
    # whole group gives them a common core so they fuse into a solid wrist
    # block while their individual shapes still read on the surface.
    hull = trimesh.Trimesh(vertices=np.vstack([c.vertices for c in carpals])).convex_hull
    core = hull.copy()
    core.apply_translation(-hull.centroid)
    core.apply_scale(0.86)
    core.apply_translation(hull.centroid)

    mount, forearm = wrist_frame(skeleton)
    boss = cylinder(WRIST_D / 2.0 + 2.5, WRIST_SOCKET + 6.0,
                    mount + forearm * (WRIST_SOCKET / 2.0 - 3.0), forearm)

    body = fuse([*carpals, *metacarpals, core, boss, *metacarpal_pegs(skeleton)],
                pitch=0.45, bridge=1.6, smooth=0.9)
    body = simplify(body, 24000)

    # Extend the bore beyond the proximal boss face. Ending the cutter exactly
    # on that face can leave a boolean cap which looks solid in the exported
    # 3MF even though most of the socket volume is empty.
    socket_length = WRIST_SOCKET + WRIST_SOCKET_LEAD_IN + 2.0
    socket_centre = mount + forearm * (
        WRIST_SOCKET / 2.0 + WRIST_SOCKET_LEAD_IN / 2.0 - 1.0
    )
    cutters = [cylinder(
        WRIST_D / 2.0,
        socket_length,
        socket_centre,
        forearm,
    )]
    # A shallow counterbore is a visible insertion cue and absorbs minor
    # elephant-foot or support scars without loosening the full engagement.
    cutters.append(cylinder(
        WRIST_D / 2.0 + 0.5,
        WRIST_SOCKET_LEAD_IN + 0.8,
        mount + forearm * (
            WRIST_SOCKET + WRIST_SOCKET_LEAD_IN / 2.0
        ),
        forearm,
    ))
    side = np.array([1.0, 0.0, 0.0])
    cutters.append(cylinder(1.9 / 2.0, WRIST_D + 14.0,
                            mount + forearm * WRIST_PIN_FROM_MOUNT, side))
    mcp_reliefs = []
    for ray in RAYS:
        direction = peg_direction(skeleton, ray)
        head = skeleton.axes[f"metacarpal-{ray}"][1]
        mcp_reliefs.append(cylinder(
            (MCP_THUMB_RELIEF_D if ray == "thumb" else MCP_RELIEF_D) / 2.0,
            MCP_RELIEF_LEN,
            head + direction * (MCP_RELIEF_START + MCP_RELIEF_LEN / 2.0),
            direction,
        ))
    body = difference(body, [*cutters, *mcp_reliefs])
    # Leave each MCP peg rooted in the metacarpal while clearing its scan-bone
    # head from the finger's 4.4 mm socket.
    return union([body, *metacarpal_pegs(skeleton)])


def palm_to_forearm_transform(
    skeleton: Skeleton,
    pin_centre_z: float,
    palm_roll_deg: float,
) -> np.ndarray:
    """Place the palm socket on the forearm spigot by its cross-pin datum."""
    mount, forearm = wrist_frame(skeleton)
    palm_pin = mount + forearm * WRIST_PIN_FROM_MOUNT
    rotate_upright = trimesh.transformations.rotation_matrix(
        np.pi / 2.0, [1.0, 0.0, 0.0]
    )
    roll = trimesh.transformations.rotation_matrix(
        np.deg2rad(palm_roll_deg), [0.0, 0.0, 1.0]
    )
    rotation = roll @ rotate_upright
    transformed_pin = (
        rotation[:3, :3] @ palm_pin + rotation[:3, 3]
    )
    translation = np.array([0.0, 0.0, pin_centre_z]) - transformed_pin
    result = rotation.copy()
    result[:3, 3] += translation
    return result


def metacarpal_pegs(skeleton: Skeleton) -> list[trimesh.Trimesh]:
    """Knuckle pegs. Their palmar tilt is the baked-in MCP flexion."""
    pegs = []
    for ray in RAYS:
        direction = peg_direction(skeleton, ray)
        head = skeleton.axes[f"metacarpal-{ray}"][1]
        pegs.append(cylinder(PEG_D / 2.0, PEG_LEN,
                             head + direction * (PEG_LEN / 2.0 - 1.5), direction))
    return pegs


def peg_direction(skeleton: Skeleton, ray: str) -> np.ndarray:
    a, b = skeleton.axes[f"metacarpal-{ray}"]
    direction = (b - a) / np.linalg.norm(b - a)
    direction = _rotate(
        direction, DORSAL, np.deg2rad(MCP_YAW_DEG.get(ray, 0.0)))
    direction = _rotate(direction, _flex_axis(direction), np.deg2rad(MCP_DEG[ray]))
    return direction / np.linalg.norm(direction)


def assemble(skeleton: Skeleton, pose: dict = GRIP_POSE) -> dict[str, trimesh.Trimesh]:
    """Palm plus all five fingers, each seated on its knuckle peg."""
    parts = {"hand-palm": build_palm(skeleton)}
    for ray in RAYS:
        parts[f"hand-finger-{ray}"] = build_finger(skeleton, ray, pose)
    return parts


if __name__ == "__main__":
    import sys

    skeleton = load_skeleton()
    target = sys.argv[1] if len(sys.argv) > 1 else "grip"
    scene = trimesh.Scene()
    for name, mesh in assemble(skeleton, FLAT_POSE if target == "flat" else GRIP_POSE).items():
        print(f"{name:22s} faces {len(mesh.faces):6d} watertight {mesh.is_watertight} "
              f"bodies {len(mesh.split(only_watertight=False))} "
              f"extents {np.round(mesh.extents, 1).tolist()}")
        scene.add_geometry(mesh, node_name=name)
    out = f"model-sources/ghouls-grip/reference/_hand_{target}.stl"
    scene.to_geometry().export(out)
    print("wrote", out)
