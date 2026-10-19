"""Turn a generated GLB/OBJ/PLY seed mesh into a watertight, mm-scaled ASCII STL.

Generated meshes (TRELLIS.2, Pixal3D, Gemini-assisted Blender output, scans) are
usually Y-up, unit-less, multi-shell and not watertight. This script:
  1. loads all geometry (textures dropped) and converts Y-up -> Z-up,
  2. removes floater shells smaller than --min-part of the largest shell,
  3. scales to --height / --max-extent / --scale (millimetres),
  4. makes it watertight: cheap repair first, voxel remesh (+ Taubin smoothing)
     when still open; overlapping shells are fused with the manifold engine,
  5. optionally decimates (--faces), drops to z=0, centers XY, exports ASCII STL.

    .venv\\Scripts\\python.exe scripts\\genai_mesh_postprocess.py build\\genai\\run1\\mesh.glb ^
        models\\<name>-seed.stl --height 80 --faces 200000

The output is a *seed* for Blender/Python refinement, never fit-critical geometry.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mesh_tool import ROUND_DECIMALS, convention_target, stats  # noqa: E402


def load_any(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(path, force="mesh", process=False)
    if not isinstance(loaded, trimesh.Trimesh) or len(loaded.faces) == 0:
        raise SystemExit(f"error: no triangle geometry in {path}")
    return trimesh.Trimesh(vertices=loaded.vertices, faces=loaded.faces, process=True)


def clean(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    mesh = mesh.copy()
    mesh.merge_vertices()
    mesh.update_faces(mesh.unique_faces())
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    return mesh


def drop_floaters(mesh: trimesh.Trimesh, min_part: float) -> tuple[trimesh.Trimesh, int]:
    parts = mesh.split(only_watertight=False)
    if len(parts) <= 1:
        return mesh, 0
    sizes = np.array([float(np.prod(np.maximum(p.extents, 1e-9))) for p in parts])
    keep = [p for p, s in zip(parts, sizes) if s >= min_part * sizes.max()]
    return trimesh.util.concatenate(keep), len(parts) - len(keep)


def scale_factor(extents: np.ndarray, height: float | None, max_extent: float | None,
                 scale: float | None) -> float:
    if height:
        return height / float(extents[2])
    if max_extent:
        return max_extent / float(extents.max())
    return scale or 1.0


def cheap_repair(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    mesh = clean(mesh)
    trimesh.repair.fix_winding(mesh)
    trimesh.repair.fix_inversion(mesh)
    trimesh.repair.fill_holes(mesh)
    trimesh.repair.fix_normals(mesh)
    return mesh


def fuse(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    parts = mesh.split(only_watertight=False)
    if len(parts) > 1 and all(p.is_watertight for p in parts):
        return trimesh.boolean.union(parts, engine="manifold")
    return mesh


def voxel_remesh(mesh: trimesh.Trimesh, resolution: int, smooth_iter: int) -> trimesh.Trimesh:
    pitch = float(mesh.extents.max()) / resolution
    grid = mesh.voxelized(pitch).fill()
    out = grid.marching_cubes
    out.apply_transform(grid.transform)
    out = clean(out)
    if smooth_iter:
        trimesh.smoothing.filter_taubin(out, iterations=smooth_iter)
    trimesh.repair.fix_normals(out)
    return out


def decimate(mesh: trimesh.Trimesh, faces: int) -> trimesh.Trimesh:
    """Halve in quadric passes and keep the last watertight result (aggressive passes can tear)."""
    import fast_simplification

    best = mesh
    while len(best.faces) > faces:
        reduction = min(0.5, 1 - faces / len(best.faces))
        v, f = fast_simplification.simplify(best.vertices, best.faces, target_reduction=reduction)
        cand = clean(trimesh.Trimesh(v, f, process=True))
        if not (cand.is_watertight and cand.is_winding_consistent) or len(cand.faces) >= len(best.faces):
            break
        best = cand
    trimesh.repair.fix_normals(best)
    return best


def postprocess(mesh: trimesh.Trimesh, *, up: str = "y", height: float | None = None,
                max_extent: float | None = None, scale: float | None = None, min_part: float = 0.02,
                resolution: int = 256, smooth: int = 10, faces: int | None = None,
                force_voxel: bool = False, convention: str = "center-origin") -> tuple[trimesh.Trimesh, dict]:
    report: dict = {"input": {"faces": len(mesh.faces), "watertight": bool(mesh.is_watertight)}}
    if up == "y":
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    mesh = clean(mesh)
    mesh, dropped = drop_floaters(mesh, min_part)
    report["floaters_removed"] = dropped
    s = scale_factor(mesh.extents, height, max_extent, scale)
    mesh.apply_scale(s)
    report["scale"] = round(s, 6)

    method = "as-is"
    if force_voxel or not mesh.is_watertight:
        repaired = cheap_repair(mesh)
        if repaired.is_watertight and not force_voxel:
            mesh, method = repaired, "repair"
        else:
            mesh, method = voxel_remesh(mesh, resolution, smooth), f"voxel{resolution}"
    mesh = fuse(mesh)
    if faces:
        mesh = decimate(mesh, faces)
    report["method"] = method

    lo, hi = mesh.bounds
    target = convention_target(convention)
    mesh.apply_translation([target[0] - (lo[0] + hi[0]) / 2, target[1] - (lo[1] + hi[1]) / 2, -lo[2]])
    mesh.vertices = np.round(mesh.vertices, ROUND_DECIMALS)
    mesh = clean(mesh)
    trimesh.repair.fix_normals(mesh)
    report["output"] = stats(mesh)
    return mesh, report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--up", choices=("y", "z"), default="y", help="input up axis (glTF is Y-up)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--height", type=float, help="target Z height in mm")
    g.add_argument("--max-extent", type=float, help="target largest extent in mm")
    g.add_argument("--scale", type=float, help="uniform scale factor")
    ap.add_argument("--min-part", type=float, default=0.02, help="drop shells below this bbox-volume ratio")
    ap.add_argument("--resolution", type=int, default=256, help="voxel cells along the largest extent")
    ap.add_argument("--smooth", type=int, default=10, help="Taubin iterations after voxel remesh")
    ap.add_argument("--faces", type=int, help="decimate toward this many faces (stops early to stay watertight)")
    ap.add_argument("--voxel", action="store_true", help="always voxel-remesh (removes internal faces)")
    ap.add_argument("--convention", choices=("center-origin", "corner-origin"), default="center-origin")
    ap.add_argument("--report", type=Path, help="write the JSON report here")
    args = ap.parse_args()

    if not args.input.exists():
        sys.exit(f"error: no such file: {args.input}")
    if args.output.suffix.lower() != ".stl":
        sys.exit("error: output must be .stl")
    if not (args.height or args.max_extent or args.scale):
        print("WARN no --height/--max-extent/--scale given; generated meshes are unit-less", file=sys.stderr)
    mesh, report = postprocess(load_any(args.input), up=args.up, height=args.height,
                               max_extent=args.max_extent, scale=args.scale, min_part=args.min_part,
                               resolution=args.resolution, smooth=args.smooth, faces=args.faces,
                               force_voxel=args.voxel, convention=args.convention)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(args.output, file_type="stl_ascii")
    report["source"] = args.input.name
    if args.report:
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    o = report["output"]
    print(f"wrote {args.output}  method={report['method']} scale={report['scale']} "
          f"floaters_removed={report['floaters_removed']}")
    print(f"  facets {o['facets']}  extents {o['extents']}  watertight {o['watertight']}  "
          f"winding {o['winding_consistent']}  euler {o['euler_number']}  bodies {o['bodies']}")
    if not (o["watertight"] and o["winding_consistent"]):
        sys.exit("FAIL output is not a closed, consistently wound solid; raise --resolution or use --voxel")


if __name__ == "__main__":
    main()
