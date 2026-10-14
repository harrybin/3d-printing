"""Build the organic Toothless (Ohnezahn) dragon figure in Blender 5.2.

This script runs headlessly in Blender (`blender --background --python ...`)
to construct the organic character sculpture (`model-sources/drache/drache-master.blend`)
and export the raw organic mesh (`build/drache/raw_organic_dragon.stl`) before
Python (`scripts/drache.py`) cuts the exact keyed joints, eye sockets with
vertical slit-pupil pillars, red left tail-fin tenon/mortise, white skull
emblem inlay, and flat paw contact planes.

Coordinate system (mm, center-origin):
  +X : forward (toward snout)
  -X : backward (toward tail)
  +Y : dragon's left side (red prosthetic tail fin side)
  -Y : dragon's right side (black natural tail fin side)
  +Z : upward from build plate / ground plane (Z = 0)
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
BLEND_OUT = ROOT / "model-sources" / "drache" / "drache-master.blend"
RAW_STL_OUT = ROOT / "build" / "drache" / "raw_organic_dragon.stl"


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001  # millimeters


def create_sculpted_dragon_objects() -> bpy.types.Object:
    """Create the complete Night Fury organic anatomy using explicit millimeter-exact
    BMesh lofts, anatomical ellipsoids, and sculpted wing blades. Each shell is
    normalized in isolation and unioned cleanly before voxel-remeshing and smoothing."""
    parts_col = bpy.data.collections.new("DragonParts")
    bpy.context.scene.collection.children.link(parts_col)
    part_objs: list[bpy.types.Object] = []

    def commit_part_bmesh(bm_part: bmesh.types.BMesh, name: str) -> None:
        bmesh.ops.recalc_face_normals(bm_part, faces=bm_part.faces)
        mesh_data = bpy.data.meshes.new(name)
        bm_part.to_mesh(mesh_data)
        bm_part.free()
        obj = bpy.data.objects.new(name, mesh_data)
        parts_col.objects.link(obj)
        part_objs.append(obj)

    def add_lofted_spine(pts_r: list[tuple[float, float, float, float, float, float]], segs: int = 24, name: str = "spine"):
        """Loft a smooth closed tube through (x, y, z, rx, ry, rz) stations."""
        bm = bmesh.new()
        n_stations = len(pts_r)
        dense = []
        substeps = 4
        for i in range(n_stations - 1):
            p0 = np.array(pts_r[i], dtype=float)
            p1 = np.array(pts_r[i + 1], dtype=float)
            for s in range(substeps if i < n_stations - 2 else substeps + 1):
                t = s / substeps
                dense.append((1.0 - t) * p0 + t * p1)

        rings = []
        for idx, st in enumerate(dense):
            cx, cy, cz, rx, ry, rz = st
            center = Vector((cx, cy, cz))
            if idx == 0:
                tang = Vector(dense[1][:3]) - center
            elif idx == len(dense) - 1:
                tang = center - Vector(dense[-2][:3])
            else:
                tang = Vector(dense[idx + 1][:3]) - Vector(dense[idx - 1][:3])
            if tang.length < 1e-6:
                tang = Vector((1.0, 0.0, 0.0))
            tang.normalize()

            up_ref = Vector((0.0, 0.0, 1.0))
            lat = up_ref.cross(tang)
            if lat.length < 1e-4:
                lat = Vector((0.0, 1.0, 0.0))
            else:
                lat.normalize()
            norm = tang.cross(lat).normalized()

            ring = []
            for j in range(segs):
                ang = 2.0 * math.pi * j / segs
                ca, sa = math.cos(ang), math.sin(ang)
                offset = lat * (ry * ca) + norm * (rz * sa)
                ring.append(bm.verts.new(center + offset))
            rings.append((center, tang, rx, ry, rz, ring))

        for i in range(len(rings) - 1):
            r0 = rings[i][5]
            r1 = rings[i + 1][5]
            for j in range(segs):
                jn = (j + 1) % segs
                bm.faces.new((r0[j], r0[jn], r1[jn], r1[j]))

        c0, t0, rx0, ry0, rz0, ring0 = rings[0]
        cap0 = bm.verts.new(c0 - t0 * rx0)
        c1, t1, rx1, ry1, rz1, ring1 = rings[-1]
        cap1 = bm.verts.new(c1 + t1 * rx1)
        for j in range(segs):
            jn = (j + 1) % segs
            bm.faces.new((cap0, ring0[jn], ring0[j]))
            bm.faces.new((cap1, ring1[j], ring1[jn]))
        commit_part_bmesh(bm, name)

    def add_ellipsoid_mesh(center: tuple[float, float, float], radii: tuple[float, float, float], euler_deg: tuple[float, float, float] = (0.0, 0.0, 0.0), u_segs: int = 20, v_segs: int = 14, name: str = "ellipsoid"):
        bm = bmesh.new()
        cx, cy, cz = center
        rx, ry, rz = radii
        rot = Matrix.Identity(3)
        if any(euler_deg):
            from mathutils import Euler
            rot = Euler([math.radians(a) for a in euler_deg], "XYZ").to_matrix()

        c_vec = Vector((cx, cy, cz))
        top_v = bm.verts.new(c_vec + rot @ Vector((0.0, 0.0, rz)))
        bot_v = bm.verts.new(c_vec + rot @ Vector((0.0, 0.0, -rz)))

        rings = []
        for iv in range(1, v_segs):
            phi = math.pi * iv / v_segs
            sp, cp = math.sin(phi), math.cos(phi)
            ring = []
            for iu in range(u_segs):
                th = 2.0 * math.pi * iu / u_segs
                local_p = Vector((rx * sp * math.cos(th), ry * sp * math.sin(th), rz * cp))
                ring.append(bm.verts.new(c_vec + rot @ local_p))
            rings.append(ring)

        for iu in range(u_segs):
            iun = (iu + 1) % u_segs
            bm.faces.new((top_v, rings[0][iu], rings[0][iun]))
            bm.faces.new((bot_v, rings[-1][iun], rings[-1][iu]))

        for iv in range(len(rings) - 1):
            r0, r1 = rings[iv], rings[iv + 1]
            for iu in range(u_segs):
                iun = (iu + 1) % u_segs
                bm.faces.new((r0[iu], r1[iu], r1[iun], r0[iun]))
        commit_part_bmesh(bm, name)

    def add_tapered_limb(pts_r: list[tuple[float, float, float, float, float]], segs: int = 18, name: str = "limb"):
        """Loft a limb or horn through (x, y, z, r_lat, r_ant) stations with rounded end caps."""
        stations = [(x, y, z, 0.65 * (rl + ra), rl, ra) for x, y, z, rl, ra in pts_r]
        add_lofted_spine(stations, segs=segs, name=name)

    def add_tapered_tube(p0: Vector, p1: Vector, r0: float, r1: float, segs: int = 16, steps: int = 8, name: str = "tube"):
        direction = (p1 - p0)
        if direction.length < 1e-5:
            return
        bm = bmesh.new()
        z_ax = direction.normalized()
        up = Vector((1.0, 0.0, 0.0)) if abs(z_ax.z) > 0.9 else Vector((0.0, 0.0, 1.0))
        x_ax = up.cross(z_ax).normalized()
        y_ax = z_ax.cross(x_ax).normalized()

        rings = []
        for s in range(steps + 1):
            t = s / steps
            center = p0.lerp(p1, t)
            r = r0 + (r1 - r0) * t
            ring = []
            for i in range(segs):
                ang = 2.0 * math.pi * i / segs
                pt = center + r * (math.cos(ang) * x_ax + math.sin(ang) * y_ax)
                ring.append(bm.verts.new(pt))
            rings.append(ring)

        for s in range(steps):
            for i in range(segs):
                inext = (i + 1) % segs
                bm.faces.new((rings[s][i], rings[s][inext], rings[s + 1][inext], rings[s + 1][i]))

        c_bot = bm.verts.new(p0 - z_ax * (r0 * 0.45))
        c_top = bm.verts.new(p1 + z_ax * (r1 * 0.45))
        for i in range(segs):
            inext = (i + 1) % segs
            bm.faces.new((c_bot, rings[0][inext], rings[0][i]))
            bm.faces.new((c_top, rings[-1][i], rings[-1][inext]))
        commit_part_bmesh(bm, name)

    def add_wing_web_panel(origin: Vector, tip_a: Vector, tip_b: Vector, half_thick: float = 1.25, scallop_depth: float = 0.22, name: str = "web"):
        """Create a closed double-sided wing membrane sheet between two finger struts
        with a concave parabolic scallop along the trailing edge (tip_a -> tip_b)."""
        n_vec = (tip_a - origin).cross(tip_b - origin)
        if n_vec.length < 1e-5:
            return
        n_vec.normalize()
        bm = bmesh.new()
        nu, nv = 10, 10

        grid_pos = []
        grid_neg = []
        mid_dir = 0.5 * ((tip_a - origin) + (tip_b - origin))
        p_origin = origin - 0.08 * mid_dir
        for iu in range(nu + 1):
            u = 0.06 + 0.94 * (iu / nu)
            row_p, row_n = [], []
            for iv in range(nv + 1):
                v = iv / nv
                pull = 1.0 - scallop_depth * (u ** 1.5) * math.sin(v * math.pi)
                base_pt = p_origin.lerp(p_origin.lerp(tip_a, u).lerp(p_origin.lerp(tip_b, u), v), pull)
                th = half_thick * (1.0 - 0.18 * u)
                row_p.append(bm.verts.new(base_pt + n_vec * th))
                row_n.append(bm.verts.new(base_pt - n_vec * th))
            grid_pos.append(row_p)
            grid_neg.append(row_n)

        for iu in range(nu):
            for iv in range(nv):
                bm.faces.new((grid_pos[iu][iv], grid_pos[iu + 1][iv], grid_pos[iu + 1][iv + 1], grid_pos[iu][iv + 1]))
                bm.faces.new((grid_neg[iu][iv], grid_neg[iu][iv + 1], grid_neg[iu + 1][iv + 1], grid_neg[iu + 1][iv]))

        for iv in range(nv):
            bm.faces.new((grid_pos[0][iv], grid_pos[0][iv + 1], grid_neg[0][iv + 1], grid_neg[0][iv]))
            bm.faces.new((grid_pos[nu][iv], grid_neg[nu][iv], grid_neg[nu][iv + 1], grid_pos[nu][iv + 1]))
        for iu in range(nu):
            bm.faces.new((grid_pos[iu][0], grid_neg[iu][0], grid_neg[iu + 1][0], grid_pos[iu + 1][0]))
            bm.faces.new((grid_pos[iu][nv], grid_pos[iu + 1][nv], grid_neg[iu + 1][nv], grid_neg[iu][nv]))
        commit_part_bmesh(bm, name)

    # 1. CONTINUOUS HEAD -> NECK -> ARCHED TORSO -> S-CURVED RAISED TAIL SPINE
    main_spine = [
        # Tail tip down through S-curve to pelvis
        (-29.8,  0.6, 56.8, 1.9, 1.9, 1.9),   # Top of tail stem inside fluke hub
        (-30.6,  0.6, 53.0, 2.1, 2.1, 2.1),
        (-31.6,  0.6, 47.5, 2.4, 2.4, 2.4),
        (-33.0,  0.6, 41.5, 2.6, 2.7, 2.6),
        (-34.4,  0.5, 35.0, 2.9, 3.0, 2.9),
        (-35.0,  0.4, 28.5, 3.2, 3.4, 3.2),   # Rearmost bend of S-curve
        (-33.8,  0.3, 22.2, 3.6, 3.9, 3.6),
        (-30.8,  0.1, 17.5, 4.1, 4.5, 4.1),
        (-26.5,  0.0, 14.8, 4.7, 5.3, 4.6),
        (-21.5,  0.0, 14.2, 5.5, 6.3, 5.3),
        # Pelvis & Arched Torso
        (-16.0,  0.0, 15.2, 6.6, 7.8, 6.2),   # Pelvis / hips
        (-9.5,   0.0, 17.0, 7.6, 8.9, 7.0),   # Lower back
        (-2.0,   0.0, 18.2, 8.2, 9.5, 7.5),   # Mid-back arch
        (5.5,    0.0, 18.5, 8.5, 9.7, 7.6),   # Shoulders under wing saddle
        (12.5,  -0.2, 16.5, 7.7, 8.7, 6.9),   # Chest
        (18.5,  -0.4, 14.8, 6.1, 6.9, 5.6),   # Neck waist
        # Broad Flattened Night Fury Head (turned slightly right -Y, held low & prowling)
        (23.5,  -0.6, 15.2, 6.6, 11.4, 6.9),  # Back of cranium / jowls
        (28.5,  -0.8, 14.8, 6.6, 12.0, 6.5),  # Wide cheek / temple region
        (33.0,  -1.0, 13.5, 5.6, 10.0, 5.3),  # Eye / muzzle region
        (36.5,  -1.1, 12.0, 3.9, 7.0,  3.9),  # Snout
        (38.0,  -1.2, 11.2, 2.0, 3.9,  2.3),  # Rounded snout tip (reaches X ~ +39.5 mm)
    ]
    add_lofted_spine(main_spine, segs=28, name="main_spine")

    # Brow ridges & cheek fullness on the head
    for side in (-1.0, 1.0):
        add_ellipsoid_mesh((31.2, -0.9 + side * 6.2, 16.8), (4.2, 2.8, 2.2), euler_deg=(0, 12, -side * 15))
        add_ellipsoid_mesh((25.5, -0.7 + side * 9.8, 13.8), (4.8, 3.6, 3.4), euler_deg=(0, 8, -side * 10))

    # 2. EAR APPENDAGES (2 long, iconic Night Fury ear lobes swept back & up)
    for side in (-1.0, 1.0):
        ear_pts = [
            (22.8, -0.6 + side * 7.2, 18.2, 3.1, 2.4),
            (18.5, -0.5 + side * 9.2, 20.8, 2.9, 2.2),
            (13.8, -0.4 + side * 11.0, 23.4, 2.7, 2.0),
            (9.2,  -0.3 + side * 12.4, 25.6, 2.1, 1.6),
        ]
        add_tapered_limb(ear_pts, segs=18)

        # Upper cheek appendage
        add_tapered_limb([
            (22.2, -0.6 + side * 9.5, 15.2, 2.1, 1.7),
            (18.2, -0.5 + side * 12.2, 16.4, 1.8, 1.4),
            (14.6, -0.4 + side * 14.2, 17.5, 1.2, 1.0),
        ], segs=14)

        # Lower cheek appendage
        add_tapered_limb([
            (23.5, -0.6 + side * 9.2, 12.4, 1.7, 1.4),
            (19.8, -0.5 + side * 11.5, 12.4, 1.4, 1.2),
            (17.2, -0.4 + side * 12.8, 12.5, 1.0, 0.9),
        ], segs=12)

        # Small jaw nub
        add_tapered_limb([
            (25.5, -0.7 + side * 7.4, 10.6, 1.3, 1.1),
            (22.5, -0.6 + side * 9.2, 10.0, 0.9, 0.8),
        ], segs=10)

    # 3. FOUR MUSCULAR CROUCHING LEGS, PAWS & TOES
    # Front-Left Leg (+Y, stepping forward X=+21.5)
    add_ellipsoid_mesh((15.5, 8.8, 11.2), (5.0, 4.2, 5.2))
    add_tapered_limb([
        (12.5,  6.5, 15.5, 4.8, 5.2),
        (16.2, 10.2, 10.5, 4.2, 4.5),
        (19.2, 11.2,  5.5, 3.8, 4.0),
        (20.8, 10.8,  1.8, 4.2, 4.5),
    ], segs=18)
    add_ellipsoid_mesh((21.8, 10.8, 2.2), (5.2, 4.8, 2.4))
    for toe_angle in (-28, -9, 10, 28):
        rad = math.radians(toe_angle)
        add_ellipsoid_mesh((21.8 + 4.5 * math.cos(rad), 10.8 + 4.5 * math.sin(rad), 1.6), (2.2, 1.5, 1.5), euler_deg=(0, 0, toe_angle))

    # Front-Right Leg (-Y, planted under chest X=+14.0)
    add_ellipsoid_mesh((12.2, -8.8, 11.2), (5.0, 4.2, 5.2))
    add_tapered_limb([
        (10.8, -6.5, 15.5, 4.8, 5.2),
        (12.2, -10.5, 10.5, 4.2, 4.5),
        (13.5, -11.2,  5.5, 3.8, 4.0),
        (14.5, -10.8,  1.8, 4.2, 4.5),
    ], segs=18)
    add_ellipsoid_mesh((15.5, -10.8, 2.2), (5.2, 4.8, 2.4))
    for toe_angle in (-28, -9, 10, 28):
        rad = math.radians(toe_angle - 8)
        add_ellipsoid_mesh((15.5 + 4.5 * math.cos(rad), -10.8 + 4.5 * math.sin(rad), 1.6), (2.2, 1.5, 1.5), euler_deg=(0, 0, toe_angle - 8))

    # Hind-Left Leg (+Y, wide muscular haunch, outer span = 40.0 mm -> Y up to +19.8 mm)
    add_ellipsoid_mesh((-10.5, 9.8, 14.2), (6.4, 5.6, 6.0), euler_deg=(12, 0, 10))
    add_ellipsoid_mesh((-11.5, 12.2, 8.8), (5.2, 4.2, 5.5))
    add_tapered_limb([
        (-10.5,  9.8, 14.0, 5.2, 5.6),
        (-13.8, 14.2,  8.8, 4.5, 4.8),
        (-12.5, 14.5,  4.5, 4.0, 4.2),
        (-11.2, 14.2,  1.8, 4.4, 4.6),
    ], segs=18)
    add_ellipsoid_mesh((-10.2, 14.4, 2.2), (5.5, 5.0, 2.4))
    for toe_angle in (-24, -6, 12, 30):
        rad = math.radians(toe_angle + 12)
        add_ellipsoid_mesh((-10.2 + 4.7 * math.cos(rad), 14.4 + 4.7 * math.sin(rad), 1.6), (2.2, 1.5, 1.5), euler_deg=(0, 0, toe_angle + 12))

    # Hind-Right Leg (-Y, wide muscular haunch, outer span = 40.0 mm -> Y down to -19.8 mm)
    add_ellipsoid_mesh((-10.5, -9.8, 14.2), (6.4, 5.6, 6.0), euler_deg=(-12, 0, -10))
    add_ellipsoid_mesh((-11.5, -12.2, 8.8), (5.2, 4.2, 5.5))
    add_tapered_limb([
        (-10.5,  -9.8, 14.0, 5.2, 5.6),
        (-13.5, -14.2,  8.8, 4.5, 4.8),
        (-12.0, -14.5,  4.5, 4.0, 4.2),
        (-10.8, -14.2,  1.8, 4.4, 4.6),
    ], segs=18)
    add_ellipsoid_mesh((-9.8, -14.4, 2.2), (5.5, 5.0, 2.4))
    for toe_angle in (-30, -12, 6, 24):
        rad = math.radians(toe_angle - 12)
        add_ellipsoid_mesh((-9.8 + 4.7 * math.cos(rad), -14.4 + 4.7 * math.sin(rad), 1.6), (2.2, 1.5, 1.5), euler_deg=(0, 0, toe_angle - 12))

    # 4. SADDLE COLLAR, NECK RIDGES, 4 ENLARGED SPINE KNOBS & TAIL RIDGES
    for ang in range(-70, 71, 10):
        rad = math.radians(ang)
        sy = 9.4 * math.sin(rad)
        sz = 18.2 + 7.6 * math.cos(rad)
        add_ellipsoid_mesh((5.2, sy, sz), (3.4, 2.2, 1.8), euler_deg=(-ang, 0, 0))

    for x_nub, z_nub in [(21.0, 21.2), (17.2, 21.8), (13.2, 22.8), (9.2, 24.2)]:
        add_ellipsoid_mesh((x_nub, -0.2, z_nub), (1.6, 1.0, 1.8))

    large_knobs = [
        (-2.2,  0.0, 26.8, 2.3, 1.9, 3.2, -8),
        (-8.6,  0.0, 25.0, 2.3, 1.9, 3.2, -14),
        (-14.8, 0.0, 22.2, 2.2, 1.8, 3.0, -20),
        (-20.8, 0.0, 19.0, 2.1, 1.8, 2.8, -22),
    ]
    for kx, ky, kz, rx, ry, rz, pitch in large_knobs:
        add_ellipsoid_mesh((kx, ky, kz), (rx, ry, rz), euler_deg=(0, pitch, 0))

    tail_ridges = [
        (-26.0, 0.0, 18.2, 1.6, 1.1, 1.8, 10),
        (-29.5, 0.2, 21.2, 1.5, 1.0, 1.7, 35),
        (-31.8, 0.4, 26.0, 1.4, 1.0, 1.6, 65),
        (-32.2, 0.5, 32.0, 1.3, 0.9, 1.5, 85),
        (-31.2, 0.6, 38.2, 1.2, 0.9, 1.4, 100),
        (-29.8, 0.6, 44.5, 1.1, 0.8, 1.3, 105),
    ]
    for rx_p, ry_p, rz_p, sx, sy, sz, pitch in tail_ridges:
        add_ellipsoid_mesh((rx_p, ry_p, rz_p), (sx, sy, sz), euler_deg=(0, pitch, 0))

    scale_patches = [
        (-9.0, 14.8, 14.5), (-11.8, 15.2, 13.0), (-10.0, 14.6, 11.2), (-12.8, 14.8, 10.0),
        (-9.0, -14.8, 14.5), (-11.8, -15.2, 13.0), (-10.0, -14.6, 11.2), (-12.8, -14.8, 10.0),
        (15.5, 11.8, 12.2), (13.8, 11.6, 10.5), (16.5, 12.2, 9.2),
        (11.5, -11.4, 12.2), (10.2, -11.2, 10.5), (12.2, -11.8, 9.2),
    ]
    for sx, sy, sz in scale_patches:
        add_ellipsoid_mesh((sx, sy, sz), (1.3, 0.9, 1.1))

    # 5. PRIMARY & SECONDARY SCALLOPED WINGS
    for side in (-1.0, 1.0):
        p_root = Vector((5.2, side * 4.2, 20.0))
        p_elbow = Vector((6.5, side * 13.8, 35.0))
        p_wrist = Vector((5.8, side * 19.5, 47.0))
        p_claw = Vector((9.2, side * 20.2, 49.2))

        f_tip_1 = Vector((-1.0, side * 22.4, 50.5))
        f_tip_2 = Vector((-6.2, side * 20.5, 41.8))
        f_tip_3 = Vector((-7.8, side * 16.8, 33.0))
        f_base = Vector((-2.2, side * 6.2, 20.5))

        add_tapered_tube(p_root, p_elbow, 2.5, 2.0)
        add_tapered_tube(p_elbow, p_wrist, 2.0, 1.7)
        add_tapered_tube(p_wrist, p_claw, 1.35, 0.70)

        add_tapered_tube(p_wrist, f_tip_1, 1.65, 1.15)
        add_tapered_tube(p_wrist, f_tip_2, 1.60, 1.10)
        add_tapered_tube(p_elbow, f_tip_3, 1.60, 1.10)
        add_tapered_tube(p_root, f_base, 2.00, 1.40)

        # Outer web panels have concave scallops; interior bridging panels have 0 scallop so they seal tightly to struts
        add_wing_web_panel(p_wrist, f_tip_1, f_tip_2, half_thick=1.25, scallop_depth=0.22)
        add_wing_web_panel(p_elbow, p_wrist, f_tip_2, half_thick=1.30, scallop_depth=0.0)
        add_wing_web_panel(p_elbow, f_tip_2, f_tip_3, half_thick=1.30, scallop_depth=0.24)
        add_wing_web_panel(p_root, p_elbow, f_tip_3, half_thick=1.35, scallop_depth=0.0)
        add_wing_web_panel(p_root, f_tip_3, f_base, half_thick=1.35, scallop_depth=0.20)

        s_root = Vector((-4.2, side * 4.2, 18.8))
        s_top = Vector((-6.8, side * 17.8, 27.2))
        s_mid = Vector((-11.2, side * 16.2, 22.8))
        s_bot = Vector((-11.5, side * 6.8, 18.2))
        add_tapered_tube(s_root, s_top, 1.90, 1.15)
        add_tapered_tube(s_root, s_mid, 1.70, 1.10)
        add_tapered_tube(s_root, s_bot, 1.80, 1.25)
        add_wing_web_panel(s_root, s_top, s_mid, half_thick=1.25, scallop_depth=0.20)
        add_wing_web_panel(s_root, s_mid, s_bot, half_thick=1.25, scallop_depth=0.18)

    # Create a master object from part_objs[0] and Boolean-Union the rest of DragonParts collection
    master_obj = part_objs[0]
    bpy.context.scene.collection.objects.link(master_obj)
    parts_col.objects.unlink(master_obj)

    bpy.ops.object.select_all(action="DESELECT")
    master_obj.select_set(True)
    bpy.context.view_layer.objects.active = master_obj

    bool_mod = master_obj.modifiers.new(name="UnionAll", type="BOOLEAN")
    bool_mod.operation = "UNION"
    bool_mod.operand_type = "COLLECTION"
    bool_mod.collection = parts_col
    try:
        bool_mod.solver = "MANIFOLD"
    except Exception:
        bool_mod.solver = "EXACT"
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    # Remove the helper objects now that they are unioned into master_obj
    for o in part_objs[1:]:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(parts_col)

    master_obj.name = "organic_body_mesh"
    return master_obj


def main() -> None:
    reset_scene()
    body_obj = create_sculpted_dragon_objects()

    # Export multi-shell mesh before remeshing OR remesh after manifold boolean in Python?
    # Let's check: in Blender 5.2, VoxelRemesh on individually-normalized outward shells
    # works cleanly when normals are not inverted, AND we also save the raw shells or
    # apply VoxelRemesh + Smooth after a self-union!
    remesh = body_obj.modifiers.new(name="VoxelRemesh", type="REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = 0.40
    remesh.adaptivity = 0.0
    bpy.ops.object.modifier_apply(modifier=remesh.name)

    smooth = body_obj.modifiers.new(name="Smooth", type="SMOOTH")
    smooth.factor = 0.45
    smooth.iterations = 5
    bpy.ops.object.modifier_apply(modifier=smooth.name)

    decim = body_obj.modifiers.new(name="Decimate", type="DECIMATE")
    decim.decimate_type = "COLLAPSE"
    decim.ratio = 0.24
    bpy.ops.object.modifier_apply(modifier=decim.name)

    BLEND_OUT.parent.mkdir(parents=True, exist_ok=True)
    RAW_STL_OUT.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT))
    bpy.ops.wm.stl_export(filepath=str(RAW_STL_OUT), export_selected_objects=True)
    print(f"Saved Blender source: {BLEND_OUT}")
    print(f"Exported raw organic STL: {RAW_STL_OUT}")


if __name__ == "__main__":
    main()
