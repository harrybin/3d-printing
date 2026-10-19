"""Check frozen printed parts, candy retention, hand motion and dish insertion."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np
import trimesh

import mechanism
import render_ghouls_grip as scene
from candy_hand import (
    DISH_HEIGHT, DISH_TOP_RADII, DISH_WALL, assembled_hand,
    build_cavity, dish_frame,
)
from mesh_kit import box
from skeleton_hand import (
    RAYS, load_skeleton, palm_to_forearm_transform, peg_direction,
)
from gothic_chest import BODY_H, CHEST_L, CHEST_W, FLOOR, FUNCTIONAL_WALL_DATUM

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "ghouls-grip-printed-box-contract.json"
PROJECT = ROOT / "models" / "ghouls-grip-print.3mf"
LIMIT = 0.5
INSERTION_LIMIT = 0.05
NS = {"c": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
PRODUCTION = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"


def project_payloads(path: Path) -> dict:
    with ZipFile(path) as archive:
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
        config = ET.fromstring(archive.read("Metadata/model_settings.config"))
        objects = {obj.get("id"): obj for obj in model.findall("c:resources/c:object", NS)}
        builds = {item.get("objectid"): item for item in model.find("c:build", NS)}
        result = {}
        for obj in config.findall("object"):
            name = obj.find("metadata[@key='name']").get("value")
            object_id = obj.get("id")
            component = objects[object_id].find("c:components/c:component", NS)
            entry = component.get(f"{{{PRODUCTION}}}path").lstrip("/")
            result[name] = {
                "mesh_sha256": hashlib.sha256(archive.read(entry)).hexdigest(),
                "print_transform": builds[object_id].get("transform"),
            }
        return result


def freeze(path: Path) -> None:
    if CONTRACT.exists():
        raise FileExistsError(f"Do not replace the printed-box contract: {CONTRACT}")
    data = {
        "baseline_project_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_sha256": {
            name: hashlib.sha256((ROOT / "scripts" / name).read_bytes()).hexdigest()
            for name in ("gothic_chest.py", "mechanism.py")
        },
        "unchanged_meshes": {
            name: value for name, value in project_payloads(path).items()
            if not name.startswith("hand-")
        },
    }
    CONTRACT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Frozen {len(data['unchanged_meshes'])} non-hand meshes: {CONTRACT}")


def frozen_errors() -> list[str]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    current = project_payloads(PROJECT)
    errors = []
    for name, digest in contract["source_sha256"].items():
        if hashlib.sha256((ROOT / "scripts" / name).read_bytes()).hexdigest() != digest:
            errors.append(f"Frozen box/drive source changed: {name}")
    for name, expected in contract["unchanged_meshes"].items():
        if current.get(name, {}).get("mesh_sha256") != expected["mesh_sha256"]:
            errors.append(f"Frozen non-hand mesh changed: {name}")
        if name in {"chest", "lid"} and current.get(name) != expected:
            errors.append(f"Printed box/lid placement changed: {name}")
    return errors


def intersection_volume(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    if np.any(np.minimum(a.bounds[1], b.bounds[1])
              <= np.maximum(a.bounds[0], b.bounds[0])):
        return 0.0
    hit = trimesh.boolean.intersection([a, b], engine="manifold")
    return 0.0 if hit is None else abs(float(hit.volume))


def hand_matrix(skeleton, theta: float) -> np.ndarray:
    wrist = palm_to_forearm_transform(
        skeleton, mechanism.FOREARM_LENGTH + 9.0 + scene.FOREARM_SEAT_Z,
        mechanism.HAND_PALM_ROLL)
    tilt = scene.rot(mechanism.forearm_angle(theta), [0.0, 1.0, 0.0])
    transform = tilt @ wrist
    transform[:3, 3] += mechanism.forearm_hinge(theta)
    return transform


def retention(skeleton, thetas) -> dict:
    cavity = build_cavity(skeleton)
    rim_angles = np.linspace(0.0, 2.0 * np.pi, 721)
    radii = DISH_TOP_RADII - DISH_WALL
    rim = np.column_stack([
        radii[0] * np.cos(rim_angles),
        radii[1] * np.sin(rim_angles),
        np.full(len(rim_angles), DISH_HEIGHT),
    ])
    samples = []
    for theta in thetas:
        transform = hand_matrix(skeleton, float(theta)) @ dish_frame(skeleton)
        world_rim = trimesh.transform_points(rim, transform)
        fill_z = float(world_rim[:, 2].min() - 2.0)
        volume = cavity.copy()
        volume.apply_transform(transform)
        low, high = volume.bounds.copy()
        high[2] = fill_z
        fill = box(high - low, (high + low) / 2.0)
        capacity = intersection_volume(volume, fill) / 1000.0
        normal = transform[:3, 2]
        samples.append({
            "theta_deg": float(theta),
            "opening_tilt_deg": float(np.rad2deg(np.arccos(np.clip(normal[2], -1, 1)))),
            "retained_ml_with_2mm_freeboard": round(capacity, 3),
        })
    return {
        "max_tilt_deg": max(row["opening_tilt_deg"] for row in samples),
        "minimum_retained_ml": min(row["retained_ml_with_2mm_freeboard"] for row in samples),
        "samples": samples,
    }


def insertion(hand, skeleton, quick: bool) -> dict:
    dish = hand["candy-dish"]
    normal = dish_frame(skeleton)[:3, 2]
    steps = (0.0, 4.0, 12.0, 30.0, 60.0) if quick else np.linspace(0.0, 60.0, 61)
    dish_max = {}
    for distance in steps:
        candidate = dish.copy()
        candidate.apply_translation(normal * distance)
        for name, mesh in hand.items():
            if name == "candy-dish":
                continue
            key = f"dish~{name}"
            dish_max[key] = max(dish_max.get(key, 0.0), intersection_volume(candidate, mesh))
    finger_max = {}
    installed = {"hand-palm": hand["hand-palm"]}
    for ray in ("index", "middle", "ring", "little", "thumb"):
        name = f"hand-finger-{ray}"
        for distance in ((0.0, 4.0, 8.0, 12.0) if quick else np.linspace(0, 24, 25)):
            candidate = hand[name].copy()
            candidate.apply_translation(peg_direction(skeleton, ray) * distance)
            for obstacle, mesh in installed.items():
                key = f"{ray}~{obstacle}"
                finger_max[key] = max(
                    finger_max.get(key, 0.0), intersection_volume(candidate, mesh))
        installed[name] = hand[name]
    return {"dish_max_intersections_mm3": dish_max,
            "finger_palm_max_intersections_mm3": finger_max}


def check(quick: bool) -> dict:
    errors = frozen_errors()
    skeleton = load_skeleton()
    hand = scene.grip_hand()
    for name, mesh in hand.items():
        if not (mesh.is_volume and mesh.is_winding_consistent
                and len(mesh.split()) == 1
                and bool(mesh.nondegenerate_faces().all())):
            errors.append(f"Invalid or disconnected mesh: {name}")
    thetas = (18, 25, 30, 36, 48, 60, 78) if quick else np.linspace(18, 78, 61)
    collision_max = {}
    closed_bounds = None
    for theta in thetas:
        named = {name: mesh for name, mesh, _ in scene.build_scene_at(float(theta))}
        for a, b in itertools.combinations(named, 2):
            if a not in hand and b not in hand:
                continue
            key = f"{a}~{b}"
            value = intersection_volume(named[a], named[b])
            if value > 0.001:
                collision_max[key] = max(collision_max.get(key, 0.0), value)
        if theta == 18:
            points = np.vstack([named[name].bounds for name in hand])
            closed_bounds = [points.min(0).round(3).tolist(), points.max(0).round(3).tolist()]
        print(f"pose {theta:g}: checked all changed-hand pairs", flush=True)
    for key, value in collision_max.items():
        if value > LIMIT:
            errors.append(f"Motion collision {key}: {value:.3f} mm3")
    cavity_low = np.array([
        -CHEST_L / 2.0 + FUNCTIONAL_WALL_DATUM,
        -CHEST_W / 2.0 + FUNCTIONAL_WALL_DATUM, FLOOR])
    cavity_high = np.array([
        CHEST_L / 2.0 - FUNCTIONAL_WALL_DATUM,
        CHEST_W / 2.0 - FUNCTIONAL_WALL_DATUM, BODY_H])
    closed_margins = np.r_[np.asarray(closed_bounds[0]) - cavity_low,
                           cavity_high - np.asarray(closed_bounds[1])]
    if closed_margins.min() < 1.0:
        errors.append(f"Closed hand/dish cavity margin below 1 mm: {closed_margins.min():.3f}")
    sweeps = insertion(hand, skeleton, quick)
    for kind, values in sweeps.items():
        for key, value in values.items():
            if value > INSERTION_LIMIT:
                errors.append(f"Insertion collision {kind}/{key}: {value:.3f} mm3")
    capacity = retention(skeleton, thetas)
    if capacity["max_tilt_deg"] > 30.01 or capacity["minimum_retained_ml"] < 10.0:
        errors.append("Dish does not retain at least 10 ml with 2 mm freeboard throughout travel")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors, "pose_count": len(thetas),
        "collision_max_mm3": collision_max, "closed_hand_bounds_mm": closed_bounds,
        "closed_cavity_margins_mm": closed_margins.round(3).tolist(),
        "insertion": sweeps, "retention": capacity,
        "physical_fit_and_loaded_motion": "not tested",
    }


def render_hand(path: Path) -> None:
    import vedo
    skeleton = load_skeleton()
    transform = hand_matrix(skeleton, mechanism.THETA_MAX)
    actors = []
    bounds = []
    for name, mesh in scene.grip_hand().items():
        mesh = mesh.copy()
        mesh.apply_transform(transform)
        bounds.append(mesh.bounds)
        color = scene.ACCENT_COLOR if name == "candy-dish" else scene.BONE_COLOR
        actors.append(vedo.Mesh([mesh.vertices, mesh.faces]).c(color).lighting("glossy"))
    centre = np.vstack(bounds).mean(axis=0)
    camera = {
        "pos": centre + [210.0, -210.0, 190.0],
        "focal_point": centre, "viewup": (0, 0, 1),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    plotter = vedo.Plotter(offscreen=True, size=(1200, 1100), bg="#E6E9ED")
    plotter.show(*actors, axes=0, camera=camera)
    plotter.screenshot(str(path))
    plotter.close()
    print(f"hand render: {path}")


def write_report(path: Path, result: dict) -> None:
    sweeps = result["insertion"]
    dish_max = max(sweeps["dish_max_intersections_mm3"].values())
    finger_max = max(sweeps["finger_palm_max_intersections_mm3"].values())
    retention_result = result["retention"]
    lines = [
        "# Ghoul's Grip: candy-hand geometry audit", "",
        f"**Status: {result['status']}**. Sampled poses: {result['pose_count']}.", "",
        "| Check | Result |",
        "| --- | --- |",
        f"| Frozen box/drive sources and 35 non-hand payloads | {'FAIL' if any('Frozen' in error or 'placement' in error for error in result['errors']) else 'PASS'} |",
        "| Hand and dish meshes | One closed, consistently wound, nondegenerate body per part required |",
        "| Motion intersections | Every changed-hand pair against the complete scene; limit 0.5 mm3 |",
        f"| Finger insertion, including already installed fingers | Maximum {finger_max:.6f} mm3; limit {INSERTION_LIMIT} mm3 |",
        f"| Dish insertion/removal over 60 mm | Maximum {dish_max:.6f} mm3; limit {INSERTION_LIMIT} mm3 |",
        f"| Smallest closed cavity margin | {min(result['closed_cavity_margins_mm']):.3f} mm |",
        f"| Maximum opening tilt | {retention_result['max_tilt_deg']:.3f} degrees |",
        f"| Minimum static capacity, 2 mm gravity freeboard | {retention_result['minimum_retained_ml']:.3f} ml |",
        "", "Finger installation order: index, middle, ring, little, thumb; dish last.",
        "Finger sockets and the gravity-seated dish are removable, not positively locked.",
        "", "This is a sampled geometric/static-gravity proof, not a physical load,",
        "friction, shock or sweets-retention test. Do not overfill; use wrapped sweets",
        "or a suitable food-contact liner. PLA food-contact suitability is not certified.",
        "", "See the assembly and dimensions document for parameter provenance and",
        "the separate complete mechanism/assembly audit for unchanged drive parts.",
    ]
    if result["errors"]:
        lines.extend(["", "## Failures", "", *[f"- {error}" for error in result["errors"]]])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--render", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "ghoul-candy-verification.json")
    args = parser.parse_args()
    if args.freeze:
        freeze(args.freeze)
        return 0
    result = check(args.quick)
    if args.render:
        render_hand(args.render)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.report:
        write_report(args.report, result)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in {"retention", "insertion"}}, indent=2))
    print("retention", result["retention"]["minimum_retained_ml"], "ml")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
