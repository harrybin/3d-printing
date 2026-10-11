"""Gothic chest and lid for the Ghoul's Grip automaton.

Everything decorative is modelled as real geometry rather than a texture. The
chest is a shell with a tapered plinth and cornice, corner pilasters, and
shallow creature reliefs built from rounded strokes. Their outward depth is
sheared upward at 45 degrees, so the lower edges grow from the wall instead of
forming unsupported shelves.

The chest prints upright and the lid prints on its long front edge. Decorative
features are shallow rounded engravings rather than unsupported raised shelves.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import trimesh

import mechanism
from mesh_kit import (arc_band, box, clean, cylinder, difference, fuse,
                      intersection, rounded_box, simplify, sphere, union)
from skull import skull_relief

CHEST_L = 200.0
CHEST_W = 120.0
BODY_H = 86.0
LID_H = 24.0
WALL = 2.0
FLOOR = 2.0
FUNCTIONAL_WALL_DATUM = 3.0

PLINTH_H = 10.0
CORNICE_H = 8.0
PROUD = 3.0            # how far plinth, cornice and pilasters stand out
PILASTER = 19.0
PANEL_DEPTH = 2.5
RELIEF = 2.6
ECONOMY_SKIN = 1.2    # three-line visual shell behind internal lightening pockets
ENGRAVING_DEPTH = 0.8
CREATURE_RELIEF_DEPTH = 3.0   # sculpted bas relief; 0.6 mm of it is buried

# Blender-sculpted relief height maps (scripts/blender_chest_reliefs.py).
RELIEF_CACHE = Path(__file__).resolve().parents[1] / "assets" / \
    "gothic-chest-reliefs"
RELIEF_BASE = 0.4             # flat backing plate under the height field
RELIEF_TARGETS = {"front": 34_000, "rear": 34_000,
                  "side": 26_000, "lid": 32_000}
PILASTER_ENGRAVE_DEPTH = 1.2  # into 5.0 mm of pilaster -> 3.8 mm remaining

RAIL_W = 4.0           # slider rail groove, as specified in the brief
RAIL_D = 3.0
LID_DROP = 74.0         # chest z of the lid local origin when closed
RAIL_Z = 8.0
HINGE_Z = 93.0          # lid pin axis, shared by chest and lid knuckles
HINGE_Y = CHEST_W / 2.0 + PROUD - 2.0  # rear long edge; axis runs along X


def _rect_frustum(bottom: tuple[float, float], top: tuple[float, float],
                  z0: float, z1: float,
                  centre: tuple[float, float] = (0.0, 0.0)
                  ) -> trimesh.Trimesh:
    """Closed rectangular frustum with a printable, sloped transition."""
    bx, by = bottom
    tx, ty = top
    cx, cy = centre
    vertices = np.asarray([
        (cx - bx / 2.0, cy - by / 2.0, z0),
        (cx + bx / 2.0, cy - by / 2.0, z0),
        (cx + bx / 2.0, cy + by / 2.0, z0),
        (cx - bx / 2.0, cy + by / 2.0, z0),
        (cx - tx / 2.0, cy - ty / 2.0, z1),
        (cx + tx / 2.0, cy - ty / 2.0, z1),
        (cx + tx / 2.0, cy + ty / 2.0, z1),
        (cx - tx / 2.0, cy + ty / 2.0, z1),
    ], dtype=float)
    faces = np.asarray([
        (0, 3, 2, 1), (4, 5, 6, 7),
        (0, 1, 5, 4), (1, 2, 6, 5),
        (2, 3, 7, 6), (3, 0, 4, 7),
    ], dtype=int)
    return clean(trimesh.Trimesh(vertices=vertices, faces=faces,
                                 process=True))


def _extrude_yz_polygon(points: list[tuple[float, float]], length: float,
                        x_centre: float = 0.0) -> trimesh.Trimesh:
    """Extrude a convex YZ profile along X without optional polygon helpers."""
    x0 = x_centre - length / 2.0
    x1 = x_centre + length / 2.0
    vertices = np.asarray(
        [(x0, y, z) for y, z in points]
        + [(x1, y, z) for y, z in points],
        dtype=float,
    )
    count = len(points)
    faces = []
    for index in range(1, count - 1):
        faces.append((0, index + 1, index))
        faces.append((count, count + index, count + index + 1))
    for index in range(count):
        nxt = (index + 1) % count
        faces.extend([
            (index, nxt, count + nxt),
            (index, count + nxt, count + index),
        ])
    return clean(trimesh.Trimesh(
        vertices=vertices,
        faces=np.asarray(faces, dtype=int),
        process=True,
    ))


def _stepped_skirt(z0: float, height: float, flip: bool) -> trimesh.Trimesh:
    """Plinth or cornice with two 45-degree-safe tapered courses.

    The former rectangular steps created continuous horizontal undersides around
    the whole chest and made Orca grow a support forest. The same maximum
    envelope is retained with printable sloped transitions.
    """
    middle = (CHEST_L + PROUD, CHEST_W + PROUD)
    body = (CHEST_L, CHEST_W)
    outer = (CHEST_L + 2.0 * PROUD, CHEST_W + 2.0 * PROUD)
    half = height / 2.0
    if flip:
        courses = (
            _rect_frustum(body, middle, z0, z0 + half),
            _rect_frustum(middle, outer, z0 + half, z0 + height),
        )
    else:
        courses = (
            _rect_frustum(outer, middle, z0, z0 + half),
            _rect_frustum(middle, body, z0 + half, z0 + height),
        )
    skirt = union(courses)
    cut_z0 = z0 - 0.2 if flip else z0 + FLOOR
    cut_z1 = z0 + height + 0.2
    cavity = box(
        (CHEST_L - 2.0 * WALL, CHEST_W - 2.0 * WALL, cut_z1 - cut_z0),
        (0.0, 0.0, (cut_z0 + cut_z1) / 2.0),
    )
    return difference(skirt, [cavity])


def _lancet(width: float, height: float, depth: float,
            centre, normal_x: bool) -> list[trimesh.Trimesh]:
    """One pointed arch: two jambs, a sill and two struck arcs."""
    half = width / 2.0
    radius = width          # equilateral arch: struck from the opposite jamb
    spring = height - np.sqrt(radius ** 2 - half ** 2)
    band = 5.0

    # The jambs run past the springing line and the arcs run past the apex,
    # so every joint is a real overlap rather than a tangential knife edge.
    jamb = spring + band
    parts = [
        box((band, jamb, depth), (-half + band / 2.0, jamb / 2.0, 0.0)),
        box((band, jamb, depth), (half - band / 2.0, jamb / 2.0, 0.0)),
        box((width, band, depth), (0.0, band / 2.0, 0.0)),
    ]
    # Equilateral arch: each flank arc is struck from the opposite springing
    # point, so both meet in a true point at the apex.
    for side, a0, a1 in ((-1.0, 0.0, 64.0), (1.0, 116.0, 180.0)):
        parts.append(arc_band(radius, band, depth,
                              np.deg2rad(a0), np.deg2rad(a1),
                              (side * half, spring, 0.0)))

    arch = union(parts)
    arch.apply_translation([0.0, 0.0, -depth / 2.0])
    arch.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2.0, [1.0, 0.0, 0.0]))
    if normal_x:
        arch.apply_transform(trimesh.transformations.rotation_matrix(
            np.pi / 2.0, [0.0, 0.0, 1.0]))
    arch.apply_translation(np.asarray(centre, dtype=float))
    inlay_centre = np.asarray(centre, dtype=float).copy()
    axis = 0 if normal_x else 1
    inlay_centre[axis] -= np.sign(inlay_centre[axis]) * 0.35
    if normal_x:
        return [arch]
    return [
        arch,
        _lancet_inlay(width, height, depth, inlay_centre, normal_x),
    ]


def _frame(size, centre, normal_x: bool, proud: float,
           band: float = 6.0) -> trimesh.Trimesh:
    """Raised border around a field, so the field reads as a sunken panel.

    The chest wall is only 3 mm thick, so decoration is added outwards instead
    of cut inwards - a 2.5 mm recess would leave a 0.5 mm wall.
    """
    w, h = size
    if normal_x:
        outer = rounded_box((proud, w + 2 * band, h + 2 * band),
                            min(3.0, proud * 0.4), centre)
        inner = box((proud + 4.0, w, h), centre)
    else:
        outer = rounded_box((w + 2 * band, proud, h + 2 * band),
                            min(3.0, proud * 0.4), centre)
        inner = box((w, proud + 4.0, h), centre)
    return difference(outer, [inner])


def _leaf(length: float, width: float, depth: float,
          centre, angle: float) -> trimesh.Trimesh:
    """Convex almond leaf used in the baroque-gothic scrollwork."""
    leaf = sphere(1.0, subdivisions=2)
    leaf.apply_scale([length / 2.0, width / 2.0, depth / 2.0])
    leaf.apply_transform(trimesh.transformations.rotation_matrix(
        angle, (0.0, 0.0, 1.0)))
    leaf.apply_translation(np.asarray(centre, dtype=float))
    return clean(leaf)


def _rounded_stroke(points, radius: float, depth: float) -> trimesh.Trimesh:
    """Flat-backed vine or rib with a rounded printable outline."""
    points = [np.asarray(point, dtype=float) for point in points]
    parts = [
        cylinder(radius, depth, (point[0], point[1], 0.0))
        for point in points
    ]
    for start, end in zip(points[:-1], points[1:]):
        vector = end - start
        length = float(np.linalg.norm(vector))
        angle = float(np.arctan2(vector[1], vector[0]))
        midpoint = (start + end) / 2.0
        parts.append(box(
            (length, 2.0 * radius, depth),
            (midpoint[0], midpoint[1], 0.0),
            (angle, (0.0, 0.0, 1.0)),
        ))
    return union(parts)


def _tapered_stroke(points, radii, depth: float) -> trimesh.Trimesh:
    """Variable-width anatomical stroke made from overlapping convex capsules."""
    points = [np.asarray(point, dtype=float) for point in points]
    radii = [float(radius) for radius in radii]
    if len(points) != len(radii):
        raise ValueError("tapered stroke needs one radius per point")
    nodes = [
        cylinder(radius, depth, (point[0], point[1], 0.0))
        for point, radius in zip(points, radii)
    ]
    segments = []
    for start, end in zip(nodes[:-1], nodes[1:]):
        segments.append(
            trimesh.util.concatenate([start, end]).convex_hull
        )
    return clean(trimesh.util.concatenate([*nodes, *segments]))


def _extrude_xy_polygon(points, depth: float) -> trimesh.Trimesh:
    """Extrude a convex local-XY membrane without optional polygon packages."""
    count = len(points)
    vertices = np.asarray(
        [(x, y, -depth / 2.0) for x, y in points]
        + [(x, y, depth / 2.0) for x, y in points],
        dtype=float,
    )
    faces = []
    for index in range(1, count - 1):
        faces.extend([
            (0, index + 1, index),
            (count, count + index, count + index + 1),
        ])
    for index in range(count):
        nxt = (index + 1) % count
        faces.extend([
            (index, nxt, count + nxt),
            (index, count + nxt, count + index),
        ])
    return clean(trimesh.Trimesh(
        vertices=vertices,
        faces=np.asarray(faces, dtype=int),
        process=True,
    ))


def _bezier_points(p0, p1, p2, p3, count: int = 8):
    """Sample a cubic curve for smooth, reproducible relief vines."""
    control = [np.asarray(point, dtype=float) for point in (p0, p1, p2, p3)]
    points = []
    for t in np.linspace(0.0, 1.0, count):
        u = 1.0 - t
        points.append(
            u ** 3 * control[0]
            + 3.0 * u ** 2 * t * control[1]
            + 3.0 * u * t ** 2 * control[2]
            + t ** 3 * control[3]
        )
    return points


def _quatrefoil(radius: float, depth: float, centre) -> trimesh.Trimesh:
    """Four rounded leaves around a small central boss."""
    cx, cy, cz = centre
    petals = [
        _leaf(radius * 1.65, radius * 0.82, depth,
              (cx + np.cos(angle) * radius * 0.72,
               cy + np.sin(angle) * radius * 0.72, cz), angle)
        for angle in (0.0, np.pi / 2.0, np.pi, 3.0 * np.pi / 2.0)
    ]
    petals.append(cylinder(radius * 0.34, depth, centre))
    return union(petals)


def _fleuron(depth: float, centre=(0.0, 0.0, 0.0),
             scale: float = 1.0) -> trimesh.Trimesh:
    """Pointed leaf crown used as a Gothic finial."""
    cx, cy, cz = centre
    parts = [
        _leaf(18.0 * scale, 6.8 * scale, depth,
              (cx, cy + 5.0 * scale, cz), np.pi / 2.0),
        _leaf(14.0 * scale, 5.8 * scale, depth,
              (cx - 5.5 * scale, cy, cz), np.deg2rad(132.0)),
        _leaf(14.0 * scale, 5.8 * scale, depth,
              (cx + 5.5 * scale, cy, cz), np.deg2rad(48.0)),
        _rounded_stroke(
            [(cx, cy - 8.0 * scale), (cx, cy + 4.0 * scale)],
            1.4 * scale, depth,
        ),
    ]
    return union(parts)


def _place_planar_relief(mesh: trimesh.Trimesh, centre,
                         normal_x: bool) -> trimesh.Trimesh:
    """Map local XY ornament coordinates onto a chest wall."""
    result = mesh.copy()
    result.apply_translation([0.0, 0.0, -result.extents[2] / 2.0])
    result.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2.0, [1.0, 0.0, 0.0]))
    if normal_x:
        result.apply_transform(trimesh.transformations.rotation_matrix(
            np.pi / 2.0, [0.0, 0.0, 1.0]))
    result.apply_translation(np.asarray(centre, dtype=float))
    return clean(result)


def _scroll_pair(depth: float) -> trimesh.Trimesh:
    """Layered thorn-and-acanthus curls in the local XY plane."""
    parts = []
    for side in (-1.0, 1.0):
        def mirror(points):
            return [(side * x, y) for x, y in points]

        lower_vine = _bezier_points(
            (24.0, -12.0), (37.0, -24.0),
            (63.0, -18.0), (57.0, 8.0),
        )
        upper_vine = _bezier_points(
            (26.0, -8.0), (30.0, 10.0),
            (51.0, 7.0), (50.0, 28.0),
        )
        curl = [
            *_bezier_points(
                (34.0, 5.0), (49.0, 13.0),
                (45.0, 31.0), (31.0, 23.0),
                8,
            ),
            *_bezier_points(
                (31.0, 23.0), (27.0, 20.0),
                (28.0, 16.0), (33.0, 15.0),
                5,
            )[1:],
        ]
        parts.extend([
            _rounded_stroke(mirror(lower_vine), 2.3, depth),
            _rounded_stroke(mirror(upper_vine), 2.0, depth),
            _rounded_stroke(mirror(curl), 1.65, depth),
            _leaf(17.0, 7.0, depth, (side * 18.0, 4.0, 0.0),
                  np.deg2rad(25.0 if side > 0 else 155.0)),
            _leaf(15.0, 6.2, depth, (side * 47.0, -16.0, 0.0),
                  np.deg2rad(-28.0 if side > 0 else 208.0)),
            _leaf(13.0, 5.4, depth, (side * 57.0, 14.0, 0.0),
                  np.deg2rad(58.0 if side > 0 else 122.0)),
            _leaf(10.0, 4.2, depth, (side * 40.0, 22.0, 0.0),
                  np.deg2rad(128.0 if side > 0 else 52.0)),
            _leaf(8.5, 3.6, depth, (side * 59.0, 1.0, 0.0),
                  np.deg2rad(18.0 if side > 0 else 162.0)),
        ])
    parts.extend([
        _fleuron(depth, (0.0, 22.0, 0.0), 0.9),
        _quatrefoil(4.8, depth, (0.0, -15.0, 0.0)),
    ])
    return union(parts)


def _seat_wall_cutter(mesh: trimesh.Trimesh, face: float, sign: float,
                      normal_x: bool) -> trimesh.Trimesh:
    """Seat a shallow engraving across an exterior wall surface."""
    result = mesh.copy()
    axis = 0 if normal_x else 1
    outer = sign * face
    if sign > 0:
        shift = outer + 0.2 - result.bounds[1, axis]
    else:
        shift = outer - 0.2 - result.bounds[0, axis]
    translation = np.zeros(3)
    translation[axis] = shift
    result.apply_translation(translation)
    return result


def _front_scrollwork(z: float) -> trimesh.Trimesh:
    depth = ENGRAVING_DEPTH + 0.4
    motif = _scroll_pair(depth)
    motif.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2.0, (1.0, 0.0, 0.0)))
    motif.apply_translation([0.0, 0.0, z])
    return _seat_wall_cutter(motif, CHEST_W / 2.0, -1.0, False)


def _small_skull(depth: float, scale: float = 1.0) -> trimesh.Trimesh:
    """Compact layered skull with brow, cheek, mandible and tooth structure."""
    cranium = _tapered_stroke([
        (-8.0 * scale, -5.0 * scale),
        (-10.0 * scale, 3.0 * scale),
        (-7.0 * scale, 11.0 * scale),
        (0.0, 14.0 * scale),
        (7.0 * scale, 11.0 * scale),
        (10.0 * scale, 3.0 * scale),
        (8.0 * scale, -5.0 * scale),
        (-8.0 * scale, -5.0 * scale),
    ], [
        1.15 * scale,
        1.45 * scale,
        1.8 * scale,
        2.0 * scale,
        1.8 * scale,
        1.45 * scale,
        1.15 * scale,
        1.15 * scale,
    ], depth)
    brow = _tapered_stroke(
        [
            (-7.0 * scale, 5.0 * scale),
            (0.0, 7.0 * scale),
            (7.0 * scale, 5.0 * scale),
        ],
        [1.25 * scale, 1.55 * scale, 1.25 * scale],
        depth * 0.78,
    )
    eyes = [
        _leaf(6.0 * scale, 4.5 * scale, depth,
              (side * 4.3 * scale, 3.0 * scale, 0.0),
              np.deg2rad(12.0 * side))
        for side in (-1.0, 1.0)
    ]
    nose = _leaf(
        4.2 * scale,
        2.6 * scale,
        depth,
        (0.0, -2.0 * scale, 0.0),
        np.pi / 2.0,
    )
    cheeks = [
        _tapered_stroke(
            [
                (side * 7.8 * scale, 0.0),
                (side * 8.5 * scale, -5.5 * scale),
                (side * 4.8 * scale, -8.5 * scale),
            ],
            [1.2 * scale, 1.45 * scale, 1.0 * scale],
            depth * 0.82,
        )
        for side in (-1.0, 1.0)
    ]
    mandible = _tapered_stroke(
        [
            (-5.5 * scale, -8.0 * scale),
            (-4.5 * scale, -12.0 * scale),
            (0.0, -13.2 * scale),
            (4.5 * scale, -12.0 * scale),
            (5.5 * scale, -8.0 * scale),
        ],
        [
            1.05 * scale,
            1.3 * scale,
            1.45 * scale,
            1.3 * scale,
            1.05 * scale,
        ],
        depth * 0.9,
    )
    teeth = [
        _rounded_stroke([
            (x * scale, -11.8 * scale),
            (x * scale, -8.0 * scale),
        ], 0.5 * scale, depth * 0.65)
        for x in (-3.4, -1.1, 1.1, 3.4)
    ]
    return clean(trimesh.util.concatenate([
        cranium, brow, *eyes, nose, *cheeks, mandible, *teeth,
    ]))


def _serpent(depth: float, side: float = 1.0,
             scale: float = 1.0) -> trimesh.Trimesh:
    """Tapered serpent with overlapping scales and a structured open jaw."""
    body_points = [
        (side * 5.0 * scale, -24.0 * scale),
        (side * 10.0 * scale, -20.0 * scale),
        (side * 18.0 * scale, -14.0 * scale),
        (side * 20.0 * scale, -4.0 * scale),
        (side * 17.0 * scale, 4.0 * scale),
        (side * 9.0 * scale, 10.0 * scale),
        (side * 12.0 * scale, 18.0 * scale),
        (side * 22.0 * scale, 23.0 * scale),
        (side * 27.0 * scale, 25.0 * scale),
    ]
    body = _tapered_stroke(
        body_points,
        [
            0.8 * scale,
            1.15 * scale,
            2.0 * scale,
            2.7 * scale,
            2.8 * scale,
            2.45 * scale,
            2.1 * scale,
            1.75 * scale,
            1.4 * scale,
        ],
        depth,
    )
    scales = []
    for index, (x, y, angle) in enumerate((
        (18.8, -11.5, 68.0),
        (20.0, -7.0, 82.0),
        (19.2, -2.5, 102.0),
        (17.2, 2.0, 122.0),
        (13.7, 6.0, 142.0),
        (10.8, 10.5, 62.0),
        (11.8, 15.0, 72.0),
        (15.2, 19.0, 42.0),
        (19.2, 21.7, 25.0),
    )):
        offset = -0.75 if index % 2 else 0.75
        scales.append(_leaf(
            4.2 * scale,
            2.2 * scale,
            depth * (0.52 if index % 2 else 0.62),
            (
                side * (x + offset) * scale,
                y * scale,
                0.0,
            ),
            np.deg2rad(angle if side > 0 else 180.0 - angle),
        ))
    head = _leaf(
        12.5 * scale,
        8.2 * scale,
        depth,
        (side * 32.0 * scale, 26.0 * scale, 0.0),
        np.deg2rad(10.0 if side > 0 else 170.0),
    )
    muzzle = _tapered_stroke(
        [
            (side * 31.0 * scale, 25.5 * scale),
            (side * 38.0 * scale, 25.0 * scale),
        ],
        [2.5 * scale, 1.55 * scale],
        depth * 0.86,
    )
    jaw = _tapered_stroke(
        [
            (side * 29.0 * scale, 23.5 * scale),
            (side * 34.5 * scale, 21.2 * scale),
            (side * 39.0 * scale, 22.5 * scale),
        ],
        [1.25 * scale, 1.05 * scale, 0.75 * scale],
        depth * 0.72,
    )
    eye = cylinder(
        1.0 * scale,
        depth * 0.62,
        (side * 33.0 * scale, 28.0 * scale, 0.0),
    )
    brow = _tapered_stroke(
        [
            (side * 29.5 * scale, 29.0 * scale),
            (side * 34.0 * scale, 29.5 * scale),
            (side * 36.5 * scale, 27.8 * scale),
        ],
        [0.75 * scale, 0.95 * scale, 0.6 * scale],
        depth * 0.7,
    )
    nostril = cylinder(
        0.55 * scale,
        depth * 0.55,
        (side * 37.0 * scale, 26.0 * scale, 0.0),
    )
    fangs = [
        _leaf(
            3.2 * scale,
            1.2 * scale,
            depth * 0.62,
            (side * x * scale, y * scale, 0.0),
            np.deg2rad(angle if side > 0 else 180.0 - angle),
        )
        for x, y, angle in ((34.5, 23.2, -68.0), (37.2, 23.0, -72.0))
    ]
    tongue = _rounded_stroke([
        (side * 39.0 * scale, 22.2 * scale),
        (side * 43.0 * scale, 20.5 * scale),
        (side * 46.0 * scale, 21.5 * scale),
    ], 0.5 * scale, depth * 0.55)
    tongue_fork = [
        _rounded_stroke([
            (side * 45.5 * scale, 21.5 * scale),
            (side * 48.0 * scale, y * scale),
        ], 0.42 * scale, depth * 0.5)
        for y in (20.2, 22.8)
    ]
    return clean(trimesh.util.concatenate([
        body, *scales, head, muzzle, jaw, eye, brow, nostril,
        *fangs, tongue, *tongue_fork,
    ]))


def _rib_cage(depth: float, scale: float = 1.0) -> trimesh.Trimesh:
    """Layered axial skeleton with varied vertebrae and anatomical rib arcs."""
    parts = [
        _tapered_stroke(
            [(0.0, -23.0 * scale), (0.0, 19.0 * scale)],
            [1.3 * scale, 1.65 * scale],
            depth,
        ),
        _small_skull(depth, 0.72 * scale),
    ]
    parts[-1].apply_translation([0.0, 27.0 * scale, 0.0])
    for index, y in enumerate(np.linspace(-19.0, 17.0, 10)):
        radius = (1.15 + 0.22 * np.sin(index * 1.7)) * scale
        vertebra = cylinder(
            radius,
            depth * (0.66 + 0.04 * (index % 3)),
            (0.0, y * scale, 0.0),
        )
        vertebra.apply_scale([1.2, 0.72, 1.0])
        parts.append(clean(vertebra))
    sternum = _tapered_stroke(
        [(0.0, -9.0 * scale), (0.0, 13.0 * scale)],
        [1.45 * scale, 1.05 * scale],
        depth * 0.62,
    )
    parts.append(sternum)
    for index, y in enumerate((-14.0, -7.5, -1.0, 5.5, 12.0)):
        reach = (16.0 + 2.2 * np.sin(index * 0.9)) * scale
        rise = (3.5 + index * 0.75) * scale
        rib_radius = (1.05 - index * 0.055) * scale
        for side in (-1.0, 1.0):
            parts.append(_tapered_stroke(
                [
                    (0.0, y * scale),
                    (side * reach * 0.42, (y + rise) * scale),
                    (side * reach * 0.82, (y + rise * 0.7) * scale),
                    (side * reach, (y + 0.5) * scale),
                    (side * reach * 0.68, (y - 2.5) * scale),
                ],
                [
                    rib_radius,
                    rib_radius * 1.05,
                    rib_radius * 0.9,
                    rib_radius * 0.72,
                    rib_radius * 0.58,
                ],
                depth,
            ))
    clavicles = [
        _tapered_stroke(
            [
                (0.0, 16.0 * scale),
                (side * 7.0 * scale, 19.0 * scale),
                (side * 13.0 * scale, 17.0 * scale),
            ],
            [1.15 * scale, 1.0 * scale, 0.72 * scale],
            depth * 0.85,
        )
        for side in (-1.0, 1.0)
    ]
    pelvis = [
        _leaf(12.0 * scale, 5.5 * scale, depth,
              (-5.5 * scale, -23.0 * scale, 0.0), np.deg2rad(155.0)),
        _leaf(12.0 * scale, 5.5 * scale, depth,
              (5.5 * scale, -23.0 * scale, 0.0), np.deg2rad(25.0)),
    ]
    return clean(trimesh.util.concatenate([*parts, *clavicles, *pelvis]))


def _dragon(depth: float, side: float = 1.0,
            scale: float = 1.0) -> trimesh.Trimesh:
    """Organic dragon with layered wing membranes, joints, claws and face."""
    torso = _tapered_stroke([
        (side * 7.0 * scale, -18.0 * scale),
        (side * 14.0 * scale, -14.0 * scale),
        (side * 19.0 * scale, -7.0 * scale),
        (side * 17.0 * scale, 2.0 * scale),
        (side * 20.0 * scale, 10.0 * scale),
    ], [
        0.75 * scale,
        1.45 * scale,
        2.7 * scale,
        3.4 * scale,
        2.8 * scale,
    ], depth)
    tail = _tapered_stroke([
        (side * 13.0 * scale, -13.0 * scale),
        (side * 5.0 * scale, -18.0 * scale),
        (side * 1.0 * scale, -25.0 * scale),
        (side * 5.0 * scale, -29.0 * scale),
    ], [
        1.55 * scale,
        1.15 * scale,
        0.8 * scale,
        0.48 * scale,
    ], depth * 0.9)
    neck = _tapered_stroke([
        (side * 20.0 * scale, 8.0 * scale),
        (side * 23.0 * scale, 17.0 * scale),
        (side * 28.0 * scale, 24.0 * scale),
        (side * 36.0 * scale, 28.0 * scale),
    ], [
        2.7 * scale,
        2.25 * scale,
        1.75 * scale,
        1.35 * scale,
    ], depth)
    head = _leaf(
        13.5 * scale,
        8.5 * scale,
        depth,
        (side * 41.0 * scale, 29.0 * scale, 0.0),
        np.deg2rad(8.0 if side > 0 else 172.0),
    )
    muzzle = _tapered_stroke(
        [
            (side * 40.0 * scale, 28.0 * scale),
            (side * 47.0 * scale, 27.0 * scale),
        ],
        [2.4 * scale, 1.25 * scale],
        depth * 0.82,
    )
    lower_jaw = _tapered_stroke(
        [
            (side * 38.5 * scale, 26.0 * scale),
            (side * 43.5 * scale, 24.0 * scale),
            (side * 48.0 * scale, 25.5 * scale),
        ],
        [1.15 * scale, 0.95 * scale, 0.58 * scale],
        depth * 0.68,
    )
    wing_root = (side * 17.0 * scale, 7.0 * scale)
    wing_knuckle = (side * 8.0 * scale, 22.0 * scale)
    wing_tips = (
        (side * 0.0 * scale, 32.0 * scale),
        (side * 12.0 * scale, 35.0 * scale),
        (side * 24.0 * scale, 31.0 * scale),
    )
    membranes = [
        _extrude_xy_polygon(
            [wing_root, wing_knuckle, wing_tips[0], wing_tips[1]],
            depth * 0.5,
        ),
        _extrude_xy_polygon(
            [wing_root, wing_tips[1], wing_tips[2]],
            depth * 0.58,
        ),
    ]
    wing_ribs = [
        _tapered_stroke(
            [wing_root, tip],
            [1.35 * scale, 0.68 * scale],
            depth * 0.9,
        )
        for tip in wing_tips
    ]
    wing_edge = _rounded_stroke([
        wing_tips[0],
        wing_tips[1],
        wing_tips[2],
    ], 1.15 * scale, depth)
    leg_paths = (
        [(18.0, -5.0), (28.0, -12.0), (34.0, -9.0)],
        [(14.0, -12.0), (22.0, -23.0), (29.0, -21.0)],
    )
    legs = [
        _tapered_stroke(
            [(side * x * scale, y * scale) for x, y in path],
            [1.65 * scale, 1.25 * scale, 0.78 * scale],
            depth,
        )
        for path in leg_paths
    ]
    claws = []
    for x, y in ((34.0, -9.0), (29.0, -21.0)):
        for offset in (-1.7, 0.0, 1.7):
            claws.append(_tapered_stroke(
                [
                    (side * x * scale, (y + offset * 0.35) * scale),
                    (
                        side * (x + 4.0) * scale,
                        (y + offset - 1.0) * scale,
                    ),
                ],
                [0.62 * scale, 0.38 * scale],
                depth * 0.65,
            ))
    facial = [
        _tapered_stroke(
            [
                (side * 38.0 * scale, 32.0 * scale),
                (side * 42.0 * scale, 32.5 * scale),
                (side * 44.0 * scale, 30.5 * scale),
            ],
            [0.72 * scale, 0.95 * scale, 0.52 * scale],
            depth * 0.68,
        ),
        cylinder(
            0.85 * scale,
            depth * 0.55,
            (side * 42.0 * scale, 31.0 * scale, 0.0),
        ),
        cylinder(
            0.5 * scale,
            depth * 0.5,
            (side * 46.0 * scale, 28.2 * scale, 0.0),
        ),
        _leaf(
            7.0 * scale,
            2.6 * scale,
            depth * 0.78,
            (side * 39.0 * scale, 35.0 * scale, 0.0),
            np.deg2rad(65.0 if side > 0 else 115.0),
        ),
        _leaf(
            5.5 * scale,
            2.2 * scale,
            depth * 0.72,
            (side * 43.0 * scale, 35.0 * scale, 0.0),
            np.deg2rad(78.0 if side > 0 else 102.0),
        ),
    ]
    return clean(trimesh.util.concatenate([
        torso, tail, neck, head, muzzle, lower_jaw,
        *membranes, *wing_ribs, wing_edge, *legs, *claws, *facial,
    ]))


@lru_cache(maxsize=None)
def _relief_field(name: str):
    """Load a cached Blender-sculpted relief height map.

    The map is stored normalised (0..1) so the printed depth stays a decision
    of this generator; see docs/gothic-chest-ornamente-quellen.md.
    """
    path = RELIEF_CACHE / f"{name}.npz"
    if not path.exists():
        raise FileNotFoundError(
            f"missing relief cache {path}; regenerate it with "
            f'blender --background --python scripts/blender_chest_reliefs.py'
        )
    data = np.load(path)
    heights = data["heights"].astype(np.float64)
    ny, nx = heights.shape
    xs = np.linspace(float(data["x0"]), float(data["x1"]), nx)
    ys = np.linspace(float(data["y0"]), float(data["y1"]), ny)
    return xs, ys, heights


def _heightfield_solid(name: str, depth: float) -> trimesh.Trimesh:
    """Closed grid prism carrying a sculpted bas relief on its top face.

    Stacking rounded primitive strokes is what made the old ornaments read as
    flat ribbon graphics.  A height field keeps the organic Blender surface and
    - just as importantly - guarantees printability: because the relief is a
    single-valued function of (x, y), shearing it by ``y += z`` later leaves no
    facet overhanging more than 45 degrees.
    """
    xs, ys, heights = _relief_field(name)
    nx, ny = xs.size, ys.size
    gx, gy = np.meshgrid(xs, ys)
    top_z = heights * depth
    # One binomial pass across the grid.  The ray-cast height map has hard
    # single-sample cliffs at every silhouette, and a cliff sampled on an
    # axis-aligned grid renders - and prints - as a visible staircase.
    kernel = np.array([0.25, 0.5, 0.25])
    for axis in (0, 1):
        padded = np.apply_along_axis(
            lambda row: np.convolve(np.pad(row, 1, mode="edge"), kernel,
                                    mode="valid"),
            axis, top_z)
        top_z = padded
    # The border of a cached field is already ramped to zero, so clamping the
    # outline here only guards against a regenerated map with a live edge.
    top_z[0, :] = top_z[-1, :] = 0.0
    top_z[:, 0] = top_z[:, -1] = 0.0

    top = np.column_stack([gx.ravel(), gy.ravel(), top_z.ravel()])
    # Only four backing-plate corners instead of a mirrored grid: a full second
    # grid doubled the face count and forced the decimator to eat the sculpted
    # surface to stay inside the budget, which is what made the first
    # height-field reliefs look faceted.
    corners = np.array([
        (xs[0], ys[0], -RELIEF_BASE), (xs[-1], ys[0], -RELIEF_BASE),
        (xs[-1], ys[-1], -RELIEF_BASE), (xs[0], ys[-1], -RELIEF_BASE),
    ])
    vertices = np.vstack([top, corners])
    base = nx * ny
    idx = np.arange(base).reshape(ny, nx)

    faces = [np.column_stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(),
                              idx[1:, 1:].ravel()]),
             np.column_stack([idx[:-1, :-1].ravel(), idx[1:, 1:].ravel(),
                              idx[1:, :-1].ravel()]),
             np.array([[base, base + 2, base + 1],
                       [base, base + 3, base + 2]])]

    walls = ((idx[0, :], base + 0, base + 1),        # y = min
             (idx[:, -1], base + 1, base + 2),       # x = max
             (idx[-1, ::-1], base + 2, base + 3),    # y = max
             (idx[::-1, 0], base + 3, base + 0))     # x = min
    for strip, a, b in walls:
        fan = np.column_stack([strip[:-1], strip[1:],
                               np.full(strip.size - 1, a)])
        faces.append(np.vstack([fan, [[strip[-1], b, a]]]))

    mesh = clean(trimesh.Trimesh(vertices=vertices,
                                 faces=np.vstack(faces), process=True))
    mesh.fix_normals()
    if not mesh.is_volume:
        raise RuntimeError(f"relief {name} did not close into a volume")
    target = RELIEF_TARGETS.get(name, 24_000)
    if len(mesh.faces) > target:
        mesh = clean(simplify(mesh, target))
        mesh.fix_normals()
    return mesh


def _creature_panel(kind: str, depth: float) -> trimesh.Trimesh:
    """Sculpted bas relief panel, loaded from the Blender height-map cache."""
    return _heightfield_solid(kind, depth - RELIEF_BASE)


def _wall_creature_reliefs(kind: str, centre,
                           normal_x: bool,
                           sign: float) -> list[trimesh.Trimesh]:
    """Map rounded strokes as 45-degree-growing raised wall reliefs."""
    depth = CREATURE_RELIEF_DEPTH
    face = CHEST_L / 2.0 if normal_x else CHEST_W / 2.0
    reliefs = []
    for component in _creature_panel(kind, depth).split(
            only_watertight=False):
        if not component.is_volume:
            raise RuntimeError(
                f"{kind} relief component is not a closed volume"
            )
        local = component.copy()
        local.vertices[:, 2] -= local.bounds[0, 2]
        local.vertices[:, 1] += local.vertices[:, 2]
        x = local.vertices[:, 0] + centre[0]
        y = local.vertices[:, 1] + centre[2]
        outward = face + local.vertices[:, 2] - 0.6
        if normal_x:
            vertices = np.column_stack([
                sign * outward,
                x,
                y,
            ])
        else:
            vertices = np.column_stack([
                x,
                sign * outward,
                y,
            ])
        relief = clean(trimesh.Trimesh(
            vertices=vertices,
            faces=local.faces.copy(),
            process=True,
        ))
        relief.fix_normals()
        reliefs.append(clean(relief))
    return reliefs


def _lancet_inlay(width: float, height: float, depth: float,
                   centre, normal_x: bool) -> trimesh.Trimesh:
    """Trefoil, dagger and thorn details nested inside a lancet bay."""
    local = [
        _rounded_stroke(
            [(0.0, 7.0), (0.0, height * 0.48)],
            1.45, depth,
        ),
        _quatrefoil(min(4.3, width * 0.14), depth,
                    (0.0, height * 0.61, 0.0)),
        _fleuron(depth, (0.0, height * 0.78, 0.0),
                 min(0.55, width / 58.0)),
    ]
    for side in (-1.0, 1.0):
        local.extend([
            _rounded_stroke([
                (0.0, height * 0.33),
                (side * width * 0.18, height * 0.42),
                (side * width * 0.27, height * 0.53),
            ], 1.15, depth),
            _leaf(width * 0.22, min(4.2, width * 0.13), depth,
                  (side * width * 0.24, height * 0.48, 0.0),
                  np.deg2rad(58.0 if side > 0 else 122.0)),
        ])
    return _place_planar_relief(union(local), centre, normal_x)


def _lid_bat_wings(depth: float, z: float) -> trimesh.Trimesh:
    """Open ribbed bat wings framing the lid skull cartouche."""
    parts = []
    for side in (-1.0, 1.0):
        def mirror(points):
            return [(side * x, y) for x, y in points]

        shoulder = (side * 25.0, -2.0)
        outline = mirror([
            (25.0, -2.0), (43.0, 18.0), (78.0, 24.0),
            (67.0, 8.0), (85.0, -2.0), (64.0, -7.0),
            (75.0, -24.0), (42.0, -17.0),
        ])
        parts.append(_rounded_stroke(outline, 2.0, depth))
        for target in mirror([
            (78.0, 24.0), (67.0, 8.0), (85.0, -2.0),
            (64.0, -7.0), (75.0, -24.0),
        ]):
            parts.append(_rounded_stroke([shoulder, target], 1.35, depth))
        parts.extend([
            _leaf(12.0, 4.4, depth, (side * 79.0, 23.0, 0.0),
                  np.deg2rad(20.0 if side > 0 else 160.0)),
            _leaf(11.0, 4.2, depth, (side * 76.0, -23.0, 0.0),
                  np.deg2rad(-20.0 if side > 0 else 200.0)),
        ])
    motif = union(parts)
    motif.apply_translation([0.0, 0.0, z])
    return clean(motif)


def _wall_decoration(length: float, x_sign: float, y_sign: float,
                     normal_x: bool, arch_count: int,
                     skip_middle: bool = False):
    """Raised frame plus tracery for one wall."""
    face = (CHEST_L / 2.0) if normal_x else (CHEST_W / 2.0)
    sign = x_sign if normal_x else y_sign
    panel_h = BODY_H - PLINTH_H - CORNICE_H - 16.0
    panel_z = PLINTH_H + 8.0 + panel_h / 2.0
    field = length - 2 * PILASTER - 10.0

    cuts = []
    centre = ((0.0, 0.0, panel_z) if normal_x
              else (0.0, 0.0, panel_z))
    cuts.append(_seat_wall_cutter(
        _frame(
            (field, panel_h),
            centre,
            normal_x,
            ENGRAVING_DEPTH + 0.4,
            band=5.0,
        ),
        face,
        sign,
        normal_x,
    ))

    pitch = field / arch_count
    arch_w = min(pitch - 10.0, 36.0)
    arch_h = panel_h - 10.0
    for i in range(arch_count):
        if skip_middle and i == arch_count // 2:
            continue      # the skull trigger sits in the middle bay
        offset = (i - (arch_count - 1) / 2.0) * pitch
        base = panel_z - arch_h / 2.0
        if normal_x:
            spot = (0.0, offset, base)
        else:
            spot = (offset, 0.0, base)
        for lancet in _lancet(
            arch_w,
            arch_h,
            ENGRAVING_DEPTH + 0.4,
            spot,
            normal_x,
        ):
            cuts.append(_seat_wall_cutter(
                lancet,
                face,
                sign,
                normal_x,
            ))
    return cuts, []


def _wall_lightening_pockets() -> list[trimesh.Trimesh]:
    """Thin broad non-functional wall fields from the inside.

    The exterior relief, corner pilasters, lower rail zone and upper hinge/
    anchor zone stay untouched.  Opening the pockets into the main cavity avoids
    enclosed support traps while retaining a 1.6 mm outer skin.
    """
    pocket_z0 = 18.0
    pocket_z1 = 70.0
    pocket_h = pocket_z1 - pocket_z0
    overlap = 0.2
    depth = WALL - ECONOMY_SKIN + overlap
    wall_offset = WALL - depth / 2.0 + overlap
    pockets = []

    # Front is split around the skull trigger; the rear can use one broad bay.
    for x in (-50.0, 50.0):
        pockets.append(box(
            (56.0, depth, pocket_h),
            (x, -CHEST_W / 2.0 + wall_offset, (pocket_z0 + pocket_z1) / 2.0),
        ))
    pockets.append(box(
        (164.0, depth, pocket_h),
        (0.0, CHEST_W / 2.0 - wall_offset, (pocket_z0 + pocket_z1) / 2.0),
    ))

    # Side pockets stop well before the corner pilasters.
    for sign in (-1.0, 1.0):
        pockets.append(box(
            (depth, 84.0, pocket_h),
            (sign * (CHEST_L / 2.0 - wall_offset), 0.0,
             (pocket_z0 + pocket_z1) / 2.0),
        ))
    return pockets


def _pilaster_flutes() -> list[trimesh.Trimesh]:
    """Engraved vertical flutes in the four corner pilasters.

    Recessed ornament is only honest where there is material to lose: the
    pilaster stands PROUD beyond a 2.0 mm wall, so the outward faces carry
    5.0 mm of stock and a 1.2 mm flute leaves 3.8 mm - far above the 1.8 mm
    floor.  Flutes run vertically with domed ends, so the recess never forms a
    horizontal ceiling and costs no support material.
    """
    depth = PILASTER_ENGRAVE_DEPTH
    radius = 2.0
    z0 = PLINTH_H + 4.0
    z1 = BODY_H - CORNICE_H - 9.0
    cutters = []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            cx = sx * (CHEST_L / 2.0 - PILASTER / 2.0 + PROUD)
            cy = sy * (CHEST_W / 2.0 - PILASTER / 2.0 + PROUD)
            faces = (
                (sx * (CHEST_L / 2.0 + PROUD + radius - depth), None, cy),
                (None, sy * (CHEST_W / 2.0 + PROUD + radius - depth), cx),
            )
            for face_x, face_y, along in faces:
                for offset in (-5.2, 0.0, 5.2):
                    if face_x is None:
                        centre = (along + offset, face_y)
                    else:
                        centre = (face_x, along + offset)
                    cutters.append(union([
                        cylinder(radius, z1 - z0,
                                 (centre[0], centre[1], (z0 + z1) / 2.0),
                                 (0.0, 0.0, 1.0)),
                        sphere(radius, (centre[0], centre[1], z0),
                               subdivisions=2),
                        sphere(radius, (centre[0], centre[1], z1),
                               subdivisions=2),
                    ]))
    return cutters


def build_chest(include_decoration: bool = True) -> trimesh.Trimesh:
    """Open-topped gothic chest with internal rails and control bores."""
    shell = rounded_box(
        (CHEST_L, CHEST_W, BODY_H),
        6.0,
        (0.0, 0.0, BODY_H / 2.0),
    )
    cavity = box((CHEST_L - 2 * WALL, CHEST_W - 2 * WALL, BODY_H),
                 (0.0, 0.0, FLOOR + BODY_H / 2.0))

    pilasters = []
    shaft_h = BODY_H - PLINTH_H - CORNICE_H
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            cx = sx * (CHEST_L / 2.0 - PILASTER / 2.0 + PROUD)
            cy = sy * (CHEST_W / 2.0 - PILASTER / 2.0 + PROUD)
            pilasters.append(rounded_box(
                (PILASTER, PILASTER, shaft_h),
                2.8,
                (cx, cy, PLINTH_H + shaft_h / 2.0),
            ))
            # Tapered base and capital preserve the column silhouette without
            # horizontal 1.5 mm ledges that trigger full-height tree supports.
            pilasters.extend([
                _rect_frustum(
                    (PILASTER + 3.0, PILASTER + 3.0),
                    (PILASTER, PILASTER),
                    0.0,
                    PLINTH_H,
                    (cx, cy),
                ),
                _rect_frustum(
                    (PILASTER, PILASTER),
                    (PILASTER + 3.0, PILASTER + 3.0),
                    BODY_H - CORNICE_H - 6.0,
                    BODY_H - CORNICE_H,
                    (cx, cy),
                ),
            ])

    cuts, adds = _wall_lightening_pockets(), []
    if include_decoration:
        cuts = cuts + _pilaster_flutes()
        panel_z = 43.0
        adds.extend(_wall_creature_reliefs(
            "front", (0.0, 0.0, panel_z), False, -1.0))
        adds.extend(_wall_creature_reliefs(
            "rear", (0.0, 0.0, panel_z), False, 1.0))
        adds.extend(_wall_creature_reliefs(
            "side", (0.0, 0.0, panel_z), True, -1.0))
        adds.extend(_wall_creature_reliefs(
            "side", (0.0, 0.0, panel_z), True, 1.0))

    rivet_dimples = []
    if include_decoration:
        for sign in (-1.0, 1.0):
            for x in np.arange(-CHEST_L / 2.0 + 16.0,
                               CHEST_L / 2.0 - 10.0, 24.0):
                for z in (PLINTH_H - 4.0, BODY_H - CORNICE_H + 4.0):
                    rivet_dimples.append(sphere(
                        2.4,
                        (
                            x,
                            sign * (CHEST_W / 2.0 + 1.8),
                            z,
                        ),
                        subdivisions=2,
                    ))
    cuts.extend(rivet_dimples)

    # Keep the functional wall shell independent while cutting rails and
    # bearings. The tapered plinth/cornice are fused only after those booleans,
    # which avoids coplanar intersections in the lower rail band.
    body = union([shell, *pilasters])
    body = difference(body, [cavity])
    for index, cutter in enumerate(cuts):
        body = difference(body, [cutter])
        if not body.is_volume:
            raise RuntimeError(f"chest engraving {index} broke the solid")
    for index, ornament in enumerate(adds):
        if not body.is_volume or not ornament.is_volume:
            raise RuntimeError(
                f"chest ornament {index} is invalid: "
                f"body={body.is_volume}, ornament={ornament.is_volume}"
            )
        body = union([body, ornament])
        if not body.is_volume:
            raise RuntimeError(f"chest ornament {index} broke the solid")

    # Decorative collar around the direct skull-drive shaft.
    collar = difference(
        cylinder(38.0 / 2.0, 6.0, (0.0, -CHEST_W / 2.0 - 1.5, 46.0),
                 (0.0, 1.0, 0.0)),
        [cylinder(31.0 / 2.0, 10.0, (0.0, -CHEST_W / 2.0 - 1.5, 46.0),
                  (0.0, 1.0, 0.0))])
    bearing = cylinder(
        8.0, 16.0,
        (mechanism.DRIVE_AXIS[0], -56.0, mechanism.DRIVE_AXIS[2]),
        (0.0, 1.0, 0.0),
    )
    for index, feature in enumerate((collar, bearing)):
        body = union([body, feature])
        if not body.is_volume:
            raise RuntimeError(f"front bearing feature {index} broke the solid")

    # Function cuts: slider rails and the skull-knob/pinion bearing.
    service = [
        box((CHEST_L, RAIL_D * 2.0, RAIL_W),
            (0.0, -(CHEST_W / 2.0 - FUNCTIONAL_WALL_DATUM), RAIL_Z + RAIL_W / 2.0)),
        box((CHEST_L, RAIL_D * 2.0, RAIL_W),
            (0.0, CHEST_W / 2.0 - FUNCTIONAL_WALL_DATUM, RAIL_Z + RAIL_W / 2.0)),
        cylinder(8.8 / 2.0, 44.0, mechanism.DRIVE_AXIS, (0.0, 1.0, 0.0)),
        box(
            (14.0, 12.0, 24.0),
            (-mechanism.DRIVE_PITCH_R, 58.0, 75.0),
        ),
    ]
    body = difference(body, service)

    # Close the full-depth internal rail grooves with a printable external
    # skin, then add the support-free tapered plinth and cornice around it.
    rail_cover_t = 1.8
    rail_covers = []
    for sign in (-1.0, 1.0):
        inner_y = sign * (CHEST_W / 2.0)
        outer_y = sign * (CHEST_W / 2.0 + rail_cover_t - 0.6)
        profile = [
            (inner_y, RAIL_Z),
            (outer_y, RAIL_Z + abs(outer_y - inner_y)),
            (outer_y, RAIL_Z + RAIL_W),
            (inner_y, RAIL_Z + RAIL_W),
        ]
        if sign < 0:
            profile.reverse()
        rail_covers.append(_extrude_yz_polygon(profile, CHEST_L))
    for cover in rail_covers:
        if not body.is_volume or not cover.is_volume:
            raise RuntimeError(
                f"rail cover input invalid: body={body.is_volume}, "
                f"cover={cover.is_volume}"
            )
        body = union([body, cover])
    for skirt in (
        _stepped_skirt(0.0, PLINTH_H, flip=False),
        _stepped_skirt(BODY_H - CORNICE_H, CORNICE_H, flip=True),
    ):
        body = union([body, skirt])
    # The decorative courses overlap the lower rail band and rear cornice.
    # Re-open only those frozen functional envelopes after the partial rebuild;
    # the outer rail cover begins at the nominal y=60 wall plane and remains.
    body = difference(body, [service[0], service[1], service[3]])

    # Fixed scissor pivots. The scissor pivot sits at x = 0 so the compact platform stays inside
    # the chest over the whole stroke (see docs, kinematics table).
    posts = []
    for sy in (-1.0, 1.0):
        posts.append(box((12.0, 6.0, 14.0),
                         (mechanism.FLOOR_PIVOT_X,
                          sy * mechanism.SCISSOR_Y, FLOOR + 7.0)))
        posts.append(cylinder(6.0, 6.0,
                              (mechanism.FLOOR_PIVOT_X,
                               sy * mechanism.SCISSOR_Y, RAIL_Z),
                              (0.0, 1.0, 0.0)))
    body = union([body, *posts])
    body = difference(body, [
        cylinder(3.2 / 2.0, 80.0,
                 (mechanism.FLOOR_PIVOT_X, 0.0, RAIL_Z),
                 (0.0, 1.0, 0.0))
    ])

    # Hinge on the long rear edge.  Three chest knuckles alternate with four
    # lid knuckles; 1 mm axial gaps stop elephant-foot swelling from binding.
    knuckles = []
    for x in (-66.0, 0.0, 66.0):
        knuckles.append(_extrude_yz_polygon(
            [
                (HINGE_Y - 5.0, BODY_H - 3.0),
                (CHEST_W / 2.0, BODY_H - 3.0),
                (HINGE_Y + 5.0, BODY_H + 3.0),
                (HINGE_Y + 5.0, BODY_H + 7.0),
                (HINGE_Y - 5.0, BODY_H + 7.0),
            ],
            28.0,
            x,
        ))
        knuckles.append(cylinder(5.0, 28.0, (x, HINGE_Y, HINGE_Z),
                                  (1.0, 0.0, 0.0)))
    body = union([body, *knuckles])
    body = difference(body, [cylinder(1.9 / 2.0, CHEST_L + 20.0,
                                      (0.0, HINGE_Y, HINGE_Z),
                                      (1.0, 0.0, 0.0))])
    components = sorted(
        body.split(only_watertight=False),
        key=lambda component: abs(component.volume),
        reverse=True,
    )
    if len(components) != 1:
        debris = components[1:]
        if any(abs(component.volume) > 5.0 for component in debris):
            details = [
                (round(abs(component.volume), 3),
                 np.round(component.bounds, 3).tolist())
                for component in components
            ]
            raise RuntimeError(
                f"chest has disconnected structural components: {details}"
            )
        body = components[0]
    return clean(body)


def build_lid() -> trimesh.Trimesh:
    """Lightweight ribbed Gothic lid printed on its long front edge."""
    top = rounded_box(
        (CHEST_L, CHEST_W, 2.4),
        6.0,
        (0.0, 0.0, LID_H - 1.2),
    )
    frame = difference(
        rounded_box(
            (CHEST_L + 2 * PROUD, CHEST_W + 2 * PROUD, 4.4),
            7.0,
            (0.0, 0.0, 19.6),
        ),
        [rounded_box(
            (CHEST_L - 14.0, CHEST_W - 14.0, 5.4),
            4.5,
            (0.0, 0.0, 19.6),
        )],
    )
    step = difference(
        rounded_box(
            (CHEST_L + PROUD, CHEST_W + PROUD, 6.2),
            6.5,
            (0.0, 0.0, 15.1),
        ),
        [rounded_box(
            (CHEST_L - 10.0, CHEST_W - 10.0, 7.2),
            4.0,
            (0.0, 0.0, 15.1),
        )],
    )
    # A full rectangular plug cannot rotate out of the chest: its front edge
    # sweeps into the front wall during the first opening degrees.  A rear-and-
    # side U-guide seats the lid just as accurately while leaving that sweep
    # volume open.
    spigot_outer_x = CHEST_L - 2 * FUNCTIONAL_WALL_DATUM - 0.6
    spigot_outer_y = CHEST_W - 2 * FUNCTIONAL_WALL_DATUM - 0.6
    spigot_wall = 3.3
    spigot_height = 12.5
    guide_front = -(CHEST_W + 2.0 * PROUD) / 2.0
    guide_rear = (spigot_outer_y - spigot_wall) / 2.0
    ramp_start = -(CHEST_W - 2.0 * WALL) / 2.0
    ramp_end = ramp_start + 12.0
    def guide_profiles(top_z: float) -> list[list[tuple[float, float]]]:
        return [
            [
                (guide_front, 12.0),
                (guide_front, top_z),
                (ramp_start, top_z),
                (ramp_start, 12.0),
            ],
            [
                (ramp_start, 12.0),
                (ramp_start, top_z),
                (ramp_end, top_z),
                (ramp_end, 0.0),
            ],
            [
                (ramp_end, 0.0),
                (ramp_end, top_z),
                (guide_rear, top_z),
                (guide_rear, 0.0),
            ],
        ]

    # The seating guide is an open truss rather than a solid U-shaped plug.
    # Its two side webs start on the selected print edge with a 45-degree lower
    # ramp, so they grow from the bed without slicer support but still clear the
    # chest front wall throughout the opening sweep. Five short rear stop pads
    # replace the former 193 mm unsupported crossbar.
    side_guides = [
        _extrude_yz_polygon(
            profile,
            spigot_wall,
            sx * (spigot_outer_x - spigot_wall) / 2.0,
        )
        for sx in (-1.0, 1.0)
        for profile in guide_profiles(21.8)
    ]
    rib_x = (-80.0, -40.0, 0.0, 40.0, 80.0)
    rear_pads = [
        box(
            (12.0, spigot_wall, spigot_height),
            (x, guide_rear, spigot_height / 2.0),
        )
        for x in rib_x
    ]

    # Each internal truss uses continuous lower and upper chords plus short
    # vertical posts. The openings are visible and inspectable; no closed void
    # relies on slicer infill, and every local bridge is at most 5.5 mm.
    ribs = []
    for x in rib_x:
        ribs.extend([
            *[
                _extrude_yz_polygon(profile, 3.0, x)
                for profile in guide_profiles(spigot_height)
            ],
            box(
                (3.0, guide_rear - guide_front, 3.8),
                (x, (guide_front + guide_rear) / 2.0, 19.9),
            ),
        ])
        ribs.extend([
            box((3.0, 3.0, 5.5), (x, y, 15.25))
            for y in (-40.0, -20.0, 0.0, 20.0, 40.0, guide_rear)
        ])
    body = union([top, frame, step, *side_guides, *rear_pads, *ribs])

    # Sunken field on the lid face.
    floor_z = LID_H - ENGRAVING_DEPTH
    field = rounded_box(
        (CHEST_L - 38.0, CHEST_W - 38.0, ENGRAVING_DEPTH + 0.4),
        7.0,
        (0.0, 0.0, LID_H),
    )
    body = difference(body, [field])

    # Rounded Gothic engraving: the skull, wings and foliage are recessed by
    # less than one millimetre. This keeps the organic detail while eliminating
    # the unsupported lower shelves of a raised vertical relief.
    # The lid prints on its long front edge, so its +y is the print-up
    # direction and the relief depth runs along +z.  The same 45-degree shear
    # that keeps the wall reliefs support-free therefore applies here too.
    engraving_depth = ENGRAVING_DEPTH + 0.4

    # Raised bead frame around the field plus corner bosses.
    bead = difference(
        rounded_box(
            (CHEST_L - 30.0, CHEST_W - 30.0, engraving_depth),
            8.0,
            (0.0, 0.0, LID_H - ENGRAVING_DEPTH / 2.0 + 0.2),
        ),
        [rounded_box(
            (CHEST_L - 42.0, CHEST_W - 42.0, engraving_depth + 1.0),
            6.0,
            (0.0, 0.0, LID_H - ENGRAVING_DEPTH / 2.0 + 0.2),
        )])
    beads = []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            beads.append(sphere(
                5.0,
                (
                    sx * (CHEST_L / 2.0 - 11.0),
                    sy * (CHEST_W / 2.0 - 11.0),
                    LID_H + 4.2,
                ),
                subdivisions=3,
            ))
    lid_engravings = [
        bead,
        *beads,
    ]
    for index, ornament in enumerate(lid_engravings):
        body = difference(body, [ornament])
        if not body.is_volume:
            raise RuntimeError(f"lid engraving {index} produced an invalid solid")

    # Sculpted winged-skull cartouche, raised out of the sunken field.  The
    # previous engraved version was the flattest part of the chest; a raised
    # height-field relief keeps the organic Blender surface and still avoids
    # unsupported shelves thanks to the ``y += z`` shear.
    cartouche = _creature_panel("lid", CREATURE_RELIEF_DEPTH)
    cartouche.vertices[:, 2] -= cartouche.bounds[0, 2]
    cartouche.vertices[:, 1] += cartouche.vertices[:, 2]
    cartouche.vertices[:, 2] += LID_H - ENGRAVING_DEPTH - 0.6
    cartouche = clean(cartouche)
    cartouche.fix_normals()
    if not cartouche.is_volume:
        raise RuntimeError("lid cartouche relief is not a closed volume")
    body = union([body, cartouche])
    if not body.is_volume:
        raise RuntimeError("lid cartouche broke the solid")

    # The decorative rear frame stops at the hinge axis. Material extending
    # behind that axis would dip into the chest rim during the first degrees
    # of opening; only the cylindrical knuckles may project farther rearward.
    body = difference(body, [
        box((CHEST_L + 8.0, 3.0, 18.0), (0.0, 62.5, 9.0))
    ])
    if not body.is_volume:
        raise RuntimeError("lid rear trim broke the solid")

    # Four lid knuckles fill the gaps between the three chest knuckles.
    lid_segments = ((-90.0, 18.0), (-33.0, 36.0),
                    (33.0, 36.0), (90.0, 18.0))
    knuckles = [
        difference(
            cylinder(
                5.0,
                length,
                (x, HINGE_Y, LID_H - 5.0),
                (1.0, 0.0, 0.0),
            ),
            [cylinder(
                2.0 / 2.0,
                length + 2.0,
                (x, HINGE_Y, LID_H - 5.0),
                (1.0, 0.0, 0.0),
            )],
        )
        for x, length in lid_segments
    ]
    body = union([body, *knuckles])
    if not body.is_volume:
        raise RuntimeError("lid knuckles broke the solid")

    # Rebuild only the rear seating region around frozen chest-side hardware.
    # Alternating pockets clear the three chest hinge supports; the small
    # right-hand notch remains as assembly clearance below the rim.
    clearance_pockets = [
        box((30.0, 12.0, 18.0), (x, HINGE_Y, 16.5))
        for x in (-66.0, 0.0, 66.0)
    ]
    clearance_pockets.append(box((16.0, 9.0, 9.0), (70.0, 54.5, 4.0)))
    # Narrow service channel for the rigid lid rack and hinge sector.  It
    # replaces a slice of one lid knuckle without weakening the other three.
    clearance_pockets.append(box(
        (14.0, 20.0, 26.0),
        (-mechanism.DRIVE_PITCH_R, mechanism.LID_RACK_Y, 13.0),
    ))
    for index, cutter in enumerate(clearance_pockets):
        body = difference(body, [cutter])
        if not body.is_volume:
            raise RuntimeError(f"lid clearance {index} broke the solid")
    components = sorted(
        body.split(only_watertight=False),
        key=lambda component: abs(component.volume),
        reverse=True,
    )
    if len(components) != 1:
        sliver_volumes = [abs(component.volume) for component in components[1:]]
        if max(sliver_volumes) > 50.0 or sum(sliver_volumes) > 100.0:
            details = [
                (round(abs(component.volume), 3), np.round(component.bounds, 3).tolist())
                for component in components
            ]
            raise RuntimeError(
                f"lid has disconnected structural components: {details}"
            )
        body = components[0]
    return clean(body)


if __name__ == "__main__":
    for name, mesh in (("chest", build_chest()), ("lid", build_lid())):
        print(f"{name:6s} faces {len(mesh.faces):6d} watertight {mesh.is_watertight} "
              f"bodies {len(mesh.split(only_watertight=False))} "
              f"euler {mesh.euler_number} extents {np.round(mesh.extents, 1).tolist()}")
        mesh.export(f"model-sources/ghouls-grip/reference/_{name}.stl")
    _ = intersection
