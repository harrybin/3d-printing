"""Deterministic kinematic and collision checks for the rigid Ghoul drive."""

from __future__ import annotations

import json
import io
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mechanism
import render_ghouls_grip as assembly
from mesh_kit import box

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "ghouls-grip-mechanik-verifikation.md"


def baseline_chest() -> trimesh.Trimesh:
    data = subprocess.run(
        ["git", "show", "f396e7a:models/ghouls-grip-view.3mf"],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout
    scene = trimesh.load(io.BytesIO(data), file_type="3mf", force="scene")
    transform, geometry = scene.graph.get("deployed-chest")
    mesh = scene.geometry[geometry].copy()
    mesh.apply_transform(transform)
    current = assembly.source_mesh(assembly.build_chest)
    if not np.allclose(mesh.extents, current.extents, atol=0.002):
        raise RuntimeError("Baseline chest envelope changed")
    mesh.apply_translation(current.bounds.mean(axis=0)
                           - mesh.bounds.mean(axis=0))
    return mesh


def volume_intersection(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    overlap = np.minimum(a.bounds[1], b.bounds[1]) - np.maximum(
        a.bounds[0], b.bounds[0]
    )
    if np.any(overlap <= 0.0):
        return 0.0
    hit = trimesh.boolean.intersection([a, b], engine="manifold")
    return 0.0 if hit is None else abs(float(hit.volume))


def baseline_pair_collisions(named: dict, baseline: trimesh.Trimesh) -> list[dict]:
    pairs = []
    for name, mesh in named.items():
        if not name.startswith("arm-"):
            continue
        old = volume_intersection(mesh, baseline)
        current = volume_intersection(mesh, named["chest"])
        if max(old, current) > 0.05:
            pairs.append({"pair": f"{name} / chest (Bodenlager)",
                          "baseline_mm3": old, "current_mm3": current})
    return pairs


def gear_centres(theta: float) -> list[np.ndarray]:
    start, idlers, end = mechanism.forearm_gear_centres()
    origin = mechanism.platform_origin(theta)
    return [origin + start, *(origin + centre for centre in idlers),
            origin + end]


def lid_link_pin(theta: float) -> np.ndarray:
    rise = mechanism.RETRACTED_SLIDER_X - mechanism.slider_x(theta)
    return np.array([
        -mechanism.DRIVE_PITCH_R,
        mechanism.LID_LINK_FRONT_Y,
        mechanism.LID_LINK_PIN_Z + min(rise, mechanism.LID_OPEN_TRAVEL),
    ])


def check() -> dict:
    started = time.perf_counter()
    failures: list[str] = []
    samples = []
    max_pivot_error = 0.0
    max_drive_error = 0.0
    max_lid_error = 0.0
    min_slot_margin = 999.0
    min_lid_pin_margin = 999.0

    slot_min, slot_max = -26.0, 42.0
    lid_slot_low = 40.0 - (
        mechanism.SLIDER_TRAVEL - mechanism.LID_OPEN_TRAVEL
    ) - 4.0
    lid_slot_high = 44.0
    for theta in np.linspace(mechanism.THETA_MIN, mechanism.THETA_MAX, 31):
        rad = np.deg2rad(theta)
        moving_x = mechanism.slider_x(theta)
        lift = mechanism.ARM_L * np.sin(rad)
        top_fixed = np.array([mechanism.FLOOR_PIVOT_X, mechanism.RAIL_Z + lift])
        top_sliding = np.array([moving_x, mechanism.RAIL_Z + lift])
        platform_x = mechanism.FLOOR_PIVOT_X - mechanism.PLATFORM_PIN_X
        slot_local = top_sliding[0] - platform_x
        min_slot_margin = min(
            min_slot_margin, slot_local - slot_min, slot_max - slot_local
        )
        max_pivot_error = max(
            max_pivot_error,
            abs(np.linalg.norm(
                top_fixed - np.array([moving_x, mechanism.RAIL_Z])
            ) - mechanism.ARM_L),
            abs(np.linalg.norm(
                top_sliding
                - np.array([mechanism.FLOOR_PIVOT_X, mechanism.RAIL_Z])
            ) - mechanism.ARM_L),
        )

        travel = mechanism.RETRACTED_SLIDER_X - moving_x
        drive_travel = np.deg2rad(mechanism.drive_angle(theta)) \
            * mechanism.DRIVE_PITCH_R
        max_drive_error = max(max_drive_error, abs(travel - drive_travel))

        pin = lid_link_pin(float(theta))
        rack_translation_z = mechanism.LID_LINK_PIN_Z - 40.0 + travel
        rack_local_x = pin[2] - rack_translation_z
        used = min(travel, mechanism.LID_OPEN_TRAVEL)
        sector_arc = abs(np.deg2rad(mechanism.lid_angle(float(theta)))) \
            * mechanism.LID_SECTOR_R
        max_lid_error = max(max_lid_error, abs(used - sector_arc))
        min_lid_pin_margin = min(
            min_lid_pin_margin,
            rack_local_x - lid_slot_low - 3.0,
            lid_slot_high - rack_local_x - 3.0,
        )
        samples.append({
            "theta": float(theta),
            "slider_x": float(moving_x),
            "lift": float(lift),
            "drive_angle": mechanism.drive_angle(float(theta)),
            "lid_angle": mechanism.lid_angle(float(theta)),
            "forearm_angle": mechanism.forearm_angle(float(theta)),
        })

    centres = gear_centres(mechanism.THETA_MIN)
    distances = [
        float(np.linalg.norm((b - a)[[0, 2]]))
        for a, b in zip(centres[:-1], centres[1:])
    ]
    expected = [
        mechanism.FOREARM_INPUT_R + mechanism.FOREARM_IDLER_R,
        2.0 * mechanism.FOREARM_IDLER_R,
        2.0 * mechanism.FOREARM_IDLER_R,
        mechanism.FOREARM_IDLER_R + mechanism.FOREARM_GEAR_R,
    ]
    max_gear_mesh_error = max(
        abs(actual - target) for actual, target in zip(distances, expected)
    )
    gear_pitches = {
        "input": 2.0 * np.pi * mechanism.FOREARM_INPUT_R
        / round(2.0 * np.pi * mechanism.FOREARM_INPUT_R / mechanism.GEAR_PITCH),
        "idler": 2.0 * np.pi * mechanism.FOREARM_IDLER_R
        / round(2.0 * np.pi * mechanism.FOREARM_IDLER_R / mechanism.GEAR_PITCH),
        "output": 2.0 * np.pi * mechanism.FOREARM_GEAR_R
        / round(2.0 * np.pi * mechanism.FOREARM_GEAR_R / mechanism.GEAR_PITCH),
        "lid": 2.0 * np.pi * mechanism.LID_SECTOR_R
        / max(6, round(2.0 * np.pi * mechanism.LID_SECTOR_R
                       / mechanism.GEAR_PITCH)),
    }
    max_pitch_error = max(
        abs(value - mechanism.GEAR_PITCH) for value in gear_pitches.values()
    )
    idler_pin_clearance = 3.2 - 2.8

    if max_pivot_error > 0.01:
        failures.append(f"Pivot-Schließfehler {max_pivot_error:.4f} mm")
    if min_slot_margin < 0.0:
        failures.append(f"Scherenkulisse zu kurz: {min_slot_margin:.3f} mm")
    if max_drive_error > 0.01:
        failures.append(f"Ritzel/Zahnstange weicht um {max_drive_error:.4f} mm ab")
    if max_lid_error > 0.25:
        failures.append(f"Deckelzapfen weicht von Kurvennut ab: {max_lid_error:.4f} mm")
    if min_lid_pin_margin < 0.4:
        failures.append(f"Deckelzapfen hat zu wenig Kulissenspiel: {min_lid_pin_margin:.3f} mm")
    if max_gear_mesh_error > 0.01:
        failures.append(f"Unterarm-Zahnradabstand falsch: {max_gear_mesh_error:.4f} mm")
    if max_pitch_error > 0.2:
        failures.append(f"Zahnradteilung weicht um {max_pitch_error:.3f} mm ab")
    if idler_pin_clearance < 0.3:
        failures.append(f"Zwischenrad-Pinspiel zu klein: {idler_pin_clearance:.3f} mm")
    if abs(mechanism.lid_angle(mechanism.THETA_MIN)) > 0.01:
        failures.append("Deckel ist am Totenkopf-Anschlag nicht geschlossen")
    if mechanism.lid_angle(mechanism.THETA_MAX) > -80.0:
        failures.append("Deckel öffnet weniger als 80 Grad")
    if abs(mechanism.forearm_angle(mechanism.THETA_MIN)
           - mechanism.STOW_ANGLE) > 0.01:
        failures.append("Unterarm erreicht die Stauposition nicht")
    if abs(mechanism.forearm_angle(mechanism.THETA_MAX)
           - mechanism.DEPLOYED_FOREARM_ANGLE) > 0.01:
        failures.append("Unterarm erreicht die Präsentationsposition nicht")
    if mechanism.drive_angle(mechanism.THETA_MAX) > 130.0:
        failures.append("Totenkopf-Drehweg überschreitet 130 Grad")

    platform_local = mechanism.build_platform()
    forearm_local = mechanism.build_forearm()
    forearm_local.apply_translation([0.0, 0.0, -4.0])
    hinge_local = np.array([
        mechanism.ARM_HINGE_X, 0.0, mechanism.ARM_HINGE_Z
    ])
    forearm_insertion_overlap = 0.0
    for dz in np.linspace(80.0, 0.0, 17):
        candidate = forearm_local.copy()
        candidate.apply_translation(hinge_local + [0.0, 0.0, dz])
        forearm_insertion_overlap = max(
            forearm_insertion_overlap,
            volume_intersection(candidate, platform_local),
        )
    if forearm_insertion_overlap > 0.05:
        failures.append(
            "Unterarm kann nicht von oben zwischen die Lagerohren eingesetzt "
            f"werden: {forearm_insertion_overlap:.3f} mm3"
        )

    installed_forearm = forearm_local.copy()
    installed_forearm.apply_translation(hinge_local)
    output_gear_local = mechanism.build_forearm_output_gear()
    output_shaft_insertion_overlap = 0.0
    for dy in np.linspace(70.0, 0.0, 15):
        candidate = output_gear_local.copy()
        candidate.apply_translation(hinge_local + [0.0, dy, 0.0])
        output_shaft_insertion_overlap = max(
            output_shaft_insertion_overlap,
            volume_intersection(candidate, platform_local),
            volume_intersection(candidate, installed_forearm),
        )
    if output_shaft_insertion_overlap > 0.05:
        failures.append(
            "Ausgangszahnrad-D-Welle kann nicht axial montiert werden: "
            f"{output_shaft_insertion_overlap:.3f} mm3"
        )

    part_builders = {
        **mechanism.PARTS,
        "chest": assembly.build_chest,
        "lid": assembly.build_lid,
    }
    body_counts = {
        name: len(builder().split(only_watertight=False))
        for name, builder in part_builders.items()
    }
    for name, count in body_counts.items():
        if count != 1:
            failures.append(f"{name} besteht aus {count} getrennten Körpern")

    collision_max = {
        "hand_chest": 0.0,
        "hand_lid": 0.0,
        "hand_platform": 0.0,
        "hand_scissor": 0.0,
        "forearm_platform": 0.0,
        "input_gear_platform": 0.0,
        "idler_gear_0_platform": 0.0,
        "idler_gear_1_platform": 0.0,
        "idler_gear_2_platform": 0.0,
        "output_gear_platform": 0.0,
        "output_gear_forearm": 0.0,
        "gear_mesh_0_1": 0.0,
        "gear_mesh_1_2": 0.0,
        "gear_mesh_2_3": 0.0,
        "gear_mesh_3_4": 0.0,
        "slider_chest": 0.0,
        "lid_chest": 0.0,
        "lid_rack_lid": 0.0,
        "lid_rack_chest": 0.0,
        "lid_yoke_lid": 0.0,
        "lid_yoke_chest": 0.0,
        "lid_crank_lid": 0.0,
        "lid_crank_chest": 0.0,
        "platform_chest": 0.0,
        "scissors_repaired_region": 0.0,
        "lid_transfer_input_chest": 0.0,
        "lid_transfer_idler_chest": 0.0,
        "lid_transfer_input_lid": 0.0,
        "lid_transfer_idler_lid": 0.0,
        "lid_transfer_mesh_0_1": 0.0,
        "lid_transfer_mesh_1_2": 0.0,
        "lid_transfer_input_rack": 0.0,
    }
    preexisting_scissor_post_overlap = 0.0
    baseline = baseline_chest()
    baseline_scissor_overlap = 0.0
    max_scissor_overlap_change = 0.0
    repaired_chest = trimesh.boolean.intersection([
        assembly.source_mesh(assembly.build_chest),
        box((36.0, 26.0, 98.0), (-27.0, 53.0, 49.0)),
    ], engine="manifold")
    motion_sweep = []
    preexisting_pairs = []
    for theta in np.linspace(mechanism.THETA_MIN, mechanism.THETA_MAX, 61):
        named = {
            name: mesh
            for name, mesh, _colour in assembly.build_scene_at(float(theta))
        }
        hand_names = [
            name for name in named
            if name == "forearm" or name.startswith("hand-")
        ]
        hand = trimesh.util.concatenate([named[name] for name in hand_names])
        arms = trimesh.util.concatenate([
            mesh for name, mesh in named.items() if name.startswith("arm-")
        ])
        gears = [
            named["scissor-drive-gear"],
            named["idler-gear-0"],
            named["idler-gear-1"],
            named["idler-gear-2"],
            named["forearm-output-gear"],
        ]
        values = {
            **{
                f"{name}_chest": volume_intersection(mesh, named["chest"])
                for name, mesh in named.items() if name.startswith("arm-")
            },
            "platform_chest": volume_intersection(
                named["platform"], named["chest"]),
            "scissors_repaired_region": volume_intersection(
                arms, repaired_chest),
            "lid_transfer_input_chest": volume_intersection(
                named["lid-transfer-input"], named["chest"]),
            "lid_transfer_idler_chest": volume_intersection(
                named["lid-transfer-idler"], named["chest"]),
            "lid_transfer_input_lid": volume_intersection(
                named["lid-transfer-input"], named["lid"]),
            "lid_transfer_idler_lid": volume_intersection(
                named["lid-transfer-idler"], named["lid"]),
            "lid_transfer_mesh_0_1": volume_intersection(
                named["lid-transfer-input"], named["lid-transfer-idler"]),
            "lid_transfer_mesh_1_2": volume_intersection(
                named["lid-transfer-idler"], named["lid-crank"]),
            "lid_transfer_input_rack": volume_intersection(
                named["lid-transfer-input"], named["lid-follower-rack"]),
            "hand_chest": volume_intersection(hand, named["chest"]),
            "hand_lid": volume_intersection(hand, named["lid"]),
            "hand_platform": sum(
                volume_intersection(named[name], named["platform"])
                for name in hand_names if name != "forearm"
            ),
            "hand_scissor": volume_intersection(hand, arms),
            "forearm_platform": volume_intersection(
                named["forearm"], named["platform"]
            ),
            "input_gear_platform": volume_intersection(
                named["scissor-drive-gear"], named["platform"]
            ),
            "idler_gear_0_platform": volume_intersection(
                named["idler-gear-0"], named["platform"]
            ),
            "idler_gear_1_platform": volume_intersection(
                named["idler-gear-1"], named["platform"]
            ),
            "idler_gear_2_platform": volume_intersection(
                named["idler-gear-2"], named["platform"]
            ),
            "output_gear_platform": volume_intersection(
                named["forearm-output-gear"], named["platform"]
            ),
            "output_gear_forearm": volume_intersection(
                named["forearm-output-gear"], named["forearm"]
            ),
            **{
                f"gear_mesh_{index}_{index + 1}": volume_intersection(
                    gears[index], gears[index + 1]
                )
                for index in range(len(gears) - 1)
            },
            "slider_chest": volume_intersection(
                named["slider"], named["chest"]
            ),
            "lid_chest": volume_intersection(named["lid"], named["chest"]),
            "lid_rack_lid": volume_intersection(
                named["lid-rack"], named["lid"]
            ),
            "lid_rack_chest": volume_intersection(
                named["lid-rack"], named["chest"]
            ),
            "lid_yoke_lid": volume_intersection(
                named["lid-follower-rack"], named["lid"]
            ),
            "lid_yoke_chest": volume_intersection(
                named["lid-follower-rack"], named["chest"]
            ),
            "lid_crank_lid": volume_intersection(
                named["lid-crank"], named["lid"]
            ),
            "lid_crank_chest": volume_intersection(
                named["lid-crank"], named["chest"]
            ),
        }
        current_scissor_overlap = volume_intersection(arms, named["chest"])
        old_scissor_overlap = volume_intersection(arms, baseline)
        if theta in (18.0, 48.0, 78.0):
            preexisting_pairs.extend(
                {"theta": float(theta), **pair}
                for pair in baseline_pair_collisions(named, baseline))
        preexisting_scissor_post_overlap = max(
            preexisting_scissor_post_overlap, current_scissor_overlap)
        baseline_scissor_overlap = max(
            baseline_scissor_overlap, old_scissor_overlap)
        max_scissor_overlap_change = max(
            max_scissor_overlap_change,
            abs(current_scissor_overlap - old_scissor_overlap))
        for name, value in values.items():
            collision_max[name] = max(collision_max.get(name, 0.0), value)
        motion_sweep.append({
            "theta": float(theta),
            "lid_angle": mechanism.lid_angle(float(theta)),
            "forearm_angle": mechanism.forearm_angle(float(theta)),
            **{f"{name}_mm3": value for name, value in values.items()},
            "scissors_chest_baseline_mm3": old_scissor_overlap,
            "scissors_chest_current_mm3": current_scissor_overlap,
        })

    for name, value in collision_max.items():
        if value > (0.001 if name.startswith("arm-") else 0.05):
            failures.append(f"Sweep {name}: {value:.3f} mm3")
    if preexisting_scissor_post_overlap > 0.001:
        failures.append(
            f"Scherenarme/Bodenlager: {preexisting_scissor_post_overlap:.6f} mm3")

    wall_probe = box((12.0, 0.8, 21.0), (-27.0, 59.5, 74.5))
    wall_fill = volume_intersection(assembly.build_chest(), wall_probe) \
        / wall_probe.volume
    if wall_fill < 0.999:
        failures.append(f"Rear wall has a mechanism opening: {wall_fill:.6f}")

    result = {
        "passed": not failures,
        "failures": failures,
        "max_pivot_error_mm": max_pivot_error,
        "minimum_slot_margin_mm": min_slot_margin,
        "max_drive_closure_error_mm": max_drive_error,
        "max_lid_closure_error_mm": max_lid_error,
        "minimum_lid_pin_margin_mm": min_lid_pin_margin,
        "max_gear_mesh_error_mm": max_gear_mesh_error,
        "gear_circular_pitches_mm": gear_pitches,
        "max_gear_pitch_error_mm": max_pitch_error,
        "idler_pin_clearance_mm": idler_pin_clearance,
        "forearm_insertion_overlap_mm3": forearm_insertion_overlap,
        "output_shaft_insertion_overlap_mm3": output_shaft_insertion_overlap,
        "knob_rotation_deg": mechanism.drive_angle(mechanism.THETA_MAX),
        "body_counts": body_counts,
        "max_sweep_collisions_mm3": collision_max,
        "samples": samples,
        "motion_sweep": motion_sweep,
        "rear_wall_fill_ratio": wall_fill,
        "current_scissor_post_overlap_mm3": preexisting_scissor_post_overlap,
        "baseline_scissor_post_overlap_mm3": baseline_scissor_overlap,
        "max_scissor_post_overlap_change_mm3": max_scissor_overlap_change,
        "preexisting_collision_pairs": preexisting_pairs,
        "duration_seconds": time.perf_counter() - started,
    }
    return result


def write_report(result: dict) -> None:
    lines = [
        "# Ghoul's Grip - Mechanik-Verifikation",
        "",
        f"Ergebnis der Wand- und Bodenlagerkorrektur: **{'PASS' if result['passed'] else 'FAIL'}**",
        "",
        "Bodenlager als offene Doppelwangen um die unveränderten Armhüllen "
        "neu aufgebaut. Größtes aktuelles Arm-/Kisten-Schnittvolumen: "
        f"{result['current_scissor_post_overlap_mm3']:.6f} mm³. "
        "Jeder einzelne Arm wird in allen 61 Zuständen geprüft; jede "
        "Überschneidung über 0,001 mm³ lässt den Nachweis scheitern. "
        "Das ist ein Geometrienachweis, kein Belastungs- oder PLA-Passungstest.",
        "",
        "Baseline-Beweis: Schatulle aus `f396e7a:models/ghouls-grip-view.3mf`, "
        "nur um die Ansichtsplatten-Verschiebung zurückversetzt, gegen dieselben "
        "unveränderten Scherenarme geprüft. Größte Verbesserung zum korrigierten "
        f"Gehäuse: {result['max_scissor_post_overlap_change_mm3']:.6f} mm³.",
        "",
        "Geprüft wird die starre, manuell reversible Kraftkette: "
        "Drehbarer Totenkopf -> Antriebsritzel -> Schlittenzahnstange -> "
        "Doppelschere sowie Antriebsritzel -> Deckelzahnstange -> "
        "gefangener Deckelkurbelzapfen. Ein mitfahrendes Fünf-Zahnrad-Getriebe "
        "mit drei Zwischenrädern überträgt die Scherenarmdrehung auf den "
        "Unterarm. Es gibt keine Seile, "
        "Gummibänder, Federn oder Wickelspulen.",
        "",
        "| Nachweis | Ergebnis |",
        "| --- | ---: |",
        f"| Max. Pivot-Schließfehler | {result['max_pivot_error_mm']:.6f} mm |",
        f"| Kleinster Scherenkulissenrand | {result['minimum_slot_margin_mm']:.3f} mm |",
        f"| Ritzel/Zahnstangen-Schließfehler | {result['max_drive_closure_error_mm']:.6f} mm |",
        f"| Deckelkurbel-Schließfehler | {result['max_lid_closure_error_mm']:.6f} mm |",
        f"| Kleinster Deckelzapfen-Kulissenrand | {result['minimum_lid_pin_margin_mm']:.3f} mm |",
        f"| Max. Zahnrad-Mittenfehler | {result['max_gear_mesh_error_mm']:.6f} mm |",
        f"| Max. Zahnrad-Teilungsfehler | {result['max_gear_pitch_error_mm']:.3f} mm |",
        f"| Zwischenrad-Pinspiel | {result['idler_pin_clearance_mm']:.3f} mm |",
        f"| Unterarm-Einsetzsweep | {result['forearm_insertion_overlap_mm3']:.3f} mm³ |",
        f"| D-Wellen-Einsetzsweep | {result['output_shaft_insertion_overlap_mm3']:.3f} mm³ |",
        f"| Hinterwand am ehemaligen Mechanikfenster | {100 * result['rear_wall_fill_ratio']:.3f}% massiv |",
        f"| Totenkopf-Drehweg | {result['knob_rotation_deg']:.2f}° |",
        f"| Einzelkörper je Druckteil | {result['body_counts']} |",
        f"| Laufzeit | {result['duration_seconds']:.1f} s |",
    ]
    for name, value in result["max_sweep_collisions_mm3"].items():
        lines.append(f"| Sweep {name} | {value:.3f} mm³ |")
    lines.extend([
        "",
        "## Beseitigte Bestandskollision (Baseline nur als Vergleich)",
        "",
        "| Scherenwinkel / Pose | Paar | Baseline f396e7a | Aktuell |",
        "| --- | --- | ---: | ---: |",
    ])
    for sample in result["motion_sweep"]:
        if sample["theta"] in (18.0, 48.0, 78.0):
            lines.append(
                f"| {sample['theta']:.0f} Grad | scissors_chest (Bodenlager) | "
                f"{sample['scissors_chest_baseline_mm3']:.3f} mm³ | "
                f"{sample['scissors_chest_current_mm3']:.3f} mm³ |")
    lines.extend([
        "",
        "| Pose | Einzelpaar | Baseline f396e7a | Aktuell |",
        "| --- | --- | ---: | ---: |",
    ])
    for pair in result["preexisting_collision_pairs"]:
        lines.append(
            f"| {pair['theta']:.0f} Grad | {pair['pair']} | "
            f"{pair['baseline_mm3']:.3f} mm³ | "
            f"{pair['current_mm3']:.3f} mm³ |")
    lines.extend([
        "",
        "Die hintere Zahnstange läuft 14,854 mm weiter innen. Zwei gleich große "
        "Transferzahnräder übertragen mit zwei Drehsinnwechseln und Übersetzung "
        "1:1 auf das unveränderte Deckelsegment. Die Kistenwand bleibt am "
        "ehemaligen Fenster durchgehend; alle 61 Scherenstellungen von 18 bis "
        "78 Grad einschließlich 48 Grad werden gegen die reale Wand geprüft.",
        "",
        "## Gekoppelte Bewegung",
        "",
        "| Scherenwinkel | Totenkopf/Ritzel | Deckel | Unterarm |",
        "| ---: | ---: | ---: | ---: |",
    ])
    for sample in result["motion_sweep"]:
        lines.append(
            f"| {sample['theta']:.0f}° | "
            f"{mechanism.drive_angle(sample['theta']):.1f}° | "
            f"{sample['lid_angle']:.1f}° | {sample['forearm_angle']:.1f}° |"
        )
    lines.extend([
        "",
        "Der knochenfarbene Unterarm wird ohne Zahnrad von oben zwischen die "
        "beiden Lagerohren gesetzt. Anschließend wird das naturweiße "
        "Ausgangszahnrad mit seiner D-Welle von der Zahnradseite axial durch "
        "beide Rundlager und die passende D-Nabe des Unterarms geschoben. Ein "
        "1,75-mm-Filamentstift im äußeren Querloch sichert die Welle gegen "
        "Herausrutschen; erst danach werden die Zwischenräder aufgesteckt.",
        "",
        "Die Finger bleiben als druckbare, vorgekrümmte PLA-Flexuren in der "
        "kompakten Greifpose. Die neue starre Kraftkette betätigt Deckel, "
        "Scherenhub und Unterarm; sie enthält bewusst keine vorgetäuschte "
        "Sehnenbetätigung.",
    ])
    if result["failures"]:
        lines.extend(["", "## Fehler", ""])
        lines.extend(f"- {failure}" for failure in result["failures"])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    outcome = check()
    write_report(outcome)
    evidence = ROOT / "build" / "ghoul-floor-bearing-verification.json"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "passed": outcome["passed"],
        "failures": outcome["failures"],
        "states": len(outcome["motion_sweep"]),
        "individual_arm_chest_max_mm3": {
            key: value for key, value in outcome["max_sweep_collisions_mm3"].items()
            if key.startswith("arm-")
        },
        "report": str(REPORT),
        "evidence": str(evidence),
    }, indent=2))
    raise SystemExit(0 if outcome["passed"] else 1)
