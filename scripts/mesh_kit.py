"""Small shared helpers for the generator scripts: primitives and booleans.

Keeping them in one place lets the chest, the relief ornaments and the skeletal
hand share the exact same cleanup policy, so every intermediate solid that goes
into a boolean is already watertight and deduplicated.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import trimesh
import trimesh.boolean as tb


def clean(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    result = mesh.copy()
    result.vertices = np.round(result.vertices, 3)
    result.merge_vertices()
    result.update_faces(result.unique_faces())
    result.update_faces(result.nondegenerate_faces())
    result.remove_unreferenced_vertices()
    result.fix_normals()
    return result


def box(extents: Sequence[float], center: Sequence[float] = (0.0, 0.0, 0.0),
        rotation=None) -> trimesh.Trimesh:
    mesh = trimesh.creation.box(extents=np.asarray(extents, dtype=float))
    if rotation is not None:
        angle, axis = rotation
        mesh.apply_transform(trimesh.transformations.rotation_matrix(angle, axis))
    mesh.apply_translation(np.asarray(center, dtype=float))
    return mesh


def cylinder(radius: float, height: float,
             center: Sequence[float] = (0.0, 0.0, 0.0),
             axis: Sequence[float] = (0.0, 0.0, 1.0),
             sections: int = 64) -> trimesh.Trimesh:
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    axis = np.asarray(axis, dtype=float)
    axis = axis / np.linalg.norm(axis)
    if not np.allclose(axis, (0.0, 0.0, 1.0)):
        rot = trimesh.geometry.align_vectors([0.0, 0.0, 1.0], axis)
        mesh.apply_transform(rot)
    mesh.apply_translation(np.asarray(center, dtype=float))
    return mesh


def sphere(radius: float, center: Sequence[float] = (0.0, 0.0, 0.0),
           subdivisions: int = 3) -> trimesh.Trimesh:
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius)
    mesh.apply_translation(np.asarray(center, dtype=float))
    return mesh


def rounded_box(extents: Sequence[float], radius: float,
                center: Sequence[float] = (0.0, 0.0, 0.0)) -> trimesh.Trimesh:
    """Box with rounded vertical edges - the standard chest/plate blank."""
    ex, ey, ez = (float(v) for v in extents)
    radius = min(radius, ex / 2.0 - 0.1, ey / 2.0 - 0.1)
    core = [
        box((ex - 2 * radius, ey, ez)),
        box((ex, ey - 2 * radius, ez)),
    ]
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            core.append(cylinder(radius, ez,
                                 (sx * (ex / 2 - radius), sy * (ey / 2 - radius), 0.0)))
    mesh = union(core)
    mesh.apply_translation(np.asarray(center, dtype=float))
    return clean(mesh)


def prism(outline: Sequence[Sequence[float]], z_lo: float, z_hi: float) -> trimesh.Trimesh:
    """Convex prism through a 2D outline.

    ``shapely`` is unavailable in this repo, so polygon extrusion goes through a
    convex hull of the duplicated outline instead.  Only convex outlines are
    reproduced faithfully; concave shapes must be assembled from several prisms.
    """
    pts = np.asarray(outline, dtype=float)
    cloud = np.vstack([
        np.column_stack([pts, np.full(len(pts), z_lo)]),
        np.column_stack([pts, np.full(len(pts), z_hi)]),
    ])
    return clean(trimesh.convex_hull(cloud))


def union(parts: Iterable[trimesh.Trimesh]) -> trimesh.Trimesh:
    parts = [p for p in parts if p is not None]
    if len(parts) == 1:
        return clean(parts[0])
    return clean(tb.union(parts, engine="manifold"))


def difference(body: trimesh.Trimesh,
               cutters: Iterable[trimesh.Trimesh]) -> trimesh.Trimesh:
    cutters = [c for c in cutters if c is not None]
    if not cutters:
        return clean(body)
    return clean(tb.difference([body, *cutters], engine="manifold"))


def intersection(parts: Iterable[trimesh.Trimesh]) -> trimesh.Trimesh:
    return clean(tb.intersection(list(parts), engine="manifold"))


def arc_band(radius: float, width: float, thickness: float,
             start: float, end: float, center: Sequence[float] = (0.0, 0.0, 0.0),
             sections: int = 96) -> trimesh.Trimesh:
    """Sector of an annulus extruded along Z - the building block of tracery.

    Angles are radians in the XY plane.  Used for gothic ogee arches, which a
    hull of two circles cannot reproduce.
    """
    outer = cylinder(radius + width / 2.0, thickness, sections=sections)
    inner = cylinder(radius - width / 2.0, thickness + 2.0, sections=sections)
    ring = difference(outer, [inner])

    span = end - start
    keep = []
    steps = max(1, int(np.ceil(span / (np.pi / 2.5))))
    reach = radius + width
    for i in range(steps):
        a0 = start + span * i / steps
        a1 = start + span * (i + 1) / steps
        mid = (a0 + a1) / 2.0
        half = (a1 - a0) / 2.0
        depth = reach / max(np.cos(half), 1e-6)
        wedge = box((depth, 2.0 * depth * np.tan(half) + 0.01, thickness + 2.0),
                    (depth / 2.0, 0.0, 0.0))
        wedge.apply_transform(
            trimesh.transformations.rotation_matrix(mid, (0.0, 0.0, 1.0))
        )
        keep.append(intersection([ring, wedge]))
    sector = union(keep)
    sector.apply_translation(np.asarray(center, dtype=float))
    return clean(sector)


def simplify(mesh: trimesh.Trimesh, target_faces: int) -> trimesh.Trimesh:
    """Reduce face count while keeping the body closed.

    Voxel fusion and marching cubes produce millions of tiny triangles that
    would blow up an ASCII STL, so every organic body is decimated before it
    enters a boolean. If the reduction opens the shell the original is kept.
    """
    if len(mesh.faces) <= target_faces:
        return mesh
    import fast_simplification

    verts, faces = fast_simplification.simplify(
        np.asarray(mesh.vertices, dtype=np.float32),
        np.asarray(mesh.faces, dtype=np.int32),
        target_count=int(target_faces))
    reduced = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    reduced.merge_vertices()
    reduced.fix_normals()
    if reduced.is_watertight and reduced.is_winding_consistent and reduced.volume > 0:
        return clean(reduced)
    return mesh


def simplify_tolerance(mesh: trimesh.Trimesh,
                       tolerance: float = 0.01) -> trimesh.Trimesh:
    """Remove sub-tolerance facets through manifold3d without opening holes.

    This is useful after several boolean cuts: a mesh can be watertight yet
    contain numerically tiny facets that OrcaSlicer refuses to process.
    """
    import manifold3d

    source = manifold3d.Mesh(
        np.asarray(mesh.vertices, dtype=np.float32),
        np.asarray(mesh.faces, dtype=np.uint32))
    solid = manifold3d.Manifold(source)
    if solid.status() != manifold3d.Error.NoError:
        return clean(mesh)
    result_mesh = solid.simplify(tolerance).to_mesh()
    result = trimesh.Trimesh(
        vertices=np.asarray(result_mesh.vert_properties)[:, :3],
        faces=np.asarray(result_mesh.tri_verts), process=True)
    result.fix_normals()
    if (result.is_watertight and result.is_winding_consistent
            and result.volume > 0.0):
        return clean(result)
    return clean(mesh)


def orient_for_print(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    result = mesh.copy()
    result.apply_translation([0.0, 0.0, -result.bounds[0, 2]])
    return clean(result)


def fuse(meshes: Sequence[trimesh.Trimesh], pitch: float = 0.5,
         bridge: float = 1.4, smooth: float = 0.6) -> trimesh.Trimesh:
    """Fuse touching or nearly touching solids into one printable body.

    Separate bones of a skeleton only graze each other at the joints, so a
    boolean union leaves them as disconnected shells. A morphological closing
    on a voxel occupancy grid bridges exactly those narrow gaps - a gap wider
    than ``2 * bridge`` stays open - and marching cubes over the resulting
    distance field returns a single smooth watertight solid instead of a
    stair-stepped voxel block.
    """
    from scipy import ndimage
    from skimage import measure

    meshes = [m for m in meshes if m is not None]
    verts = np.vstack([m.vertices for m in meshes])
    pad = bridge + 4.0 * pitch
    lo = verts.min(axis=0) - pad
    hi = verts.max(axis=0) + pad
    dims = np.ceil((hi - lo) / pitch).astype(int) + 1

    occupancy = np.zeros(tuple(dims), dtype=bool)
    for mesh in meshes:
        grid = mesh.voxelized(pitch=pitch).fill()
        idx = np.round((grid.points - lo) / pitch).astype(int)
        keep = np.all((idx >= 0) & (idx < dims), axis=1)
        idx = idx[keep]
        occupancy[idx[:, 0], idx[:, 1], idx[:, 2]] = True
    if not occupancy.any():
        raise RuntimeError("voxelisation produced an empty grid")

    radius = bridge / pitch
    outside = ndimage.distance_transform_edt(~occupancy)
    dilated = outside <= radius
    inside = ndimage.distance_transform_edt(dilated)
    closed = inside >= radius
    closed |= occupancy

    # Signed distance of the closed set, lightly smoothed so marching cubes
    # sees a continuous surface rather than the voxel staircase.
    field = (ndimage.distance_transform_edt(~closed)
             - ndimage.distance_transform_edt(closed)) * pitch
    if smooth > 0.0:
        field = ndimage.gaussian_filter(field, smooth)
    field = np.pad(field, 1, mode="constant", constant_values=float(np.max(field)) + 1.0)

    for level in (0.0, 0.004, 0.013, 0.03, 0.06):
        verts_mc, faces_mc, _, _ = measure.marching_cubes(
            field, level=level, spacing=(pitch,) * 3)
        result = trimesh.Trimesh(vertices=verts_mc + (lo - pitch),
                                 faces=faces_mc, process=True)
        result.merge_vertices()
        result.fix_normals()
        if result.is_watertight and result.is_winding_consistent:
            return clean(result)
    raise RuntimeError("fused surface stays non-manifold at every iso level")
