"""Mesh organic bone-like solids from blended capsule fields.

Skeletal bones are not primitives: every long bone is a slim shaft with two
swollen articular heads, and neighbouring bones of one finger have to merge
into a single printable body without a crease.  Boolean unions of cylinders and
spheres always leave those creases, so the bones are described as a list of
round cones (tapered capsules) whose signed distance fields are combined with a
polynomial smooth minimum and re-meshed with marching cubes.

The same machinery builds the skull relief: eye sockets and the nasal aperture
are subtracted as smooth maxima so they blend into the cranium instead of
cutting a sharp rim into it.

``round_cone_sdf`` and ``smin`` are reused from :mod:`sdf_blend`.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import trimesh
from skimage import measure

from sdf_blend import round_cone_sdf, smin


Segment = tuple[Sequence[float], Sequence[float], float, float]


def sphere(center: Sequence[float], radius: float) -> Segment:
    """A round cone whose two ends coincide degenerates to a sphere."""
    return (tuple(center), tuple(center), radius, radius)


def bone(a: Sequence[float], b: Sequence[float], shaft: float,
         head_a: float | None = None, head_b: float | None = None,
         waist: float = 0.42) -> list[Segment]:
    """A long bone: two articular heads joined by a tapered diaphysis.

    ``waist`` is the fraction of the bone length taken up by the slim middle
    section; the remainder flares out into the heads.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    head_a = shaft * 1.45 if head_a is None else head_a
    head_b = shaft * 1.35 if head_b is None else head_b
    t0 = (1.0 - waist) * 0.5
    t1 = 1.0 - t0
    m0 = a + (b - a) * t0
    m1 = a + (b - a) * t1
    return [
        (a, m0, head_a, shaft),
        (m0, m1, shaft, shaft),
        (m1, b, shaft, head_b),
    ]


def smax(a: np.ndarray, b: np.ndarray, k: float) -> np.ndarray:
    """Smooth maximum - the complement of :func:`smin`."""
    return -smin(-a, -b, k)


def _accumulate(field: np.ndarray, grid: np.ndarray, lo: np.ndarray,
                pitch: float, segments: Iterable[Segment], blend: float,
                combine) -> None:
    dims = np.asarray(field.shape)
    for a, b, r1, r2 in segments:
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)
        reach = max(r1, r2) + blend + 3.0 * pitch
        i0 = np.clip(np.floor((np.minimum(a, b) - reach - lo) / pitch).astype(int),
                     0, dims - 1)
        i1 = np.clip(np.ceil((np.maximum(a, b) + reach - lo) / pitch).astype(int) + 1,
                     0, dims)
        if np.any(i1 <= i0):
            continue
        sl = tuple(slice(i0[i], i1[i]) for i in range(3))
        d = round_cone_sdf(grid[sl], a, b, r1, r2)
        field[sl] = combine(field[sl], d)


def segment_mesh(segments: Sequence[Segment], pitch: float = 0.55,
                 blend: float = 1.2, voids: Sequence[Segment] = (),
                 void_blend: float = 0.0, pad: float = 4.0,
                 clip_below: float | None = None) -> trimesh.Trimesh:
    """Marching-cubes mesh of ``smin`` over ``segments`` minus ``voids``."""
    if not segments:
        raise ValueError("segment_mesh needs at least one segment")

    points = []
    for a, b, r1, r2 in segments:
        r = max(r1, r2)
        points.append(np.asarray(a, dtype=float) - r)
        points.append(np.asarray(a, dtype=float) + r)
        points.append(np.asarray(b, dtype=float) - r)
        points.append(np.asarray(b, dtype=float) + r)
    stacked = np.asarray(points, dtype=float)
    lo = stacked.min(axis=0) - pad
    hi = stacked.max(axis=0) + pad

    dims = np.ceil((hi - lo) / pitch).astype(int) + 1
    axes = [lo[i] + np.arange(dims[i]) * pitch for i in range(3)]
    grid = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1)
    far = float(np.linalg.norm(hi - lo))

    field = np.full(tuple(dims), far, dtype=float)
    if blend > 0.0:
        _accumulate(field, grid, lo, pitch, segments, blend,
                    lambda cur, d: smin(cur, d, blend))
    else:
        _accumulate(field, grid, lo, pitch, segments, 0.0, np.minimum)

    if voids:
        void = np.full(tuple(dims), far, dtype=float)
        _accumulate(void, grid, lo, pitch, voids, void_blend,
                    np.minimum if void_blend <= 0.0
                    else (lambda cur, d: smin(cur, d, void_blend)))
        field = (smax(field, -void, void_blend) if void_blend > 0.0
                 else np.maximum(field, -void))

    if clip_below is not None:
        field = np.maximum(field, clip_below - grid[..., 2])

    field = np.pad(field, 1, mode="constant", constant_values=far)

    # A grid sample landing exactly on the iso-surface makes marching cubes emit
    # a non-manifold pinch.  Only non-negative offsets are tried: they erode the
    # solid by a few thousandths of a millimetre, which never grows it into a
    # neighbouring feature.
    last = None
    for level in (0.0, 0.004, 0.011, 0.025, 0.05, 0.09, 0.15):
        verts, faces, _, _ = measure.marching_cubes(field, level=level,
                                                    spacing=(pitch,) * 3)
        verts = verts + (lo - pitch)
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
        mesh.merge_vertices()
        mesh.fix_normals()
        last = mesh
        if mesh.is_watertight and mesh.is_winding_consistent:
            return mesh

    raise RuntimeError(
        "capsule surface stays non-manifold at every iso level "
        f"(watertight={last.is_watertight}, winding={last.is_winding_consistent})"
    )


def chain(points: Sequence[Sequence[float]],
          radii: Sequence[float]) -> list[Segment]:
    """Round cones through a polyline with per-node radii."""
    if len(points) != len(radii):
        raise ValueError("chain needs one radius per point")
    return [
        (points[i], points[i + 1], radii[i], radii[i + 1])
        for i in range(len(points) - 1)
    ]
