#!/usr/bin/env python
"""mesh_tool.py - inspect, validate, repair, measure and edit meshes from the CLI.

Companion tool for the parametric generators in ``scripts/``. Generators stay the
source of truth for geometry; this tool answers the recurring questions about an
STL that already exists (is it watertight, where is it on the bed, does the
requested feature really exist, how much filament does it need).

Project conventions applied here:

* units are millimetres, bed is 250 x 250 mm
* ``.stl`` output is always written as ASCII STL
* booleans use the ``manifold`` engine
* repair is the lossless recipe from ``.github/skills/validate-stl-mesh``
  (round to 0.001 mm, merge, dedupe, drop degenerate) - never ``pymeshfix``
* ``shapely``/``rtree`` are not installed, so feature presence is proven with a
  boolean volume probe instead of ``mesh.contains()``

Run ``python scripts/mesh_tool.py <command> -h`` for per-command options.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh

BED_X = 250.0
BED_Y = 250.0
ROUND_DECIMALS = 3          # 0.001 mm grid, print-neutral
FILAMENT_DIA_MM = 1.75
PLA_DENSITY_G_CM3 = 1.24


# --------------------------------------------------------------------------
# loading / saving
# --------------------------------------------------------------------------
def load_mesh(path: str) -> trimesh.Trimesh:
    p = Path(path)
    if not p.exists():
        sys.exit(f"error: no such file: {p}")
    mesh = trimesh.load(p, force="mesh")
    if not isinstance(mesh, trimesh.Trimesh):
        sys.exit(f"error: {p} does not contain a single mesh")
    return mesh


def export_mesh(mesh: trimesh.Trimesh, path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix.lower() == ".stl":
        mesh.export(p, file_type="stl_ascii")
    else:
        mesh.export(p)
    print(f"wrote {p}")


# --------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------
def degenerate_face_count(mesh: trimesh.Trimesh) -> int:
    return int((~mesh.nondegenerate_faces()).sum())


def stats(mesh: trimesh.Trimesh) -> dict:
    lo, hi = mesh.bounds
    extents = hi - lo
    watertight = bool(mesh.is_watertight)
    winding = bool(mesh.is_winding_consistent)
    return {
        "facets": int(len(mesh.faces)),
        "vertices": int(len(mesh.vertices)),
        "bounds_min": [round(float(v), 3) for v in lo],
        "bounds_max": [round(float(v), 3) for v in hi],
        "extents": [round(float(v), 3) for v in extents],
        "xy_center": [round(float(v), 3) for v in ((lo + hi) / 2.0)[:2]],
        "watertight": watertight,
        "winding_consistent": winding,
        "is_volume": bool(mesh.is_volume),
        "volume_mm3": round(float(mesh.volume), 3) if watertight else None,
        "area_mm2": round(float(mesh.area), 3),
        "euler_number": int(mesh.euler_number),
        "degenerate_faces": degenerate_face_count(mesh),
        "bodies": int(len(mesh.split(only_watertight=False))),
    }


def detect_convention(mesh: trimesh.Trimesh, forced: str | None = None) -> str:
    """center-origin target is (0, 0), corner-origin target is (125, 125)."""
    if forced:
        return forced
    return "center-origin" if float(mesh.bounds[0][:2].min()) < 0 else "corner-origin"


def convention_target(convention: str) -> np.ndarray:
    return np.array([0.0, 0.0]) if convention == "center-origin" else np.array([BED_X / 2, BED_Y / 2])


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------
def cmd_info(args) -> None:
    mesh = load_mesh(args.file)
    s = stats(mesh)
    convention = detect_convention(mesh, args.convention)
    s["convention"] = convention
    s["centered"] = bool(np.allclose(s["xy_center"], convention_target(convention), atol=0.01))
    if args.json:
        print(json.dumps(s, indent=2))
        return
    print(f"{args.file}")
    print(f"  facets        {s['facets']}   vertices {s['vertices']}   bodies {s['bodies']}")
    print(f"  extents (mm)  {s['extents'][0]} x {s['extents'][1]} x {s['extents'][2]}")
    print(f"  bounds        {s['bounds_min']} -> {s['bounds_max']}")
    print(f"  volume        {s['volume_mm3']} mm^3")
    print(f"  watertight    {s['watertight']}   winding {s['winding_consistent']}")
    print(f"  euler_number  {s['euler_number']}   degenerate {s['degenerate_faces']}")
    print(f"  placement     {convention}, centered={s['centered']} (xy center {s['xy_center']})")


def cmd_validate(args) -> None:
    mesh = load_mesh(args.file)
    s = stats(mesh)
    convention = detect_convention(mesh, args.convention)
    problems: list[str] = []
    warnings: list[str] = []

    if not s["watertight"]:
        problems.append("not watertight - run: mesh_tool.py repair")
    if not s["winding_consistent"]:
        problems.append("inconsistent winding, normals are not all outward")
    if s["degenerate_faces"]:
        problems.append(f"{s['degenerate_faces']} degenerate faces")
    if s["bodies"] > 1 and not args.allow_multibody:
        problems.append(f"{s['bodies']} disconnected bodies (pass --allow-multibody if intended)")

    ext = s["extents"]
    if ext[0] > BED_X or ext[1] > BED_Y:
        problems.append(f"footprint {ext[0]} x {ext[1]} mm exceeds the {BED_X:.0f} x {BED_Y:.0f} mm bed")
    if not np.allclose(s["xy_center"], convention_target(convention), atol=0.01):
        warnings.append(
            f"not centered for {convention} (xy center {s['xy_center']}, "
            f"target {[round(float(v), 3) for v in convention_target(convention)]}) "
            "- run: mesh_tool.py center"
        )
    if abs(float(mesh.bounds[0][2])) > 0.01:
        warnings.append(f"lowest z is {float(mesh.bounds[0][2]):.3f} mm, not resting on the bed")

    for w in warnings:
        print(f"WARN {w}")
    if problems:
        print(f"FAIL {args.file}")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print(f"PASS {args.file} - watertight, manifold, euler_number {s['euler_number']}, ready to slice")


def cmd_repair(args) -> None:
    mesh = load_mesh(args.file)
    before = stats(mesh)

    mesh.vertices = np.round(mesh.vertices, ROUND_DECIMALS)
    mesh.merge_vertices()
    mesh.update_faces(mesh.unique_faces())
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    trimesh.repair.fix_winding(mesh)
    trimesh.repair.fix_inversion(mesh)
    trimesh.repair.fix_normals(mesh)
    if args.fill_holes:
        trimesh.repair.fill_holes(mesh)

    after = stats(mesh)
    print(f"repair {args.file}")
    for key in ("facets", "watertight", "winding_consistent", "degenerate_faces", "euler_number"):
        print(f"  {key:<20} {before[key]} -> {after[key]}")
    if not after["watertight"]:
        print(
            "  still not watertight: open edges == 0 means non-manifold edges from tangential\n"
            "  knife-edge contact. Fix the source script by overlapping the solids; do not run\n"
            "  pymeshfix on thin-walled parts.",
            file=sys.stderr,
        )
    export_mesh(mesh, args.output)


def cmd_measure(args) -> None:
    mesh = load_mesh(args.file)
    s = stats(mesh)
    ext = s["extents"]
    print(f"bounding box : {ext[0]} x {ext[1]} x {ext[2]} mm")
    print(f"surface area : {s['area_mm2']:.1f} mm^2")
    if s["volume_mm3"] is None:
        print("volume       : n/a - mesh is not watertight, repair first")
        return
    vol_cm3 = s["volume_mm3"] / 1000.0
    print(f"volume       : {s['volume_mm3']:.1f} mm^3  ({vol_cm3:.2f} cm^3)")
    solid_mass = vol_cm3 * args.density
    fil_area_mm2 = math.pi * (FILAMENT_DIA_MM / 2.0) ** 2
    solid_len_m = s["volume_mm3"] / fil_area_mm2 / 1000.0
    frac = args.infill / 100.0
    print(
        f"solid (100%) : {solid_mass:.1f} g, {solid_len_m:.2f} m of "
        f"{FILAMENT_DIA_MM} mm at {args.density} g/cm^3"
    )
    print(
        f"est. {args.infill:.0f}% infill: ~{solid_mass * frac:.1f} g, ~{solid_len_m * frac:.2f} m "
        "(shell excluded, lower bound)"
    )


def cmd_center(args) -> None:
    mesh = load_mesh(args.file)
    convention = detect_convention(mesh, args.convention)
    target = convention_target(convention)
    lo, hi = mesh.bounds
    delta_xy = target - ((lo + hi) / 2.0)[:2]
    delta_z = -float(lo[2]) if args.drop else 0.0
    mesh.apply_translation([float(delta_xy[0]), float(delta_xy[1]), delta_z])
    print(f"convention {convention}, translation ({delta_xy[0]:.3f}, {delta_xy[1]:.3f}, {delta_z:.3f}) mm")
    print(f"new bounds {[round(float(v), 3) for v in mesh.bounds[0]]} -> "
          f"{[round(float(v), 3) for v in mesh.bounds[1]]}")
    export_mesh(mesh, args.output or args.file)


def cmd_transform(args) -> None:
    mesh = load_mesh(args.file)
    if args.scale is not None:
        mesh.apply_scale(args.scale)
    if args.fit:
        target = np.array([float(v) for v in args.fit.lower().split("x")])
        factor = float(np.min(target / (mesh.bounds[1] - mesh.bounds[0])))
        mesh.apply_scale(factor)
        print(f"fit factor {factor:.4f}")
    if args.rotate:
        axis_name, deg = args.rotate.split(",")
        axis = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}[axis_name.strip().lower()]
        mesh.apply_transform(
            trimesh.transformations.rotation_matrix(math.radians(float(deg)), axis, mesh.centroid)
        )
    if args.translate:
        mesh.apply_translation([float(v) for v in args.translate.split(",")])
    print(f"extents {[round(float(v), 3) for v in (mesh.bounds[1] - mesh.bounds[0])]} mm")
    export_mesh(mesh, args.output)


def cmd_boolean(args) -> None:
    meshes = [load_mesh(f) for f in args.files]
    if len(meshes) < 2:
        sys.exit("error: boolean needs at least two input meshes")
    result = trimesh.boolean.boolean_manifold(meshes, args.op)
    s = stats(result)
    print(f"{args.op}: watertight {s['watertight']}, volume {s['volume_mm3']} mm^3, "
          f"euler_number {s['euler_number']}")
    export_mesh(result, args.output)


def cmd_probe(args) -> None:
    """Prove that a feature really occupies a volume (shapely-free alternative to contains())."""
    mesh = load_mesh(args.file)
    lo = np.array([float(v) for v in args.min.split(",")])
    hi = np.array([float(v) for v in args.max.split(",")])
    box = trimesh.creation.box(extents=hi - lo)
    box.apply_translation((lo + hi) / 2.0)
    inter = trimesh.boolean.intersection([mesh, box], engine="manifold")
    ratio = float(inter.volume) / float(box.volume) if box.volume else 0.0
    print(f"probe {[round(float(v), 3) for v in lo]} -> {[round(float(v), 3) for v in hi]}")
    print(f"  box volume    {box.volume:.3f} mm^3")
    print(f"  solid inside  {inter.volume:.3f} mm^3")
    print(f"  fill ratio    {ratio * 100:.1f} %")
    print("  interpretation: ~100% = feature present, ~0% = empty. Always probe the mirrored")
    print("  position too - equal values on both sides mean the feature is not where you think.")


def cmd_slices(args) -> None:
    """Cross-section sweep: cross-sectional area vs. z, to locate floors and lids."""
    mesh = load_mesh(args.file)
    z0, z1 = float(mesh.bounds[0][2]), float(mesh.bounds[1][2])
    thickness = args.thickness
    print(f"z from {z0:.3f} to {z1:.3f} mm, slab {thickness} mm")
    z = z0
    while z < z1:
        top = min(z + thickness, z1)
        extents = np.array([mesh.extents[0] + 2, mesh.extents[1] + 2, top - z])
        slab = trimesh.creation.box(extents=extents)
        slab.apply_translation([mesh.centroid[0], mesh.centroid[1], (z + top) / 2.0])
        inter = trimesh.boolean.intersection([mesh, slab], engine="manifold")
        area = float(inter.volume) / (top - z) if top > z else 0.0
        print(f"  z {z:7.2f} - {top:7.2f}   cross-section {area:9.2f} mm^2")
        z += args.step


def cmd_overhang(args) -> None:
    """Report the downward-facing area that exceeds the overhang limit."""
    mesh = load_mesh(args.file)
    normals = mesh.face_normals
    areas = mesh.area_faces
    # angle of the face from the horizontal build plane; 90 deg = vertical wall
    down = normals[:, 2] < 0
    angle_from_horizontal = np.degrees(np.arcsin(np.clip(np.abs(normals[:, 2]), 0, 1)))
    steep = down & (angle_from_horizontal < (90.0 - args.limit))
    flat_down = down & (angle_from_horizontal > 89.0)
    bed = flat_down & (mesh.triangles[:, :, 2].max(axis=1) <= mesh.bounds[0][2] + 1e-3)

    total = float(areas.sum())
    print(f"overhang limit {args.limit} deg from vertical (self-supporting up to that)")
    print(f"  total area          {total:9.2f} mm^2")
    print(f"  bed contact area    {float(areas[bed].sum()):9.2f} mm^2")
    print(f"  unsupported area    {float(areas[steep & ~bed].sum()):9.2f} mm^2 "
          f"({float(areas[steep & ~bed].sum()) / total * 100:.1f} %)")
    print(f"  ceilings (>=89 deg) {float(areas[flat_down & ~bed].sum()):9.2f} mm^2  "
          "-> bridges, check span")
    if float(areas[steep & ~bed].sum()) > 0:
        print("  reduce by reorienting, adding 45 deg chamfers, or using teardrop holes")


def cmd_arrange(args) -> None:
    meshes = [load_mesh(f) for f in args.files]
    cols = max(1, int(math.ceil(math.sqrt(len(meshes)))))
    placed, x, y, row_h = [], 0.0, 0.0, 0.0
    for i, m in enumerate(meshes):
        ext = m.bounds[1] - m.bounds[0]
        m.apply_translation(-m.bounds[0])
        m.apply_translation([x, y, 0.0])
        placed.append(m)
        x += float(ext[0]) + args.gap
        row_h = max(row_h, float(ext[1]))
        if (i + 1) % cols == 0:
            x, y, row_h = 0.0, y + row_h + args.gap, 0.0
    combined = trimesh.util.concatenate(placed)
    convention = args.convention or "corner-origin"
    target = convention_target(convention)
    lo, hi = combined.bounds
    combined.apply_translation([*(target - ((lo + hi) / 2.0)[:2]), 0.0])
    ext = combined.bounds[1] - combined.bounds[0]
    print(f"arranged {len(meshes)} parts in {cols} columns, gap {args.gap} mm, {convention}")
    print(f"  footprint {ext[0]:.2f} x {ext[1]:.2f} mm on a {BED_X:.0f} x {BED_Y:.0f} mm bed")
    if ext[0] > BED_X or ext[1] > BED_Y:
        print("  WARNING: layout exceeds the bed", file=sys.stderr)
    export_mesh(combined, args.output)


def cmd_convert(args) -> None:
    export_mesh(load_mesh(args.input), args.output)


def cmd_compare(args) -> None:
    """Compare the same model across checkouts before trusting a bug report."""
    for path in args.files:
        p = Path(path)
        if not p.exists():
            print(f"{p}  MISSING")
            continue
        mesh = load_mesh(path)
        s = stats(mesh)
        mtime = __import__("datetime").datetime.fromtimestamp(p.stat().st_mtime)
        print(f"{p}")
        print(f"  mtime {mtime:%Y-%m-%d %H:%M:%S}  facets {s['facets']}  "
              f"euler {s['euler_number']}  extents {s['extents']}")


# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mesh_tool.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("info", help="mesh statistics and placement")
    s.add_argument("file")
    s.add_argument("--json", action="store_true")
    s.add_argument("--convention", choices=["center-origin", "corner-origin"])
    s.set_defaults(func=cmd_info)

    s = sub.add_parser("validate", help="exit 1 when the mesh is not print ready")
    s.add_argument("file")
    s.add_argument("--allow-multibody", action="store_true")
    s.add_argument("--convention", choices=["center-origin", "corner-origin"])
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("repair", help="lossless repair recipe for CAD kernel exports")
    s.add_argument("file")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--fill-holes", action="store_true", help="also attempt trimesh fill_holes")
    s.set_defaults(func=cmd_repair)

    s = sub.add_parser("measure", help="dimensions, volume, filament estimate")
    s.add_argument("file")
    s.add_argument("--density", type=float, default=PLA_DENSITY_G_CM3, help="g/cm^3, default PLA 1.24")
    s.add_argument("--infill", type=float, default=20.0, help="percent, default 20")
    s.set_defaults(func=cmd_measure)

    s = sub.add_parser("center", help="center on the bed for the active convention")
    s.add_argument("file")
    s.add_argument("-o", "--output", help="default: overwrite the input file")
    s.add_argument("--convention", choices=["center-origin", "corner-origin"])
    s.add_argument("--drop", action="store_true", help="also drop the model to z=0")
    s.set_defaults(func=cmd_center)

    s = sub.add_parser("transform", help="scale / rotate / translate")
    s.add_argument("file")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--scale", type=float, help="uniform factor")
    s.add_argument("--fit", help="uniformly scale into XxYxZ mm, e.g. 250x250x260")
    s.add_argument("--rotate", help="axis,degrees e.g. z,90")
    s.add_argument("--translate", help="dx,dy,dz in mm")
    s.set_defaults(func=cmd_transform)

    s = sub.add_parser("boolean", help="CSG with the manifold engine")
    s.add_argument("op", choices=["union", "difference", "intersection"])
    s.add_argument("files", nargs="+")
    s.add_argument("-o", "--output", required=True)
    s.set_defaults(func=cmd_boolean)

    s = sub.add_parser("probe", help="volume probe: prove a feature exists at a location")
    s.add_argument("file")
    s.add_argument("--min", required=True, help="x,y,z of the probe box corner")
    s.add_argument("--max", required=True, help="x,y,z of the opposite corner")
    s.set_defaults(func=cmd_probe)

    s = sub.add_parser("slices", help="cross-section area sweep over z")
    s.add_argument("file")
    s.add_argument("--step", type=float, default=1.0, help="mm between samples")
    s.add_argument("--thickness", type=float, default=0.2, help="slab thickness in mm")
    s.set_defaults(func=cmd_slices)

    s = sub.add_parser("overhang", help="unsupported area for the current orientation")
    s.add_argument("file")
    s.add_argument("--limit", type=float, default=45.0, help="degrees from vertical, default 45")
    s.set_defaults(func=cmd_overhang)

    s = sub.add_parser("arrange", help="lay several parts out on the bed")
    s.add_argument("files", nargs="+")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--gap", type=float, default=5.0)
    s.add_argument("--convention", choices=["center-origin", "corner-origin"])
    s.set_defaults(func=cmd_arrange)

    s = sub.add_parser("convert", help="convert between mesh formats")
    s.add_argument("input")
    s.add_argument("output")
    s.set_defaults(func=cmd_convert)

    s = sub.add_parser("compare", help="compare the same model across checkouts/worktrees")
    s.add_argument("files", nargs="+")
    s.set_defaults(func=cmd_compare)

    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
