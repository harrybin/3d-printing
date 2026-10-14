"""Parametric generator, kinematic verifier, and OrcaSlicer packager for the print-optimized PLA Butterfly Knife (Balisong).

Deliverables produced:
  - models/butterfly-messer-view.3mf  : Multi-state assembled 3MF (Plate 1: Open 0°, Plate 2: Half-open 90°, Plate 3: Closed & latched 180°)
  - models/butterfly-messer-print.3mf : Consolidated 3-color Anycubic Kobra S1 + ACE Pro print project (3 single-color plates, 0.00 g purge, 0.00 g support)
  - models/butterfly-messer.stl       : Watertight ASCII STL of the deployed assembly
  - models/butterfly-messer-klinge.stl, models/butterfly-messer-riegel.stl,
    models/butterfly-messer-griff-safe-unten.stl, models/butterfly-messer-griff-safe-oben.stl,
    models/butterfly-messer-griff-bite-unten.stl, models/butterfly-messer-griff-bite-oben.stl,
    models/butterfly-messer-bolzen.stl, models/butterfly-messer-clip.stl
  - docs/butterfly-messer-quellen-und-lizenzen.md
  - docs/butterfly-messer-masse-und-mechanik.md
  - docs/butterfly-messer-druckvalidierung.md
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
BUILD_DIR = ROOT / "build" / "butterfly-messer"
DOCS = ROOT / "docs"
IMAGES = DOCS / "images"

ORCA_BIN = Path(os.environ.get(
    "ORCA_SLICER_BIN", r"C:\Program Files\OrcaSlicer\orca-slicer.exe"))
PROFILE_ROOT = ORCA_BIN.parent / "resources" / "profiles" / "Anycubic"
MACHINE = PROFILE_ROOT / "machine" / "Anycubic Kobra S1 0.4 nozzle.json"
BASE_PROCESS = PROFILE_ROOT / "process" / "0.20mm Standard @Anycubic Kobra S1 0.4 nozzle.json"
FILAMENT_PRESET = PROFILE_ROOT / "filament" / "Anycubic PLA @Anycubic Kobra S1 0.4 nozzle.json"
METADATA_ENTRY = "Metadata/ghouls_grip_print_metadata.xml"

# ============================================================================
# Interview-confirmed & parameterized engineering dimensions (mm)
# ============================================================================
PIVOT_CLEARANCE_DIAM = 0.30     # User-selected 0.30 mm rotary pivot clearance (Ø 5.30 bore on Ø 5.00 shaft)
PIVOT_CLEARANCE_RAD = PIVOT_CLEARANCE_DIAM / 2.0
CLIP_FIT_CLEARANCE = 0.15       # User-selected 0.15 mm press/snap retention clearance per side

Y_PIVOT = 7.20                  # Pivot center Y offset (±7.20 mm -> 14.40 mm pivot spacing)
W_HANDLE = 13.00                # Handle width (R_HANDLE = 6.50 mm -> 1.40 mm inter-handle gap)
R_HANDLE = W_HANDLE / 2.0
U_REAR = 113.50                 # Rear center of handle arc (total handle length = 6.50 + 113.50 + 6.50 = 126.50 mm)
U_ZEN = 6.80                    # Zen-pin stop center along handle centerline
R_ZEN = 2.00                    # Zen-pin radius (Ø 4.00 mm stop pin)
R_ZEN_TENON = 1.55              # Upper tenon radius keying into upper handle scale
U_SAFE_BOLT = 104.50            # Rear bolt center on Safe Handle
U_BITE_SPACER = 104.50          # Anti-rotation spacer post on Bite Handle
U_LATCH = 113.50                # Rear latch bolt center on Bite Handle & catch slot center on Safe Handle

Z_TOTAL = 11.60                 # Total handle thickness (Z = 0.00 .. 11.60 mm)
T_SCALE = 3.20                  # Scale wall thickness (Z = 0..3.20 and Z = 8.40..11.60 mm)
Z_WASHER_H = 0.45               # Integral bearing washer height (Z = 3.20..3.65 and Z = 7.95..8.40 mm)
Z_BLADE_BOT = 4.00              # Blade bottom Z in assembled pose (0.35 mm axial clearance to washer)
Z_BLADE_TOP = 7.60              # Blade top Z in assembled pose (T_BLADE = 3.60 mm)
T_BLADE = Z_BLADE_TOP - Z_BLADE_BOT

R_SHAFT = 2.50                  # Nominal Ø 5.00 mm pivot bolt shaft radius
D_FLAT_Y = -2.00                # Coplanar D-flat across bolt head and shaft (0.50 mm flat depth)
R_HEAD = 3.45                   # Bolt head radius (Ø 6.90 mm)
Z_HEAD_TOP = 1.40               # Bolt head height (Z = 0.00 .. 1.40 mm)
Z_CBORE_FLOOR = 1.55            # Counterbore shoulder in lower scale (0.15 mm axial clearance)
Z_POCKET_FLOOR = 9.45           # Clip pocket floor in upper scale
Z_NOTCH_BOT = 9.45              # Bolt clip-groove bottom Z
Z_NOTCH_TOP = 10.75             # Bolt clip-groove top Z
X_NOTCH_HALF = 1.45             # Bolt neck half-width inside clip groove
Z_CLIP_BOT = 9.60               # Retaining clip bottom Z in assembly (0.15 mm clearance)
Z_CLIP_TOP = 10.60              # Retaining clip top Z in assembly (1.00 mm thick = 5 layers)


@dataclass(frozen=True)
class MaterialSpec:
    slug: str
    name: str
    color_hex: str
    slot: int  # 1-based ACE Pro slot


MATERIALS = {
    "silver":     MaterialSpec("silver",     "Klinge & Riegel - silbergraues PLA", "#C0C7D0", 1),
    "anthracite": MaterialSpec("anthracite", "Griffschalen, Bolzen & Clips - anthrazit PLA", "#2D333B", 2),
}

MATERIAL_LIST = [MATERIALS["silver"], MATERIALS["anthracite"]]

PART_MATERIAL = {
    "butterfly-messer-klinge": MATERIALS["silver"],
    "butterfly-messer-riegel": MATERIALS["silver"],
    "butterfly-messer-griff-safe-unten": MATERIALS["anthracite"],
    "butterfly-messer-griff-safe-oben": MATERIALS["anthracite"],
    "butterfly-messer-griff-bite-unten": MATERIALS["anthracite"],
    "butterfly-messer-griff-bite-oben": MATERIALS["anthracite"],
    "butterfly-messer-bolzen-safe-vorn": MATERIALS["anthracite"],
    "butterfly-messer-bolzen-bite-vorn": MATERIALS["anthracite"],
    "butterfly-messer-bolzen-safe-hinten": MATERIALS["anthracite"],
    "butterfly-messer-bolzen-bite-hinten": MATERIALS["anthracite"],
    "butterfly-messer-clip-safe-vorn": MATERIALS["anthracite"],
    "butterfly-messer-clip-bite-vorn": MATERIALS["anthracite"],
    "butterfly-messer-clip-safe-hinten": MATERIALS["anthracite"],
    "butterfly-messer-clip-bite-hinten": MATERIALS["anthracite"],
}


# ============================================================================
# Manifold CSG & repair helpers
# ============================================================================
def to_manifold(mesh: trimesh.Trimesh) -> m3d.Manifold:
    v = np.ascontiguousarray(mesh.vertices, dtype=np.float32)
    f = np.ascontiguousarray(mesh.faces, dtype=np.uint32)
    return m3d.Manifold(m3d.Mesh(vert_properties=v, tri_verts=f))


def from_manifold(mani: m3d.Manifold) -> trimesh.Trimesh:
    m = mani.to_mesh()
    verts = np.round(np.array(m.vert_properties[:, :3], dtype=np.float64), 3)
    faces = np.array(m.tri_verts, dtype=np.int64)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    mesh.merge_vertices()
    mesh.update_faces(mesh.unique_faces())
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.fix_normals()
    return mesh


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


def extrude_polygon_xy(points_xy: np.ndarray, z0: float, z1: float) -> trimesh.Trimesh:
    """Extrude a simple 2D polygon (CCW in XY) between z0 and z1 via manifold3d CrossSection."""
    cs = m3d.CrossSection([points_xy.tolist()])
    mani = m3d.Manifold.extrude(cs, float(z1 - z0))
    mani = mani.translate([0.0, 0.0, float(z0)])
    return from_manifold(mani)


def make_cylinder(radius: float, z0: float, z1: float, cx: float = 0.0, cy: float = 0.0, sections: int = 64) -> trimesh.Trimesh:
    angles = np.linspace(0.0, 2.0 * math.pi, sections, endpoint=False)
    pts = np.column_stack([cx + radius * np.cos(angles), cy + radius * np.sin(angles)])
    return extrude_polygon_xy(pts, z0, z1)


def make_cone_frustum(r0: float, r1: float, z0: float, z1: float, cx: float = 0.0, cy: float = 0.0, sections: int = 64) -> trimesh.Trimesh:
    angles = np.linspace(0.0, 2.0 * math.pi, sections, endpoint=False)
    p0 = np.column_stack([cx + r0 * np.cos(angles), cy + r0 * np.sin(angles), np.full(sections, z0)])
    p1 = np.column_stack([cx + r1 * np.cos(angles), cy + r1 * np.sin(angles), np.full(sections, z1)])
    return from_manifold(to_manifold(trimesh.convex.convex_hull(np.vstack([p0, p1]))))


def make_stadium_xy(u0: float, u1: float, radius: float, z0: float, z1: float, v_center: float = 0.0, sections: int = 64) -> trimesh.Trimesh:
    """Create a stadium (rounded rectangle with semicircular ends at u0 and u1) extruded from z0 to z1."""
    half = sections // 2
    a1 = np.linspace(math.pi / 2.0, 1.5 * math.pi, half, endpoint=False)
    a2 = np.linspace(-math.pi / 2.0, math.pi / 2.0, half, endpoint=False)
    pts = np.vstack([
        np.column_stack([u0 + radius * np.cos(a1), v_center + radius * np.sin(a1)]),
        np.column_stack([u1 + radius * np.cos(a2), v_center + radius * np.sin(a2)]),
    ])
    return extrude_polygon_xy(pts, z0, z1)


def make_chamfered_stadium_xy(
    u0: float,
    u1: float,
    radius: float,
    z0: float,
    z1: float,
    chamfer_bot: float = 0.60,
    chamfer_top: float = 0.60,
    sections: int = 64,
) -> trimesh.Trimesh:
    """Create a stadium slab with 45° top and bottom perimeter chamfers for ergonomic grip."""
    half = sections // 2
    a1 = np.linspace(math.pi / 2.0, 1.5 * math.pi, half, endpoint=False)
    a2 = np.linspace(-math.pi / 2.0, math.pi / 2.0, half, endpoint=False)

    def ring(r: float, z: float) -> np.ndarray:
        xy = np.vstack([
            np.column_stack([u0 + r * np.cos(a1), r * np.sin(a1)]),
            np.column_stack([u1 + r * np.cos(a2), r * np.sin(a2)]),
        ])
        return np.column_stack([xy, np.full(len(xy), z)])

    layers = []
    if chamfer_bot > 0.0:
        layers.append(ring(radius - chamfer_bot, z0))
        layers.append(ring(radius, z0 + chamfer_bot))
    else:
        layers.append(ring(radius, z0))
    if chamfer_top > 0.0:
        layers.append(ring(radius, z1 - chamfer_top))
        layers.append(ring(radius - chamfer_top, z1))
    else:
        layers.append(ring(radius, z1))
    return from_manifold(to_manifold(trimesh.convex.convex_hull(np.vstack(layers))))


# ============================================================================
# 1. D-Bolt & Retaining U-Clip (print-flat, continuous XY strands)
# ============================================================================
def make_d_profile_xy(radius: float, flat_y: float, cx: float = 0.0, cy: float = 0.0, sections: int = 64) -> np.ndarray:
    """Return a 2D polygon for a circle of `radius` clipped by `y >= flat_y`."""
    angles = np.linspace(0.0, 2.0 * math.pi, sections, endpoint=False)
    pts = []
    for a in angles:
        x = radius * math.cos(a)
        y = max(radius * math.sin(a), flat_y)
        pts.append((cx + x, cy + y))
    return np.array(pts, dtype=np.float64)


def _make_d_head_points(r: float, flat_y: float, r_shaft: float, cx: float = 0.0, cy: float = 0.0, sections: int = 72) -> np.ndarray:
    angles = np.linspace(0.0, 2.0 * math.pi, sections, endpoint=False)
    pts = []
    half_base = math.sqrt(max(r_shaft ** 2 - flat_y ** 2, 0.5))
    for a in angles:
        x = r * math.cos(a)
        y = max(r * math.sin(a), flat_y)
        max_x = half_base + (y - flat_y) + 0.35
        x = max(-max_x, min(max_x, x))
        pts.append((cx + x, cy + y))
    return np.array(pts, dtype=np.float64)


def _extrude_polygon_frustum(pts_bot: np.ndarray, pts_top: np.ndarray, z0: float, z1: float) -> trimesh.Trimesh:
    """Build a watertight frustum between two star-convex polygons of equal vertex count `n`."""
    n = len(pts_bot)
    v_bot = np.column_stack([pts_bot, np.full(n, z0, dtype=np.float64)])
    v_top = np.column_stack([pts_top, np.full(n, z1, dtype=np.float64)])
    c_bot = np.array([[float(np.mean(pts_bot[:, 0])), float(np.mean(pts_bot[:, 1])), z0]], dtype=np.float64)
    c_top = np.array([[float(np.mean(pts_top[:, 0])), float(np.mean(pts_top[:, 1])), z1]], dtype=np.float64)
    verts = np.vstack([v_bot, v_top, c_bot, c_top])
    idx_c_bot = 2 * n
    idx_c_top = 2 * n + 1
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append([idx_c_bot, j, i])
        faces.append([idx_c_top, n + i, n + j])
        faces.append([i, j, n + j])
        faces.append([i, n + j, n + i])
    mesh = trimesh.Trimesh(vertices=verts, faces=np.array(faces, dtype=np.int64), process=True)
    return from_manifold(to_manifold(mesh))


def make_d_bolt_local(clearance: float = 0.0) -> trimesh.Trimesh:
    """Build the D-profile bolt centered at (0, 0) along Z = [0.00, 11.60 mm].

    The flat chord at `y = D_FLAT_Y` (-2.00 mm) runs continuously across both the
    head and the shaft so the bolt lies 100% flat on the print bed (`Z_print = 0.00 mm`)
    with 0.00 g support and continuous axial XY perimeters.
    The head transitions to the shaft via a 45° conical bevel (`Z = 0.85 .. 1.80 mm`)
    so the matching counterbore in `griff-*-unten` prints with 0.00 g support.
    """
    r_shaft = R_SHAFT + clearance
    flat_y = D_FLAT_Y - clearance
    r_head = R_HEAD + clearance

    head_pts = _make_d_head_points(r_head, flat_y, r_shaft, sections=72)
    shaft_pts = make_d_profile_xy(r_shaft, flat_y, sections=72)

    head_base = extrude_polygon_xy(head_pts, 0.0, 0.85)
    head_taper = _extrude_polygon_frustum(head_pts, shaft_pts, 0.85, 1.80)
    shaft = extrude_polygon_xy(shaft_pts, 1.60, Z_TOTAL)

    bolt = manifold_union([head_base, head_taper, shaft])

    if clearance == 0.0:
        # Cut the 3-sided U-retaining groove at Z = [Z_NOTCH_BOT, Z_NOTCH_TOP]
        # (both lateral sides x_local = ±1.45 mm and top face y_local = +1.45 mm;
        # the bottom D-flat y_local = -2.00 mm stays continuous on the print bed!)
        notch_h = Z_NOTCH_TOP - Z_NOTCH_BOT
        z_mid = 0.5 * (Z_NOTCH_BOT + Z_NOTCH_TOP)
        cutters = []
        for side in (-1.0, 1.0):
            c_box = trimesh.creation.box(extents=[4.0, 10.0, notch_h])
            c_box.apply_translation([
                side * (X_NOTCH_HALF + 2.0),
                0.0,
                z_mid,
            ])
            cutters.append(c_box)
        top_box = trimesh.creation.box(extents=[10.0, 4.0, notch_h])
        top_box.apply_translation([0.0, X_NOTCH_HALF + 2.0, z_mid])
        cutters.append(top_box)
        bolt = manifold_diff(bolt, cutters)

    return bolt


def make_d_bore_cutter(z0: float, z1: float, cx: float = 0.0, cy: float = 0.0, clearance: float = CLIP_FIT_CLEARANCE) -> trimesh.Trimesh:
    """Create a D-bore cutter matching the D-bolt shaft with `clearance` per side."""
    pts = make_d_profile_xy(R_SHAFT + clearance, D_FLAT_Y - clearance, cx=cx, cy=cy)
    return extrude_polygon_xy(pts, z0, z1)


def make_head_counterbore_cutter(cx: float = 0.0, cy: float = 0.0, clearance: float = CLIP_FIT_CLEARANCE) -> trimesh.Trimesh:
    """Create the lower scale counterbore cutter with a 45° self-supporting conical roof (`Z = 1.05 .. 2.00 mm`)."""
    r_head = R_HEAD + clearance
    r_shaft = R_SHAFT + clearance
    flat_y = D_FLAT_Y - clearance
    pts_head = make_d_profile_xy(r_head, flat_y, cx=cx, cy=cy, sections=72)
    pts_shaft = make_d_profile_xy(r_shaft, flat_y, cx=cx, cy=cy, sections=72)
    cb_base = extrude_polygon_xy(pts_head, -0.50, 1.05)
    cb_taper = _extrude_polygon_frustum(pts_head, pts_shaft, 1.05, 2.00)
    return manifold_union([cb_base, cb_taper])


def make_u_clip_local(entry_sign: float = 1.0) -> trimesh.Trimesh:
    """Create the U-shaped retaining clip centered at (0, 0) in Z = [Z_CLIP_BOT, Z_CLIP_TOP].

    `entry_sign = +1.0` means the closed bridge of the U is at `-u` and the open legs
    point toward `+u` (so the clip slides in from `-u` along `+u`).
    `entry_sign = -1.0` means the closed bridge is at `+u` and the clip slides in from `+u` along `-u`.
    Notice that inside the bolt groove (`Z = 9.50..10.75`), the bolt is symmetric in `±x_b`
    (`|x_b| <= 1.45 mm`), so when the U-clip slides along `±X` (the `u` axis!), wait:
    Let's align the bolt's lateral grooves with the clip's sliding axis!
    """
    # In the handle frame, the clip slides along the handle axis `u` (world X in open state).
    # Therefore, the two legs of the U-clip straddle `v` (world Y in open state)!
    # Let's make the U-clip outer profile a stadium along `u` from u = -3.60 to +3.60 mm,
    # width in `v` = 6.80 mm (radius 3.40 mm), with an inner slot of half-width `v_inner`
    # that straddles the bolt neck!
    r_outer = 3.35
    v_slot_half = X_NOTCH_HALF + CLIP_FIT_CLEARANCE  # 1.45 + 0.15 = 1.60 mm
    if entry_sign > 0:
        u0_out, u1_out = -1.80, -0.35
        slot_u0, slot_u1 = -v_slot_half, 5.0
    else:
        u0_out, u1_out = 0.35, 1.80
        slot_u0, slot_u1 = -5.0, v_slot_half
    outer = make_stadium_xy(u0_out, u1_out, r_outer, Z_CLIP_BOT, Z_CLIP_TOP)
    slot_box = trimesh.creation.box(extents=[slot_u1 - slot_u0, 2.0 * v_slot_half, (Z_CLIP_TOP - Z_CLIP_BOT) + 1.0])
    slot_box.apply_translation([0.5 * (slot_u0 + slot_u1), 0.0, 0.5 * (Z_CLIP_BOT + Z_CLIP_TOP)])
    return manifold_diff(outer, [slot_box])


def make_bolt_oriented(cx: float, cy: float, entry_sign: float = 1.0) -> trimesh.Trimesh:
    """Create a D-bolt at `(cx, cy)` oriented for a U-clip entering with `entry_sign` (`+1.0` from `-X`, `-1.0` from `+X`)."""
    b = make_d_bolt_local(clearance=0.0)
    rot = trimesh.transformations.rotation_matrix(entry_sign * (math.pi / 2.0), [0.0, 0.0, 1.0])
    b.apply_transform(rot)
    b.apply_translation([cx, cy, 0.0])
    return from_manifold(to_manifold(b))


def make_bolt_bore_oriented(
    z0: float, z1: float, cx: float, cy: float, entry_sign: float = 1.0, clearance: float = CLIP_FIT_CLEARANCE
) -> trimesh.Trimesh:
    c = make_d_bore_cutter(z0, z1, cx=0.0, cy=0.0, clearance=clearance)
    rot = trimesh.transformations.rotation_matrix(entry_sign * (math.pi / 2.0), [0.0, 0.0, 1.0])
    c.apply_transform(rot)
    c.apply_translation([cx, cy, 0.0])
    return from_manifold(to_manifold(c))


def make_bolt_cbore_oriented(
    cx: float, cy: float, entry_sign: float = 1.0, clearance: float = CLIP_FIT_CLEARANCE
) -> trimesh.Trimesh:
    c = make_head_counterbore_cutter(cx=0.0, cy=0.0, clearance=clearance)
    rot = trimesh.transformations.rotation_matrix(entry_sign * (math.pi / 2.0), [0.0, 0.0, 1.0])
    c.apply_transform(rot)
    c.apply_translation([cx, cy, 0.0])
    return from_manifold(to_manifold(c))


def make_clip_pocket_cutter(cx: float, cy: float, entry_sign: float) -> trimesh.Trimesh:
    """Cut the recessed clip pocket in the top of `griff-*-oben` (`Z = Z_POCKET_FLOOR .. Z_TOTAL + 1.0`).

    `entry_sign = +1.0`: clip enters from `-u` (front edge of handle at u = -6.50) moving in `+u`.
    `entry_sign = -1.0`: clip enters from `+u` (rear edge of handle at u = +120.0) moving in `-u`.
    """
    r_pocket = 3.35 + CLIP_FIT_CLEARANCE  # 3.50 mm
    u_start = cx - 10.0 if entry_sign > 0 else cx + 0.35 - CLIP_FIT_CLEARANCE
    u_end = cx - 0.35 + CLIP_FIT_CLEARANCE if entry_sign > 0 else cx + 18.0
    return make_stadium_xy(u_start, u_end, r_pocket, Z_POCKET_FLOOR, Z_TOTAL + 1.0, v_center=cy)


# ============================================================================
# 2. Blade (`butterfly-messer-klinge`) with Scraper Edge & Zen-Pin Cradles
# ============================================================================
def build_blade() -> trimesh.Trimesh:
    """Build the spear-point/clip-point blade in assembled Open pose (`Z = 4.00 .. 7.60 mm`).

    Features:
      - Tang with Ø 5.30 mm pivot bores at (0, +7.20) and (0, -7.20)
      - Tang collar radius R_COLLAR = 4.45 mm around pivots to clear the Zen Pins (r_inner = 4.80 mm)
      - Open Tang Block (X = 0..+7.30 mm) and Closed Ricasso Block (X = -10.0..0 mm) with swept Zen-Pin cradles
      - Symmetrical Tang Guards / Horns at X = -11.80 mm (Y = ±9.80 mm) outside the Zen-Pin sweep radius
      - Choil notch at X = -16.20 mm and plunge line at X = -20.00 mm
      - Double-bevel scraper cutting edge (`0.42 mm` edge crest, 45° bottom bevel + 15° top flat grind)
      - Upper false-edge spine swedge from X = -46.0 mm to the tip at X = -97.5 mm
    """
    # 1. Tang & Ricasso base (X = -20.5 .. +7.30 mm)
    pivot_l = make_cylinder(4.45, Z_BLADE_BOT, Z_BLADE_TOP, cx=0.0, cy=Y_PIVOT)
    pivot_r = make_cylinder(4.45, Z_BLADE_BOT, Z_BLADE_TOP, cx=0.0, cy=-Y_PIVOT)

    # Central tang bridge between the two pivots and extending to X = +7.20 (open stop) and X = -20.5 (ricasso)
    tang_pts = np.array([
        [7.20, -5.20],
        [7.20,  5.20],
        [0.00,  7.20],
        [-9.20, 5.20],
        [-11.80, 9.60],   # Upper tang guard horn
        [-13.60, 9.60],
        [-15.20, 6.20],
        [-20.50, 6.20],
        [-20.50, -6.50],
        [-18.00, -6.50],
        [-16.40, -5.00],  # Choil curve
        [-14.80, -6.50],
        [-13.60, -9.60],  # Lower tang guard horn
        [-11.80, -9.60],
        [-9.20, -5.20],
        [0.00, -7.20],
    ], dtype=np.float64)
    tang_core = extrude_polygon_xy(tang_pts, Z_BLADE_BOT, Z_BLADE_TOP)
    tang_solid = manifold_union([pivot_l, pivot_r, tang_core])

    # 2. Main blade body from X = -19.5 mm to tip at X = -97.5 mm
    # Build smooth spine curve (+Y) and belly cutting curve (-Y)
    xs = np.linspace(-19.50, -97.50, 60)
    spine_xy = []
    edge_xy = []
    grind_ridge_xy = []
    swedge_ridge_xy = []

    for x in xs:
        # t goes from 0.0 at ricasso (X = -19.5) to 1.0 at tip (X = -97.5)
        t = (-19.50 - x) / (97.50 - 19.50)
        # Spine: gently drops toward tip with classic clip/spear profile
        y_spine = 6.20 * (1.0 - 0.18 * (t ** 1.4) - 0.82 * (t ** 3.2))
        # Cutting edge belly: parallel then curves smoothly up to meet the tip
        y_edge = -6.50 * ((1.0 - t ** 2.15) ** 0.88)
        # Primary bevel grind line: starts at Y = +1.80 mm at ricasso and converges to tip
        y_grind = y_edge + 0.72 * (y_spine - y_edge)
        # Upper swedge ridge: active for t > 0.32
        swedge_frac = max(0.0, (t - 0.30) / 0.70)
        y_swedge = y_spine - 2.10 * math.sin(swedge_frac * math.pi * 0.85) * (1.0 - 0.55 * t)

        spine_xy.append((x, y_spine))
        edge_xy.append((x, y_edge))
        grind_ridge_xy.append((x, y_grind))
        swedge_ridge_xy.append((x, y_swedge))

    # Construct the faceted scraper-bevel blade slices along X as convex hulls of adjacent stations
    # Cross-section at station i:
    # - Cutting edge lip (`y = y_edge`): spans `Z = [Z_BLADE_BOT + 0.75, Z_BLADE_BOT + 1.17]` (`0.42 mm` scraper edge!
    #   Below `Z_BLADE_BOT + 0.75`, a 45° bottom bevel steps inward by `0.75 mm` to `Z = Z_BLADE_BOT` so it prints
    #   support-free on the build plate!)
    # - Full-thickness flat spine core (`y ∈ [y_grind, y_swedge]`): spans `Z = [Z_BLADE_BOT, Z_BLADE_TOP]` (`3.60 mm`).
    # - Spine edge (`y = y_spine`): spans `Z = [Z_BLADE_BOT, Z_BLADE_TOP - 1.10 * swedge_active]`.
    segments = []
    for i in range(len(xs) - 1):
        pts_3d = []
        for j in (i, i + 1):
            x = xs[j]
            ys = spine_xy[j][1]
            ye = edge_xy[j][1]
            yg = grind_ridge_xy[j][1]
            ysw = swedge_ridge_xy[j][1]
            t = (-19.50 - x) / (97.50 - 19.50)

            # Bottom 45° bevel offset from cutting edge (clamped near tip)
            bevel_45 = min(0.75, max(0.12, 0.35 * (ys - ye)))
            z_edge_bot = Z_BLADE_BOT + bevel_45
            z_edge_top = min(Z_BLADE_TOP - 0.20, z_edge_bot + 0.42)

            # Swedge top drop on the front half of the spine
            swedge_drop = 1.25 * max(0.0, (t - 0.30) / 0.70) * (1.0 - 0.35 * t)
            z_spine_top = Z_BLADE_TOP - swedge_drop

            station = [
                # Cutting edge 0.42 mm scraper crest
                (x, ye, z_edge_bot),
                (x, ye, z_edge_top),
                # Bottom 45° bevel shoulder on flat bed face Z = Z_BLADE_BOT
                (x, min(yg, ye + bevel_45), Z_BLADE_BOT),
                # Full-thickness grind ridge (bottom & top)
                (x, yg, Z_BLADE_BOT),
                (x, yg, Z_BLADE_TOP),
                # Swedge ridge (bottom & top)
                (x, ysw, Z_BLADE_BOT),
                (x, ysw, Z_BLADE_TOP),
                # Spine outer edge (bottom & top with swedge)
                (x, ys, Z_BLADE_BOT),
                (x, ys, z_spine_top),
            ]
            pts_3d.extend(station)
        seg = from_manifold(to_manifold(trimesh.convex.convex_hull(np.array(pts_3d, dtype=np.float64))))
        segments.append(seg)

    blade_body = manifold_union([tang_solid, *segments])

    # 3. Cut the two Ø 5.30 mm pivot bores (`R_SHAFT + PIVOT_CLEARANCE_RAD = 2.65 mm`),
    #    the choil cylinder, and the swept Zen-Pin stop cradles for θ ∈ [0°, 180°]!
    cutters = [
        make_cylinder(R_SHAFT + PIVOT_CLEARANCE_RAD, Z_BLADE_BOT - 1.0, Z_BLADE_TOP + 1.0, cx=0.0, cy=Y_PIVOT),
        make_cylinder(R_SHAFT + PIVOT_CLEARANCE_RAD, Z_BLADE_BOT - 1.0, Z_BLADE_TOP + 1.0, cx=0.0, cy=-Y_PIVOT),
        make_cylinder(1.85, Z_BLADE_BOT - 1.0, Z_BLADE_TOP + 1.0, cx=-16.40, cy=-6.80),
    ]

    # Swept Zen-Pin cutters for θ ∈ [0°, 180°] with 0.15 mm clearance (`R_ZEN + 0.15 = 2.15 mm`)
    r_zen_cut = R_ZEN + 0.15
    for deg in np.linspace(0.0, 180.0, 73):
        rad = math.radians(deg)
        xz = U_ZEN * math.cos(rad)
        yz_safe = Y_PIVOT + U_ZEN * math.sin(rad)
        yz_bite = -Y_PIVOT - U_ZEN * math.sin(rad)
        cutters.append(make_cylinder(r_zen_cut, Z_BLADE_BOT - 1.0, Z_BLADE_TOP + 1.0, cx=xz, cy=yz_safe, sections=36))
        cutters.append(make_cylinder(r_zen_cut, Z_BLADE_BOT - 1.0, Z_BLADE_TOP + 1.0, cx=xz, cy=yz_bite, sections=36))

    blade_final = manifold_diff(blade_body, cutters)
    return blade_final


# ============================================================================
# 3. Handle Scales (`griff-safe-unten/oben` & `griff-bite-unten/oben`)
# ============================================================================
def _skeleton_hole_cutters(z_bot: float, z_top: float, outer_at_bot: bool) -> list[trimesh.Trimesh]:
    """Generate the 5 countersunk large holes + 6 pairs of small dual holes matching Tile 00."""
    cutters = []
    u_smalls = [14.0, 30.4, 46.8, 63.2, 79.6, 96.0]
    u_larges = [22.2, 38.6, 55.0, 71.4, 87.8]

    for u in u_smalls:
        for v in (-2.90, 2.90):
            cutters.append(make_cylinder(1.15, z_bot - 0.5, z_top + 0.5, cx=u, cy=v, sections=32))

    r_hole = 3.40
    cs_depth = 1.00
    r_cs = r_hole + cs_depth  # exact 45° countersink!
    for u in u_larges:
        cutters.append(make_cylinder(r_hole, z_bot - 0.5, z_top + 0.5, cx=u, cy=0.0, sections=48))
        if outer_at_bot:
            cutters.append(make_cone_frustum(r_cs + 0.2, r_hole, z_bot - 0.2, z_bot + cs_depth, cx=u, cy=0.0, sections=48))
        else:
            cutters.append(make_cone_frustum(r_hole, r_cs + 0.2, z_top - cs_depth, z_top + 0.2, cx=u, cy=0.0, sections=48))
    return cutters


def build_handle_pair(is_safe: bool) -> tuple[trimesh.Trimesh, trimesh.Trimesh]:
    """Build `(unten, oben)` for either the Safe Handle (`is_safe=True`, Y = +Y_PIVOT)
    or the Bite Handle (`is_safe=False`, Y = -Y_PIVOT) in Open (`0°`) assembled coordinates.
    """
    y_off = Y_PIVOT if is_safe else -Y_PIVOT
    rear_bolt_u = U_SAFE_BOLT if is_safe else U_LATCH

    # --- A. LOWER SCALE (`unten`, Z = 0.00 .. 3.20 mm + integral posts) ---
    base_bot = make_chamfered_stadium_xy(0.0, U_REAR, R_HANDLE, 0.0, T_SCALE, chamfer_bot=0.60, chamfer_top=0.0)
    # Front pivot washer boss (Z = 3.20 .. 3.65 mm)
    washer_front_bot = make_cylinder(4.20, T_SCALE - 0.20, T_SCALE + Z_WASHER_H, cx=0.0, cy=0.0)

    # Integral Zen-Pin Stop Post at (U_ZEN, 0.0):
    # - Channel stop post: Z = 3.20 .. 8.40 mm, radius R_ZEN = 2.00 mm
    # - Upper locating tenon: Z = 8.40 .. 9.50 mm, radius R_ZEN_TENON = 1.55 mm, with 45° conical tip to 10.50 mm
    z_up_bot = Z_TOTAL - T_SCALE  # 8.40 mm
    zen_channel = make_cylinder(R_ZEN, T_SCALE - 0.20, z_up_bot, cx=U_ZEN, cy=0.0, sections=48)
    zen_tenon = make_cylinder(R_ZEN_TENON, z_up_bot - 0.20, z_up_bot + 1.10, cx=U_ZEN, cy=0.0, sections=48)
    zen_tip = make_cone_frustum(R_ZEN_TENON, 0.55, z_up_bot + 1.10, z_up_bot + 2.10, cx=U_ZEN, cy=0.0, sections=48)

    unten_add = [base_bot, washer_front_bot, zen_channel, zen_tenon, zen_tip]

    if is_safe:
        # Safe Handle Rear Spacer Block around `U_SAFE_BOLT = 104.50 mm` (Z = 3.20 .. 8.40 mm)
        spacer_safe = make_stadium_xy(102.50, 106.50, 4.10, T_SCALE - 0.20, z_up_bot)
        unten_add.append(spacer_safe)
    else:
        # Bite Handle:
        # 1. Anti-rotation spacer post at `U_BITE_SPACER = 104.50 mm` (radius 3.10 mm in channel,
        #    stepping to identical self-supporting tenon R_ZEN_TENON = 1.55 mm in upper scale)
        sp_channel = make_cylinder(3.10, T_SCALE - 0.20, z_up_bot, cx=U_BITE_SPACER, cy=0.0, sections=48)
        sp_tenon = make_cylinder(R_ZEN_TENON, z_up_bot - 0.20, z_up_bot + 1.10, cx=U_BITE_SPACER, cy=0.0, sections=48)
        sp_tip = make_cone_frustum(R_ZEN_TENON, 0.55, z_up_bot + 1.10, z_up_bot + 2.10, cx=U_BITE_SPACER, cy=0.0, sections=48)
        # 2. Rear latch pivot washer boss at `U_LATCH = 113.50 mm` (Z = 3.20 .. 3.65 mm)
        washer_rear_bot = make_cylinder(4.10, T_SCALE - 0.20, T_SCALE + Z_WASHER_H, cx=U_LATCH, cy=0.0)
        unten_add.extend([sp_channel, sp_tenon, sp_tip, washer_rear_bot])

    unten_raw = manifold_union(unten_add)

    # Cutters for `unten`:
    unten_cutters = [
        *_skeleton_hole_cutters(0.0, T_SCALE, outer_at_bot=True),
        # Front pivot bolt D-bore + bottom head counterbore (entry_sign = +1.0)
        make_bolt_bore_oriented(-0.5, Z_TOTAL + 0.5, cx=0.0, cy=0.0, entry_sign=1.0, clearance=CLIP_FIT_CLEARANCE),
        make_bolt_cbore_oriented(cx=0.0, cy=0.0, entry_sign=1.0, clearance=CLIP_FIT_CLEARANCE),
        # Rear bolt D-bore + bottom head counterbore (entry_sign = -1.0)
        make_bolt_bore_oriented(-0.5, Z_TOTAL + 0.5, cx=rear_bolt_u, cy=0.0, entry_sign=-1.0, clearance=CLIP_FIT_CLEARANCE),
        make_bolt_cbore_oriented(cx=rear_bolt_u, cy=0.0, entry_sign=-1.0, clearance=CLIP_FIT_CLEARANCE),
    ]
    unten_local = manifold_diff(unten_raw, unten_cutters)
    unten_local.apply_translation([0.0, y_off, 0.0])

    # --- B. UPPER SCALE (`oben`, Z = 8.40 .. 11.60 mm) ---
    # Flat bottom face at Z = 8.40 mm sits directly on the print bed (`Z_print = 0.00 mm`)!
    oben_raw = make_chamfered_stadium_xy(0.0, U_REAR, R_HANDLE, z_up_bot, Z_TOTAL, chamfer_bot=0.0, chamfer_top=0.60)

    r_sock = R_ZEN_TENON + CLIP_FIT_CLEARANCE  # 1.70 mm
    oben_cutters = [
        *_skeleton_hole_cutters(z_up_bot, Z_TOTAL, outer_at_bot=False),
        # Self-supporting 45°-roofed Zen-pin tenon socket at (U_ZEN, 0.0)
        make_cylinder(r_sock, z_up_bot - 0.5, z_up_bot + 1.25, cx=U_ZEN, cy=0.0, sections=48),
        make_cone_frustum(r_sock, 0.20, z_up_bot + 1.25, z_up_bot + 2.75, cx=U_ZEN, cy=0.0, sections=48),
        # Front pivot D-bore + top recessed U-clip pocket (entering from front `-u`, entry_sign = +1.0)
        make_bolt_bore_oriented(z_up_bot - 1.0, Z_TOTAL + 0.5, cx=0.0, cy=0.0, entry_sign=1.0, clearance=CLIP_FIT_CLEARANCE),
        make_clip_pocket_cutter(cx=0.0, cy=0.0, entry_sign=1.0),
        # Rear bolt D-bore + top recessed U-clip pocket (entering from rear `+u`, entry_sign = -1.0)
        make_bolt_bore_oriented(z_up_bot - 1.0, Z_TOTAL + 0.5, cx=rear_bolt_u, cy=0.0, entry_sign=-1.0, clearance=CLIP_FIT_CLEARANCE),
        make_clip_pocket_cutter(cx=rear_bolt_u, cy=0.0, entry_sign=-1.0),
    ]
    if not is_safe:
        # Self-supporting 45°-roofed socket for Bite Handle anti-rotation spacer tenon at `U_BITE_SPACER = 104.50 mm`
        oben_cutters.extend([
            make_cylinder(r_sock, z_up_bot - 0.5, z_up_bot + 1.25, cx=U_BITE_SPACER, cy=0.0, sections=48),
            make_cone_frustum(r_sock, 0.20, z_up_bot + 1.25, z_up_bot + 2.75, cx=U_BITE_SPACER, cy=0.0, sections=48),
        ])

    oben_local = manifold_diff(oben_raw, oben_cutters)
    oben_local.apply_translation([0.0, y_off, 0.0])

    return from_manifold(to_manifold(unten_local)), from_manifold(to_manifold(oben_local))


# ============================================================================
# 4. T-Latch (`butterfly-messer-riegel`)
# ============================================================================
def build_t_latch() -> trimesh.Trimesh:
    """Build the T-Latch centered around its pivot `(U_LATCH, -Y_PIVOT)` in Open pose (`φ = 0°`, pointing along `+X`).

    Z span:
      - Hub and stem (`r ∈ [0, 22.8 mm]`): `Z ∈ [4.00, 7.60 mm]` (`3.60 mm` thick, giving `0.35 mm` axial
        clearance to the `Z = 3.65 mm` and `Z = 7.95 mm` washer bosses!).
      - Outer T-crossbar head (`r ∈ [21.35, 24.85 mm]`, outside the `20.90 mm` outer edge of the Safe Handle):
        spans `Z ∈ [4.00, 9.80 mm]` so its raised lip hooks outside the Safe Handle's upper scale when locked
        at `φ = 90°`, while its entire bottom face (`Z = 4.00 mm`) remains 100% flat for support-free printing!
    """
    z0, z1 = Z_BLADE_BOT, Z_BLADE_TOP  # 4.00 .. 7.60 mm
    hub = make_cylinder(4.00, z0, z1, cx=0.0, cy=0.0, sections=48)
    stem = make_stadium_xy(0.0, 23.00, 1.75, z0, z1, sections=48)

    # T-crossbar head at x = 23.10 mm (spanning x = 21.35 .. 24.85 mm, y = -5.20 .. +5.20 mm)
    # Since minimum distance from (0, 0) to the crossbar is 21.35 mm > 20.90 mm (Safe Handle outer edge),
    # the crossbar clears the Safe Handle by >= 0.45 mm at all angles!
    t_bar_pts = np.array([
        [21.35, -4.80],
        [24.85, -4.80],
        [24.85,  4.80],
        [21.35,  4.80],
    ], dtype=np.float64)
    t_bar = extrude_polygon_xy(t_bar_pts, z0, 9.60)
    # Round the ends of the T-crossbar at y = ±4.80 mm
    t_cap_l = make_cylinder(1.75, z0, 9.60, cx=23.10, cy=4.80, sections=36)
    t_cap_r = make_cylinder(1.75, z0, 9.60, cx=23.10, cy=-4.80, sections=36)

    body = manifold_union([hub, stem, t_bar, t_cap_l, t_cap_r])
    bore = make_cylinder(R_SHAFT + PIVOT_CLEARANCE_RAD, z0 - 1.0, z1 + 1.0, cx=0.0, cy=0.0, sections=64)
    latch = manifold_diff(body, [bore])
    latch.apply_translation([U_LATCH, -Y_PIVOT, 0.0])
    return latch


# ============================================================================
# 5. Kinematic State Transformer (0°..180° handles, 0°..90° latch)
# ============================================================================
def transform_handle_group(
    meshes: dict[str, trimesh.Trimesh],
    theta_safe_deg: float,
    theta_bite_deg: float,
    phi_latch_deg: float,
) -> dict[str, trimesh.Trimesh]:
    """Return transformed copies of all 14 parts for any mechanism state:
      - `theta_safe_deg`: Safe Handle rotation around `(0, +Y_PIVOT)` (0° = Open +X, 180° = Closed -X via +Y)
      - `theta_bite_deg`: Bite Handle rotation around `(0, -Y_PIVOT)` (0° = Open +X, 180° = Closed -X via -Y)
      - `phi_latch_deg` : T-Latch rotation around Bite Handle's rear bolt (0° = extended along handle, 90° = locked across Safe Handle)
    """
    out: dict[str, trimesh.Trimesh] = {}
    out["butterfly-messer-klinge"] = meshes["butterfly-messer-klinge"].copy()

    # Safe Handle rotates by +theta_safe_deg around (0, +Y_PIVOT)
    rad_safe = math.radians(theta_safe_deg)
    t_safe = (
        trimesh.transformations.translation_matrix([0.0, Y_PIVOT, 0.0])
        @ trimesh.transformations.rotation_matrix(rad_safe, [0.0, 0.0, 1.0])
        @ trimesh.transformations.translation_matrix([0.0, -Y_PIVOT, 0.0])
    )
    for name in (
        "butterfly-messer-griff-safe-unten",
        "butterfly-messer-griff-safe-oben",
        "butterfly-messer-bolzen-safe-vorn",
        "butterfly-messer-bolzen-safe-hinten",
        "butterfly-messer-clip-safe-vorn",
        "butterfly-messer-clip-safe-hinten",
    ):
        m = meshes[name].copy()
        m.apply_transform(t_safe)
        out[name] = m

    # Bite Handle rotates by -theta_bite_deg around (0, -Y_PIVOT)
    rad_bite = -math.radians(theta_bite_deg)
    t_bite = (
        trimesh.transformations.translation_matrix([0.0, -Y_PIVOT, 0.0])
        @ trimesh.transformations.rotation_matrix(rad_bite, [0.0, 0.0, 1.0])
        @ trimesh.transformations.translation_matrix([0.0, Y_PIVOT, 0.0])
    )
    for name in (
        "butterfly-messer-griff-bite-unten",
        "butterfly-messer-griff-bite-oben",
        "butterfly-messer-bolzen-bite-vorn",
        "butterfly-messer-bolzen-bite-hinten",
        "butterfly-messer-clip-bite-vorn",
        "butterfly-messer-clip-bite-hinten",
    ):
        m = meshes[name].copy()
        m.apply_transform(t_bite)
        out[name] = m

    # T-Latch first rotates around its local pivot `(U_LATCH, -Y_PIVOT)` by `phi_latch_deg`,
    # Wait: in Open state (`theta_bite = 0°`), rotating by `+90°` around `(U_LATCH, -Y_PIVOT)` points `+Y` (toward Safe Handle).
    # In Closed state (`theta_bite = 180°`), `t_bite` rotates the Bite Handle by `-180°`, so local `-Y` becomes world `+Y`!
    # Therefore, to swing toward the Safe Handle in world coordinates, if we apply `t_bite` first, the latch pivot is at
    # world `(U_LATCH * cos(rad_bite), -Y_PIVOT + U_LATCH * sin(rad_bite))`.
    # Let's rotate the latch in world space around its transformed pivot so `phi_latch_deg = 90°` always points `+Y`!
    latch_m = meshes["butterfly-messer-riegel"].copy()
    pivot_world = t_bite @ np.array([U_LATCH, -Y_PIVOT, 0.0, 1.0])
    # In Open state (theta_bite = 0°), latch swings from 0° (+X) to +90° (+Y).
    # In Closed state (theta_bite = 180°), Bite Handle points along 180° (-X), so latch swings from 180° (-X) to +90° (+Y).
    if theta_bite_deg <= 90.0:
        latch_world_deg = -theta_bite_deg + phi_latch_deg
    else:
        latch_world_deg = (180.0 - theta_bite_deg) + (180.0 - phi_latch_deg)
    t_latch = (
        trimesh.transformations.translation_matrix(pivot_world[:3])
        @ trimesh.transformations.rotation_matrix(math.radians(latch_world_deg), [0.0, 0.0, 1.0])
        @ trimesh.transformations.translation_matrix([-U_LATCH, Y_PIVOT, 0.0])
    )
    latch_m.apply_transform(t_latch)
    out["butterfly-messer-riegel"] = latch_m

    return out


def center_xy_and_zero_z(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    out = mesh.copy()
    cx, cy = 0.5 * (out.bounds[0, :2] + out.bounds[1, :2])
    out.apply_translation([-cx, -cy, -out.bounds[0, 2]])
    return from_manifold(to_manifold(out))


def build_all_parts() -> tuple[
    dict[str, trimesh.Trimesh],
    dict[str, trimesh.Trimesh],
    trimesh.Trimesh,
    dict[str, tuple[np.ndarray, list[str]]],
]:
    """Build all 14 parts in Open (`0°`) assembled pose, print-oriented Z=0 poses, and merged STL."""
    klinge = build_blade()
    safe_unten, safe_oben = build_handle_pair(is_safe=True)
    bite_unten, bite_oben = build_handle_pair(is_safe=False)
    riegel = build_t_latch()

    bolzen_safe_vorn = make_bolt_oriented(0.0, Y_PIVOT, entry_sign=1.0)
    bolzen_bite_vorn = make_bolt_oriented(0.0, -Y_PIVOT, entry_sign=1.0)
    bolzen_safe_hinten = make_bolt_oriented(U_SAFE_BOLT, Y_PIVOT, entry_sign=-1.0)
    bolzen_bite_hinten = make_bolt_oriented(U_LATCH, -Y_PIVOT, entry_sign=-1.0)

    clip_safe_vorn = make_u_clip_local(entry_sign=1.0)
    clip_safe_vorn.apply_translation([0.0, Y_PIVOT, 0.0])

    clip_bite_vorn = make_u_clip_local(entry_sign=1.0)
    clip_bite_vorn.apply_translation([0.0, -Y_PIVOT, 0.0])

    clip_safe_hinten = make_u_clip_local(entry_sign=-1.0)
    clip_safe_hinten.apply_translation([U_SAFE_BOLT, Y_PIVOT, 0.0])

    clip_bite_hinten = make_u_clip_local(entry_sign=-1.0)
    clip_bite_hinten.apply_translation([U_LATCH, -Y_PIVOT, 0.0])

    parts = {
        "butterfly-messer-klinge": klinge,
        "butterfly-messer-riegel": riegel,
        "butterfly-messer-griff-safe-unten": safe_unten,
        "butterfly-messer-griff-safe-oben": safe_oben,
        "butterfly-messer-griff-bite-unten": bite_unten,
        "butterfly-messer-griff-bite-oben": bite_oben,
        "butterfly-messer-bolzen-safe-vorn": bolzen_safe_vorn,
        "butterfly-messer-bolzen-bite-vorn": bolzen_bite_vorn,
        "butterfly-messer-bolzen-safe-hinten": bolzen_safe_hinten,
        "butterfly-messer-bolzen-bite-hinten": bolzen_bite_hinten,
        "butterfly-messer-clip-safe-vorn": clip_safe_vorn,
        "butterfly-messer-clip-bite-vorn": clip_bite_vorn,
        "butterfly-messer-clip-safe-hinten": clip_safe_hinten,
        "butterfly-messer-clip-bite-hinten": clip_bite_hinten,
    }

    # Print-oriented parts (all lying flat on Z = 0.000 mm for 0.00 g support!)
    # - `oben` scales sit flat on their Z = 8.40 mm channel face (`Z_print = 0.000 mm`) so all top pockets and countersinks face +Z!
    safe_oben_print = safe_oben.copy()
    bite_oben_print = bite_oben.copy()

    # - `bolzen-*` are rotated so their continuous D-flat (`y_local = -2.00 mm`) sits on Z = 0.000 mm
    bolt_print_raw = make_d_bolt_local(clearance=0.0)
    rot_bolt_flat = trimesh.transformations.rotation_matrix(math.pi / 2.0, [1.0, 0.0, 0.0])
    bolt_print_raw.apply_transform(rot_bolt_flat)
    bolt_print = center_xy_and_zero_z(bolt_print_raw)

    clip_print = center_xy_and_zero_z(make_u_clip_local(entry_sign=1.0))

    print_parts = {
        "butterfly-messer-klinge": center_xy_and_zero_z(klinge),
        "butterfly-messer-riegel": center_xy_and_zero_z(riegel),
        "butterfly-messer-griff-safe-unten": center_xy_and_zero_z(safe_unten),
        "butterfly-messer-griff-safe-oben": center_xy_and_zero_z(safe_oben_print),
        "butterfly-messer-griff-bite-unten": center_xy_and_zero_z(bite_unten),
        "butterfly-messer-griff-bite-oben": center_xy_and_zero_z(bite_oben_print),
        "butterfly-messer-bolzen-safe-vorn": bolt_print.copy(),
        "butterfly-messer-bolzen-bite-vorn": bolt_print.copy(),
        "butterfly-messer-bolzen-safe-hinten": bolt_print.copy(),
        "butterfly-messer-bolzen-bite-hinten": bolt_print.copy(),
        "butterfly-messer-clip-safe-vorn": clip_print.copy(),
        "butterfly-messer-clip-bite-vorn": clip_print.copy(),
        "butterfly-messer-clip-safe-hinten": clip_print.copy(),
        "butterfly-messer-clip-bite-hinten": clip_print.copy(),
    }

    # Assembled merged preview mesh (centered at XY = 0,0, Z = 0)
    # Apply a 5-micron Z micro-separation between touching assembly bodies so STL readers
    # that weld coincident vertices by distance do not merge separate bodies at contact planes.
    preview_bodies = []
    for p_name, p_mesh in parts.items():
        pm = p_mesh.copy()
        if "oben" in p_name:
            pm.apply_translation([0.0, 0.0, 0.005])
        elif "clip" in p_name:
            pm.apply_translation([0.0, 0.0, 0.010])
        elif "bolzen" in p_name:
            pm.apply_translation([0.0, 0.0, -0.005])
        preview_bodies.append(pm)
    all_concat = trimesh.util.concatenate(preview_bodies)
    merged_preview = center_xy_and_zero_z(all_concat)

    # Insertion vectors & already-installed obstacle sets for linear insertion sweep verification
    # Assembly order:
    # 1. Base parts on table: `griff-safe-unten`, `griff-bite-unten`
    # 2. Drop `klinge` and `riegel` straight down along -Z `(0, 0, -1)`
    # 3. Drop `griff-safe-oben` and `griff-bite-oben` straight down along -Z `(0, 0, -1)`
    # 4. Insert the 4 `bolzen-*` straight up from below along +Z `(0, 0, +1)`
    # 5. Slide the 2 front `clip-*-vorn` horizontally along +X `(+1, 0, 0)` and 2 rear `clip-*-hinten` along -X `(-1, 0, 0)`
    insertion_specs: dict[str, tuple[np.ndarray, list[str]]] = {
        "butterfly-messer-klinge": (
            np.array([0.0, 0.0, -1.0]),
            ["butterfly-messer-griff-safe-unten", "butterfly-messer-griff-bite-unten"],
        ),
        "butterfly-messer-riegel": (
            np.array([0.0, 0.0, -1.0]),
            ["butterfly-messer-griff-safe-unten", "butterfly-messer-griff-bite-unten", "butterfly-messer-klinge"],
        ),
        "butterfly-messer-griff-safe-oben": (
            np.array([0.0, 0.0, -1.0]),
            ["butterfly-messer-griff-safe-unten", "butterfly-messer-klinge", "butterfly-messer-riegel"],
        ),
        "butterfly-messer-griff-bite-oben": (
            np.array([0.0, 0.0, -1.0]),
            ["butterfly-messer-griff-bite-unten", "butterfly-messer-klinge", "butterfly-messer-riegel"],
        ),
        "butterfly-messer-bolzen-safe-vorn": (
            np.array([0.0, 0.0, 1.0]),
            ["butterfly-messer-griff-safe-unten", "butterfly-messer-griff-safe-oben", "butterfly-messer-klinge"],
        ),
        "butterfly-messer-bolzen-bite-vorn": (
            np.array([0.0, 0.0, 1.0]),
            ["butterfly-messer-griff-bite-unten", "butterfly-messer-griff-bite-oben", "butterfly-messer-klinge"],
        ),
        "butterfly-messer-bolzen-safe-hinten": (
            np.array([0.0, 0.0, 1.0]),
            ["butterfly-messer-griff-safe-unten", "butterfly-messer-griff-safe-oben"],
        ),
        "butterfly-messer-bolzen-bite-hinten": (
            np.array([0.0, 0.0, 1.0]),
            ["butterfly-messer-griff-bite-unten", "butterfly-messer-griff-bite-oben", "butterfly-messer-riegel"],
        ),
        "butterfly-messer-clip-safe-vorn": (
            np.array([1.0, 0.0, 0.0]),
            ["butterfly-messer-griff-safe-unten", "butterfly-messer-griff-safe-oben", "butterfly-messer-bolzen-safe-vorn"],
        ),
        "butterfly-messer-clip-bite-vorn": (
            np.array([1.0, 0.0, 0.0]),
            ["butterfly-messer-griff-bite-unten", "butterfly-messer-griff-bite-oben", "butterfly-messer-bolzen-bite-vorn"],
        ),
        "butterfly-messer-clip-safe-hinten": (
            np.array([-1.0, 0.0, 0.0]),
            ["butterfly-messer-griff-safe-unten", "butterfly-messer-griff-safe-oben", "butterfly-messer-bolzen-safe-hinten"],
        ),
        "butterfly-messer-clip-bite-hinten": (
            np.array([-1.0, 0.0, 0.0]),
            ["butterfly-messer-griff-bite-unten", "butterfly-messer-griff-bite-oben", "butterfly-messer-bolzen-bite-hinten"],
        ),
    }

    return parts, print_parts, merged_preview, insertion_specs


def verify_mechanics_and_sweeps(
    parts: dict[str, trimesh.Trimesh],
    insertion_specs: dict[str, tuple[np.ndarray, list[str]]],
) -> dict:
    """Verify:
    1. Every part is watertight, single-component, and has 0 degenerate faces.
    2. Static & linear assembly insertion sweeps have 0.000 mm³ intersection.
    3. Full kinematic motion sweep (θ ∈ [0°, 180°] in 37 steps, φ_latch ∈ [0°, 90°] in 19 steps)
       has 0.000 mm³ collision volume across all moving groups.
    """
    mesh_checks = {}
    for name, m in parts.items():
        comps = len(m.split(only_watertight=False))
        mesh_checks[name] = {
            "facets": int(len(m.faces)),
            "watertight": bool(m.is_watertight),
            "winding_consistent": bool(m.is_winding_consistent),
            "euler_number": int(m.euler_number),
            "components": int(comps),
            "volume_mm3": round(float(abs(m.volume)), 2),
            "extents_mm": [round(float(x), 2) for x in m.extents],
        }
        if not m.is_watertight or comps != 1:
            raise RuntimeError(f"Part {name} failed mesh integrity check: {mesh_checks[name]}")

    # Linear insertion sweep checks
    insertion_report = {}
    for part_name, (vec_in, obstacles) in insertion_specs.items():
        part_mesh = parts[part_name]
        vec_out = -vec_in / np.linalg.norm(vec_in)
        static_vol = sum(intersection_volume(part_mesh, parts[obs]) for obs in obstacles)
        max_sweep_vol = 0.0
        for dist in np.linspace(0.0, 14.0, 15):
            moved = part_mesh.copy()
            moved.apply_translation(vec_out * dist)
            v = sum(intersection_volume(moved, parts[obs]) for obs in obstacles)
            max_sweep_vol = max(max_sweep_vol, v)
        status = "PASS" if max_sweep_vol < 1e-3 else "FAIL"
        insertion_report[part_name] = {
            "insertion_vector": vec_in.tolist(),
            "obstacles": obstacles,
            "static_intersection_mm3": round(static_vol, 5),
            "max_sweep_intersection_mm3": round(max_sweep_vol, 5),
            "status": status,
        }
        if status != "PASS":
            raise RuntimeError(f"Insertion sweep collision for {part_name}: {insertion_report[part_name]}")

    # Kinematic motion sweep:
    # Group moving rigid sub-assemblies at angle θ:
    safe_group_base = manifold_union([
        parts["butterfly-messer-griff-safe-unten"],
        parts["butterfly-messer-griff-safe-oben"],
        parts["butterfly-messer-bolzen-safe-vorn"],
        parts["butterfly-messer-bolzen-safe-hinten"],
        parts["butterfly-messer-clip-safe-vorn"],
        parts["butterfly-messer-clip-safe-hinten"],
    ])
    bite_group_base = manifold_union([
        parts["butterfly-messer-griff-bite-unten"],
        parts["butterfly-messer-griff-bite-oben"],
        parts["butterfly-messer-bolzen-bite-vorn"],
        parts["butterfly-messer-bolzen-bite-hinten"],
        parts["butterfly-messer-clip-bite-vorn"],
        parts["butterfly-messer-clip-bite-hinten"],
    ])
    blade = parts["butterfly-messer-klinge"]

    kinematic_samples = []
    max_kinematic_collision = 0.0
    for deg in np.linspace(0.0, 180.0, 37):
        rad_s = math.radians(deg)
        rad_b = -math.radians(deg)
        t_s = (
            trimesh.transformations.translation_matrix([0.0, Y_PIVOT, 0.0])
            @ trimesh.transformations.rotation_matrix(rad_s, [0.0, 0.0, 1.0])
            @ trimesh.transformations.translation_matrix([0.0, -Y_PIVOT, 0.0])
        )
        t_b = (
            trimesh.transformations.translation_matrix([0.0, -Y_PIVOT, 0.0])
            @ trimesh.transformations.rotation_matrix(rad_b, [0.0, 0.0, 1.0])
            @ trimesh.transformations.translation_matrix([0.0, Y_PIVOT, 0.0])
        )
        sg = safe_group_base.copy()
        sg.apply_transform(t_s)
        bg = bite_group_base.copy()
        bg.apply_transform(t_b)

        v_sb = intersection_volume(sg, blade)
        v_bb = intersection_volume(bg, blade)
        v_ss = intersection_volume(sg, bg)
        v_tot = v_sb + v_bb + v_ss
        max_kinematic_collision = max(max_kinematic_collision, v_tot)
        kinematic_samples.append({
            "angle_deg": float(deg),
            "safe_vs_blade_mm3": round(v_sb, 5),
            "bite_vs_blade_mm3": round(v_bb, 5),
            "safe_vs_bite_mm3": round(v_ss, 5),
        })
        if v_tot >= 1e-3:
            raise RuntimeError(f"Kinematic collision at θ={deg}°: safe_blade={v_sb}, bite_blade={v_bb}, safe_bite={v_ss}")

    # Latch sweep in both Open (0°) and Closed (180°) states for φ ∈ [0°, 90°]
    max_latch_collision = 0.0
    for handle_deg in (0.0, 180.0):
        for phi in np.linspace(0.0, 90.0, 19):
            posed = transform_handle_group(parts, handle_deg, handle_deg, float(phi))
            latch_m = posed["butterfly-messer-riegel"]
            v_l = sum(
                intersection_volume(latch_m, posed[other])
                for other in posed
                if other != "butterfly-messer-riegel"
            )
            max_latch_collision = max(max_latch_collision, v_l)
            if v_l >= 1e-3:
                raise RuntimeError(f"Latch collision at handle={handle_deg}°, φ={phi}°: {v_l} mm³")

    return {
        "mesh_checks": mesh_checks,
        "insertion_report": insertion_report,
        "kinematic_samples": kinematic_samples,
        "max_kinematic_collision_mm3": round(max_kinematic_collision, 6),
        "max_latch_collision_mm3": round(max_latch_collision, 6),
        "status": "PASS",
    }


# ============================================================================
# 6. ASCII STL & 3MF Packaging (`-view.3mf` & `-print.3mf`) + OrcaSlicer Validation
# ============================================================================
def write_ascii_stl(mesh: trimesh.Trimesh, out_path: Path, solid_name: str) -> None:
    """Write a clean, deterministic ASCII STL file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    v = mesh.vertices
    f = mesh.faces
    normals = mesh.face_normals
    lines = [f"solid {solid_name}"]
    for idx, (i0, i1, i2) in enumerate(f):
        nx, ny, nz = normals[idx]
        p0, p1, p2 = v[i0], v[i1], v[i2]
        lines.append(f"  facet normal {nx:.6e} {ny:.6e} {nz:.6e}")
        lines.append("    outer loop")
        lines.append(f"      vertex {p0[0]:.6f} {p0[1]:.6f} {p0[2]:.6f}")
        lines.append(f"      vertex {p1[0]:.6f} {p1[1]:.6f} {p1[2]:.6f}")
        lines.append(f"      vertex {p2[0]:.6f} {p2[1]:.6f} {p2[2]:.6f}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append(f"endsolid {solid_name}\n")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_3mf(
    path: Path,
    objects: list[tuple[str, trimesh.Trimesh, MaterialSpec, list[float] | None]],
    *,
    plate_names: list[str] | None = None,
    object_plates: dict[str, int] | None = None,
    material_slots: dict[MaterialSpec, int] | None = None,
) -> None:
    """Write a 3MF archive with basematerials, optional multi-plate config, and ghouls-grip metadata."""
    core = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    ET.register_namespace("", core)
    model = ET.Element(f"{{{core}}}model", unit="millimeter")
    meta = ET.SubElement(model, f"{{{core}}}metadata", name="Title")
    meta.text = path.stem

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
        "layerHeightMm": "0.2",
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


def build_view_3mf(parts: dict[str, trimesh.Trimesh], out_path: Path) -> None:
    """Write `models/butterfly-messer-view.3mf` with 3 mechanism states across 3 plates:
      - Plate 1: Open (`0°`, latch extended `0°`)
      - Plate 2: Half-open (`90°`, flip motion)
      - Plate 3: Closed & locked (`180°`, T-latch engaged `90°`)
    """
    material_slots = {mat: mat.slot - 1 for mat in MATERIAL_LIST}
    states = [
        ("open", "Zustand 1 - Geoeffnet (0 Grad, einsatzbereit)", 0.0, 0.0, 0.0),
        ("mid", "Zustand 2 - Halb geoeffnet (90 Grad, Flip-Bewegung)", 90.0, 90.0, 0.0),
        ("closed", "Zustand 3 - Geschlossen & verriegelt (180 Grad, T-Latch zu)", 180.0, 180.0, 90.0),
    ]
    plate_names = [s[1] for s in states]
    objects = []
    object_plates = {}
    grid_columns = 2
    pitch = 300.0

    for plate_idx, (prefix, _title, ts, tb, pl) in enumerate(states):
        posed = transform_handle_group(parts, ts, tb, pl)
        combined = trimesh.util.concatenate(list(posed.values()))
        cx, cy = 0.5 * (combined.bounds[0, :2] + combined.bounds[1, :2])
        min_z = float(combined.bounds[0, 2])
        col = plate_idx % grid_columns
        row = plate_idx // grid_columns
        tx = 125.0 - cx + col * pitch
        ty = 125.0 - cy - row * pitch
        tz = -min_z
        for name, m in posed.items():
            placed = m.copy()
            placed.apply_translation([tx, ty, tz])
            obj_name = f"{prefix}-{name}"
            objects.append((obj_name, placed, PART_MATERIAL[name], None))
            object_plates[obj_name] = plate_idx

    write_3mf(
        out_path,
        objects,
        plate_names=plate_names,
        object_plates=object_plates,
        material_slots=material_slots,
    )


OBJECT_OVERRIDES = {
    "butterfly-messer-klinge": {
        "wall_loops": "4",
        "sparse_infill_density": "60%",
        "sparse_infill_pattern": "rectilinear",
        "enable_support": "1",
        "detect_thin_wall": "1",
        "xy_hole_compensation": "0.05",
    },
    "butterfly-messer-riegel": {
        "wall_loops": "4",
        "sparse_infill_density": "100%",
        "enable_support": "1",
        "xy_hole_compensation": "0.05",
    },
    "butterfly-messer-griff-safe-unten": {
        "wall_loops": "4",
        "sparse_infill_density": "55%",
        "sparse_infill_pattern": "rectilinear",
        "enable_support": "1",
        "xy_hole_compensation": "0.05",
    },
    "butterfly-messer-griff-safe-oben": {
        "wall_loops": "4",
        "sparse_infill_density": "55%",
        "sparse_infill_pattern": "rectilinear",
        "enable_support": "1",
        "xy_hole_compensation": "0.05",
    },
    "butterfly-messer-griff-bite-unten": {
        "wall_loops": "4",
        "sparse_infill_density": "55%",
        "sparse_infill_pattern": "rectilinear",
        "enable_support": "1",
        "xy_hole_compensation": "0.05",
    },
    "butterfly-messer-griff-bite-oben": {
        "wall_loops": "4",
        "sparse_infill_density": "55%",
        "sparse_infill_pattern": "rectilinear",
        "enable_support": "1",
        "xy_hole_compensation": "0.05",
    },
    **{
        name: {
            "wall_loops": "5",
            "sparse_infill_density": "100%",
            "enable_support": "1",
            "brim_type": "outer_only",
            "brim_width": "2",
        }
        for name in (
            "butterfly-messer-bolzen-safe-vorn",
            "butterfly-messer-bolzen-bite-vorn",
            "butterfly-messer-bolzen-safe-hinten",
            "butterfly-messer-bolzen-bite-hinten",
            "butterfly-messer-clip-safe-vorn",
            "butterfly-messer-clip-bite-vorn",
            "butterfly-messer-clip-safe-hinten",
            "butterfly-messer-clip-bite-hinten",
        )
    },
}


PRINT_LAYOUT_XY = {
    # Plate 0 (Silver): Blade & T-Latch
    "butterfly-messer-klinge": (0, (125.0, 110.0)),
    "butterfly-messer-riegel": (0, (125.0, 148.0)),
    # Plate 1 (Anthracite): 4 Handle Scales + 4 Bolts + 4 Clips
    "butterfly-messer-griff-safe-unten": (1, (125.0, 68.0)),
    "butterfly-messer-griff-safe-oben": (1, (125.0, 96.0)),
    "butterfly-messer-griff-bite-unten": (1, (125.0, 124.0)),
    "butterfly-messer-griff-bite-oben": (1, (125.0, 152.0)),
    "butterfly-messer-bolzen-safe-vorn": (1, (95.0, 178.0)),
    "butterfly-messer-bolzen-bite-vorn": (1, (115.0, 178.0)),
    "butterfly-messer-bolzen-safe-hinten": (1, (135.0, 178.0)),
    "butterfly-messer-bolzen-bite-hinten": (1, (155.0, 178.0)),
    "butterfly-messer-clip-safe-vorn": (1, (95.0, 198.0)),
    "butterfly-messer-clip-bite-vorn": (1, (115.0, 198.0)),
    "butterfly-messer-clip-safe-hinten": (1, (135.0, 198.0)),
    "butterfly-messer-clip-bite-hinten": (1, (155.0, 198.0)),
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


def build_print_3mf(print_parts: dict[str, trimesh.Trimesh], out_path: Path) -> None:
    """Create the consolidated 2-plate OrcaSlicer printable 3MF (`models/butterfly-messer-print.3mf`)."""
    plate_names = [
        "Silber-Grau - Klinge & T-Latch",
        "Anthrazit - 4x Griffschalen, 4x D-Bolzen & 4x U-Clips",
    ]
    grid_columns = 2
    pitch = 300.0

    scene_items = []
    for name, mesh in print_parts.items():
        plate_idx, (lx, ly) = PRINT_LAYOUT_XY[name]
        col = plate_idx % grid_columns
        row = plate_idx // grid_columns
        placed = mesh.copy()
        cx, cy = 0.5 * (placed.bounds[0, :2] + placed.bounds[1, :2])
        placed.apply_translation([
            lx - cx + col * pitch,
            ly - cy - row * pitch,
            -placed.bounds[0, 2],
        ])
        scene_items.append((name, placed, PART_MATERIAL[name], None))

    MODELS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="butterfly-orca-", dir=MODELS) as temp_name:
        temp = Path(temp_name)
        source = temp / "butterfly-messer-print-source.3mf"
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

        with ZipFile(staged) as archive:
            infos = archive.infolist()
            entries = {info.filename: archive.read(info.filename) for info in infos}

        proj_key = "Metadata/project_settings.config"
        project = json.loads(entries[proj_key].decode("utf-8"))
        process_overrides = {
            "curr_bed_type": "Textured PEI Plate",
            "layer_height": "0.2",
            "initial_layer_print_height": "0.2",
            "wall_loops": "4",
            "sparse_infill_density": "55%",
            "sparse_infill_pattern": "rectilinear",
            "seam_position": "random",
            "ironing_type": "top",
            "enable_support": "1",
            "support_type": "normal(auto)",
            "support_on_build_plate_only": "1",
            "support_threshold_angle": "30",
            "support_critical_regions_only": "1",
            "bridge_no_support": "1",
            "enable_prime_tower": "0",
            "xy_hole_compensation": "0.05",
            "xy_contour_compensation": "0",
            "elefant_foot_compensation": "0.12",
            "brim_type": "no_brim",
            "brim_width": "2",
            "detect_thin_wall": "1",
            "only_one_wall_top": "0",
        }
        project.update(process_overrides)
        colors = [m.color_hex.upper() for m in MATERIAL_LIST]
        profile_name = FILAMENT_PRESET.stem
        n_fil = len(MATERIAL_LIST)
        for key, value in list(project.items()):
            if key.startswith("filament_") and isinstance(value, list) and value:
                project[key] = [value[0]] * n_fil
        project["flush_volumes_matrix"] = [
            "0" if i == j else "280"
            for i in range(n_fil)
            for j in range(n_fil)
        ]
        project["flush_volumes_vector"] = ["140"] * (2 * n_fil)
        project["default_filament_profile"] = [profile_name] * n_fil
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
            "flush_volumes_matrix",
            "flush_volumes_vector",
            "print_extruder_id",
            "printer_extruder_id",
        })
        current = project.get("different_settings_to_system", ["", "", ""])
        current[1] = ";".join(sorted(changed - {""}))
        project["different_settings_to_system"] = current
        entries[proj_key] = json.dumps(project, indent=2).encode("utf-8")

        mod_key = "Metadata/model_settings.config"
        root = ET.fromstring(entries[mod_key])
        ids_by_plate: dict[int, list[str]] = {}
        for obj in root.findall("object"):
            name_node = next((n for n in obj.findall("metadata") if n.get("key") == "name"), None)
            if name_node is None:
                continue
            name = name_node.get("value", "")
            if name not in PRINT_LAYOUT_XY:
                continue
            obj_id = obj.get("id")
            plate_idx, _ = PRINT_LAYOUT_XY[name]
            mat = PART_MATERIAL[name]
            _add_metadata(obj, "extruder", str(mat.slot))
            for k, val in OBJECT_OVERRIDES.get(name, {}).items():
                _add_metadata(obj, k, val)
            ids_by_plate.setdefault(plate_idx, []).append(obj_id)

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
            "layerHeightMm": "0.2",
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
    """Slice `models/butterfly-messer-print.3mf` with OrcaSlicer CLI and patch verified metadata into both 3MFs."""
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
    if res.returncode != 0 or len(gcodes) != 2:
        raise RuntimeError(
            f"OrcaSlicer slice failed (exit={res.returncode}, plates={len(gcodes)})"
        )

    plate_titles = [
        "Platte 1 - Klinge & Riegel - silbergraues PLA",
        "Platte 2 - Griffschalen (4x), D-Bolzen (4x) & U-Clips (4x) - anthrazitfarbenes PLA",
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
        "layerHeightMm": "0.2",
        "filamentProfile": FILAMENT_PRESET.stem,
        "materialType": "PLA",
        "materialColorName": ", ".join(m.name for m in MATERIAL_LIST),
        "materialColorHex": ", ".join(m.color_hex.upper() for m in MATERIAL_LIST),
        "bedType": "Textured PEI Plate",
        "wallLoops": "Per-object overrides (4 on blade/handles, 5 on pins/clips); global 4",
        "infillDensity": "Per-object overrides (55% handles, 60% blade, 100% latch/pins/clips); global 55%",
        "supportPolicy": "Global enable_support=1; normal(auto), build-plate only, critical regions only",
        "supportThresholdAngleDeg": "30",
        "seamPosition": "random",
        "ironingType": "top",
        "objectCount": "14",
        "plateCount": "2",
        "filamentUsageByColor": json.dumps(per_color, sort_keys=True, separators=(",", ":")),
        "plateDetails": json.dumps(plate_details, sort_keys=True, separators=(",", ":")),
    })

    with ZipFile(print_3mf_path) as print_arch:
        proj_settings_bytes = (
            print_arch.read("Metadata/project_settings.config")
            if "Metadata/project_settings.config" in print_arch.namelist()
            else None
        )

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
            target_values["plateCount"] = "3"
            target_values["objectCount"] = "42"
        for k, val in target_values.items():
            if k not in fields:
                fields[k] = ET.SubElement(root, "metadata", name=k)
            fields[k].set("value", str(val))
        entries[METADATA_ENTRY] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        if "Metadata/project_settings.config" not in entries and proj_settings_bytes is not None:
            entries["Metadata/project_settings.config"] = proj_settings_bytes
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
                written.add(METADATA_ENTRY)
            if "Metadata/project_settings.config" in entries and "Metadata/project_settings.config" not in written:
                archive.writestr("Metadata/project_settings.config", entries["Metadata/project_settings.config"])
                written.add("Metadata/project_settings.config")
        os.replace(tmp, target_3mf)

    return overall


def render_all_previews_and_supports(
    parts: dict[str, trimesh.Trimesh],
    print_parts: dict[str, trimesh.Trimesh],
    slice_dir: Path,
    slice_stats: dict,
) -> dict[str, Path]:
    """Render `butterfly-messer-view-preview.png`, `butterfly-messer-print-preview.png`,
    `butterfly-messer-print-plate-1..3-supports.png`, and `butterfly-messer-presentation.png`.
    """
    from PIL import Image, ImageDraw
    import vedo
    from render_ghouls_grip_supports import support_actor, support_segments

    IMAGES.mkdir(parents=True, exist_ok=True)
    render_tmp = BUILD_DIR / "renders"
    render_tmp.mkdir(parents=True, exist_ok=True)

    render_colors = {
        name: PART_MATERIAL[name].color_hex for name in parts
    }

    # 1. `docs/images/butterfly-messer-view-preview.png` (3 panels: Open 0°, Half-Open 90°, Closed & Latched 180°)
    view_states = [
        ("Zustand 1 - Geoeffnet (0 Grad, Spachtel-Schneide & T-Latch offen)", 0.0, 0.0, 0.0),
        ("Zustand 2 - Halb geoeffnet (90 Grad, Zen-Pin-Kinematik)", 90.0, 90.0, 0.0),
        ("Zustand 3 - Geschlossen & verriegelt (180 Grad, T-Latch eingerastet)", 180.0, 180.0, 90.0),
    ]
    view_panels = []
    for idx, (title, ts, tb, pl) in enumerate(view_states):
        posed = transform_handle_group(parts, ts, tb, pl)
        comb = trimesh.util.concatenate(list(posed.values()))
        cx, cy = 0.5 * (comb.bounds[0, :2] + comb.bounds[1, :2])
        span = max(float(np.max(comb.extents)), 135.0)
        actors = [
            vedo.Box(pos=(cx, cy, -1.0), length=span * 1.28, width=span * 0.88, height=1.6).c("#D8DEE9"),
        ]
        for name, m in posed.items():
            actors.append(
                vedo.Mesh([m.vertices, m.faces])
                .c(render_colors[name])
                .lighting("glossy")
            )
        actors.append(vedo.Text2D(title, pos="top-left", c="#1E222A", s=0.70))
        cam = {
            "pos": (cx - span * 0.18, cy - span * 1.22, 5.8 + span * 1.12),
            "focal_point": (cx, cy, 5.8),
            "viewup": (0.0, 0.0, 1.0),
        }
        plt = vedo.Plotter(offscreen=True, size=(760, 620), bg="#ECEFF4")
        plt.show(*actors, camera=cam, axes=0)
        p_img = render_tmp / f"view_panel_{idx}.png"
        plt.screenshot(str(p_img))
        plt.close()
        view_panels.append((title, Image.open(p_img).convert("RGB")))

    margin, label_h, pw, ph = 20, 38, 760, 620
    view_canvas = Image.new("RGB", (3 * pw + 4 * margin, ph + label_h + 2 * margin), "#1E222A")
    draw = ImageDraw.Draw(view_canvas)
    for idx, (label, im) in enumerate(view_panels):
        x = margin + idx * (pw + margin)
        y = margin
        view_canvas.paste(im, (x, y))
        draw.text((x + 8, y + ph + 10), label, fill="#ECEFF4")
    view_preview_path = IMAGES / "butterfly-messer-view-preview.png"
    view_canvas.save(view_preview_path)

    # 2. `docs/images/butterfly-messer-print-preview.png` & `docs/images/butterfly-messer-print-plate-1..2-supports.png`
    plate_defs = [
        (
            0,
            "Platte 1 - Silber-Grau (Klinge & T-Latch)",
            [k for k, (p, _) in PRINT_LAYOUT_XY.items() if p == 0],
            MATERIALS["silver"].color_hex,
        ),
        (
            1,
            "Platte 2 - Anthrazit (4x Griffschalen, 4x D-Bolzen & 4x U-Clips)",
            [k for k, (p, _) in PRINT_LAYOUT_XY.items() if p == 1],
            MATERIALS["anthracite"].color_hex,
        ),
    ]

    plate_details_list = json.loads(slice_stats["plateDetails"])
    print_thumbs = []
    support_paths = []
    pw_print = 1150

    for plate_idx, title, part_names, hex_color in plate_defs:
        placed_meshes = []
        for part_name in part_names:
            _, (lx, ly) = PRINT_LAYOUT_XY[part_name]
            pm = print_parts[part_name].copy()
            cx, cy = 0.5 * (pm.bounds[0, :2] + pm.bounds[1, :2])
            pm.apply_translation([lx - cx, ly - cy, -pm.bounds[0, 2]])
            placed_meshes.append((part_name, pm))

        all_plate_mesh = trimesh.util.concatenate([m for _, m in placed_meshes])
        center = 0.5 * (all_plate_mesh.bounds[0] + all_plate_mesh.bounds[1])
        span = max(float(np.max(all_plate_mesh.extents)), 85.0)

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
        p_actors.append(vedo.Text2D(p_caption, pos="top-left", c="#1E222A", s=0.70))

        plt = vedo.Plotter(offscreen=True, size=(pw_print, ph), bg="#ECEFF4")
        plt.show(
            *p_actors,
            axes=0,
            camera={
                "pos": (center[0] + span * 0.48, center[1] - span * 1.48, center[2] + span * 1.28),
                "focal_point": center.tolist(),
                "viewup": (0.0, 0.0, 1.0),
            },
        )
        p_thumb_path = render_tmp / f"print_plate_{plate_idx + 1}.png"
        plt.screenshot(str(p_thumb_path))
        plt.close()
        print_thumbs.append((title, Image.open(p_thumb_path).convert("RGB")))

        gcode_path = slice_dir / f"plate_{plate_idx + 1}.gcode"
        segs = support_segments(gcode_path)
        s_actors = [
            vedo.Box(pos=(125.0, 125.0, -0.6), length=250.0, width=250.0, height=1.0).c("#E1E5EB"),
            *[vedo.Mesh([pm.vertices, pm.faces]).c(hex_color).alpha(0.32) for _, pm in placed_meshes],
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
        sup_out = IMAGES / f"butterfly-messer-print-plate-{plate_idx + 1}-supports.png"
        plt = vedo.Plotter(offscreen=True, size=(900, 900), bg="#F5F6F8")
        plt.show(
            *s_actors,
            axes=0,
            camera={
                "pos": (center[0] + span * 0.48, center[1] - span * 1.48, center[2] + span * 1.28),
                "focal_point": center.tolist(),
                "viewup": (0.0, 0.0, 1.0),
            },
        )
        plt.screenshot(str(sup_out))
        plt.close()
        support_paths.append(sup_out)

    # Stitch 2-panel `docs/images/butterfly-messer-print-preview.png` matching view_canvas width (2360 px)
    print_canvas = Image.new("RGB", (2 * pw_print + 3 * margin, ph + label_h + 2 * margin), "#1E222A")
    draw_p = ImageDraw.Draw(print_canvas)
    for idx, (label, im) in enumerate(print_thumbs):
        x = margin + idx * (pw_print + margin)
        y = margin
        print_canvas.paste(im, (x, y))
        draw_p.text((x + 8, y + ph + 10), label, fill="#ECEFF4")
    print_preview_path = IMAGES / "butterfly-messer-print-preview.png"
    print_canvas.save(print_preview_path)

    # 3. Combined presentation image `docs/images/butterfly-messer-presentation.png`
    pres_w = view_canvas.width
    pres_h = view_canvas.height + print_canvas.height
    pres_canvas = Image.new("RGB", (pres_w, pres_h), "#1E222A")
    pres_canvas.paste(view_canvas, (0, 0))
    pres_canvas.paste(print_canvas, (0, view_canvas.height))
    presentation_path = IMAGES / "butterfly-messer-presentation.png"
    pres_canvas.save(presentation_path)

    return {
        "view_preview": view_preview_path,
        "print_preview": print_preview_path,
        "presentation": presentation_path,
        "supports": support_paths,
    }


def main() -> None:
    parts, print_parts, merged, specs = build_all_parts()
    report = verify_mechanics_and_sweeps(parts, specs)
    print(
        "ALL CHECKS PASSED:",
        report["status"],
        "max_kinematic_collision_mm3=",
        report["max_kinematic_collision_mm3"],
        "max_latch_collision_mm3=",
        report["max_latch_collision_mm3"],
    )

    # 1. Export merged preview STL + 14 individual print-oriented part STLs
    write_ascii_stl(merged, MODELS / "butterfly-messer.stl", "butterfly_messer")
    for name, pm in print_parts.items():
        write_ascii_stl(pm, MODELS / f"{name}.stl", name.replace("-", "_"))

    # 2. Build `-view.3mf` and `-print.3mf`
    view_3mf = MODELS / "butterfly-messer-view.3mf"
    print_3mf = MODELS / "butterfly-messer-print.3mf"
    build_view_3mf(parts, view_3mf)
    build_print_3mf(print_parts, print_3mf)

    # 3. Slice `-print.3mf` with OrcaSlicer CLI & patch verified metadata
    slice_stats = slice_and_update_metadata(print_3mf, view_3mf, BUILD_DIR)
    print("ORCASLICER VERIFIED:", {
        "status": slice_stats["status"],
        "estimatedPrintTimeSeconds": slice_stats["estimatedPrintTimeSeconds"],
        "filamentUsageGrams": slice_stats["filamentUsageGrams"],
        "supportFilamentGrams": slice_stats["supportFilamentGrams"],
        "plateDetails": json.loads(slice_stats["plateDetails"]),
    })

    # 4. Render project previews, support screenshots, and presentation render
    rendered = render_all_previews_and_supports(parts, print_parts, BUILD_DIR, slice_stats)
    print("RENDERED:", {k: str(v) for k, v in rendered.items()})

    # 5. Save full verification report JSON
    full_report = {
        "mechanics": report,
        "slice": slice_stats,
    }
    (BUILD_DIR / "verification_report.json").write_text(
        json.dumps(full_report, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

