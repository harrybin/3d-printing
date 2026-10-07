"""Extract one anatomically correct hand skeleton from the NIH 3D reference.

Source model
------------
NIH 3D Print Exchange, entry 3DPX-016815
"Wrist Bones Full Hand_Human Skeleton" by My Segmenter (mysegmenter.com)
https://3d.nih.gov/entries/3DPX-016815 - licensed CC-BY.

The download holds both hands as 54 individually watertight bone shells. This
script isolates the right hand, rotates it into the canonical frame used by the
Ghoul's Grip generator, names every bone, decimates it to a printable face
budget and caches the result as ``hand_bones.npz`` so the generator never has
to touch the 12 MB original.

Canonical frame
---------------
``+Y`` points from the wrist towards the fingertips, ``+Z`` is dorsal (the back
of the hand), ``+X`` points towards the thumb, and the origin sits in the
centre of the carpal block.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "model-sources" / "ghouls-grip" / "reference" / "nih-3dpx-016815-hand.stl"
CACHE = ROOT / "model-sources" / "ghouls-grip" / "reference" / "hand_bones.npz"

FACE_BUDGET = 1400  # per bone; 27 bones stay well under a sane ASCII STL size

DOWNLOAD = (
    "https://3d.nih.gov/api/submissions/22638/runs/"
    "c22644d8-ffe9-4939-a21d-2693460da9aa/output-files/497335"
)

RAYS = ("thumb", "index", "middle", "ring", "little")


def proximity_groups(bodies, threshold: float = 4.0) -> list[list[int]]:
    """Group bone shells into hands by surface proximity.

    The two hands sit in a V with their wrists close together, so clustering
    bone centroids misassigns the carpals. Articulating bones of one hand are
    always within a couple of millimetres of a neighbour while the gap between
    the hands never closes: every threshold from 2 to 8 mm yields exactly two
    components of 27 bones.
    """
    trees = [cKDTree(b.vertices) for b in bodies]
    parent = list(range(len(bodies)))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            if trees[i].query(bodies[j].vertices[::4])[0].min() < threshold:
                parent[find(i)] = find(j)

    groups: dict[int, list[int]] = {}
    for i in range(len(bodies)):
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=len, reverse=True)


def bone_axis(mesh: trimesh.Trimesh) -> tuple[np.ndarray, np.ndarray]:
    """The two articular ends of a bone along its own principal axis."""
    verts = mesh.vertices
    centre = verts.mean(axis=0)
    _, _, vh = np.linalg.svd(verts - centre, full_matrices=False)
    axis = vh[0]
    t = (verts - centre) @ axis
    return centre + axis * t.min(), centre + axis * t.max()


def canonical_transform(bones) -> tuple[np.ndarray, float]:
    """Canonical frame plus the sign of the thumb's X coordinate.

    The sign identifies handedness, which lets the caller keep the hand whose
    thumb ends up on +X without ever mirroring a mesh.
    """
    verts = np.vstack([b.vertices for b in bones])
    centre = verts.mean(axis=0)
    sample = (verts - centre)[:: max(1, len(verts) // 20000)]
    _, _, vh = np.linalg.svd(sample, full_matrices=False)
    long_axis, thin_axis = vh[0], vh[2]

    # The wrist half carries far more bone volume than the fingertip half, so
    # the volume-weighted centre is displaced towards the wrist.
    weights = np.array([b.volume for b in bones], dtype=float)
    centroids = np.array([b.centroid for b in bones], dtype=float) - centre
    mass_t = float((centroids @ long_axis * weights).sum() / weights.sum())
    y_axis = long_axis if mass_t < 0 else -long_axis

    order = np.argsort(centroids @ y_axis)
    meta = [int(i) for i in order[8:13]]
    # The thumb metacarpal is the one sitting furthest from the other four.
    thumb = max(meta, key=lambda i: np.linalg.norm(
        centroids[i] - np.mean([centroids[j] for j in meta if j != i], axis=0)))
    palm_plane = np.mean([centroids[j] for j in meta if j != thumb], axis=0)

    # Metacarpal I lies palmar to the plane of II-V, so dorsal is the side the
    # thumb is *not* on.
    z_axis = thin_axis
    if (centroids[thumb] - palm_plane) @ z_axis > 0:
        z_axis = -z_axis
    x_axis = np.cross(y_axis, z_axis)
    x_axis /= np.linalg.norm(x_axis)
    z_axis = np.cross(x_axis, y_axis)
    z_axis /= np.linalg.norm(z_axis)

    matrix = np.eye(4)
    matrix[:3, :3] = np.array([x_axis, y_axis, z_axis])
    matrix[:3, 3] = -matrix[:3, :3] @ centre
    thumb_x = float(centroids[thumb] @ x_axis)
    return matrix, thumb_x


def classify(bones: list[trimesh.Trimesh]) -> list[str]:
    """Name every bone from wrist order and articular adjacency.

    The eight bones closest to the wrist are the carpals and the next five are
    the metacarpals. Each finger ray is then grown outward by repeatedly taking
    the unassigned phalanx whose nearer end sits closest to the previous bone's
    distal end. Following real joint contacts is far more robust than bucketing
    phalanges by X position, which confuses the thumb with the index ray.
    """
    ends = []
    for mesh in bones:
        a, b = bone_axis(mesh)
        # The principal axis has an arbitrary sign, so order the ends along the
        # wrist-to-fingertip axis: without this the chain grows from the wrong
        # end of a metacarpal and hands the index ray its neighbour's phalanges.
        ends.append((a, b) if a[1] <= b[1] else (b, a))
    order = [int(i) for i in np.argsort([b.centroid[1] for b in bones])]
    names = [""] * len(bones)

    for i, idx in enumerate(order[:8]):
        names[idx] = f"carpal-{i + 1}"

    metacarpals = sorted(order[8:13], key=lambda i: -bones[i].centroid[0])
    free = set(order[13:])
    for ray, mc in zip(RAYS, metacarpals):
        names[mc] = f"metacarpal-{ray}"
        tip = ends[mc][1]
        labels = (["proximal", "distal"] if ray == "thumb"
                  else ["proximal", "middle", "distal"])
        for label in labels:
            if not free:
                break
            pick = min(free, key=lambda i: np.linalg.norm(ends[i][0] - tip))
            free.discard(pick)
            names[pick] = f"{ray}-{label}"
            tip = ends[pick][1]
    for idx in free:
        names[idx] = f"unassigned-{idx}"
    return names


def decimate(mesh: trimesh.Trimesh, budget: int) -> trimesh.Trimesh:
    if len(mesh.faces) <= budget:
        return mesh
    result = mesh.simplify_quadric_decimation(face_count=budget)
    result.merge_vertices()
    result.update_faces(result.nondegenerate_faces())
    result.remove_unreferenced_vertices()
    result.fix_normals()
    return result


def main() -> None:
    if not SOURCE.exists():
        sys.exit(f'missing {SOURCE}\ndownload it with:\n'
                 f'  curl -L -o "{SOURCE}" "{DOWNLOAD}"')

    bodies = trimesh.load(SOURCE).split(only_watertight=False)
    clusters = [[bodies[i] for i in idx] for idx in proximity_groups(bodies)]
    for k, grp in enumerate(clusters):
        print(f"cluster {k}: {len(grp)} bones, "
              f"{sum(b.volume for b in grp) / 1000:.1f} cm^3")

    chosen = None
    for cluster in clusters:
        if len(cluster) != 27:
            continue
        matrix, thumb_x = canonical_transform(cluster)
        if thumb_x > 0:
            chosen = (cluster, matrix)
            break
    if chosen is None:
        sys.exit("no hand cluster canonicalised with the thumb on +X")
    cluster, matrix = chosen

    bones = []
    for body in cluster:
        mesh = body.copy()
        mesh.apply_transform(matrix)
        bones.append(decimate(mesh, FACE_BUDGET))

    wrist_idx = np.argsort([b.centroid[1] for b in bones])[:8]
    wrist = np.vstack([bones[i].vertices for i in wrist_idx]).mean(axis=0)
    for mesh in bones:
        mesh.apply_translation(-wrist)

    names = classify(bones)
    rank = {name: i for i, name in enumerate(
        [f"carpal-{i}" for i in range(1, 9)]
        + [f"metacarpal-{r}" for r in RAYS]
        + [f"{r}-{p}" for r in RAYS for p in ("proximal", "middle", "distal")]
    )}
    order = sorted(range(len(bones)), key=lambda i: rank.get(names[i], 999))
    bones = [bones[i] for i in order]
    names = [names[i] for i in order]

    payload: dict[str, np.ndarray] = {}
    print("\nname                     len   vol/mm3   proximal -> distal")
    for i, (mesh, name) in enumerate(zip(bones, names)):
        payload[f"v{i}"] = mesh.vertices.astype(np.float32)
        payload[f"f{i}"] = mesh.faces.astype(np.int32)
        a, b = bone_axis(mesh)
        if a[1] > b[1]:
            a, b = b, a
        payload[f"a{i}"] = np.vstack([a, b]).astype(np.float32)
        print(f"{name:22s} {np.linalg.norm(b - a):5.1f} {mesh.volume:8.0f}   "
              f"{np.round(a, 1).tolist()} -> {np.round(b, 1).tolist()}")
    payload["count"] = np.array([len(bones)])
    payload["names"] = np.array(names)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **payload)

    allv = np.vstack([b.vertices for b in bones])
    print(f"\n{len(bones)} bones -> {CACHE}")
    print("extents", np.round(allv.max(0) - allv.min(0), 1).tolist())
    print("faces  ", sum(len(b.faces) for b in bones))


def load_bones() -> tuple[dict[str, trimesh.Trimesh], dict[str, np.ndarray]]:
    """Cached canonical bones plus their proximal/distal articular points."""
    if not CACHE.exists():
        sys.exit(f"missing {CACHE} - run `python scripts/extract_hand_bones.py` first")
    data = np.load(CACHE)
    count = int(data["count"][0])
    names = [str(n) for n in data["names"]]
    meshes, axes = {}, {}
    for i in range(count):
        meshes[names[i]] = trimesh.Trimesh(vertices=data[f"v{i}"].astype(float),
                                           faces=data[f"f{i}"], process=False)
        axes[names[i]] = data[f"a{i}"].astype(float)
    return meshes, axes


if __name__ == "__main__":
    main()
