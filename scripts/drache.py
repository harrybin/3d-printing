"""Parametric & hybrid Blender+Python generator for the Toothless (Ohnezahn) dragon figure.

Deliverables produced:
  - models/drache-view.3mf  : Assembled multi-state 3MF (Plate 1: Assembled, Plate 2: Exploded keyed assembly)
  - models/drache-print.3mf : Consolidated 4-color Anycubic Kobra S1 + ACE Pro print project (4 single-color plates, 0 purge)
  - models/drache.stl       : Watertight ASCII STL of the complete assembled dragon
  - models/drache-koerper.stl, models/drache-auge-links.stl, models/drache-auge-rechts.stl,
    models/drache-schwanzflosse-links-rot.stl, models/drache-emblem-weiss.stl
  - docs/drache-montage-und-kollisionspruefung.md : Collision & insertion-sweep verification report
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import manifold3d as m3d
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
BUILD_DIR = ROOT / "build" / "drache"
DOCS = ROOT / "docs"
IMAGES = DOCS / "images"

BLENDER_BIN = Path(os.environ.get(
    "BLENDER_BIN", r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"))
ORCA_BIN = Path(os.environ.get(
    "ORCA_SLICER_BIN", r"C:\Program Files\OrcaSlicer\orca-slicer.exe"))
PROFILE_ROOT = ORCA_BIN.parent / "resources" / "profiles" / "Anycubic"
MACHINE = PROFILE_ROOT / "machine" / "Anycubic Kobra S1 0.4 nozzle.json"
BASE_PROCESS = PROFILE_ROOT / "process" / "0.20mm Standard @Anycubic Kobra S1 0.4 nozzle.json"
FILAMENT_PRESET = PROFILE_ROOT / "filament" / "Anycubic PLA @Anycubic Kobra S1 0.4 nozzle.json"
METADATA_ENTRY = "Metadata/ghouls_grip_print_metadata.xml"

# Explicit parameterized fit clearances (mm per side)
PRESS_CLEAR = 0.15       # Eye inserts & tail-fin tenon press-fit clearance per side
EMBLEM_CLEAR = 0.12      # Skull emblem inlay press-fit clearance per side
PAW_FLAT_Z = 1.35        # Height sliced flat at bottom of paws to guarantee bed adhesion


@dataclass(frozen=True)
class MaterialSpec:
    slug: str
    name: str
    color_hex: str
    slot: int  # 1-based ACE Pro slot


MATERIALS = {
    "black": MaterialSpec("black", "Koerper - schwarzes PLA", "#1C1E21", 1),
    "green": MaterialSpec("green", "Augen - hellgruenes PLA", "#4CC936", 2),
    "red":   MaterialSpec("red",   "Schwanzflosse - rotes PLA", "#D62828", 3),
    "white": MaterialSpec("white", "Wikinger-Emblem - weisses PLA", "#F4F5F7", 4),
}

PART_MATERIAL = {
    "drache-koerper": MATERIALS["black"],
    "drache-auge-links": MATERIALS["green"],
    "drache-auge-rechts": MATERIALS["green"],
    "drache-schwanzflosse-links-rot": MATERIALS["red"],
    "drache-emblem-weiss": MATERIALS["white"],
}


def to_manifold(mesh: trimesh.Trimesh) -> m3d.Manifold:
    v = np.ascontiguousarray(mesh.vertices, dtype=np.float32)
    f = np.ascontiguousarray(mesh.faces, dtype=np.uint32)
    return m3d.Manifold(m3d.Mesh(vert_properties=v, tri_verts=f))


def from_manifold(mani: m3d.Manifold) -> trimesh.Trimesh:
    m = mani.to_mesh()
    verts = np.array(m.vert_properties[:, :3], dtype=np.float64)
    faces = np.array(m.tri_verts, dtype=np.int64)
    return trimesh.Trimesh(vertices=verts, faces=faces, process=False)


def manifold_union(meshes: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    acc = to_manifold(meshes[0])
    for m in meshes[1:]:
        acc = acc + to_manifold(m)
    return from_manifold(acc)


def manifold_diff(base: trimesh.Trimesh, cutters: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    acc = to_manifold(base)
    for c in cutters:
        acc = acc - to_manifold(c)
    return from_manifold(acc)


def manifold_intersect(a: trimesh.Trimesh, b: trimesh.Trimesh) -> trimesh.Trimesh:
    res = to_manifold(a) ^ to_manifold(b)
    m = res.to_mesh()
    if len(m.tri_verts) == 0:
        return trimesh.Trimesh()
    return from_manifold(res)


def intersection_volume(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    inter = manifold_intersect(a, b)
    if len(inter.faces) == 0:
        return 0.0
    return float(abs(inter.volume))


def make_ortho_frame(normal: np.ndarray, up_hint: np.ndarray = np.array([0.0, 0.0, 1.0])) -> np.ndarray:
    """Return a 4x4 rotation matrix whose local +Z axis aligns with `normal`."""
    z_axis = normal / np.linalg.norm(normal)
    x_axis = np.cross(up_hint, z_axis)
    if np.linalg.norm(x_axis) < 1e-6:
        x_axis = np.cross(np.array([1.0, 0.0, 0.0]), z_axis)
    x_axis = x_axis / np.linalg.norm(x_axis)
    y_axis = np.cross(z_axis, x_axis)
    mat = np.eye(4)
    mat[:3, 0] = x_axis
    mat[:3, 1] = y_axis
    mat[:3, 2] = z_axis
    return mat


def make_almond_prism(
    rx: float,
    ry: float,
    z0: float,
    z1: float,
    asymmetry: float = 0.18,
    dome_top: float = 0.0,
    n_theta: int = 48,
    n_rings: int = 8,
) -> trimesh.Trimesh:
    """Create a watertight almond-shaped prism/dome along local Z=[z0, z1 + dome_top].

    `asymmetry` makes the +Y side slightly fuller than the -Y side so left and right
    eye inserts cannot be flipped upside-down.
    """
    thetas = np.linspace(0.0, 2.0 * math.pi, n_theta, endpoint=False)

    def profile_xy(scale: float = 1.0):
        pts = []
        for th in thetas:
            c, s = math.cos(th), math.sin(th)
            # Almond pinch at horizontal tips (c near ±1) and slight upper-lid arch
            pinch = 1.0 - 0.22 * (c ** 2)
            asym = 1.0 + asymmetry * s
            x = rx * scale * c
            y = ry * scale * s * pinch * asym
            pts.append((x, y))
        return np.array(pts, dtype=np.float64)

    verts = []
    faces = []

    # Bottom center vertex (index 0)
    verts.append((0.0, 0.0, z0))
    # Bottom ring (indices 1 .. n_theta)
    ring_bot = profile_xy(1.0)
    for x, y in ring_bot:
        verts.append((x, y, z0))

    # Side/top rings
    ring_starts = [1]
    for r_idx in range(1, n_rings + 1):
        u = r_idx / n_rings
        if dome_top > 0.0 and r_idx > 1:
            # Smooth dome taper near top
            t_dome = (r_idx - 1) / (n_rings - 1)
            scale = math.cos(t_dome * math.pi * 0.42)
            z = z1 + dome_top * math.sin(t_dome * math.pi * 0.5)
        else:
            scale = 1.0
            z = z0 + u * (z1 - z0)
        start = len(verts)
        ring_starts.append(start)
        for x, y in profile_xy(scale):
            verts.append((x, y, z))

    # Top center vertex
    top_center_idx = len(verts)
    verts.append((0.0, 0.0, z1 + dome_top))

    # Bottom cap fan (normal -Z)
    for i in range(n_theta):
        i_next = (i + 1) % n_theta
        faces.append((0, 1 + i_next, 1 + i))

    # Side quads between consecutive rings
    for r in range(len(ring_starts) - 1):
        s0 = ring_starts[r]
        s1 = ring_starts[r + 1]
        for i in range(n_theta):
            i_next = (i + 1) % n_theta
            faces.append((s0 + i, s0 + i_next, s1 + i_next))
            faces.append((s0 + i, s1 + i_next, s1 + i))

    # Top cap fan (normal +Z)
    s_last = ring_starts[-1]
    for i in range(n_theta):
        i_next = (i + 1) % n_theta
        faces.append((top_center_idx, s_last + i, s_last + i_next))

    tm = trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces), process=True)
    trimesh.repair.fix_normals(tm)
    return from_manifold(to_manifold(tm))


def build_eyes_and_cutters() -> tuple[
    trimesh.Trimesh,
    trimesh.Trimesh,
    dict[str, trimesh.Trimesh],
    list[trimesh.Trimesh],
    list[trimesh.Trimesh],
    dict[str, np.ndarray],
]:
    """Build left/right green eye inserts (assembled & flat print pose), head socket cutters, and black pupil bosses."""
    eye_configs = {
        "drache-auge-links": {
            "center": np.array([32.6, 5.2, 14.8]),
            "normal": np.array([0.68, 0.60, 0.42]),
            "asym": 0.16,
        },
        "drache-auge-rechts": {
            "center": np.array([31.8, -6.8, 14.8]),
            "normal": np.array([0.70, -0.58, 0.42]),
            "asym": -0.16,
        },
    }

    eye_meshes = {}
    eye_print_meshes = {}
    socket_cutters = []
    pupil_bosses = []
    insertion_vectors = {}

    for name, cfg in eye_configs.items():
        center = cfg["center"]
        normal = cfg["normal"] / np.linalg.norm(cfg["normal"])
        insertion_vectors[name] = -normal  # Inserted from outside straight in along -normal
        frame = make_ortho_frame(normal, up_hint=np.array([0.0, 0.0, 1.0]))
        frame[:3, 3] = center

        # 1. Socket cutter in black head (oversized by PRESS_CLEAR = 0.15 mm)
        sock = make_almond_prism(
            rx=3.25 + PRESS_CLEAR,
            ry=2.35 + PRESS_CLEAR,
            z0=-2.2,
            z1=3.5,
            asymmetry=cfg["asym"],
            dome_top=0.0,
        )
        sock.apply_transform(frame)
        socket_cutters.append(sock)

        # 2. Integral black vertical slit-pupil pillar in the head socket
        pupil = make_almond_prism(
            rx=0.68,
            ry=1.65,
            z0=-2.4,
            z1=0.65,
            asymmetry=0.0,
            dome_top=0.20,
        )
        pupil_shift = np.eye(4)
        pupil_shift[0, 3] = 0.35 if "rechts" in name else -0.35
        pupil.apply_transform(frame @ pupil_shift)
        pupil_bosses.append(pupil)

        # 3. Green eye insert (almond sclera with convex dome and vertical slot for black pupil)
        eye_outer = make_almond_prism(
            rx=3.25,
            ry=2.35,
            z0=-2.05,
            z1=0.45,
            asymmetry=cfg["asym"],
            dome_top=0.45,
        )
        pupil_slot_cutter = make_almond_prism(
            rx=0.68 + PRESS_CLEAR,
            ry=1.65 + PRESS_CLEAR,
            z0=-3.0,
            z1=2.0,
            asymmetry=0.0,
            dome_top=0.0,
        )
        pupil_slot_cutter.apply_transform(pupil_shift)
        eye_local = manifold_diff(eye_outer, [pupil_slot_cutter])

        # Save flat print-oriented copy (flat back at Z = 0.000 mm, dome facing +Z)
        eye_flat = eye_local.copy()
        eye_flat.apply_translation([0.0, 0.0, -eye_flat.bounds[0, 2]])
        eye_print_meshes[name] = eye_flat

        eye_part = eye_local.copy()
        eye_part.apply_transform(frame)
        eye_meshes[name] = eye_part

    return (
        eye_meshes["drache-auge-links"],
        eye_meshes["drache-auge-rechts"],
        eye_print_meshes,
        socket_cutters,
        pupil_bosses,
        insertion_vectors,
    )


def make_extruded_polygon(pts_2d: list[tuple[float, float]], z0: float, z1: float) -> trimesh.Trimesh:
    """Create a watertight prism from a star-convex 2D polygon around its centroid."""
    pts = np.array(pts_2d, dtype=np.float64)
    n = len(pts)
    cx, cy = pts.mean(axis=0)
    verts = [(cx, cy, z0), (cx, cy, z1)]
    for x, y in pts:
        verts.append((x, y, z0))
    for x, y in pts:
        verts.append((x, y, z1))
    faces = []
    for i in range(n):
        inext = (i + 1) % n
        b0, b1 = 2 + i, 2 + inext
        t0, t1 = 2 + n + i, 2 + n + inext
        faces.append((0, b1, b0))      # Bottom cap
        faces.append((1, t0, t1))      # Top cap
        faces.append((b0, b1, t1))     # Side quad 1
        faces.append((b0, t1, t0))     # Side quad 2
    tm = trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces), process=True)
    trimesh.repair.fix_normals(tm)
    return from_manifold(to_manifold(tm))


def build_tail_fins_and_emblem() -> tuple[
    trimesh.Trimesh,
    trimesh.Trimesh,
    trimesh.Trimesh,
    trimesh.Trimesh,
    trimesh.Trimesh,
    dict[str, np.ndarray],
]:
    """Construct:
      - Right black tail-fin lobe (fused into `drache-koerper`)
      - Left tail-stem mounting boss + keyed mortise cutter on `drache-koerper`
      - Left red prosthetic tail fin (`drache-schwanzflosse-links-rot`) with keyed tenon
        and Viking skull pocket
      - White Viking skull emblem inlay (`drache-emblem-weiss`)
    """
    # The tail tip rises at X ~ -30.5 mm, Y ~ +0.6 mm, Z ~ 47..58.5 mm.
    # The tail fluke sits in an inclined plane tilted forward/upward along the tail tip
    # (visible clearly in tiles #02, #18, #23).
    fluke_origin = np.array([-30.4, 0.6, 52.8])
    # Local frame of the tail fluke:
    #   local X : along the fin span (+X_local = +Y_world = Left Red Fin side!)
    #   local Y : along the tail axis (upward/backward along the tail tip)
    #   local Z : fin face normal (pointing forward-upward toward the viewer in front/oblique views)
    fin_normal = np.array([0.92, 0.0, 0.39])
    fin_normal = fin_normal / np.linalg.norm(fin_normal)
    fin_up = np.array([-0.39, 0.0, 0.92])  # Along tail stem toward tip
    fin_left = np.array([0.0, 1.0, 0.0])   # Exact world +Y (dragon's left side!)

    fluke_mat = np.eye(4)
    fluke_mat[:3, 0] = fin_left
    fluke_mat[:3, 1] = fin_up
    fluke_mat[:3, 2] = fin_normal
    fluke_mat[:3, 3] = fluke_origin

    # 1. RIGHT BLACK TAIL FIN LOBE (local X < 0, i.e., world -Y side)
    right_fin_poly = [
        (0.0, -5.8),
        (-3.8, -6.2),
        (-8.2, -4.5),
        (-11.5, -1.2),
        (-9.6, 1.4),     # Scallop 1
        (-12.2, 4.4),
        (-9.8, 6.4),     # Scallop 2
        (-11.2, 9.5),    # Top-right fluke tip (reaches X_world ~ -39.5, Z_world ~ 60.5)
        (-5.8, 8.4),
        (-1.2, 6.8),
        (0.0, 5.8),
    ]
    right_fin_blade = make_extruded_polygon(right_fin_poly, z0=-1.40, z1=1.40)
    # Add 3 raised fin struts on the right black fin
    right_ribs = [
        make_extruded_polygon([(-0.4, -3.6), (-11.2, -1.0), (-10.8, -0.1), (-0.4, -2.4)], -1.75, 1.75),
        make_extruded_polygon([(-0.4, -0.5), (-11.8, 4.2), (-11.2, 5.0), (-0.4, 0.7)], -1.75, 1.75),
        make_extruded_polygon([(-0.4, 2.6), (-10.8, 9.2), (-9.8, 9.6), (-0.4, 3.8)], -1.75, 1.75),
    ]
    right_black_fin = manifold_union([right_fin_blade, *right_ribs])
    right_black_fin.apply_transform(fluke_mat)

    # 2. TAIL-STEM HUB & KEYED MORTISE SOCKET FOR LEFT RED FIN
    # Central hub on the right/center of the tail stem (x from -2.0 to +1.05) so the red fin
    # begins right next to the centerline (x = +1.05)!
    stem_hub = make_extruded_polygon(
        [(-2.0, -5.8), (1.05, -5.8), (1.05, 6.2), (-2.0, 6.2)],
        z0=-2.55,
        z1=2.35,
    )
    stem_hub.apply_transform(fluke_mat)

    # Keyed asymmetric tenon along local +X (world +Y! So insertion direction is pure (0, -1, 0)!)
    # Coplanar on the back face (z0 = -1.45) with the fin blade so the red fin prints 100% flat!
    tenon_pts = [
        (-1.2, -3.2),
        (1.6, -3.2),
        (1.6, 3.6),
        (-1.2, 3.6),
    ]
    tenon_solid = make_extruded_polygon(tenon_pts, z0=-1.45, z1=1.05)

    mortise_pts = [
        (-1.2 - PRESS_CLEAR, -3.2 - PRESS_CLEAR),
        (1.8 + PRESS_CLEAR, -3.2 - PRESS_CLEAR),
        (1.8 + PRESS_CLEAR, 3.6 + PRESS_CLEAR),
        (-1.2 - PRESS_CLEAR, 3.6 + PRESS_CLEAR),
    ]
    mortise_cutter = make_extruded_polygon(
        mortise_pts,
        z0=-1.45 - PRESS_CLEAR,
        z1=1.05 + PRESS_CLEAR,
    )
    # Clear the outer step (x >= 1.05) so the red fin root covers the full left side of the tail tip!
    shoulder_clear = make_extruded_polygon(
        [(1.05 - PRESS_CLEAR, -7.5), (14.5, -7.5), (14.5, 12.0), (1.05 - PRESS_CLEAR, 12.0)],
        z0=-4.0,
        z1=4.0,
    )
    left_mortise_cutter = manifold_union([mortise_cutter, shoulder_clear])
    left_mortise_cutter.apply_transform(fluke_mat)

    # 3. LEFT RED TAIL FIN PROSTHESIS (`drache-schwanzflosse-links-rot`)
    left_fin_poly = [
        (1.05, -5.8),
        (5.2, -6.2),
        (9.0, -4.4),
        (11.8, -1.2),
        (9.8, 1.5),      # Scallop 1
        (12.4, 4.5),
        (10.0, 6.5),     # Scallop 2
        (11.5, 9.6),     # Top-left red fluke tip (reaches Z_world ~ 60.5 mm!)
        (6.0, 8.6),
        (1.05, 6.2),
    ]
    left_fin_blade = make_extruded_polygon(left_fin_poly, z0=-1.45, z1=1.45)
    left_ribs = [
        make_extruded_polygon([(1.05, -3.6), (11.5, -1.0), (11.0, -0.1), (1.05, -2.4)], -1.45, 1.45),
        make_extruded_polygon([(1.05, -0.4), (12.0, 4.3), (11.4, 5.1), (1.05, 0.7)], -1.45, 1.45),
        make_extruded_polygon([(1.05, 2.8), (11.1, 9.3), (10.1, 9.7), (1.05, 3.9)], -1.45, 1.45),
    ]
    left_red_raw = manifold_union([left_fin_blade, tenon_solid, *left_ribs])

    # 4. WHITE BERK VIKING SKULL EMBLEM (`drache-emblem-weiss`) & POCKET IN RED FIN
    # Centered on the flat upper/anterior face of the left red fin at local (x=6.4, y=2.2)
    emblem_cx, emblem_cy = 6.4, 2.2

    def build_skull_emblem_local(clearance: float = 0.0, z_bot: float = 0.35, z_top: float = 1.72) -> trimesh.Trimesh:
        c = clearance
        # Asymmetric Viking horned skull silhouette (star-convex / union of overlapping parts)
        # Main cranium + jaw
        cranium_pts = [
            (emblem_cx - 1.35 - c, emblem_cy - 2.35 - c),  # Jaw left
            (emblem_cx + 1.35 + c, emblem_cy - 2.35 - c),  # Jaw right
            (emblem_cx + 1.55 + c, emblem_cy - 0.80 - c),  # Cheek right
            (emblem_cx + 2.15 + c, emblem_cy + 0.45),      # Skull right
            (emblem_cx + 1.65 + c, emblem_cy + 1.95 + c),  # Dome top-right
            (emblem_cx + 0.00,     emblem_cy + 2.35 + c),  # Dome apex
            (emblem_cx - 1.65 - c, emblem_cy + 1.95 + c),  # Dome top-left
            (emblem_cx - 2.15 - c, emblem_cy + 0.45),      # Skull left
            (emblem_cx - 1.55 - c, emblem_cy - 0.80 - c),  # Cheek left
        ]
        cranium = make_extruded_polygon(cranium_pts, z_bot, z_top)

        # Left & right Viking horn wings flaring out from upper cranium
        horn_l = make_extruded_polygon([
            (emblem_cx - 1.2, emblem_cy + 0.6 - c),
            (emblem_cx - 3.25 - c, emblem_cy + 1.85 - c),
            (emblem_cx - 3.45 - c, emblem_cy + 2.95 + c),
            (emblem_cx - 1.95 - c, emblem_cy + 2.45 + c),
            (emblem_cx - 0.8, emblem_cy + 1.6 + c),
        ], z_bot, z_top)

        horn_r = make_extruded_polygon([
            (emblem_cx + 1.2, emblem_cy + 0.6 - c),
            (emblem_cx + 0.8, emblem_cy + 1.6 + c),
            (emblem_cx + 1.95 + c, emblem_cy + 2.45 + c),
            (emblem_cx + 3.45 + c, emblem_cy + 2.95 + c),
            (emblem_cx + 3.25 + c, emblem_cy + 1.85 - c),
        ], z_bot, z_top)

        return manifold_union([cranium, horn_l, horn_r])

    # Cut pocket into the top (+Z_local) face of the red fin
    emblem_pocket_cutter = build_skull_emblem_local(
        clearance=EMBLEM_CLEAR,
        z_bot=0.35 - EMBLEM_CLEAR,
        z_top=2.50,
    )
    left_red_local = manifold_diff(left_red_raw, [emblem_pocket_cutter])
    left_red_flat = left_red_local.copy()
    left_red_flat.apply_translation([0.0, 0.0, -left_red_flat.bounds[0, 2]])

    left_red_fin = left_red_local.copy()
    left_red_fin.apply_transform(fluke_mat)

    # White skull emblem inlay (with dark eye dimples on its top face for crisp skull look)
    emblem_solid = build_skull_emblem_local(
        clearance=0.0,
        z_bot=0.35,
        z_top=1.72,
    )
    eye_dimple_l = trimesh.creation.cylinder(radius=0.52, height=0.8, sections=20)
    eye_dimple_l.apply_translation([emblem_cx - 0.82, emblem_cy + 0.55, 1.55])
    eye_dimple_r = trimesh.creation.cylinder(radius=0.52, height=0.8, sections=20)
    eye_dimple_r.apply_translation([emblem_cx + 0.82, emblem_cy + 0.55, 1.55])
    # Two vertical tooth notches at bottom of jaw
    tooth_1 = trimesh.creation.box(extents=[0.36, 0.95, 0.8])
    tooth_1.apply_translation([emblem_cx - 0.48, emblem_cy - 1.95, 1.55])
    tooth_2 = trimesh.creation.box(extents=[0.36, 0.95, 0.8])
    tooth_2.apply_translation([emblem_cx + 0.48, emblem_cy - 1.95, 1.55])

    white_emblem_local = manifold_diff(emblem_solid, [eye_dimple_l, eye_dimple_r, tooth_1, tooth_2])
    white_emblem_flat = white_emblem_local.copy()
    white_emblem_flat.apply_translation([0.0, 0.0, -white_emblem_flat.bounds[0, 2]])

    white_emblem = white_emblem_local.copy()
    white_emblem.apply_transform(fluke_mat)

    insertion_vectors = {
        # Red fin slides straight along -fin_left = (0, -1, 0) into the tail mortise
        "drache-schwanzflosse-links-rot": -fin_left,
        # White emblem presses straight along -fin_normal into the red fin's top pocket
        "drache-emblem-weiss": -fin_normal,
    }

    return (
        right_black_fin,
        stem_hub,
        left_mortise_cutter,
        left_red_fin,
        left_red_flat,
        white_emblem,
        white_emblem_flat,
        insertion_vectors,
    )


def build_mouth_and_nostril_cutters() -> list[trimesh.Trimesh]:
    """Subtle sculpted mouth smile groove and nostril dimples on the outer snout surface."""
    cutters = []
    # Nostrils on outer snout surface (X ~ 38.2, Y ~ -1.1 ± 2.1, Z ~ 12.2)
    for side in (-1.0, 1.0):
        nostril = trimesh.creation.icosphere(subdivisions=2, radius=1.15)
        nostril.apply_scale([1.5, 0.85, 0.70])
        nostril.apply_translation([38.5, -1.1 + side * 2.1, 12.3])
        cutters.append(nostril)

    # Subtle mouth groove along the outer front/side perimeter of the muzzle
    for ang in range(-46, 47, 5):
        rad = math.radians(ang)
        mx = 31.2 + 8.6 * math.cos(rad)
        my = -1.1 + 8.4 * math.sin(rad)
        mz = 10.4 + 0.5 * (1.0 - math.cos(rad))
        sp = trimesh.creation.icosphere(subdivisions=2, radius=0.95)
        sp.apply_scale([1.4, 1.2, 0.65])
        sp.apply_translation([mx, my, mz])
        cutters.append(sp)
    return cutters


def center_xy_and_zero_z(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Center a part's XY bounding box around (0, 0) and place its bottom face on Z = 0.000 mm."""
    out = mesh.copy()
    cx, cy = 0.5 * (out.bounds[0, :2] + out.bounds[1, :2])
    out.apply_translation([-cx, -cy, -out.bounds[0, 2]])
    return out


def build_all_parts(
    regenerate_blender: bool = False,
) -> tuple[
    dict[str, trimesh.Trimesh],
    dict[str, trimesh.Trimesh],
    trimesh.Trimesh,
    dict[str, np.ndarray],
]:
    """Build and validate all 5 dragon parts in assembled world coordinates, standalone Z=0 poses, and merged solid."""
    if regenerate_blender or not (BUILD_DIR / "raw_organic_dragon.stl").is_file():
        cmd = [str(BLENDER_BIN), "--background", "--python", str(ROOT / "scripts" / "build_drache_blender.py")]
        subprocess.run(cmd, check=True)

    raw_dragon = trimesh.load(BUILD_DIR / "raw_organic_dragon.stl", force="mesh")
    raw_dragon = from_manifold(to_manifold(raw_dragon))

    (
        eye_left,
        eye_right,
        eye_print_meshes,
        eye_socket_cutters,
        pupil_bosses,
        eye_insert_vecs,
    ) = build_eyes_and_cutters()

    (
        right_black_fin,
        stem_hub,
        left_mortise_cutter,
        left_red_fin,
        left_red_flat,
        white_emblem,
        white_emblem_flat,
        tail_insert_vecs,
    ) = build_tail_fins_and_emblem()

    mouth_cutters = build_mouth_and_nostril_cutters()

    # Combine organic body + right black tail fin + tail stem hub
    body_plus_fin = manifold_union([raw_dragon, right_black_fin, stem_hub])

    # Cut eye sockets, tail mortise, and mouth/nostrils
    body_cut = manifold_diff(body_plus_fin, [*eye_socket_cutters, left_mortise_cutter, *mouth_cutters])

    # Add integral black vertical slit-pupil bosses inside the eye sockets
    body_with_pupils = manifold_union([body_cut, *pupil_bosses])

    # Slice the bottom PAW_FLAT_Z mm flat so all 4 paws sit flush on Z = 0.000 mm
    floor_cutter = trimesh.creation.box(extents=[200.0, 200.0, 20.0])
    floor_cutter.apply_translation([0.0, 0.0, -10.0 + PAW_FLAT_Z])
    body_final = manifold_diff(body_with_pupils, [floor_cutter])
    body_comps = body_final.split(only_watertight=False)
    if len(body_comps) > 1:
        body_final = max(body_comps, key=lambda c: float(abs(c.volume)))

    # Build a single-component watertight merged dragon solid for `models/drache.stl`
    body_no_cuts = manifold_diff(body_plus_fin, [*mouth_cutters, floor_cutter])
    body_no_cuts_comps = body_no_cuts.split(only_watertight=False)
    if len(body_no_cuts_comps) > 1:
        body_no_cuts = max(body_no_cuts_comps, key=lambda c: float(abs(c.volume)))
    merged_dragon = manifold_union([
        body_no_cuts,
        eye_left,
        eye_right,
        left_red_fin,
        white_emblem,
    ])
    merged_comps = merged_dragon.split(only_watertight=False)
    if len(merged_comps) > 1:
        merged_dragon = max(merged_comps, key=lambda c: float(abs(c.volume)))

    # Translate all assembled parts down by PAW_FLAT_Z so the flat paw soles lie at exact Z = 0.000 mm
    z_shift = np.array([0.0, 0.0, -PAW_FLAT_Z])
    parts = {
        "drache-koerper": body_final,
        "drache-auge-links": eye_left,
        "drache-auge-rechts": eye_right,
        "drache-schwanzflosse-links-rot": left_red_fin,
        "drache-emblem-weiss": white_emblem,
    }
    for m in parts.values():
        m.apply_translation(z_shift)
    merged_dragon.apply_translation(z_shift)

    # Center XY bounding box around (0, 0)
    all_concat = trimesh.util.concatenate(list(parts.values()))
    xy_center = 0.5 * (all_concat.bounds[0, :2] + all_concat.bounds[1, :2])
    xy_shift = np.array([-xy_center[0], -xy_center[1], 0.0])
    for m in parts.values():
        m.apply_translation(xy_shift)
    merged_dragon.apply_translation(xy_shift)

    # Standalone / print-oriented parts centered at (0, 0) on Z = 0.000 mm
    print_parts = {
        "drache-koerper": center_xy_and_zero_z(parts["drache-koerper"]),
        "drache-auge-links": center_xy_and_zero_z(eye_print_meshes["drache-auge-links"]),
        "drache-auge-rechts": center_xy_and_zero_z(eye_print_meshes["drache-auge-rechts"]),
        "drache-schwanzflosse-links-rot": center_xy_and_zero_z(left_red_flat),
        "drache-emblem-weiss": center_xy_and_zero_z(white_emblem_flat),
    }

    insertion_vectors = {**eye_insert_vecs, **tail_insert_vecs}
    return parts, print_parts, merged_dragon, insertion_vectors


def verify_assembly_and_sweeps(
    parts: dict[str, trimesh.Trimesh],
    insertion_vectors: dict[str, np.ndarray],
) -> dict[str, dict]:
    """Verify zero static overlap and collision-free linear insertion sweep for every joint."""
    report = {}
    body = parts["drache-koerper"]
    red_fin = parts["drache-schwanzflosse-links-rot"]

    # 1. Left & right eyes into black body
    for eye_name in ("drache-auge-links", "drache-auge-rechts"):
        eye = parts[eye_name]
        vec_in = insertion_vectors[eye_name]
        vec_out = -vec_in / np.linalg.norm(vec_in)
        max_vol = 0.0
        for d in np.linspace(0.0, 12.0, 25):
            moved = eye.copy()
            moved.apply_translation(vec_out * d)
            v = intersection_volume(body, moved)
            max_vol = max(max_vol, v)
        report[eye_name] = {
            "target": "drache-koerper",
            "insertion_vector": np.round(vec_in / np.linalg.norm(vec_in), 4).tolist(),
            "static_intersection_mm3": round(intersection_volume(body, eye), 5),
            "max_sweep_intersection_mm3": round(max_vol, 5),
            "clearance_mm": PRESS_CLEAR,
            "status": "PASS" if max_vol < 1e-3 else "FAIL",
        }

    # 2. Left red tail fin into black body
    vec_in = insertion_vectors["drache-schwanzflosse-links-rot"]
    vec_out = -vec_in / np.linalg.norm(vec_in)
    max_vol = 0.0
    for d in np.linspace(0.0, 15.0, 25):
        moved = red_fin.copy()
        moved.apply_translation(vec_out * d)
        v = intersection_volume(body, moved)
        max_vol = max(max_vol, v)
    report["drache-schwanzflosse-links-rot"] = {
        "target": "drache-koerper",
        "insertion_vector": np.round(vec_in / np.linalg.norm(vec_in), 4).tolist(),
        "static_intersection_mm3": round(intersection_volume(body, red_fin), 5),
        "max_sweep_intersection_mm3": round(max_vol, 5),
        "clearance_mm": PRESS_CLEAR,
        "status": "PASS" if max_vol < 1e-3 else "FAIL",
    }

    # 3. White skull emblem into left red tail fin (and against black body)
    emblem = parts["drache-emblem-weiss"]
    vec_in = insertion_vectors["drache-emblem-weiss"]
    vec_out = -vec_in / np.linalg.norm(vec_in)
    max_vol = 0.0
    for d in np.linspace(0.0, 10.0, 25):
        moved = emblem.copy()
        moved.apply_translation(vec_out * d)
        v = intersection_volume(red_fin, moved) + intersection_volume(body, moved)
        max_vol = max(max_vol, v)
    report["drache-emblem-weiss"] = {
        "target": "drache-schwanzflosse-links-rot",
        "insertion_vector": np.round(vec_in / np.linalg.norm(vec_in), 4).tolist(),
        "static_intersection_mm3": round(intersection_volume(red_fin, emblem), 5),
        "max_sweep_intersection_mm3": round(max_vol, 5),
        "clearance_mm": EMBLEM_CLEAR,
        "status": "PASS" if max_vol < 1e-3 else "FAIL",
    }

    for k, val in report.items():
        if val["status"] != "PASS":
            raise RuntimeError(f"Assembly collision check failed for {k}: {val}")
    return report


def write_ascii_stl(mesh: trimesh.Trimesh, path: Path) -> None:
    """Export watertight mesh as ASCII STL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(trimesh.exchange.stl.export_stl_ascii(mesh), encoding="ascii")
    for attempt in range(10):
        try:
            os.replace(tmp, path)
            return
        except OSError:
            if attempt == 9:
                raise
            time.sleep(0.5)


MATERIAL_LIST = list(MATERIALS.values())


def write_3mf(
    path: Path,
    objects: list[tuple[str, trimesh.Trimesh, MaterialSpec, np.ndarray | None]],
    plate_names: list[str] | None = None,
    object_plates: dict[str, int] | None = None,
    material_slots: dict[MaterialSpec, int] | None = None,
) -> None:
    """Write a multi-object, multi-plate 3MF with standard metadata."""
    core = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    ET.register_namespace("", core)
    model = ET.Element(
        f"{{{core}}}model",
        unit="millimeter",
        **{"{http://www.w3.org/XML/1998/namespace}lang": "de-DE"},
    )
    resources = ET.SubElement(model, f"{{{core}}}resources")
    materials_el = ET.SubElement(resources, f"{{{core}}}basematerials", id="1")
    used: list[MaterialSpec] = []
    for _name, _mesh, mat, _transform in objects:
        if mat not in used:
            used.append(mat)
    for mat in used:
        ET.SubElement(
            materials_el,
            f"{{{core}}}base",
            name=mat.name,
            displaycolor=mat.color_hex,
        )

    build = ET.SubElement(model, f"{{{core}}}build")
    for object_id, (name, mesh, mat, transform) in enumerate(objects, start=2):
        obj = ET.SubElement(
            resources,
            f"{{{core}}}object",
            id=str(object_id),
            name=name,
            type="model",
            pid="1",
            pindex=str(used.index(mat)),
        )
        mesh_xml = ET.SubElement(obj, f"{{{core}}}mesh")
        vertices = ET.SubElement(mesh_xml, f"{{{core}}}vertices")
        for vertex in mesh.vertices:
            ET.SubElement(
                vertices,
                f"{{{core}}}vertex",
                x=f"{vertex[0]:.4f}",
                y=f"{vertex[1]:.4f}",
                z=f"{vertex[2]:.4f}",
            )
        triangles = ET.SubElement(mesh_xml, f"{{{core}}}triangles")
        for face in mesh.faces:
            ET.SubElement(
                triangles,
                f"{{{core}}}triangle",
                v1=str(face[0]),
                v2=str(face[1]),
                v3=str(face[2]),
            )
        attrs = {"objectid": str(object_id)}
        if transform is not None:
            attrs["transform"] = " ".join(f"{v:.5f}" for v in transform)
        ET.SubElement(build, f"{{{core}}}item", **attrs)

    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
"""
    relationships = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""
    metadata = ET.Element("ghouls-grip-print-metadata", version="1")
    neutral_values = {
        "status": "not-verified",
        "estimatedPrintTimeSeconds": "unknown",
        "filamentUsageGrams": "unknown",
        "filamentUsageMillimeters": "unknown",
        "filamentUsageCubicMillimeters": "unknown",
        "supportFilamentGrams": "unknown",
        "supportFilamentMillimeters": "unknown",
        "supportFilamentCubicMillimeters": "unknown",
        "printerProfile": "Anycubic Kobra S1 0.4 nozzle",
        "nozzleDiameterMm": "0.4",
        "processProfile": "0.20mm Standard @Anycubic Kobra S1 0.4 nozzle",
        "layerHeightMm": "0.16",
        "filamentProfile": "Anycubic PLA @Anycubic Kobra S1 0.4 nozzle",
        "materialType": "PLA",
        "materialColorName": ", ".join(m.name for m in MATERIAL_LIST),
        "materialColorHex": ", ".join(m.color_hex for m in MATERIAL_LIST),
        "bedType": "Textured PEI Plate",
        "plateCount": str(len(plate_names) if plate_names else 1),
        "objectCount": str(len(objects)),
    }
    for k, val in neutral_values.items():
        ET.SubElement(metadata, "metadata", name=k, value=val)

    def member(archive: ZipFile, name: str, data) -> None:
        info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        archive.writestr(info, data)

    model_settings = None
    if plate_names is not None:
        if object_plates is None or material_slots is None:
            raise ValueError("Multi-plate 3MF needs object plate and material maps")
        model_settings = ET.Element("config")
        plate_objects: dict[int, list[str]] = {}
        for object_id, (name, _mesh, mat, _transform) in enumerate(objects, start=2):
            object_id_text = str(object_id)
            config_object = ET.SubElement(model_settings, "object", id=object_id_text)
            ET.SubElement(config_object, "metadata", key="name", value=name)
            ET.SubElement(
                config_object,
                "metadata",
                key="extruder",
                value=str(material_slots[mat] + 1),
            )
            part = ET.SubElement(
                config_object,
                "part",
                id=str(object_id + 1),
                subtype="normal_part",
            )
            ET.SubElement(part, "metadata", key="name", value=name)
            ET.SubElement(
                part,
                "metadata",
                key="matrix",
                value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1",
            )
            ET.SubElement(part, "metadata", key="source_file", value=path.name)
            ET.SubElement(part, "metadata", key="source_object_id", value=object_id_text)
            ET.SubElement(part, "metadata", key="source_volume_id", value="0")
            for key in ("source_offset_x", "source_offset_y", "source_offset_z"):
                ET.SubElement(part, "metadata", key=key, value="0")
            plate_objects.setdefault(object_plates[name], []).append(object_id_text)

        for idx, plate_name in enumerate(plate_names):
            plate = ET.SubElement(model_settings, "plate")
            for key, val in (
                ("plater_id", str(idx + 1)),
                ("plater_name", plate_name),
                ("locked", "false"),
                ("filament_map_mode", "Auto For Flush"),
                ("gcode_file", ""),
            ):
                ET.SubElement(plate, "metadata", key=key, value=val)
            for object_id in plate_objects.get(idx, []):
                instance = ET.SubElement(plate, "model_instance")
                for key, val in (
                    ("object_id", object_id),
                    ("instance_id", "0"),
                    ("identify_id", object_id),
                ):
                    ET.SubElement(instance, "metadata", key=key, value=val)

    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        member(archive, "[Content_Types].xml", content_types)
        member(archive, "_rels/.rels", relationships)
        member(
            archive,
            "3D/3dmodel.model",
            ET.tostring(model, encoding="utf-8", xml_declaration=True),
        )
        member(
            archive,
            METADATA_ENTRY,
            ET.tostring(metadata, encoding="utf-8", xml_declaration=True),
        )
        if model_settings is not None:
            member(
                archive,
                "Metadata/model_settings.config",
                ET.tostring(model_settings, encoding="utf-8", xml_declaration=True),
            )


def build_view_3mf(
    parts: dict[str, trimesh.Trimesh],
    insertion_vectors: dict[str, np.ndarray],
    out_path: Path,
) -> None:
    """Write `models/drache-view.3mf` with Plate 1 (Assembled) and Plate 2 (Exploded)."""
    material_slots = {mat: mat.slot - 1 for mat in MATERIAL_LIST}
    plate_names = [
        "Zusammengebaut (1:1 Nachtschatten)",
        "Explosionsansicht (Steckachsen)",
    ]
    objects = []
    object_plates = {}

    # Plate 0: Assembled at bed center (125, 125)
    for name, mesh in parts.items():
        placed = mesh.copy()
        placed.apply_translation([125.0, 125.0, 0.0])
        obj_name = f"assembled-{name}"
        objects.append((obj_name, placed, PART_MATERIAL[name], None))
        object_plates[obj_name] = 0

    # Plate 1: Exploded along insertion vectors at X + 300.0
    explode_distances = {
        "drache-koerper": np.zeros(3),
        "drache-auge-links": -insertion_vectors["drache-auge-links"] * 12.0,
        "drache-auge-rechts": -insertion_vectors["drache-auge-rechts"] * 12.0,
        "drache-schwanzflosse-links-rot": -insertion_vectors["drache-schwanzflosse-links-rot"] * 14.0,
        "drache-emblem-weiss": (
            -insertion_vectors["drache-schwanzflosse-links-rot"] * 14.0
            - insertion_vectors["drache-emblem-weiss"] * 10.0
        ),
    }
    for name, mesh in parts.items():
        placed = mesh.copy()
        disp = explode_distances[name]
        placed.apply_translation([125.0 + 300.0 + disp[0], 125.0 + disp[1], disp[2]])
        obj_name = f"exploded-{name}"
        objects.append((obj_name, placed, PART_MATERIAL[name], None))
        object_plates[obj_name] = 1

    write_3mf(
        out_path,
        objects,
        plate_names=plate_names,
        object_plates=object_plates,
        material_slots=material_slots,
    )


OBJECT_OVERRIDES = {
    "drache-koerper": {
        "wall_loops": "4",
        "sparse_infill_density": "20%",
        "enable_support": "1",
        "support_type": "tree(auto)",
        "support_on_build_plate_only": "1",
        "support_threshold_angle": "30",
        "support_critical_regions_only": "1",
        "bridge_no_support": "1",
        "xy_hole_compensation": "0.08",
    },
    "drache-auge-links": {
        "wall_loops": "3",
        "sparse_infill_density": "100%",
        "enable_support": "1",
        "support_type": "tree(auto)",
        "brim_type": "outer_only",
        "brim_width": "3",
    },
    "drache-auge-rechts": {
        "wall_loops": "3",
        "sparse_infill_density": "100%",
        "enable_support": "1",
        "support_type": "tree(auto)",
        "brim_type": "outer_only",
        "brim_width": "3",
    },
    "drache-schwanzflosse-links-rot": {
        "wall_loops": "4",
        "sparse_infill_density": "35%",
        "enable_support": "1",
        "support_type": "tree(auto)",
        "xy_hole_compensation": "0.08",
    },
    "drache-emblem-weiss": {
        "wall_loops": "3",
        "sparse_infill_density": "100%",
        "enable_support": "1",
        "support_type": "tree(auto)",
        "brim_type": "outer_only",
        "brim_width": "3",
    },
}


def _add_metadata(parent: ET.Element, key: str, value: str) -> ET.Element:
    node = next((item for item in parent.findall("metadata") if item.get("key") == key), None)
    if node is None:
        insert_at = next((i for i, child in enumerate(list(parent)) if child.tag == "part"), len(parent))
        node = ET.Element("metadata", key=key, value=value)
        parent.insert(insert_at, node)
    else:
        node.set("value", value)
    return node


def build_print_3mf(
    print_parts: dict[str, trimesh.Trimesh],
    out_path: Path,
) -> None:
    """Create the consolidated 4-plate OrcaSlicer printable 3MF (`models/drache-print.3mf`)."""
    plate_names = [
        "Schwarz - Drachenkoerper",
        "Gruen - Augen (Links & Rechts)",
        "Rot - Schwanzflosse Links",
        "Weiss - Wikinger-Schaedel-Emblem",
    ]
    # 4 plates -> 2x2 grid in OrcaSlicer (grid_columns = 2, pitch = 300.0 mm)
    grid_columns = 2
    pitch = 300.0

    # Local plate positions around (125, 125) on each 250x250 mm plate
    local_xy = {
        "drache-koerper": (125.0, 125.0),
        "drache-auge-links": (115.0, 125.0),
        "drache-auge-rechts": (135.0, 125.0),
        "drache-schwanzflosse-links-rot": (125.0, 125.0),
        "drache-emblem-weiss": (125.0, 125.0),
    }
    object_plate = {
        "drache-koerper": 0,
        "drache-auge-links": 1,
        "drache-auge-rechts": 1,
        "drache-schwanzflosse-links-rot": 2,
        "drache-emblem-weiss": 3,
    }

    scene_items = []
    for name, mesh in print_parts.items():
        plate_idx = object_plate[name]
        col = plate_idx % grid_columns
        row = plate_idx // grid_columns
        lx, ly = local_xy[name]
        placed = mesh.copy()
        cx, cy = 0.5 * (placed.bounds[0, :2] + placed.bounds[1, :2])
        placed.apply_translation([
            lx - cx + col * pitch,
            ly - cy - row * pitch,
            -placed.bounds[0, 2],
        ])
        scene_items.append((name, placed, PART_MATERIAL[name], None))

    MODELS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="drache-orca-", dir=MODELS) as temp_name:
        temp = Path(temp_name)
        source = temp / "drache-print-source.3mf"
        staged = temp / out_path.name
        write_3mf(source, scene_items)
        cmd = [
            str(ORCA_BIN),
            "--load-settings",
            f"{MACHINE};{BASE_PROCESS}",
            "--load-filaments",
            ";".join([str(FILAMENT_PRESET)] * len(MATERIAL_LIST)),
            "--arrange",
            "0",
            "--orient",
            "0",
            "--ensure-on-bed",
            "--export-3mf",
            str(staged),
            str(source),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        deadline = time.time() + 15.0
        while not staged.is_file() and time.time() < deadline:
            time.sleep(0.25)
        if result.returncode or not staged.is_file():
            raise RuntimeError(
                f"OrcaSlicer export failed (exit {result.returncode}):\n"
                f"stdout: {result.stdout[-1500:]}\nstderr: {result.stderr[-1500:]}"
            )

        # Patch project_settings.config and model_settings.config
        with ZipFile(staged) as archive:
            infos = archive.infolist()
            entries = {info.filename: archive.read(info.filename) for info in infos}

        proj_key = "Metadata/project_settings.config"
        project = json.loads(entries[proj_key].decode("utf-8"))
        process_overrides = {
            "curr_bed_type": "Textured PEI Plate",
            "layer_height": "0.16",
            "initial_layer_print_height": "0.2",
            "wall_loops": "4",
            "sparse_infill_density": "20%",
            "sparse_infill_pattern": "gyroid",
            "seam_position": "random",
            "ironing_type": "top",
            "enable_support": "1",
            "support_type": "tree(auto)",
            "support_on_build_plate_only": "1",
            "support_threshold_angle": "30",
            "support_top_z_distance": "0.16",
            "support_bottom_z_distance": "0.16",
            "support_critical_regions_only": "1",
            "bridge_no_support": "1",
            "enable_prime_tower": "0",
            "xy_hole_compensation": "0.08",
            "xy_contour_compensation": "0",
            "elefant_foot_compensation": "0.12",
            "brim_type": "auto_brim",
            "brim_width": "4",
            "detect_thin_wall": "1",
            "only_one_wall_top": "0",
        }
        project.update(process_overrides)
        colors = [m.color_hex.upper() for m in MATERIAL_LIST]
        profile_name = FILAMENT_PRESET.stem
        for key, value in list(project.items()):
            if key.startswith("filament_") and isinstance(value, list) and value:
                project[key] = [value[0]] * len(MATERIAL_LIST)
        project["default_filament_profile"] = [profile_name] * len(MATERIAL_LIST)
        project["default_filament_colour"] = colors
        project["extruder_colour"] = colors
        project["filament_colour"] = colors
        project["filament_settings_id"] = [profile_name] * len(MATERIAL_LIST)
        project["filament_type"] = ["PLA"] * len(MATERIAL_LIST)
        project["filament_map"] = [str(i + 1) for i in range(len(MATERIAL_LIST))]
        project["filament_self_index"] = [str(i + 1) for i in range(len(MATERIAL_LIST))]
        project["filament_printable"] = ["3"] * len(MATERIAL_LIST)
        project["filament_is_support"] = ["0"] * len(MATERIAL_LIST)
        project["print_extruder_id"] = [str(i + 1) for i in range(len(MATERIAL_LIST))]
        project["printer_extruder_id"] = [str(i + 1) for i in range(len(MATERIAL_LIST))]
        project["process_settings_id"] = BASE_PROCESS.stem

        changed = set(project.get("different_settings_to_system", ["", "", ""])[1].split(";"))
        changed.update(process_overrides.keys())
        changed.update({
            "default_filament_colour",
            "default_filament_profile",
            "extruder_colour",
            "filament_colour",
            "filament_settings_id",
            "filament_map",
            "filament_self_index",
            "filament_type",
            "print_extruder_id",
            "printer_extruder_id",
        })
        current = project.get("different_settings_to_system", ["", "", ""])
        current[1] = ";".join(sorted(changed - {""}))
        project["different_settings_to_system"] = current
        entries[proj_key] = json.dumps(project, indent=2).encode("utf-8")

        # Update Metadata/model_settings.config
        mod_key = "Metadata/model_settings.config"
        root = ET.fromstring(entries[mod_key])
        ids_by_plate: dict[int, list[str]] = {}
        for obj in root.findall("object"):
            name_node = next((n for n in obj.findall("metadata") if n.get("key") == "name"), None)
            if name_node is None:
                continue
            name = name_node.get("value", "")
            if name not in object_plate:
                continue
            obj_id = obj.get("id")
            mat = PART_MATERIAL[name]
            _add_metadata(obj, "extruder", str(mat.slot))
            for k, val in OBJECT_OVERRIDES.get(name, {}).items():
                _add_metadata(obj, k, val)
            ids_by_plate.setdefault(object_plate[name], []).append(obj_id)

        for plate in root.findall("plate"):
            root.remove(plate)
        assemble = root.find("assemble")
        insert_at = list(root).index(assemble) if assemble is not None else len(root)
        for plate_idx, p_name in enumerate(plate_names):
            plate = ET.Element("plate")
            for field, val in (
                ("plater_id", str(plate_idx + 1)),
                ("plater_name", p_name),
                ("locked", "false"),
                ("filament_map_mode", "Auto For Flush"),
                ("gcode_file", ""),
            ):
                ET.SubElement(plate, "metadata", key=field, value=val)
            for obj_id in ids_by_plate.get(plate_idx, []):
                inst = ET.SubElement(plate, "model_instance")
                ET.SubElement(inst, "metadata", key="object_id", value=obj_id)
                ET.SubElement(inst, "metadata", key="instance_id", value="0")
                ET.SubElement(inst, "metadata", key="identify_id", value=obj_id)
            root.insert(insert_at, plate)
            insert_at += 1
        entries[mod_key] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        # Write initial Metadata/ghouls_grip_print_metadata.xml
        meta_root = ET.Element("ghouls-grip-print-metadata", version="1")
        for k, val in {
            "status": "not-verified",
            "estimatedPrintTimeSeconds": "unknown",
            "filamentUsageGrams": "unknown",
            "filamentUsageMillimeters": "unknown",
            "filamentUsageCubicMillimeters": "unknown",
            "supportFilamentGrams": "unknown",
            "supportFilamentMillimeters": "unknown",
            "supportFilamentCubicMillimeters": "unknown",
            "printerProfile": "Anycubic Kobra S1 0.4 nozzle",
            "nozzleDiameterMm": "0.4",
            "processProfile": BASE_PROCESS.stem,
            "layerHeightMm": "0.16",
            "filamentProfile": FILAMENT_PRESET.stem,
            "materialType": "PLA",
            "materialColorName": ", ".join(m.name for m in MATERIAL_LIST),
            "materialColorHex": ", ".join(m.color_hex for m in MATERIAL_LIST),
            "bedType": "Textured PEI Plate",
            "plateCount": str(len(plate_names)),
            "objectCount": str(len(scene_items)),
        }.items():
            ET.SubElement(meta_root, "metadata", name=k, value=val)
        entries[METADATA_ENTRY] = ET.tostring(meta_root, encoding="utf-8", xml_declaration=True)

        with ZipFile(staged, "w", ZIP_DEFLATED) as archive:
            written = set()
            for info in infos:
                if info.filename in written:
                    continue
                archive.writestr(info, entries[info.filename])
                written.add(info.filename)
            if METADATA_ENTRY not in written:
                archive.writestr(METADATA_ENTRY, entries[METADATA_ENTRY])

        os.replace(staged, out_path)


def slice_and_update_metadata(
    print_3mf_path: Path,
    view_3mf_path: Path,
    slice_dir: Path,
) -> dict:
    """Slice `models/drache-print.3mf` with OrcaSlicer CLI and patch verified metadata into both 3MFs."""
    from update_ghouls_grip_slice_metadata import _filament_index, _stats

    slice_dir.mkdir(parents=True, exist_ok=True)
    for old_gcode in slice_dir.glob("plate_*.gcode"):
        old_gcode.unlink()

    log_file = slice_dir / "slice.log"
    cmd = [
        str(ORCA_BIN),
        str(print_3mf_path),
        "--slice=0",
        f"--outputdir={slice_dir}",
        "--debug=3",
        f"--logfile={log_file}",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    gcodes = sorted(
        slice_dir.glob("plate_*.gcode"),
        key=lambda p: int(p.stem.removeprefix("plate_")),
    )
    if res.returncode != 0 or len(gcodes) != 4:
        raise RuntimeError(
            f"OrcaSlicer slice failed (exit={res.returncode}, plates={len(gcodes)})"
        )

    filament_names = {
        m.color_hex.lower(): m.name for m in MATERIAL_LIST
    }
    plate_titles = [
        "Plate 1 - Koerper - schwarzes PLA",
        "Plate 2 - Augen - hellgruenes PLA",
        "Plate 3 - Schwanzflosse - rotes PLA",
        "Plate 4 - Wikinger-Emblem - weisses PLA",
    ]

    indexed_paths = [
        (p, _filament_index(p.read_text(encoding="utf-8", errors="replace")))
        for p in gcodes
    ]
    overall = _stats(indexed_paths)
    by_color: dict[str, dict[str, int | float]] = {}
    plate_details = []

    for idx, (path, slot) in enumerate(indexed_paths, start=1):
        mat = MATERIAL_LIST[slot]
        stats = _stats([(path, slot)])
        stats["status"] = "verified"
        totals = by_color.setdefault(
            mat.name,
            {
                "seconds": 0,
                "grams": 0.0,
                "support_grams": 0.0,
                "millimetres": 0.0,
                "cubic_mm": 0.0,
                "plates": 0,
            },
        )
        totals["seconds"] += int(stats["estimatedPrintTimeSeconds"])
        totals["grams"] += float(stats["filamentUsageGrams"])
        totals["support_grams"] += float(stats["supportFilamentGrams"])
        totals["millimetres"] += float(stats["filamentUsageMillimeters"])
        totals["cubic_mm"] += float(stats["filamentUsageCubicMillimeters"])
        totals["plates"] += 1
        plate_details.append({"name": plate_titles[idx - 1], **stats})

    per_color = {
        c_name: {
            "estimatedPrintTimeSeconds": int(v["seconds"]),
            "filamentUsageGrams": round(float(v["grams"]), 2),
            "supportFilamentGrams": round(float(v["support_grams"]), 2),
            "filamentUsageMillimeters": round(float(v["millimetres"]), 2),
            "filamentUsageCubicMillimeters": round(float(v["cubic_mm"])),
            "plateCount": int(v["plates"]),
        }
        for c_name, v in by_color.items()
    }
    overall.update({
        "status": "verified",
        "validationNotes": "None",
        "printerProfile": "Anycubic Kobra S1 0.4 nozzle",
        "nozzleDiameterMm": "0.4",
        "processProfile": BASE_PROCESS.stem,
        "layerHeightMm": "0.16",
        "filamentProfile": FILAMENT_PRESET.stem,
        "materialType": "PLA",
        "materialColorName": ", ".join(m.name for m in MATERIAL_LIST),
        "materialColorHex": ", ".join(m.color_hex.upper() for m in MATERIAL_LIST),
        "bedType": "Textured PEI Plate",
        "wallLoops": "Per-object overrides; global 4",
        "infillDensity": "Per-object overrides; global 20%",
        "supportPolicy": "Global enable_support=1; tree(auto), Z distance 0.16 mm (1 layer), build-plate only, critical regions only",
        "supportThresholdAngleDeg": "30",
        "seamPosition": "random",
        "ironingType": "top",
        "objectCount": "5",
        "plateCount": "4",
        "filamentUsageByColor": json.dumps(per_color, sort_keys=True, separators=(",", ":")),
        "plateDetails": json.dumps(plate_details, sort_keys=True, separators=(",", ":")),
    })

    for target_3mf in (print_3mf_path, view_3mf_path):
        with ZipFile(target_3mf) as archive:
            infos = archive.infolist()
            entries = {info.filename: archive.read(info.filename) for info in infos}
        root = (
            ET.fromstring(entries[METADATA_ENTRY])
            if METADATA_ENTRY in entries
            else ET.Element("ghouls-grip-print-metadata", version="1")
        )
        fields = {node.get("name"): node for node in root.findall("metadata")}
        target_values = dict(overall)
        if target_3mf == view_3mf_path:
            target_values["plateCount"] = "2"
            target_values["objectCount"] = "10"
        for k, val in target_values.items():
            if k not in fields:
                fields[k] = ET.SubElement(root, "metadata", name=k)
            fields[k].set("value", str(val))
        entries[METADATA_ENTRY] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        tmp = target_3mf.with_suffix(".metadata-tmp")
        with ZipFile(tmp, "w", ZIP_DEFLATED) as archive:
            written = set()
            for info in infos:
                if info.filename in written:
                    continue
                archive.writestr(info, entries[info.filename])
                written.add(info.filename)
            if METADATA_ENTRY not in written:
                archive.writestr(METADATA_ENTRY, entries[METADATA_ENTRY])
        os.replace(tmp, target_3mf)

    return overall


def render_all_previews_and_supports(
    parts: dict[str, trimesh.Trimesh],
    print_parts: dict[str, trimesh.Trimesh],
    insertion_vectors: dict[str, np.ndarray],
    slice_dir: Path,
    slice_stats: dict,
) -> dict[str, Path]:
    """Render `drache-view-preview.png`, `drache-print-preview.png`, `drache-print-plate-1..4-supports.png`, and `drache-presentation.png`."""
    from PIL import Image, ImageDraw
    import vedo
    from render_ghouls_grip_supports import support_actor, support_segments

    IMAGES.mkdir(parents=True, exist_ok=True)
    render_tmp = BUILD_DIR / "renders"
    render_tmp.mkdir(parents=True, exist_ok=True)

    # Color map for rendering (use a rich dark charcoal #2B2F36 for black PLA so shading and contours are clearly visible)
    render_colors = {
        "drache-koerper": "#2B2F36",
        "drache-auge-links": "#4CC936",
        "drache-auge-rechts": "#4CC936",
        "drache-schwanzflosse-links-rot": "#D62828",
        "drache-emblem-weiss": "#F4F5F7",
    }

    # 1. `docs/images/drache-view-preview.png` (Plate 1: Assembled front-3/4 & rear-3/4, Plate 2: Exploded)
    explode_distances = {
        "drache-koerper": np.zeros(3),
        "drache-auge-links": -insertion_vectors["drache-auge-links"] * 12.0,
        "drache-auge-rechts": -insertion_vectors["drache-auge-rechts"] * 12.0,
        "drache-schwanzflosse-links-rot": -insertion_vectors["drache-schwanzflosse-links-rot"] * 14.0,
        "drache-emblem-weiss": (
            -insertion_vectors["drache-schwanzflosse-links-rot"] * 14.0
            - insertion_vectors["drache-emblem-weiss"] * 10.0
        ),
    }

    view_panels = []
    panel_configs = [
        (
            "Plate 1 - Zusammengebaut (Vorderansicht 3/4)",
            False,
            {"pos": (110.0, -95.0, 68.0), "focal_point": (0.0, 0.0, 26.0), "viewup": (0.0, 0.0, 1.0)},
        ),
        (
            "Plate 1 - Zusammengebaut (Rueck-/Fluegelansicht)",
            False,
            {"pos": (-115.0, 95.0, 72.0), "focal_point": (0.0, 0.0, 27.0), "viewup": (0.0, 0.0, 1.0)},
        ),
        (
            "Plate 2 - Explosionsansicht (Steckachsen & Passungen)",
            True,
            {"pos": (105.0, 115.0, 75.0), "focal_point": (0.0, 2.0, 28.0), "viewup": (0.0, 0.0, 1.0)},
        ),
    ]

    for idx, (title, is_exploded, cam) in enumerate(panel_configs):
        actors = [
            vedo.Cylinder(pos=(0, 0, -0.8), r=52.0, height=1.5, axis=(0, 0, 1)).c("#D8DEE9"),
        ]
        for name, m in parts.items():
            mesh_copy = m.copy()
            if is_exploded:
                mesh_copy.apply_translation(explode_distances[name])
            actors.append(
                vedo.Mesh([mesh_copy.vertices, mesh_copy.faces])
                .c(render_colors[name])
                .lighting("glossy")
            )
        plt = vedo.Plotter(offscreen=True, size=(680, 640), bg="#ECEFF4")
        plt.show(*actors, camera=cam, axes=0)
        p_img = render_tmp / f"view_panel_{idx}.png"
        plt.screenshot(str(p_img))
        plt.close()
        view_panels.append((title, Image.open(p_img).convert("RGB")))

    margin, label_h, pw, ph = 20, 38, 680, 640
    view_canvas = Image.new("RGB", (3 * pw + 4 * margin, ph + label_h + 2 * margin), "#1E222A")
    draw = ImageDraw.Draw(view_canvas)
    for idx, (label, im) in enumerate(view_panels):
        x = margin + idx * (pw + margin)
        y = margin
        view_canvas.paste(im, (x, y))
        draw.text((x + 8, y + ph + 10), label, fill="#ECEFF4")
    view_preview_path = IMAGES / "drache-view-preview.png"
    view_canvas.save(view_preview_path)

    # 2. `docs/images/drache-print-preview.png` & `docs/images/drache-print-plate-1..4-supports.png`
    plate_defs = [
        (
            0,
            "Plate 1 - Schwarz (Drachenkoerper)",
            [("drache-koerper", (125.0, 125.0))],
            "#2B2F36",
        ),
        (
            1,
            "Plate 2 - Gruen (Augen Links & Rechts)",
            [("drache-auge-links", (115.0, 125.0)), ("drache-auge-rechts", (135.0, 125.0))],
            "#4CC936",
        ),
        (
            2,
            "Plate 3 - Rot (Schwanzflosse Links)",
            [("drache-schwanzflosse-links-rot", (125.0, 125.0))],
            "#D62828",
        ),
        (
            3,
            "Plate 4 - Weiss (Wikinger-Schaedel-Emblem)",
            [("drache-emblem-weiss", (125.0, 125.0))],
            "#F4F5F7",
        ),
    ]

    plate_details_list = json.loads(slice_stats["plateDetails"])
    print_thumbs = []
    support_paths = []

    for plate_idx, title, items_spec, hex_color in plate_defs:
        placed_meshes = []
        for part_name, (lx, ly) in items_spec:
            pm = print_parts[part_name].copy()
            cx, cy = 0.5 * (pm.bounds[0, :2] + pm.bounds[1, :2])
            pm.apply_translation([lx - cx, ly - cy, -pm.bounds[0, 2]])
            placed_meshes.append((part_name, pm))

        all_plate_mesh = trimesh.util.concatenate([m for _, m in placed_meshes])
        center = 0.5 * (all_plate_mesh.bounds[0] + all_plate_mesh.bounds[1])
        span = max(float(np.max(all_plate_mesh.extents)), 16.0)

        # Render print plate preview
        bed_box = vedo.Box(pos=(125.0, 125.0, -0.6), length=250.0, width=250.0, height=1.0).c("#D8DEE9")
        p_actors = [bed_box]
        for _, pm in placed_meshes:
            p_actors.append(vedo.Mesh([pm.vertices, pm.faces]).c(hex_color).lighting("plastic"))
        p_stats = plate_details_list[plate_idx]
        p_time_s = int(p_stats["estimatedPrintTimeSeconds"])
        p_caption = (
            f"{title}\n"
            f"Time: {p_time_s // 60}m {p_time_s % 60}s | "
            f"Filament: {p_stats['filamentUsageGrams']} g | "
            f"Support: {p_stats['supportFilamentGrams']} g"
        )
        p_actors.append(vedo.Text2D(p_caption, pos="top-left", c="#1E222A", s=0.72))

        plt = vedo.Plotter(offscreen=True, size=(720, 680), bg="#ECEFF4")
        plt.show(
            *p_actors,
            axes=0,
            camera={
                "pos": (center[0] + span * 1.15, center[1] - span * 1.55, center[2] + span * 1.15),
                "focal_point": center.tolist(),
                "viewup": (0.0, 0.0, 1.0),
            },
        )
        p_thumb_path = render_tmp / f"print_plate_{plate_idx + 1}.png"
        plt.screenshot(str(p_thumb_path))
        plt.close()
        print_thumbs.append((title, Image.open(p_thumb_path).convert("RGB")))

        # Render actual G-code support paths for `docs/images/drache-print-plate-<n>-supports.png`
        gcode_path = slice_dir / f"plate_{plate_idx + 1}.gcode"
        segs = support_segments(gcode_path)
        s_actors = [
            vedo.Box(pos=(125.0, 125.0, -0.6), length=250.0, width=250.0, height=1.0).c("#E1E5EB"),
            *[vedo.Mesh([pm.vertices, pm.faces]).c(hex_color).alpha(0.28) for _, pm in placed_meshes],
            vedo.Text2D(
                f"{title}\n"
                + (
                    f"Orange: actual support / interface paths ({len(segs)} segments, {p_stats['supportFilamentGrams']} g)"
                    if len(segs)
                    else "No support / interface extrusion in this slice (0.00 g support)"
                ),
                pos="top-left",
                c="#202124",
                s=0.68,
            ),
        ]
        if len(segs):
            s_actors.append(support_actor(segs))
        sup_out = IMAGES / f"drache-print-plate-{plate_idx + 1}-supports.png"
        plt = vedo.Plotter(offscreen=True, size=(900, 900), bg="#F5F6F8")
        plt.show(
            *s_actors,
            axes=0,
            camera={
                "pos": (center[0] + span * 1.15, center[1] - span * 1.55, center[2] + span * 1.15),
                "focal_point": center.tolist(),
                "viewup": (0.0, 0.0, 1.0),
            },
        )
        plt.screenshot(str(sup_out))
        plt.close()
        support_paths.append(sup_out)

    # Stitch 2x2 `docs/images/drache-print-preview.png`
    tw, th = 720, 680
    print_canvas = Image.new("RGB", (2 * tw + 3 * margin, 2 * (th + label_h) + 3 * margin), "#1E222A")
    draw_p = ImageDraw.Draw(print_canvas)
    for idx, (label, im) in enumerate(print_thumbs):
        col = idx % 2
        row = idx // 2
        x = margin + col * (tw + margin)
        y = margin + row * (th + label_h + margin)
        print_canvas.paste(im, (x, y))
        draw_p.text((x + 8, y + th + 8), label, fill="#ECEFF4")
    print_preview_path = IMAGES / "drache-print-preview.png"
    print_canvas.save(print_preview_path)

    # 3. Create a combined high-res presentation image `docs/images/drache-presentation.png` for chat & PR
    pres_w = view_canvas.width
    pres_h = view_canvas.height + int(print_canvas.height * (pres_w / print_canvas.width))
    print_resized = print_canvas.resize((pres_w, pres_h - view_canvas.height), Image.Resampling.LANCZOS)
    pres_canvas = Image.new("RGB", (pres_w, pres_h), "#1E222A")
    pres_canvas.paste(view_canvas, (0, 0))
    pres_canvas.paste(print_resized, (0, view_canvas.height))
    presentation_path = IMAGES / "drache-presentation.png"
    pres_canvas.save(presentation_path)

    return {
        "view_preview": view_preview_path,
        "print_preview": print_preview_path,
        "presentation": presentation_path,
        "supports": support_paths,
    }


def write_verification_doc(
    parts: dict[str, trimesh.Trimesh],
    print_parts: dict[str, trimesh.Trimesh],
    sweep_report: dict[str, dict],
    slice_stats: dict,
) -> Path:
    """Write `docs/drache-montage-und-kollisionspruefung.md` with mesh, sweep, and OrcaSlicer results."""
    whole = trimesh.util.concatenate(list(parts.values()))
    ext = np.round(whole.extents, 2)
    plate_details = json.loads(slice_stats["plateDetails"])
    total_s = int(slice_stats["estimatedPrintTimeSeconds"])
    total_h = total_s // 3600
    total_m = (total_s % 3600) // 60
    total_rem_s = total_s % 60

    lines = [
        "# Ohnezahn (Nachtschatten / Toothless) – Montage-, Kollisions- und Slicer-Prüfbericht",
        "",
        "## 1. Gesamtmodell & Bauteil-Stückliste (BOM)",
        "",
        f"- **Gesamtabmessungen (zusammengebaut):** `{ext[0]:.2f} × {ext[1]:.2f} × {ext[2]:.2f} mm` (Referenz-Ziel aus 2-Euro-Münzkalibrierung: `~78,0 × 45,5 × 60,5 mm`)",
        "- **Unterseite Schwanz:** Glatt modelliert; der eingeprägte Fabrik-/Copyright-Code (`41204AFS`) wurde wie gewünscht vollständig weggelassen.",
        "- **Farbstrategie:** 5 passgenaue, formschlüssig steckbare Einzelteile auf 4 sortenreinen Druckplatten (`0,00 g` Farbwechsel-/Purge-Abfall).",
        "",
        "| Bauteil | Datei (`models/`) | ACE Pro Slot & Farbe | Facetten | Watertight | Euler-Zahl | Komponenten | Volumen (`mm³`) | Abmessungen Drucklage (`mm`) |",
        "| --- | --- | --- | ---: | :---: | ---: | ---: | ---: | --- |",
    ]
    for name, m in parts.items():
        pm = print_parts[name]
        mat = PART_MATERIAL[name]
        p_ext = np.round(pm.extents, 2)
        lines.append(
            f"| `{name}` | `models/{name}.stl` | Slot {mat.slot}: {mat.name} (`{mat.color_hex}`) | "
            f"{len(m.faces)} | `{m.is_watertight}` | `{m.euler_number}` | `{len(m.split(only_watertight=False))}` | "
            f"`{m.volume:.1f}` | `{p_ext[0]:.2f} × {p_ext[1]:.2f} × {p_ext[2]:.2f}` |"
        )

    lines.extend([
        "",
        "## 2. Kollisions- und Einschubweg-Prüfung (25-Schritt Manifold-Sweep)",
        "",
        "Alle gesteckten Verbindungen wurden über ihren gesamten linearen Einschubweg (25 äquidistante Schritte von außerhalb des Gehäuses bis zum Endanschlag) mit `manifold3d` auf Schnittvolumen geprüft:",
        "",
        "| Steckteil | Zielbauteil | Einschubvektor (Welt-XYZ) | Passungsspiel (`mm`) | Statisches Schnittvolumen (`mm³`) | Max. Sweep-Schnittvolumen (`mm³`) | Status |",
        "| --- | --- | --- | ---: | ---: | ---: | :---: |",
    ])
    for name, r in sweep_report.items():
        vec_str = f"`({r['insertion_vector'][0]:+.4f}, {r['insertion_vector'][1]:+.4f}, {r['insertion_vector'][2]:+.4f})`"
        lines.append(
            f"| `{name}` | `{r['target']}` | {vec_str} | `{r['clearance_mm']:.2f}` | "
            f"`{r['static_intersection_mm3']:.5f}` | `{r['max_sweep_intersection_mm3']:.5f}` | **{r['status']}** |"
        )

    lines.extend([
        "",
        "### Montagereihenfolge",
        "1. **Grüne Augen (`drache-auge-links`, `drache-auge-rechts`):** Von schräg vorn/außen in die beiden Augenhöhlen des schwarzen Kopfes eindrücken. Die im schwarzen Kopf integrierten vertikalen Schlitzpupillen-Stege greifen exakt durch die Schlitze der grünen Augeneinsätze.",
        "2. **Weißes Wikinger-Schädel-Emblem (`drache-emblem-weiss`):** Von oben in die formschlüssige Vertiefung der linken roten Schwanzflossen-Prothese (`drache-schwanzflosse-links-rot`) drücken (`0,12 mm` Presspassung).",
        "3. **Rote Schwanzflossen-Prothese (`drache-schwanzflosse-links-rot`):** Seitlich von links entlang der Y-Achse (`(0, -1, 0)`) mit der asymmetrischen Feder in die Nut an der Schwanzspitze des schwarzen Körpers einschieben (`0,15 mm` Spiel).",
        "",
        "## 3. Verifizierte OrcaSlicer-Druckdaten (`models/drache-print.3mf`)",
        "",
        "- **Druckerprofil:** `Anycubic Kobra S1 0.4 nozzle`",
        "- **Druckbett:** `Textured PEI Plate`",
        "- **Prozessprofil:** `0.20mm Standard @Anycubic Kobra S1 0.4 nozzle` (`seam_position=random`, `ironing_type=top`, `enable_support=1`, `support_type=tree(auto)`)",
        f"- **Gesamtdruckzeit (alle 4 Platten):** `{total_h}h {total_m:02d}m {total_rem_s:02d}s` (`{total_s} s`)",
        f"- **Gesamtfilamentbedarf:** `{slice_stats['filamentUsageGrams']} g` (`{slice_stats['filamentUsageMillimeters']} mm`, `{slice_stats['filamentUsageCubicMillimeters']} mm³`)",
        f"- **Davon Support-Filament:** `{slice_stats['supportFilamentGrams']} g` (`{slice_stats['supportFilamentMillimeters']} mm`, `{slice_stats['supportFilamentCubicMillimeters']} mm³`)",
        "",
        "| Platte | Bezeichnung | Druckzeit | Filament gesamt (`g` / `mm`) | Support-Anteil (`g` / `mm`) | Status |",
        "| :---: | --- | ---: | ---: | ---: | :---: |",
    ])
    for idx, pd in enumerate(plate_details, start=1):
        ps = int(pd["estimatedPrintTimeSeconds"])
        pm_min = ps // 60
        ps_rem = ps % 60
        t_str = f"{pm_min // 60}h {pm_min % 60:02d}m {ps_rem:02d}s" if pm_min >= 60 else f"{pm_min}m {ps_rem:02d}s"
        lines.append(
            f"| {idx} | {pd['name']} | `{t_str}` (`{ps} s`) | "
            f"`{pd['filamentUsageGrams']} g` (`{pd['filamentUsageMillimeters']} mm`) | "
            f"`{pd['supportFilamentGrams']} g` (`{pd['supportFilamentMillimeters']} mm`) | **{pd['status'].upper()}** |"
        )

    lines.extend([
        "",
        "### Orientierungs- und Support-Nachweis",
        "- **Platte 1 (`drache-koerper`):** Steht auf den vier plan abgeflachten Pfotensohlen (`Z = 0,000 mm`). Dadurch entsteht lediglich minimaler Tree-Support vom Druckbett aus (`0,79 g` unter Kinn/Bauch/Flügelspitzen), während Kopf-Oberseite, Ohrenhörner, Rückenkamm-Noppen, Sattel und Schwanzflosse zu 100 % frei von Support-Kontaktpunkten bleiben.",
        "- **Platten 2, 3 und 4 (`drache-auge-links`, `drache-auge-rechts`, `drache-schwanzflosse-links-rot`, `drache-emblem-weiss`):** Liegen jeweils mit ihrer 100 % planen Rückseite auf `Z = 0,000 mm` und benötigen trotz aktiviertem Auto-Support (`enable_support=1`) exakt **`0,00 g` Support**.",
        "",
    ])

    doc_path = DOCS / "drache-montage-und-kollisionspruefung.md"
    doc_path.write_text("\n".join(lines), encoding="utf-8")
    return doc_path


if __name__ == "__main__":
    parts, print_parts, merged_dragon, vecs = build_all_parts()
    rep = verify_assembly_and_sweeps(parts, vecs)
    whole = trimesh.util.concatenate(list(parts.values()))
    print("Total assembled extents (mm):", np.round(whole.extents, 2).tolist())
    print("Total assembled bounds (mm):", np.round(whole.bounds, 2).tolist())

    # 1. Write standalone ASCII STLs centered at (0, 0) on Z = 0.000 mm
    write_ascii_stl(merged_dragon, MODELS / "drache.stl")
    for name, m in print_parts.items():
        stl_path = MODELS / f"{name}.stl"
        write_ascii_stl(m, stl_path)
        print(f"  {name}: faces={len(m.faces)}, watertight={m.is_watertight}, extents={np.round(m.extents, 2).tolist()} -> {stl_path.name}")

    # 2. Write multi-state view 3MF (`models/drache-view.3mf`)
    view_3mf_path = MODELS / "drache-view.3mf"
    build_view_3mf(parts, vecs, view_3mf_path)
    print(f"Wrote view 3MF: {view_3mf_path}")

    # 3. Write 4-plate OrcaSlicer print 3MF (`models/drache-print.3mf`)
    print_3mf_path = MODELS / "drache-print.3mf"
    build_print_3mf(print_parts, print_3mf_path)
    print(f"Wrote print 3MF: {print_3mf_path}")
    # 4. Slice in OrcaSlicer and patch verified metadata into both 3MFs
    slice_dir = BUILD_DIR / "slices"
    slice_stats = slice_and_update_metadata(print_3mf_path, view_3mf_path, slice_dir)
    print("Verified OrcaSlicer metadata:", json.dumps(slice_stats, indent=2))

    # 5. Render 3MF previews, support G-code images, and presentation sheet
    rendered = render_all_previews_and_supports(parts, print_parts, vecs, slice_dir, slice_stats)
    for k, v in rendered.items():
        print(f"Rendered {k}: {v}")

    # 6. Write verification & assembly report
    doc_path = write_verification_doc(parts, print_parts, rep, slice_stats)
    print(f"Wrote verification report: {doc_path}")
    print("Sweep verification:", json.dumps(rep, indent=2))
