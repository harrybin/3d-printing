"""Gothic chest and lid for the Ghoul's Grip automaton.

Everything decorative is modelled as real geometry rather than a texture: the
chest is a shell with a stepped plinth and cornice, corner pilasters, sunken
panels and lancet tracery built from annulus sectors, because a pointed arch
cannot be hulled from two circles. Every relief stands at least 1.2 mm proud,
well above the 0.4 mm a 0.4 mm nozzle can resolve.

The chest prints upright and the lid prints face down, so no decorated surface
is ever a bridge.
"""

from __future__ import annotations

import numpy as np
import trimesh

import mechanism
from mesh_kit import (arc_band, box, clean, cylinder, difference,
                      intersection, rounded_box, sphere, union)
from skull import skull_relief

CHEST_L = 200.0
CHEST_W = 120.0
BODY_H = 86.0
LID_H = 24.0
WALL = 3.0
FLOOR = 3.0

PLINTH_H = 10.0
CORNICE_H = 8.0
PROUD = 3.0            # how far plinth, cornice and pilasters stand out
PILASTER = 19.0
PANEL_DEPTH = 2.5
RELIEF = 2.6
ECONOMY_SKIN = 1.2    # three-line visual shell behind internal lightening pockets

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
    return [union([
        arch,
        _lancet_inlay(width, height, depth, inlay_centre, normal_x),
    ])]


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


def _front_scrollwork(z: float) -> list[trimesh.Trimesh]:
    depth = RELIEF + 1.5
    motif = _scroll_pair(depth)
    # Local Y becomes world Z and local Z becomes -world Y.
    motif.apply_transform(trimesh.transformations.rotation_matrix(
        np.pi / 2.0, (1.0, 0.0, 0.0)))
    motif.apply_translation([0.0,
                             -CHEST_W / 2.0 - (RELIEF - 1.5) / 2.0,
                             z])
    # A shallow plaque gives every thorn and leaf a robust common root instead
    # of relying on coincident contacts between many small relief islands.
    backing = box(
        (142.0, 3.0, 56.0),
        (0.0, -CHEST_W / 2.0 + 0.2, 46.0),
    )
    return [union([backing, motif])]


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

    adds = []
    # Decoration is sunk 1.5 mm into the wall so the union has real overlap
    # instead of a tangential knife edge.
    frame_plane = face + (PANEL_DEPTH - 1.5) / 2.0
    centre = ((sign * frame_plane, 0.0, panel_z) if normal_x
              else (0.0, sign * frame_plane, panel_z))
    adds.append(_frame((field, panel_h), centre, normal_x, PANEL_DEPTH + 1.5))

    pitch = field / arch_count
    arch_w = min(pitch - 10.0, 36.0)
    arch_h = panel_h - 10.0
    plane = face + (RELIEF - 1.5) / 2.0
    for i in range(arch_count):
        if skip_middle and i == arch_count // 2:
            continue      # the skull trigger sits in the middle bay
        offset = (i - (arch_count - 1) / 2.0) * pitch
        base = panel_z - arch_h / 2.0
        if normal_x:
            spot = (sign * plane, offset, base)
        else:
            spot = (offset, sign * plane, base)
        adds += _lancet(arch_w, arch_h, RELIEF + 1.5, spot, normal_x)
    return [], adds


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


def build_chest() -> trimesh.Trimesh:
    """Open-topped gothic chest with internal rails and control bores."""
    shell = box((CHEST_L, CHEST_W, BODY_H), (0.0, 0.0, BODY_H / 2.0))
    cavity = box((CHEST_L - 2 * WALL, CHEST_W - 2 * WALL, BODY_H),
                 (0.0, 0.0, FLOOR + BODY_H / 2.0))

    pilasters = []
    shaft_h = BODY_H - PLINTH_H - CORNICE_H
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            cx = sx * (CHEST_L / 2.0 - PILASTER / 2.0 + PROUD)
            cy = sy * (CHEST_W / 2.0 - PILASTER / 2.0 + PROUD)
            pilasters.append(box((PILASTER, PILASTER, shaft_h),
                                 (cx, cy, PLINTH_H + shaft_h / 2.0)))
            # Tapered base and capital preserve the column silhouette without
            # horizontal 1.5 mm ledges that trigger full-height tree supports.
            pilasters.extend([
                _rect_frustum(
                    (PILASTER + 3.0, PILASTER + 3.0),
                    (PILASTER, PILASTER),
                    PLINTH_H,
                    PLINTH_H + 6.0,
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
    front_plaque = _front_scrollwork(40.0)[0]
    for normal_x, sign, length, count, skip in ((False, 1.0, CHEST_L, 3, False),
                                                (True, -1.0, CHEST_W, 2, False),
                                                (True, 1.0, CHEST_W, 2, False)):
        c, a = _wall_decoration(length, sign, sign, normal_x, count, skip)
        cuts += c
        adds += a

    # The concept art is dominated by raised acanthus scrolls.  Lancet arches
    # alone read as plain architecture, so a deep paired curl frames the skull
    # trigger on the front while preserving the 3 mm structural wall.
    rivets = []
    for sign in (-1.0, 1.0):
        for x in np.arange(-CHEST_L / 2.0 + 16.0, CHEST_L / 2.0 - 10.0, 24.0):
            for z in (PLINTH_H - 4.0, BODY_H - CORNICE_H + 4.0):
                rivets.append(sphere(2.4, (x, sign * (CHEST_W / 2.0 + PROUD - 1.0), z),
                                     subdivisions=2))

    # Keep the functional wall shell independent while cutting rails and
    # bearings. The tapered plinth/cornice are fused only after those booleans,
    # which avoids coplanar intersections in the lower rail band.
    body = union([shell, *pilasters, front_plaque])
    body = difference(body, [cavity, *cuts])
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
            (0.0, -(CHEST_W / 2.0 - WALL), RAIL_Z + RAIL_W / 2.0)),
        box((CHEST_L, RAIL_D * 2.0, RAIL_W),
            (0.0, CHEST_W / 2.0 - WALL, RAIL_Z + RAIL_W / 2.0)),
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
    rail_cover_y = CHEST_W / 2.0 + rail_cover_t / 2.0 - 0.6
    rail_covers = [
        box(
            (CHEST_L, rail_cover_t, RAIL_W),
            (0.0, sign * rail_cover_y, RAIL_Z + RAIL_W / 2.0),
        )
        for sign in (-1.0, 1.0)
    ]
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
    for index, rivet in enumerate(rivets):
        body = union([body, rivet])
        if not body.is_volume:
            raise RuntimeError(f"chest rivet {index} broke the solid")
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
    return clean(body)


def build_lid() -> trimesh.Trimesh:
    """Flat-topped gothic lid with a skull cartouche, printed face down."""
    top = box((CHEST_L, CHEST_W, 6.0), (0.0, 0.0, LID_H - 3.0))
    frame = box((CHEST_L + 2 * PROUD, CHEST_W + 2 * PROUD, 6.0),
                (0.0, 0.0, LID_H - 9.0))
    step = box((CHEST_L + PROUD, CHEST_W + PROUD, 3.0),
               (0.0, 0.0, LID_H - 10.5))
    # A full rectangular plug cannot rotate out of the chest: its front edge
    # sweeps into the front wall during the first opening degrees.  A rear-and-
    # side U-guide seats the lid just as accurately while leaving that sweep
    # volume open.
    spigot_outer_x = CHEST_L - 2 * WALL - 0.6
    spigot_outer_y = CHEST_W - 2 * WALL - 0.6
    spigot_wall = 3.3
    side_length = spigot_outer_y - 18.0
    spigot = union([
        box((spigot_outer_x, spigot_wall, 12.0),
            (0.0, (spigot_outer_y - spigot_wall) / 2.0, 6.0)),
        box((spigot_wall, side_length, 12.0),
            (-(spigot_outer_x - spigot_wall) / 2.0, 9.0, 6.0)),
        box((spigot_wall, side_length, 12.0),
            ((spigot_outer_x - spigot_wall) / 2.0, 9.0, 6.0)),
    ])

    body = union([top, frame, step, spigot])

    # Narrow underside channels replace the former mostly solid 12 mm slab with
    # a 2.0 mm face skin, a wide perimeter and a rib grid. Each channel now has
    # a 45-degree tapered roof and only a short final bridge, rather than a
    # broad horizontal ceiling that forces tree support. The
    # seating guide, hinge, catch and opening-band interfaces are added outside
    # these channels and retain their original dimensions.
    pocket_z0 = 9.0
    pocket_z1 = 17.0
    lid_pockets = [
        box((80.0, 10.0, 5.0), (x, y, pocket_z0 + 2.5))
        for x in (-50.0, 50.0)
        for y in (-39.0, -25.0, -11.0, 11.0, 25.0, 39.0)
    ]
    lid_pockets += [
        _rect_frustum(
            (80.0, 10.0), (72.0, 2.0), pocket_z0 + 5.0, pocket_z1,
            (x, y),
        )
        for x in (-50.0, 50.0)
        for y in (-39.0, -25.0, -11.0, 11.0, 25.0, 39.0)
    ]
    body = difference(body, lid_pockets)

    # Sunken field on the lid face.
    floor_z = LID_H - PANEL_DEPTH
    field = rounded_box((CHEST_L - 38.0, CHEST_W - 38.0, PANEL_DEPTH * 2.0),
                        4.0, (0.0, 0.0, LID_H))
    body = difference(body, [field])

    # Skull cartouche, sunk 1.5 mm into the field so the union really overlaps.
    cartouche = skull_relief(1.5, depth=RELIEF + PANEL_DEPTH)
    cartouche.apply_translation([0.0, 0.0, floor_z - 1.5])

    # Raised bead frame around the field plus corner bosses.
    bead = difference(
        box((CHEST_L - 30.0, CHEST_W - 30.0, PANEL_DEPTH + 1.5),
            (0.0, 0.0, floor_z + (PANEL_DEPTH - 1.5) / 2.0)),
        [box((CHEST_L - 42.0, CHEST_W - 42.0, PANEL_DEPTH + 6.0),
             (0.0, 0.0, floor_z))])
    beads = []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            beads.append(sphere(5.0, (sx * (CHEST_L / 2.0 - 11.0),
                                      sy * (CHEST_W / 2.0 - 11.0),
                                      LID_H - 1.5), subdivisions=3))
    bat_wings = _lid_bat_wings(
        RELIEF + 1.5,
        floor_z + (RELIEF - 1.5) / 2.0,
    )
    corner_foils = []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            corner_foils.append(_quatrefoil(
                4.3,
                RELIEF + 1.5,
                (
                    sx * (CHEST_L / 2.0 - 22.0),
                    sy * (CHEST_W / 2.0 - 22.0),
                    floor_z + (RELIEF - 1.5) / 2.0,
                ),
            ))

    lid_ornaments = [
        cartouche,
        bead,
        *bat_wings.split(only_watertight=False),
        *beads,
        *corner_foils,
    ]
    for index, ornament in enumerate(lid_ornaments):
        body = union([body, ornament])
        if not body.is_volume:
            raise RuntimeError(f"lid ornament {index} produced an invalid solid")

    # The decorative rear frame stops at the hinge axis. Material extending
    # behind that axis would dip into the chest rim during the first degrees
    # of opening; only the cylindrical knuckles may project farther rearward.
    body = difference(body, [
        box((CHEST_L + 8.0, 3.0, 18.0), (0.0, 62.5, 9.0))
    ])

    # Four lid knuckles fill the gaps between the three chest knuckles.
    lid_segments = ((-90.0, 18.0), (-33.0, 36.0),
                    (33.0, 36.0), (90.0, 18.0))
    knuckles = [cylinder(5.0, length, (x, HINGE_Y, LID_H - 5.0),
                         (1.0, 0.0, 0.0)) for x, length in lid_segments]
    body = union([body, *knuckles])
    body = difference(body, [cylinder(2.0 / 2.0, CHEST_L + 24.0,
                                      (0.0, HINGE_Y, LID_H - 5.0),
                                      (1.0, 0.0, 0.0))])

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
    return clean(difference(body, clearance_pockets))


if __name__ == "__main__":
    for name, mesh in (("chest", build_chest()), ("lid", build_lid())):
        print(f"{name:6s} faces {len(mesh.faces):6d} watertight {mesh.is_watertight} "
              f"bodies {len(mesh.split(only_watertight=False))} "
              f"euler {mesh.euler_number} extents {np.round(mesh.extents, 1).tolist()}")
        mesh.export(f"model-sources/ghouls-grip/reference/_{name}.stl")
    _ = intersection
