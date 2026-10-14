"""Generate the Chibi Hooded Skeleton Figurine (models/skelett_kapuzenfigur.stl).

Reconstructs the figurine from the reference video (calibrated via the 2 Euro coin,
Ø 25.75 mm, 2.20 mm thickness on z = 0) using a parametric volumetric SDF field
combined with a headless Blender 5.2 sculpting/smoothing/decimation roundtrip and
trimesh + manifold3d watertight export.

Coordinate system (center-origin on build plate):
  X: left (-) / right (+), centered at 0.0 mm (hood width ~28.6 mm)
  Y: front (-Y, face look direction) / back (+Y) (hood depth ~27.2 mm)
  Z: build plate (0.0 mm) to top of hood (58.7 mm)
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter
import trimesh
import vedo


REPO_ROOT = Path(__file__).resolve().parent.parent
STL_PATH = REPO_ROOT / "models" / "skelett_kapuzenfigur.stl"
BLEND_PATH = REPO_ROOT / "models" / "skelett_kapuzenfigur.blend"
BLENDER_EXE = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")

# Calibrated primary target dimensions (mm) from 2 Euro coin reference
TOTAL_HEIGHT_MM = 58.70
HOOD_WIDTH_MM = 28.60
HOOD_DEPTH_MM = 27.20
SHOE_BASE_WIDTH_MM = 18.68


def smin(a: np.ndarray, b: np.ndarray, k: float) -> np.ndarray:
    """Polynomial smooth minimum (smooth union) with blending radius k (mm)."""
    if k <= 1e-6:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1.0 - h) + a * h - k * h * (1.0 - h)


def smax(a: np.ndarray, b: np.ndarray, k: float) -> np.ndarray:
    """Polynomial smooth maximum (smooth intersection / subtraction)."""
    return -smin(-a, -b, k)


def sd_sphere(X: np.ndarray, Y: np.ndarray, Z: np.ndarray, cx: float, cy: float, cz: float, r: float) -> np.ndarray:
    return np.sqrt((X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2) - r


def sd_ellipsoid(
    X: np.ndarray, Y: np.ndarray, Z: np.ndarray,
    cx: float, cy: float, cz: float,
    rx: float, ry: float, rz: float,
) -> np.ndarray:
    """Approximate signed distance to an axis-aligned ellipsoid in mm."""
    dx = (X - cx) / rx
    dy = (Y - cy) / ry
    dz = (Z - cz) / rz
    k0 = np.sqrt(dx * dx + dy * dy + dz * dz + 1e-12)
    k1 = np.sqrt((dx / rx) ** 2 + (dy / ry) ** 2 + (dz / rz) ** 2 + 1e-12)
    return k0 * (k0 - 1.0) / k1


def sd_capsule(
    X: np.ndarray, Y: np.ndarray, Z: np.ndarray,
    ax: float, ay: float, az: float,
    bx: float, by: float, bz: float,
    ra: float, rb: float | None = None,
) -> np.ndarray:
    """Signed distance to a capsule (or linearly tapered capsule) between A and B."""
    pax = X - ax
    pay = Y - ay
    paz = Z - az
    bax = bx - ax
    bay = by - ay
    baz = bz - az
    b2 = bax * bax + bay * bay + baz * baz + 1e-12
    h = np.clip((pax * bax + pay * bay + paz * baz) / b2, 0.0, 1.0)
    dist = np.sqrt((pax - bax * h) ** 2 + (pay - bay * h) ** 2 + (paz - baz * h) ** 2 + 1e-12)
    if rb is None:
        return dist - ra
    return dist - (ra + (rb - ra) * h)


def sd_polyline_capsules(
    X: np.ndarray, Y: np.ndarray, Z: np.ndarray,
    points: list[tuple[float, float, float, float]],
    k_blend: float = 0.4,
) -> np.ndarray:
    """Signed distance to a smooth chain of tapered capsules through (x, y, z, r) nodes."""
    d = None
    for i in range(len(points) - 1):
        ax, ay, az, ra = points[i]
        bx, by, bz, rb = points[i + 1]
        seg = sd_capsule(X, Y, Z, ax, ay, az, bx, by, bz, ra, rb)
        d = seg if d is None else smin(d, seg, k_blend)
    return d


def build_sdf_volume(pitch: float = 0.18) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate the complete signed distance field of the hooded skeleton figurine."""
    xs = np.arange(-15.6, 15.6 + pitch * 0.5, pitch, dtype=np.float32)
    ys = np.arange(-15.0, 15.0 + pitch * 0.5, pitch, dtype=np.float32)
    zs = np.arange(-0.6, 60.0 + pitch * 0.5, pitch, dtype=np.float32)
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")

    # Symmetry coordinate for bilateral body parts
    AX = np.abs(X)

    # =========================================================================
    # 1. SNEAKERS / SHOES (Z = 0.0 .. 5.6 mm, outer width = 18.68 mm)
    # =========================================================================
    yaw = math.radians(7.0)
    cos_y, sin_y = math.cos(yaw), math.sin(yaw)
    sx0 = 4.95
    sy0 = -0.40
    dx_s = AX - sx0
    dy_s = Y - sy0
    sx = dx_s * cos_y + dy_s * sin_y
    sy = -dx_s * sin_y + dy_s * cos_y

    # Chunky sneaker footprint (rounded forefoot at sy = -8.3, heel at sy = +7.9)
    shoe_rx = np.clip(3.95 - 0.035 * sy, 3.45, 4.20)
    shoe_ry = 8.10
    qx = np.maximum(np.abs(sx) - (shoe_rx - 2.80), 0.0)
    qy = np.maximum(np.abs(sy + 0.15) - (shoe_ry - 3.65), 0.0)
    d_shoe_2d = np.sqrt(qx * qx + qy * qy + 1e-12) - 2.95

    shoe_top_z = 4.45 + 1.15 * np.tanh((sy + 2.4) * 0.38) - 0.09 * (sx * sx)
    d_shoe = smax(d_shoe_2d, Z - shoe_top_z, 1.25)
    d_shoe = smax(d_shoe, -Z, 0.12)

    shoe_surf_mask = np.exp(-((d_shoe_2d) / 1.0) ** 2) * (Z >= 0.0) * (Z < 5.6)
    sole_bulge = 0.28 * np.exp(-((Z - 0.90) / 0.62) ** 2) * shoe_surf_mask
    sole_groove = 0.46 * np.exp(-((Z - 1.90) / 0.26) ** 2) * shoe_surf_mask
    toecap_seam = 0.34 * np.exp(-((sy + 4.20) / 0.30) ** 2) * (Z > 1.8) * (Z < 4.7) * shoe_surf_mask
    lace_1 = 0.34 * np.exp(-((sy + 2.9) / 0.38) ** 2) * np.exp(-((sx) / 1.7) ** 2) * np.exp(-((Z - 4.25) / 0.55) ** 2)
    lace_2 = 0.34 * np.exp(-((sy + 1.6) / 0.38) ** 2) * np.exp(-((sx) / 1.7) ** 2) * np.exp(-((Z - 4.75) / 0.55) ** 2)
    d_shoe = d_shoe - sole_bulge + sole_groove + toecap_seam - lace_1 - lace_2

    # =========================================================================
    # 2. BAGGY PANTS (Z = 4.2 .. 16.5 mm, two naturally separate cylindrical legs)
    # =========================================================================
    d_leg_core = sd_capsule(AX, Y, Z, 4.80, 0.15, 4.5, 4.65, 0.30, 15.8, 3.75, 3.85)
    d_leg_front = sd_capsule(AX, Y, Z, 4.75, -1.35, 4.9, 4.60, -0.95, 15.2, 3.15, 3.30)
    d_leg_back = sd_capsule(AX, Y, Z, 4.75, 1.65, 4.9, 4.60, 1.75, 15.2, 3.25, 3.45)
    d_pants = smin(d_leg_core, smin(d_leg_front, d_leg_back, 0.95), 0.95)

    # Stacked horizontal/diagonal baggy cloth folds on pants
    pant_surf = np.exp(-((d_pants) / 1.4) ** 2) * np.clip((Z - 4.5) / 1.0, 0.0, 1.0) * np.clip((15.2 - Z) / 1.0, 0.0, 1.0)
    fold_phase = (Z - 5.5 + 0.15 * Y - 0.12 * (AX - 4.75)) * (2.0 * math.pi / 2.95)
    pant_puff = 0.36 * np.maximum(np.cos(fold_phase), 0.0) * pant_surf
    pant_crease = 0.52 * (np.maximum(-np.cos(fold_phase), 0.0) ** 2) * pant_surf
    d_pants = d_pants - pant_puff + pant_crease

    # Join pelvis above Z = 14.5 mm
    d_pelvis = sd_ellipsoid(X, Y, Z, 0.0, 0.35, 16.6, 8.2, 6.2, 2.2)
    d_pants = smin(d_pants, d_pelvis, 0.85)

    pant_cuff_groove = 0.48 * np.exp(-((Z - (4.35 - 0.10 * Y)) / 0.28) ** 2) * np.exp(-((d_pants) / 1.2) ** 2)
    d_lower = smin(d_shoe, d_pants, 0.32) + pant_cuff_groove

    # =========================================================================
    # 3. TORSO / PUFFER HOODIE JACKET & ARMS IN POCKETS (Z = 15.2 .. 29.0 mm)
    # =========================================================================
    d_torso_core = sd_capsule(X, Y, Z, 0.0, 0.45, 16.6, 0.0, 0.75, 27.6, 7.50, 7.90)
    d_torso_sides = sd_capsule(AX, Y, Z, 4.35, 0.30, 16.8, 4.75, 0.50, 26.8, 4.75, 4.95)
    d_torso = smin(d_torso_core, d_torso_sides, 1.4)

    d_pouch = sd_ellipsoid(X, Y, Z, 0.0, -3.25, 20.4, 8.10, 5.35, 4.40)
    d_torso = smin(d_torso, d_pouch, 1.2)

    # Ribbed bottom waistband hem (Z = 15.3 .. 17.8 mm, width = 19.1 mm, 45-deg self-supporting bottom transition)
    d_hem_ring = sd_ellipsoid(X, Y, Z, 0.0, 0.15, 16.55, 9.45, 7.55, 1.85)
    hem_top_crease = 0.42 * np.exp(-((Z - 17.85) / 0.28) ** 2) * np.exp(-((d_torso) / 1.2) ** 2) * (AX > 1.5)
    hem_angle = np.arctan2(Y, X + 1e-6)
    hem_surf = np.exp(-((d_hem_ring) / 1.0) ** 2) * np.exp(-((Z - 16.55) / 0.95) ** 2) * (AX > 1.6)
    hem_ribs = 0.20 * np.sin(32.0 * hem_angle) * hem_surf
    d_torso = smin(d_torso, d_hem_ring - hem_ribs, 0.65) + hem_top_crease

    # Arms: curved chain from shoulder -> elbow -> pocket
    d_arm = sd_polyline_capsules(
        AX, Y, Z,
        [
            (7.10, 0.55, 26.8, 3.00),
            (8.45, -0.10, 24.2, 2.65),
            (9.15, -0.65, 21.8, 2.35),
            (7.40, -3.60, 20.5, 2.25),
            (4.85, -6.25, 19.5, 2.05),
        ],
        k_blend=0.65,
    )

    # 3 crisp diagonal cloth creases at the crook of the elbow (Z = 20.2 .. 25.0 mm)
    sleeve_surf = (
        np.exp(-((d_arm) / 1.2) ** 2)
        * np.exp(-((AX - 8.8) / 2.6) ** 2)
        * np.exp(-((Z - 22.4) / 2.8) ** 2)
        * np.exp(-((Y + 1.8) / 3.8) ** 2)
    )
    sleeve_phase = (Z - 20.2 - 0.40 * Y + 0.20 * (AX - 8.5)) * (2.0 * math.pi / 1.95)
    sleeve_puff = 0.30 * np.maximum(np.cos(sleeve_phase), 0.0) * sleeve_surf
    sleeve_crease = 0.55 * (np.maximum(-np.cos(sleeve_phase), 0.0) ** 2) * sleeve_surf
    d_arm = d_arm - sleeve_puff + sleeve_crease

    d_jacket = smin(d_torso, d_arm, 0.65)
    jacket_surf = np.exp(-((d_jacket) / 1.3) ** 2)

    # Diagonal pocket entry groove + raised pocket welt lip
    pocket_plane = (AX - 4.70) * 0.78 + (Y + 6.15) * 0.45 + (Z - 19.8) * 0.42
    pocket_region = (
        jacket_surf
        * np.exp(-((AX - 4.9) / 1.8) ** 2)
        * np.exp(-((Z - 19.8) / 2.3) ** 2)
        * (Y < -4.2)
    )
    pocket_groove = 1.05 * np.exp(-(pocket_plane / 0.32) ** 2) * pocket_region
    pocket_welt = 0.50 * np.exp(-((pocket_plane + 0.55) / 0.42) ** 2) * pocket_region
    armpit_crease = (
        0.75
        * jacket_surf
        * np.exp(-((AX - 7.25) / 0.45) ** 2)
        * np.exp(-((Z - 23.6) / 2.2) ** 2)
        * (Y < -2.2)
    )
    d_jacket = d_jacket + pocket_groove - pocket_welt + armpit_crease

    # Open front zipper channel down the center of the jacket (X = 0, Y < -5.2, Z = 15.1 .. 28.2)
    d_zipper_slot = sd_capsule(X, Y, Z, 0.0, -8.50, 15.40, 0.0, -7.80, 28.00, 0.72, 0.65)
    d_jacket = smax(d_jacket, -d_zipper_slot, 0.18)
    front_mask = jacket_surf * (Y < -5.0) * np.clip((Z - 15.2) / 0.4, 0.0, 1.0) * np.clip((28.0 - Z) / 0.6, 0.0, 1.0)
    lapel_ridge = 0.46 * np.exp(-((AX - 1.35) / 0.40) ** 2) * front_mask
    d_jacket = d_jacket - lapel_ridge

    # Secondary draped lower hood / collar fold on the upper back (Z = 27.6 .. 34.5 mm, Y > +3.5 mm)
    d_back_collar = sd_ellipsoid(X, Y, Z, 0.0, 5.55, 31.20, 10.20, 6.30, 3.40)
    back_collar_surf = np.exp(-((d_back_collar) / 1.3) ** 2) * (Y > 7.5)
    back_collar_dip = 0.45 * np.exp(-((X / 2.6) ** 2)) * np.exp(-((Z - 31.0) / 2.0) ** 2) * back_collar_surf
    d_jacket = smin(d_jacket, d_back_collar + back_collar_dip, 0.65)

    # Clean separation slot between the two shoes and inner pant legs (Z = 0.0 .. 12.8 mm)
    d_leg_gap = sd_capsule(X, Y, Z, 0.0, -4.50, 0.80, 0.0, -1.50, 12.20, 0.62, 0.58)
    d_leg_gap_sole = sd_capsule(X, Y, Z, 0.0, -9.50, 0.40, 0.0, 4.50, 0.40, 0.62, 0.58)
    d_lower = smax(d_lower, -np.minimum(d_leg_gap, d_leg_gap_sole), 0.16)

    jacket_bottom_crease = 0.62 * np.exp(-((Z - 15.25) / 0.28) ** 2) * np.exp(-((d_pants) / 1.2) ** 2)
    d_body = smin(d_lower + jacket_bottom_crease, d_jacket, 0.30)

    # =========================================================================
    # 4. OVERSIZED HOOD & ROLLED CUFF TUBE (Z = 27.1 .. 58.7 mm, W = 28.6, D = 27.2)
    # =========================================================================
    # Main rear/upper hood dome + forward hood barrel + 45-deg self-supporting lower collar transition
    d_hood_dome = sd_ellipsoid(X, Y, Z, 0.0, 0.90, 43.40, 14.30, 12.70, 15.30)
    d_hood_barrel = sd_ellipsoid(X, Y, Z, 0.0, -3.50, 41.40, 13.30, 7.50, 13.40)
    d_hood_neck_cone = sd_capsule(X * 0.82, Y * 0.92, Z, 0.0, -0.40, 22.00, 0.0, 0.40, 35.50, 6.20, 11.40)
    d_hood_base = smin(smin(d_hood_dome, d_hood_barrel, 1.80), d_hood_neck_cone, 1.80)

    # Rolled front hood cuff built as a continuous 3D tube framing the face opening:
    d_cuff_tube = sd_polyline_capsules(
        AX, Y, Z,
        [
            (0.00, -8.00, 27.60, 2.20),
            (3.70, -8.55, 28.35, 2.40),
            (7.65, -9.25, 31.00, 2.65),
            (10.60, -9.65, 35.60, 2.80),
            (11.35, -9.80, 41.20, 2.85),
            (10.35, -9.70, 46.60, 2.80),
            (7.20, -9.55, 50.65, 2.70),
            (3.25, -9.40, 52.90, 2.60),
            (0.00, -9.25, 54.00, 2.50),
        ],
        k_blend=0.80,
    )

    d_hood_outer = smin(d_hood_base, d_cuff_tube, 0.90)
    hood_surf = np.exp(-((d_hood_outer) / 1.4) ** 2)

    # Crisp fold crease right behind the rolled cuff tube (at Y ≈ -6.5 mm)
    cuff_back_crease = (
        0.72
        * np.exp(-((d_cuff_tube - 0.15) / 0.50) ** 2)
        * np.exp(-((Y + 6.55) / 0.90) ** 2)
        * (Z > 28.5)
        * hood_surf
    )
    # Chin V-seam notch at bottom center of the hood cuff (X = 0, Z = 27.2 .. 30.0)
    chin_v_notch = (
        0.78
        * hood_surf
        * np.exp(-((AX / 0.42) ** 2))
        * np.exp(-((Z - 28.0) / 1.5) ** 2)
        * (Y < -6.2)
    )
    d_hood_outer = d_hood_outer + cuff_back_crease + chin_v_notch

    # Deep interior hood opening recess with a 45-deg gothic pointed ceiling so it prints cleanly!
    cav_z_center = 40.55 + 0.85 * np.exp(-((AX / 2.6) ** 1.5))
    cav_rx = np.clip(9.80 - 0.12 * np.maximum(0.0, 35.5 - Z) - 0.06 * np.maximum(0.0, Z - 45.5), 5.4, 9.85)
    d_hood_cavity = sd_ellipsoid(X, Y, Z, 0.0, -9.80, cav_z_center, cav_rx, 5.40, 11.15)
    d_gothic_roof = (Z - (51.80 - 0.82 * AX - 0.45 * np.maximum(0.0, Y + 9.20))) * 0.707
    d_hood_cavity = smax(d_hood_cavity, d_gothic_roof, 0.40)
    d_hood_shell = smax(d_hood_outer, -d_hood_cavity, 0.28)

    # =========================================================================
    # 5. CHIBI SKULL HEAD INSIDE THE HOOD (Z = 29.0 .. 49.4 mm, Y = -11.0 .. -1.0)
    # =========================================================================
    # Full, expressive chibi cranium + cheekbones + rounded jaw projecting to Y = -10.9 mm
    d_cranium = sd_ellipsoid(X, Y, Z, 0.0, -4.35, 41.55, 8.55, 6.65, 7.75)
    d_cheek = sd_ellipsoid(AX, Y, Z, 5.35, -7.85, 35.50, 3.05, 3.05, 2.65)
    d_jaw = sd_ellipsoid(X, Y, Z, 0.0, -6.65, 32.30, 5.80, 4.45, 3.65)
    d_skull = smin(d_cranium, smin(d_cheek, d_jaw, 1.00), 1.10)

    # Sub-cheek hollow (inward contour on the sides of the lower jaw at X = ±5.9, Z = 32.2)
    jaw_hollow = (
        0.65
        * np.exp(-((AX - 5.9) / 1.20) ** 2)
        * np.exp(-((Z - 32.2) / 1.80) ** 2)
        * np.exp(-((Y + 8.0) / 2.0) ** 2)
    )
    d_skull = d_skull + jaw_hollow

    # --- 5a. Large Tilted Oval Eye Sockets (deep crisp recessed cavities!) ---
    eye_tilt = math.radians(11.0)
    ce, se = math.cos(eye_tilt), math.sin(eye_tilt)
    ex0, ez0 = 3.95, 37.75
    dex = AX - ex0
    dez = Z - ez0
    ex_rot = dex * ce - dez * se
    ez_rot = dex * se + dez * ce
    d_eye_socket = sd_ellipsoid(ex_rot, Y, ez_rot, 0.0, -10.85, 0.0, 3.05, 3.10, 2.55)
    d_skull = smax(d_skull, -d_eye_socket, 0.18)

    # --- 5b. Triangular / Piriform Nasal Aperture (deep crisp recessed cavity!) ---
    nz = Z - 35.15
    nose_half_w = np.clip(0.92 - 0.36 * nz, 0.16, 1.52)
    d_nose_x = AX - nose_half_w
    d_nose_z = np.abs(nz) - 1.42
    d_nose_2d = np.sqrt(np.maximum(d_nose_x + 0.22, 0.0) ** 2 + np.maximum(d_nose_z + 0.22, 0.0) ** 2) - 0.22
    d_nose = smax(d_nose_2d, np.abs(Y + 10.85) - 2.40, 0.16)
    d_skull = smax(d_skull, -d_nose, 0.16)

    # --- 5c. Forehead Vertical Crack / Cranial Suture (2D zig-zag extruded in Y into forehead!) ---
    Y_ZERO = np.zeros_like(Y)
    d_suture_2d = sd_polyline_capsules(
        X, Y_ZERO, Z,
        [
            (-0.10, 0.0, 48.80, 0.28),
            (0.48, 0.0, 46.90, 0.28),
            (-0.24, 0.0, 45.05, 0.28),
            (0.38, 0.0, 43.30, 0.26),
            (0.05, 0.0, 41.45, 0.22),
        ],
        k_blend=0.08,
    )
    d_suture_branch_2d = sd_capsule(X, Y_ZERO, Z, -0.24, 0.0, 45.05, -1.55, 0.0, 43.90, 0.24, 0.18)
    d_suture_xz = np.minimum(d_suture_2d, d_suture_branch_2d)
    d_suture = smax(d_suture_xz, np.abs(Y + 10.65) - 1.65, 0.12)
    d_skull = smax(d_skull, -d_suture, 0.12)

    # --- 5d. Stitched / Toothed Grin (2D smile curve + 7 vertical stitch bars extruded into jaw!) ---
    smile_z = 31.05 + 0.062 * (X ** 2)
    d_smile_2d = np.maximum(np.abs(Z - smile_z) - 0.26, AX - 4.75)
    # 7 vertical stitch bars at X = 0.0, ±1.40, ±2.80, ±4.15 mm
    d_st_x = np.minimum(
        np.minimum(AX, np.abs(AX - 1.40)),
        np.minimum(np.abs(AX - 2.80), np.abs(AX - 4.15)),
    ) - 0.24
    d_st_z = np.abs(Z - smile_z) - 0.98
    d_stitches_2d = np.maximum(d_st_x, d_st_z)
    d_mouth_xz = np.minimum(d_smile_2d, d_stitches_2d)
    # Depth follows jaw curvature: deeper at center (Y = -9.3), curving back at sides
    jaw_cut_y_back = -9.15 + 0.075 * (X ** 2)
    d_mouth_3d = smax(d_mouth_xz, Y - jaw_cut_y_back, 0.12)
    d_skull = smax(d_skull, -d_mouth_3d, 0.12)

    # Combine hood shell and skull with crisp recess (0.12 mm)
    d_head_hood = smin(d_hood_shell, d_skull, 0.12)
    d_total = smin(d_body, d_head_hood, 0.32)

    # Enforce strict flat build-plate plane at Z = 0.0 mm
    d_total = smax(d_total, -Z, 0.08)

    return xs, ys, zs, d_total


def run_blender_roundtrip(raw_stl: Path, out_stl: Path, blend_path: Path) -> dict:
    """Run headless Blender 5.2 to smooth, sculpt-polish, decimate, and save .blend checkpoint."""
    blender_script = f"""
import bpy
import json
from pathlib import Path

bpy.ops.wm.read_factory_settings(use_empty=True)

raw_stl = r"{raw_stl}"
out_stl = r"{out_stl}"
blend_path = r"{blend_path}"

bpy.ops.wm.stl_import(filepath=raw_stl)
obj = bpy.context.selected_objects[0]
obj.name = "Skelett_Kapuzenfigur"
bpy.context.view_layer.objects.active = obj

# Save initial checkpoint before modifiers
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

# 1. Corrective Smooth modifier to polish voxel staircase while preserving crisp crevices
mod_smooth = obj.modifiers.new(name="PolishSmooth", type='CORRECTIVE_SMOOTH')
mod_smooth.factor = 0.35
mod_smooth.iterations = 3
mod_smooth.smooth_type = 'LENGTH_WEIGHTED'
mod_smooth.use_only_smooth = True

# 2. Decimate modifier to produce a clean, lightweight high-detail mesh (~85k faces)
mod_dec = obj.modifiers.new(name="CleanDecimate", type='DECIMATE')
mod_dec.decimate_type = 'COLLAPSE'
mod_dec.ratio = 0.18
mod_dec.use_collapse_triangulate = True

bpy.ops.object.modifier_apply(modifier=mod_smooth.name)
bpy.ops.object.modifier_apply(modifier=mod_dec.name)

# Ensure shade smooth for .blend presentation
bpy.ops.object.shade_smooth()

# Save final .blend source artifact
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

# Export processed STL
bpy.ops.wm.stl_export(filepath=out_stl, export_selected_objects=True, ascii_format=False)

info = {{
    "blender_version": bpy.app.version_string,
    "vertices": len(obj.data.vertices),
    "polygons": len(obj.data.polygons),
    "dimensions": list(obj.dimensions),
}}
print("BLENDER_INFO_JSON:" + json.dumps(info))
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write(blender_script)
        script_path = Path(tf.name)

    try:
        proc = subprocess.run(
            [str(BLENDER_EXE), "--background", "--python", str(script_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        info = {}
        for line in proc.stdout.splitlines():
            if line.startswith("BLENDER_INFO_JSON:"):
                info = json.loads(line.split("BLENDER_INFO_JSON:", 1)[1])
        return info
    finally:
        script_path.unlink(missing_ok=True)


def finalize_and_validate_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Flatten sole at Z=0, scale to exact calibrated bounds, repair, and export ASCII STL."""
    v = mesh.vertices.copy()

    # Flatten vertices within 0.22 mm of the bottom sole plane to exact Z = 0.000
    z_min = float(v[:, 2].min())
    v[:, 2] -= z_min
    sole_mask = v[:, 2] < 0.22
    v[sole_mask, 2] = 0.0

    # Center XY at (0, 0) and scale Z to exact 58.70 mm total height
    x_mid = 0.5 * (float(v[:, 0].min()) + float(v[:, 0].max()))
    y_mid = 0.5 * (float(v[:, 1].min()) + float(v[:, 1].max()))
    v[:, 0] -= x_mid
    v[:, 1] -= y_mid

    cur_h = float(v[:, 2].max())
    if cur_h > 1e-6:
        v[:, 2] *= TOTAL_HEIGHT_MM / cur_h

    mesh.vertices = np.round(v, 3)
    mesh.merge_vertices(digits_vertex=3)
    mesh.update_faces(mesh.unique_faces())
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    trimesh.repair.fix_normals(mesh)
    trimesh.repair.fix_winding(mesh)
    trimesh.repair.fill_holes(mesh)

    # Keep only the main connected component if any tiny disconnected island exists
    parts = mesh.split(only_watertight=False)
    if len(parts) > 1:
        parts.sort(key=lambda m: len(m.faces), reverse=True)
        mesh = parts[0]

    # Re-round to 3 decimals (0.001 mm) for clean ASCII STL output
    mesh.vertices = np.round(mesh.vertices, 3)
    mesh.merge_vertices(digits_vertex=3)
    mesh.update_faces(mesh.unique_faces())
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    return mesh


def main() -> int:
    print("1. Evaluating volumetric SDF field for Skelett-Kapuzenfigur...")
    pitch = 0.18
    xs, ys, zs, sdf = build_sdf_volume(pitch=pitch)
    # Slight sub-voxel smoothing for organic continuity
    sdf = gaussian_filter(sdf, sigma=0.32)
    # Pad outer boundary with positive values so isosurface is strictly closed
    sdf = np.pad(sdf, 1, mode="constant", constant_values=5.0)

    vol = vedo.Volume(
        sdf,
        spacing=(pitch, pitch, pitch),
        origin=(float(xs[0]) - pitch, float(ys[0]) - pitch, float(zs[0]) - pitch),
    )
    iso = vol.isosurface(0.0).triangulate()
    verts = np.asarray(iso.vertices, dtype=np.float64)
    faces = np.asarray(iso.cells, dtype=np.int64)

    raw_mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    trimesh.repair.fix_normals(raw_mesh)
    trimesh.repair.fix_winding(raw_mesh)
    print(f"   Raw marching-cubes mesh: {len(raw_mesh.faces)} faces, extents={np.round(raw_mesh.extents, 2)}")

    STL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_in = Path(tmpdir) / "raw_in.stl"
        tmp_out = Path(tmpdir) / "blender_out.stl"
        raw_mesh.export(tmp_in)

        if BLENDER_EXE.exists():
            print("2. Running headless Blender 5.2 sculpting/smoothing/decimation roundtrip...")
            binfo = run_blender_roundtrip(tmp_in, tmp_out, BLEND_PATH)
            print(f"   Blender roundtrip complete: {binfo}")
            mesh = trimesh.load_mesh(tmp_out, process=True)
        else:
            print("2. Blender not found; using raw mesh fallback...")
            mesh = raw_mesh

    print("3. Finalizing and validating watertight mesh...")
    mesh = finalize_and_validate_mesh(mesh)

    print(f"4. Writing ASCII STL to {STL_PATH} ...")
    stl_text = trimesh.exchange.stl.export_stl_ascii(mesh)
    STL_PATH.write_text(stl_text, encoding="utf-8")

    bmin, bmax = mesh.bounds
    print("=== Validation Summary ===")
    print(f"  File       : {STL_PATH}")
    print(f"  Facets     : {len(mesh.faces)}")
    print(f"  Vertices   : {len(mesh.vertices)}")
    print(f"  Bounds min : ({bmin[0]:.3f}, {bmin[1]:.3f}, {bmin[2]:.3f}) mm")
    print(f"  Bounds max : ({bmax[0]:.3f}, {bmax[1]:.3f}, {bmax[2]:.3f}) mm")
    print(f"  Extents    : ({mesh.extents[0]:.3f}, {mesh.extents[1]:.3f}, {mesh.extents[2]:.3f}) mm")
    print(f"  Watertight : {mesh.is_watertight}")
    print(f"  Winding ok : {mesh.is_winding_consistent}")
    print(f"  Volume     : {mesh.volume:.1f} mm^3")
    print(f"  Euler num  : {mesh.euler_number}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
