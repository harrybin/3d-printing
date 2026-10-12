"""Sculpt the gothic chest relief panels in Blender and cache them as height maps.

Run head-less and deterministically:

    "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" ^
        --background --python scripts\\blender_chest_reliefs.py

Why Blender instead of more Python primitives
---------------------------------------------
``gothic_chest.py`` used to stack rounded strokes and voxel-fuse them.  That
reads as flat ribbon graphics, not as a carved creature.  Here every motif is a
meta-ball sculpture: overlapping organic masses blend into each other with real
anatomical transitions, negative meta-balls hollow out eye sockets, nostrils and
tooth gaps, and a noise displacement adds bone/scale grain.  The result is then
flattened into a bas-relief the same way a real carver would: a height field
sampled straight down onto the sculpture.

Output contract
---------------
One ``assets/gothic-chest-reliefs/<panel>.npz`` per panel with

* ``heights``  - ``(ny, nx)`` float32, normalised to ``0.0 .. 1.0``
* ``x0 x1 y0 y1`` - panel extent in millimetres, panel-local
* ``pitch``    - sample spacing in millimetres

Heights are normalised, so the printable relief depth stays a parameter of
``gothic_chest.py`` and does not require a Blender re-run.  A height field is
also the single geometric property that makes the relief support free: after the
45 degree shear in ``gothic_chest.py`` no facet of a height field can overhang
by more than 45 degrees.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy  # type: ignore
import numpy as np
from mathutils import Quaternion, Vector  # type: ignore
from mathutils.bvhtree import BVHTree  # type: ignore

ROOT = Path(bpy.path.abspath("//")) if bpy.data.filepath else Path.cwd()
OUT_DIR = ROOT / "assets" / "gothic-chest-reliefs"
BLEND_DIR = ROOT / "build" / "blender"

META_RESOLUTION = 0.6      # meta-ball polygonisation step in mm
NOISE_STRENGTH = 0.55      # bone grain / scale texture amplitude in mm
NOISE_SCALE = 2.4          # texture feature size in mm
BORDER_FALLOFF = 5.0       # mm over which the panel ramps back into the wall
TONE_K = 2.2               # soft tone compression constant in mm
TONE_REF = 5.5             # sculpt height that maps to full relief depth


# --------------------------------------------------------------------------
# meta-ball element helpers.  Everything is expressed in panel-local
# millimetres: x across the wall, y upward, z out of the wall.
# --------------------------------------------------------------------------

class Sculpt:
    """Meta-ball masses plus hard boolean cutters for the deep hollows.

    Negative meta-balls only dent the field; eye sockets, nostrils and tooth
    gaps need to read as black holes in the relief, so they are cut with real
    boolean geometry after the meta-balls are polygonised.
    """

    def __init__(self, mball):
        self.mb = mball
        self.cuts: list[tuple[float, float, float, float, float, float]] = []

    def carve(self, x, y, r, z=0.0, scale=(1.0, 1.0, 1.0), rot_z=0.0):
        """Record a hollow as an ellipsoid cutter in panel-local millimetres.

        The cut is resolved on the extracted height field rather than with a
        Blender boolean: a cutter built from dozens of overlapping ellipsoids
        makes the EXACT solver flip inside/outside by parity, which previously
        deleted most of the relief (24k raw faces collapsed to 4k).  On a bas
        relief the two are equivalent anyway, because the relief *is* a height
        field, and the 2D form is deterministic and cheap.
        """
        floor = z - r * scale[2]
        self.cuts.append((x, y, max(r * scale[0], 1e-3),
                          max(r * scale[1], 1e-3), floor, rot_z))


def _element(mball, kind, centre, radius, size=(0.0, 0.0, 0.0),
             rot_z=0.0, negative=False, stiffness=2.0):
    el = mball.elements.new()
    el.type = kind
    el.co = Vector((centre[0], centre[1], centre[2]))
    el.radius = radius
    el.stiffness = stiffness
    el.size_x, el.size_y, el.size_z = size
    el.rotation = Quaternion((0.0, 0.0, 1.0), rot_z)
    el.use_negative = negative
    return el


def ball(sculpt, x, y, r, z=0.0, negative=False, stiffness=2.0):
    return _element(sculpt.mb, 'BALL', (x, y, z), r, negative=negative,
                    stiffness=stiffness)


def blob(sculpt, x, y, r, size, z=0.0, rot_z=0.0, negative=False,
         stiffness=2.0):
    return _element(sculpt.mb, 'ELLIPSOID', (x, y, z), r, size=size,
                    rot_z=rot_z, negative=negative, stiffness=stiffness)


def chain(sculpt, points, radii, z=0.0, stiffness=2.0):
    """Organic tube through ``points`` with a radius ramp.

    The sample spacing follows the local radius.  A fixed step count left wide
    gaps between meta-balls on long segments, which is why vines and scroll
    tails came out as dotted lines instead of continuous carved stems.
    """
    count = len(points)
    for i in range(count - 1):
        (x0, y0), (x1, y1) = points[i], points[i + 1]
        r0, r1 = radii[i], radii[i + 1]
        z0 = z[i] if isinstance(z, (list, tuple)) else z
        z1 = z[i + 1] if isinstance(z, (list, tuple)) else z
        length = math.hypot(x1 - x0, y1 - y0)
        steps = max(2, int(math.ceil(length / max(0.5 * min(r0, r1), 0.8))))
        for s in range(steps):
            t = s / steps
            ball(sculpt,
                 x0 + (x1 - x0) * t,
                 y0 + (y1 - y0) * t,
                 r0 + (r1 - r0) * t,
                 z=z0 + (z1 - z0) * t,
                 stiffness=stiffness)
    ball(sculpt, points[-1][0], points[-1][1], radii[-1],
         z=z[-1] if isinstance(z, (list, tuple)) else z, stiffness=stiffness)


def _sample_curve(fn, t0, t1, count):
    return [fn(t0 + (t1 - t0) * i / (count - 1)) for i in range(count)]


def membrane(sc, apex, tips, z=0.0, thick=1.5, scallop=0.12, rays=7):
    """Continuous webbed skin spanning a spar fan.

    Spacing a handful of discrete blobs between the spars made the wings read
    as dotted crab legs.  Filling the fan with interpolated radial chains gives
    a closed skin that still dips between the spars, which is what makes a bat
    or wyvern wing legible at relief depth.
    """
    for i in range(len(tips) - 1):
        a_tip, b_tip = tips[i], tips[i + 1]
        for k in range(1, rays + 1):
            u = k / (rays + 1)
            tx = a_tip[0] + (b_tip[0] - a_tip[0]) * u
            ty = a_tip[1] + (b_tip[1] - a_tip[1]) * u
            pull = 1.0 - scallop * math.sin(math.pi * u)
            end = (apex[0] + (tx - apex[0]) * pull,
                   apex[1] + (ty - apex[1]) * pull)
            chain(sc, [apex, end], [thick * 1.3, thick * 0.85], z=z)


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# motifs - every mass is a meta-ball, every hollow is a boolean cutter
# --------------------------------------------------------------------------

def skull(sc, cx, cy, s=1.0, z=0.0, tilt=0.0):
    """Leering skull: cranium, brow, zygomatic arches, maxilla, mandible.

    Eye sockets, nasal aperture, mouth slit and tooth gaps are boolean cuts.
    Negative meta-balls only dented the field and left the skull reading as a
    puffy ball; a real cut carves the socket down to the panel ground.
    """
    a = math.radians(tilt)

    def P(x, y):
        return (cx + (x * math.cos(a) - y * math.sin(a)) * s,
                cy + (x * math.sin(a) + y * math.cos(a)) * s)

    def r(v):
        return v * s

    cranium = P(0.0, 5.0)
    blob(sc, cranium[0], cranium[1], r(2.6), (r(5.0), r(4.2), r(1.1)),
         z=z, rot_z=a)
    occiput = P(0.0, 8.2)
    blob(sc, occiput[0], occiput[1], r(2.1), (r(3.4), r(1.0), r(0.6)), z=z,
         rot_z=a)
    brow = P(0.0, 0.9)
    blob(sc, brow[0], brow[1], r(1.7), (r(4.6), r(0.4), r(0.7)),
         z=z + r(0.7), rot_z=a)
    maxilla = P(0.0, -4.2)
    blob(sc, maxilla[0], maxilla[1], r(1.9), (r(2.9), r(0.6), r(0.4)),
         z=z + r(0.3), rot_z=a)
    mandible = P(0.0, -7.4)
    blob(sc, mandible[0], mandible[1], r(1.8), (r(2.8), r(0.4), r(0.3)),
         z=z, rot_z=a)

    for sx in (-1.0, 1.0):
        temple = P(sx * 5.3, 3.4)
        ball(sc, temple[0], temple[1], r(2.7), z=z - r(0.4))
        arch = [P(sx * 2.6, -1.4), P(sx * 5.4, 0.4), P(sx * 6.0, 3.0)]
        chain(sc, arch, [r(1.25), r(1.15), r(1.0)], z=z + r(0.5))
        cheek = P(sx * 4.4, -2.8)
        blob(sc, cheek[0], cheek[1], r(1.7), (r(1.2), r(0.7), r(0.4)),
             z=z + r(0.3), rot_z=a - math.radians(sx * 25.0))
        angle = P(sx * 4.4, -6.3)
        ball(sc, angle[0], angle[1], r(1.9), z=z - r(0.2))
        ramus = [P(sx * 4.4, -6.3), P(sx * 5.4, -3.2)]
        chain(sc, ramus, [r(1.5), r(1.0)], z=z - r(0.3))

    # hollows
    for sx in (-1.0, 1.0):
        eye = P(sx * 3.5, 1.2)
        # tilted ovals, floor just above the panel ground -> real black holes
        sc.carve(eye[0], eye[1], r(3.45), z=z + r(3.3),
                 scale=(1.0, 0.86, 1.0), rot_z=a - math.radians(sx * 12.0))
    for ny, nr, nsx, nz in ((-1.9, 0.62, 1.15, 0.95),
                            (-2.9, 1.05, 1.0, 1.35),
                            (-3.6, 0.78, 1.5, 1.1)):
        nose = P(0.0, ny)       # inverted-heart nasal aperture
        sc.carve(nose[0], nose[1], r(nr), z=z + r(nz),
                 scale=(nsx, 1.0, 1.0), rot_z=a)
    mouth = P(0.0, -6.1)
    sc.carve(mouth[0], mouth[1], r(1.0), z=z + r(0.85),
             scale=(3.1, 0.3, 1.0), rot_z=a)
    for i in range(-3, 4):
        for row_y, row_z in ((-5.3, 0.55), (-7.0, 0.5)):
            gap = P(i * 1.08, row_y)
            sc.carve(gap[0], gap[1], r(0.42), z=z + r(row_z), rot_z=a)
    for sx in (-1.0, 1.0):      # sunken temporal fossa behind the arch
        fossa = P(sx * 7.6, 1.6)
        # shallow dent, not a hole: a full-depth cut here read as a second
        # pair of eye sockets and turned the skull into a four-eyed blob.
        sc.carve(fossa[0], fossa[1], r(2.2), z=z + r(3.6),
                 scale=(0.85, 1.25, 1.0), rot_z=a)


def serpent(sc, points, head_dir, r0=3.4, r1=0.8, z=0.0):
    """Coiling serpent: tapering body, wedge head, fangs, carved eyes."""
    radii = [r0 + (r1 - r0) * (i / (len(points) - 1)) ** 0.8
             for i in range(len(points))]
    chain(sc, points, radii, z=z)

    hx, hy = points[0]
    a = math.radians(head_dir)
    fwd = (math.cos(a), math.sin(a))
    side = (-fwd[1], fwd[0])

    def H(fo, so, zo=0.0):
        return (hx + fwd[0] * fo + side[0] * so,
                hy + fwd[1] * fo + side[1] * so, z + zo)

    cranium = H(1.2, 0.0, 0.3)
    blob(sc, cranium[0], cranium[1], r0 * 0.78,
         (r0 * 0.75, r0 * 0.6, r0 * 0.35), z=cranium[2], rot_z=a)
    snout = H(3.3, 0.0, 0.0)
    blob(sc, snout[0], snout[1], r0 * 0.52,
         (r0 * 0.85, r0 * 0.3, r0 * 0.22), z=snout[2], rot_z=a)
    for sg in (-1.0, 1.0):
        brow = H(1.5, sg * r0 * 0.6, 0.6)
        ball(sc, brow[0], brow[1], r0 * 0.44, z=brow[2])
        eye = H(1.6, sg * r0 * 0.62, 0.0)
        sc.carve(eye[0], eye[1], r0 * 0.34, z=eye[2] + r0 * 0.55)
        fang = H(4.2, sg * r0 * 0.22, -0.2)
        ball(sc, fang[0], fang[1], r0 * 0.26, z=fang[2])
    gape = H(3.0, 0.0, 0.0)
    sc.carve(gape[0], gape[1], r0 * 0.3, z=gape[2] + r0 * 0.42,
             scale=(2.0, 0.35, 1.0), rot_z=a)


def dragon(sc, cx, cy, s=1.0, facing=1.0, z=0.0):
    """Wyvern: S-body with a spiked spine, ribbed wing, horned head, claws."""
    def P(x, y):
        return (cx + facing * x * s, cy + y * s)

    body = _sample_curve(
        lambda t: P(-17.0 + 31.0 * t,
                    -10.0 + 13.0 * math.sin(math.pi * t * 1.05)),
        0.0, 1.0, 11)
    radii = [1.0, 1.9, 2.8, 3.4, 3.7, 3.7, 3.4, 2.9, 2.3, 1.7, 1.1]
    chain(sc, body, [v * s for v in radii], z=z)
    # dorsal spikes along the back give the silhouette its reptile read
    for i in range(2, 9):
        bx, by = body[i]
        nx, ny = body[i + 1]
        dx, dy = nx - bx, ny - by
        norm = math.hypot(dx, dy) or 1.0
        spike = (bx - dy / norm * radii[i] * s * 1.25,
                 by + dx / norm * radii[i] * s * 1.25)
        chain(sc, [(bx, by), spike], [0.9 * s, 0.25 * s], z=z + 0.2 * s)

    tail = P(-21.0, -12.0)
    blob(sc, tail[0], tail[1], 1.2 * s, (1.7 * s, 0.4 * s, 0.3 * s),
         z=z, rot_z=math.radians(200.0 if facing > 0 else -20.0))

    neck = _sample_curve(
        lambda t: P(12.0 + 7.5 * t, 3.0 + 7.6 * t - 2.0 * t * t),
        0.0, 1.0, 5)
    chain(sc, neck, [3.2 * s, 2.8 * s, 2.5 * s, 2.3 * s, 2.2 * s],
          z=z + 0.4 * s)
    head = P(20.8, 8.8)
    blob(sc, head[0], head[1], 2.9 * s, (2.2 * s, 1.6 * s, 1.0 * s),
         z=z + 1.1 * s, rot_z=math.radians(18.0 * facing))
    snout = P(25.4, 9.6)
    blob(sc, snout[0], snout[1], 2.0 * s, (2.4 * s, 0.75 * s, 0.5 * s),
         z=z + 0.9 * s, rot_z=math.radians(10.0 * facing))
    jaw = P(24.2, 6.8)
    blob(sc, jaw[0], jaw[1], 1.55 * s, (1.9 * s, 0.45 * s, 0.35 * s),
         z=z + 0.4 * s, rot_z=math.radians(-4.0 * facing))
    for i in range(4):
        tooth = P(22.4 + i * 1.1, 8.4)
        ball(sc, tooth[0], tooth[1], 0.4 * s, z=z + 0.9 * s)
    eye = P(20.8, 10.0)
    sc.carve(eye[0], eye[1], 0.95 * s, z=z + 2.0 * s)
    sc.carve(*P(25.6, 10.0), 0.45 * s, z=z + 1.5 * s)
    sc.carve(*P(23.3, 8.5), 0.5 * s, z=z + 1.4 * s,
             scale=(2.6, 0.4, 1.0), rot_z=math.radians(6.0 * facing))
    for horn_y, horn_len in ((11.4, 6.4), (10.0, 4.4)):
        horn = _sample_curve(
            lambda t, hy=horn_y, hl=horn_len: P(19.0 - hl * t,
                                                hy + hl * 0.72 * t
                                                + 1.2 * t * t),
            0.0, 1.0, 4)
        chain(sc, horn, [1.1 * s, 0.85 * s, 0.6 * s, 0.3 * s], z=z + 0.3 * s)

    # wing: four spars with a webbed membrane.  The fan is swept back over the
    # shoulder so it never buries the head, which it did when it fanned
    # forward.
    shoulder = P(5.0, 5.0)
    tips = [P(-15.0, 20.0), P(-4.0, 25.5), P(7.0, 24.0), P(15.0, 17.0)]
    for tip in tips:
        chain(sc, [shoulder, ((shoulder[0] + tip[0]) / 2.0,
                              (shoulder[1] + tip[1]) / 2.0 + 1.2 * s),
                   tip],
              [2.2 * s, 1.5 * s, 0.8 * s], z=z + 0.6 * s)
        ball(sc, tip[0], tip[1], 0.9 * s, z=z + 0.5 * s)
        chain(sc, [tip, (tip[0] + facing * 1.6 * s, tip[1] + 1.6 * s)],
              [0.6 * s, 0.22 * s], z=z + 0.4 * s)
    membrane(sc, shoulder, tips, z=z + 0.1 * s, thick=1.8 * s, scallop=0.13)

    leg = [P(8.0, -1.5), P(10.5, -6.5), P(14.5, -9.0)]
    chain(sc, leg, [2.1 * s, 1.4 * s, 1.0 * s], z=z + 0.3 * s)
    for claw_a in (-8.0, 8.0, 24.0):
        rad = math.radians(claw_a)
        claw = P(14.5 + 3.6 * math.cos(rad), -9.0 - 3.6 * math.sin(rad))
        chain(sc, [P(14.5, -9.0), claw], [0.85 * s, 0.3 * s], z=z + 0.2 * s)


def rib_cage(sc, cx, cy, s=1.0, z=0.0):
    """Spine with vertebrae, six curved rib pairs and a sternum plate."""
    spine = _sample_curve(lambda t: (cx + 0.9 * s * math.sin(t * 4.0),
                                     cy + s * (13.0 - 26.0 * t)),
                          0.0, 1.0, 9)
    chain(sc, spine, [1.5 * s] * 9, z=z - 0.2 * s)
    for point in spine:
        ball(sc, point[0], point[1], 1.8 * s, z=z + 0.25 * s)
        sc.carve(point[0], point[1] + 1.3 * s, 0.9 * s, z=z + 1.9 * s,
                 scale=(2.4, 0.5, 1.0))
    for i in range(6):
        y0 = cy + s * (10.0 - i * 3.6)
        span = s * (5.0 + 4.2 * math.sin(math.pi * (i + 1) / 8.0)) * 1.75
        drop = s * (3.0 + i * 0.7)
        for sg in (-1.0, 1.0):
            rib = _sample_curve(
                lambda t, sg=sg, y0=y0, span=span, drop=drop: (
                    cx + sg * span * math.sin(t * math.pi * 0.52),
                    y0 - drop * (t ** 1.7)),
                0.0, 1.0, 6)
            chain(sc, rib, [1.35 * s, 1.25 * s, 1.15 * s,
                            1.05 * s, 0.95 * s, 0.8 * s], z=z)
    sternum = (cx, cy - s * 2.0)
    blob(sc, sternum[0], sternum[1], 1.4 * s, (0.6 * s, 4.6 * s, 0.4 * s),
         z=z + 0.3 * s)


def scroll(sc, cx, cy, r0, turns=1.35, phase=0.0, direction=1.0,
           thick0=1.5, thick1=0.45, z=0.0):
    """Gothic scrollwork volute, tapering into a curled tip."""
    count = 20
    pts, radii = [], []
    for i in range(count):
        t = i / (count - 1)
        ang = phase + direction * turns * 2.0 * math.pi * t
        rad = r0 * (1.0 - 0.82 * t)
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        radii.append(thick0 + (thick1 - thick0) * t)
    chain(sc, pts, radii, z=z)
    ball(sc, pts[-1][0], pts[-1][1], thick1 * 1.5, z=z + thick1 * 0.3)


def vine(sc, points, r0=1.6, r1=0.8, z=0.0, leaf_at=()):
    radii = [r0 + (r1 - r0) * i / (len(points) - 1)
             for i in range(len(points))]
    chain(sc, points, radii, z=z)
    for idx, ang in leaf_at:
        x, y = points[idx]
        blob(sc, x, y, 1.6, (2.4, 0.8, 0.35), z=z,
             rot_z=math.radians(ang))
        sc.carve(x, y, 0.5, z=z + 1.4, scale=(3.0, 0.3, 1.0),
                 rot_z=math.radians(ang))


def bat_wing(sc, cx, cy, s=1.0, side=1.0, z=0.0):
    """Ribbed bat wing used by the lid cartouche."""
    shoulder = (cx + side * 4.0 * s, cy + 2.0 * s)
    tips = [(cx + side * 15.0 * s, cy + 13.5 * s),
            (cx + side * 28.0 * s, cy + 11.5 * s),
            (cx + side * 37.0 * s, cy + 3.5 * s),
            (cx + side * 33.0 * s, cy - 7.5 * s)]
    for tip in tips:
        chain(sc, [shoulder,
                   ((shoulder[0] + tip[0]) / 2.0,
                    (shoulder[1] + tip[1]) / 2.0 + 1.0 * s),
                   tip],
              [2.2 * s, 1.4 * s, 0.7 * s], z=z + 0.4 * s)
        ball(sc, tip[0], tip[1], 0.9 * s, z=z + 0.3 * s)
        chain(sc, [tip, (tip[0] + side * 1.8 * s, tip[1] + 1.8 * s)],
              [0.6 * s, 0.22 * s], z=z + 0.3 * s)
    membrane(sc, shoulder, tips, z=z + 0.15 * s, thick=1.9 * s, scallop=0.14,
             rays=8)


# --------------------------------------------------------------------------
# panel definitions
# --------------------------------------------------------------------------

def panel_front(sc):
    """Twin serpents rising out of the plinth past two leering skulls."""
    for sx in (-1.0, 1.0):
        skull(sc, sx * 56.0, 4.0, s=1.3, tilt=sx * 6.0)
        body = _sample_curve(
            lambda t, sx=sx: (sx * (26.0 + 48.0 * t),
                              14.0 - 31.0 * t
                              + 7.5 * math.sin(math.pi * 2.1 * t)),
            0.0, 1.0, 10)
        serpent(sc, body, head_dir=120.0 if sx > 0 else 60.0,
                r0=3.6, r1=1.2)
        scroll(sc, sx * 71.0, 17.0, 6.4, turns=1.2,
               phase=math.radians(200.0), direction=-sx,
               thick0=2.1, thick1=0.8)
        scroll(sc, sx * 24.0, -18.0, 6.0, turns=1.3,
               phase=math.radians(40.0), direction=sx,
               thick0=2.0, thick1=0.7)
        scroll(sc, sx * 39.0, 19.5, 5.2, turns=1.1,
               phase=math.radians(120.0), direction=-sx,
               thick0=1.9, thick1=0.7)
        scroll(sc, sx * 70.0, -17.0, 5.0, turns=1.15,
               phase=math.radians(310.0), direction=sx,
               thick0=1.8, thick1=0.7)
        vine(sc, [(sx * 20.0, -22.5), (sx * 38.0, -20.0),
                  (sx * 52.0, -17.0), (sx * 63.0, -21.0)],
             r0=2.1, r1=1.1, leaf_at=((1, 30.0 * sx), (2, -25.0 * sx)))
        vine(sc, [(sx * 46.0, 21.5), (sx * 56.0, 23.0),
                  (sx * 66.0, 21.0)], r0=1.9, r1=1.0,
             leaf_at=((1, -40.0 * sx),))


def panel_rear(sc):
    """Confronted wyverns guarding a rib cage."""
    rib_cage(sc, 0.0, 1.0, s=1.15)
    for sx in (-1.0, 1.0):
        # pushed outward so the head reads against clear field instead of
        # colliding with the rib cage
        dragon(sc, sx * 48.0, -3.0, s=1.0, facing=-sx)
        scroll(sc, sx * 71.0, -16.0, 6.0, turns=1.3,
               phase=math.radians(150.0), direction=sx,
               thick0=2.1, thick1=0.8)
        scroll(sc, sx * 20.0, 20.0, 5.4, turns=1.2,
               phase=math.radians(260.0), direction=-sx,
               thick0=1.9, thick1=0.7)
        vine(sc, [(sx * 14.0, -20.5), (sx * 30.0, -22.5),
                  (sx * 48.0, -20.0)], r0=2.0, r1=1.0,
             leaf_at=((1, -20.0 * sx),))
        vine(sc, [(sx * 60.0, 20.5), (sx * 70.0, 14.0)],
             r0=1.7, r1=0.9, leaf_at=((0, 50.0 * sx),))


def panel_side(sc):
    """Skull with a serpent threaded past the eye socket."""
    skull(sc, 0.0, 5.0, s=1.55)
    body = _sample_curve(
        lambda t: (-29.0 + 58.0 * t,
                   -17.0 + 9.0 * math.sin(math.pi * 1.9 * t) + 6.0 * t),
        0.0, 1.0, 9)
    serpent(sc, body, head_dir=35.0, r0=3.0, r1=1.1)
    for sx in (-1.0, 1.0):
        scroll(sc, sx * 26.0, 18.5, 5.8, turns=1.3,
               phase=math.radians(230.0), direction=-sx,
               thick0=2.0, thick1=0.7)
        vine(sc, [(sx * 8.0, -23.0), (sx * 19.0, -21.0),
                  (sx * 29.0, -15.5)], r0=1.8, r1=0.9,
             leaf_at=((1, 35.0 * sx),))


def panel_lid(sc):
    """Winged skull cartouche with serpents along the lower edge."""
    skull(sc, 0.0, 2.0, s=2.0)
    for sx in (-1.0, 1.0):
        bat_wing(sc, sx * 13.0, 6.0, s=1.3, side=sx)
        body = _sample_curve(
            lambda t, sx=sx: (sx * (9.0 + 56.0 * t),
                              -22.0 + 6.5 * math.sin(math.pi * 2.0 * t)),
            0.0, 1.0, 8)
        serpent(sc, body, head_dir=180.0 if sx > 0 else 0.0,
                r0=3.0, r1=1.0)
        scroll(sc, sx * 59.0, 24.0, 6.8, turns=1.3,
               phase=math.radians(200.0), direction=-sx,
               thick0=2.2, thick1=0.8)
        scroll(sc, sx * 32.0, 27.0, 5.0, turns=1.1,
               phase=math.radians(300.0), direction=sx,
               thick0=1.9, thick1=0.7)


PANELS = {
    # name:      (half width, half height, pitch mm, builder, mask ellipse)
    "front": (76.0, 25.0, 0.62, panel_front, (0.0, 3.0, 23.0, 20.0)),
    "rear": (76.0, 25.0, 0.62, panel_rear, None),
    "side": (34.0, 25.0, 0.58, panel_side, None),
    "lid": (70.0, 33.0, 0.65, panel_lid, None),
}

# --------------------------------------------------------------------------
# sculpt -> height field
# --------------------------------------------------------------------------

def _reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 0.001
    bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'


def _noise_texture():
    tex = bpy.data.textures.get("chest_grain")
    if tex is None:
        tex = bpy.data.textures.new("chest_grain", type='CLOUDS')
    tex.noise_scale = NOISE_SCALE
    tex.noise_depth = 3
    tex.noise_basis = 'BLENDER_ORIGINAL'
    return tex


def _sculpt(name, builder):
    mball_data = bpy.data.metaballs.new(f"MB_{name}")
    mball_data.resolution = META_RESOLUTION
    mball_data.render_resolution = META_RESOLUTION
    obj = bpy.data.objects.new(f"organic_{name}", mball_data)
    bpy.context.collection.objects.link(obj)
    sculpt = Sculpt(mball_data)
    builder(sculpt)

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    mesh_obj = bpy.context.view_layer.objects.active
    mesh_obj.name = f"organic_{name}"
    print(f"  {name}: {len(mball_data.elements)} metaball elements -> "
          f"{len(mesh_obj.data.polygons)} raw faces")

    grain = mesh_obj.modifiers.new("grain", 'DISPLACE')
    grain.texture = _noise_texture()
    grain.texture_coords = 'LOCAL'
    grain.strength = NOISE_STRENGTH
    grain.mid_level = 0.5
    smooth = mesh_obj.modifiers.new("smooth", 'SMOOTH')
    smooth.factor = 0.55
    smooth.iterations = 2
    bpy.context.view_layer.objects.active = mesh_obj
    for mod in list(mesh_obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    print(f"  {name}: {len(mesh_obj.data.polygons)} faces, "
          f"{len(sculpt.cuts)} hollows")
    return mesh_obj, sculpt.cuts


def _apply_cuts(xs, ys, heights, cuts):
    """Sink the recorded hollows into the extracted height field.

    Each cutter is an axis-aligned (optionally rotated) ellipse whose floor is
    the cutter's lowest point.  The floor is blended back to the untouched
    surface over the outer quarter of the ellipse so the socket keeps a
    rounded, carved wall instead of a punched cylinder.
    """
    gx, gy = np.meshgrid(xs, ys)
    for cx, cy, rx, ry, floor, rot_z in cuts:
        dx, dy = gx - cx, gy - cy
        if rot_z:
            ca, sa = math.cos(-rot_z), math.sin(-rot_z)
            dx, dy = dx * ca - dy * sa, dx * sa + dy * ca
        d = np.sqrt((dx / rx) ** 2 + (dy / ry) ** 2)
        inside = d < 1.0
        if not inside.any():
            continue
        blend = np.clip((d - 0.55) / 0.45, 0.0, 1.0) ** 2
        target = np.maximum(floor, 0.0) * (1.0 - blend) + heights * blend
        heights = np.where(inside, np.minimum(heights, target), heights)
    return heights


def _height_field(mesh_obj, half_w, half_h, pitch):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(mesh_obj, depsgraph)
    top = max(v.co.z for v in mesh_obj.data.vertices) + 5.0

    nx = int(round(2.0 * half_w / pitch)) + 1
    ny = int(round(2.0 * half_h / pitch)) + 1
    xs = np.linspace(-half_w, half_w, nx)
    ys = np.linspace(-half_h, half_h, ny)
    heights = np.zeros((ny, nx), dtype=np.float64)
    down = Vector((0.0, 0.0, -1.0))
    for iy, y in enumerate(ys):
        for ix, x in enumerate(xs):
            hit, _, _, _ = bvh.ray_cast(Vector((x, y, top)), down)
            if hit is not None:
                heights[iy, ix] = max(0.0, hit.z)
    return xs, ys, heights


def _border_falloff(xs, ys, heights):
    """Ramp the panel edge back into the wall so no vertical step survives."""
    def ramp(values):
        d = np.minimum(values - values.min(), values.max() - values)
        return np.clip(d / BORDER_FALLOFF, 0.0, 1.0) ** 0.9

    fx = ramp(xs)
    fy = ramp(ys)
    return heights * fy[:, None] * fx[None, :]


def _mask_ellipse(xs, ys, heights, mask):
    cx, cy, rx, ry = mask
    gx, gy = np.meshgrid(xs, ys)
    d = np.sqrt(((gx - cx) / rx) ** 2 + ((gy - cy) / ry) ** 2)
    return heights * np.clip((d - 1.0) / 0.22, 0.0, 1.0)


def build_panel(name):
    half_w, half_h, pitch, builder, mask = PANELS[name]
    _reset_scene()
    mesh_obj, cuts = _sculpt(name, builder)
    xs, ys, heights = _height_field(mesh_obj, half_w, half_h, pitch)
    heights = _apply_cuts(xs, ys, heights, cuts)
    if mask is not None:
        heights = _mask_ellipse(xs, ys, heights, mask)
    heights = _border_falloff(xs, ys, heights)

    peak = float(heights.max())
    if peak <= 0.0:
        raise RuntimeError(f"panel {name} sculpted nothing")
    # Soft tone compression instead of a linear squash.  A 7 mm meta-ball
    # sculpture scaled linearly into a 2.6 mm relief leaves slim elements
    # (serpent bodies, scroll tips, ribs) as invisible scratches next to a
    # saturated cranium.  ``1 - exp(-h/k)`` lifts the mid tones while keeping
    # the rounded falloff of the large masses.
    normalised = (1.0 - np.exp(-heights / TONE_K))
    normalised = np.clip(normalised / (1.0 - math.exp(-TONE_REF / TONE_K)),
                         0.0, 1.0)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    BLEND_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        OUT_DIR / f"{name}.npz",
        heights=normalised.astype(np.float32),
        x0=xs[0], x1=xs[-1], y0=ys[0], y1=ys[-1], pitch=pitch,
    )
    bpy.ops.wm.save_as_mainfile(
        filepath=str(BLEND_DIR / f"gothic_chest_relief_{name}.blend"))
    coverage = float((normalised > 0.23).mean())
    print(f"panel {name:5s} grid {normalised.shape[1]}x{normalised.shape[0]} "
          f"sculpt peak {peak:.2f} mm coverage {coverage * 100:.1f}%")
    return {"panel": name, "grid": list(normalised.shape),
            "sculpt_peak_mm": round(peak, 3),
            "coverage_fraction": round(coverage, 4),
            "pitch_mm": pitch}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = argv or list(PANELS)
    report = [build_panel(name) for name in names]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "manifest.json").write_text(json.dumps({
        "generator": "scripts/blender_chest_reliefs.py",
        "blender": bpy.app.version_string,
        "meta_resolution_mm": META_RESOLUTION,
        "noise_strength_mm": NOISE_STRENGTH,
        "noise_scale_mm": NOISE_SCALE,
        "panels": report,
    }, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT_DIR / "manifest.json")


if __name__ == "__main__":
    main()
