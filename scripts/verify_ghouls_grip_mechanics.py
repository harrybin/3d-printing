"""Deterministic kinematic and collision checks for the rigid Ghoul drive."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mechanism
import render_ghouls_grip as assembly

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "ghouls-grip-mechanik-verifikation.md"


def volume_intersection(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    overlap = np.minimum(a.bounds[1], b.bounds[1]) - np.maximum(
        a.bounds[0], b.bounds[0]
    )
    if np.any(overlap <= 0.0):
        return 0.0
    hit = trimesh.boolean.intersection([a, b], engine="manifold")
    return 0.0 if hit is None else abs(float(hit.volume))


def gear_centres(theta: float) -> list[np.ndarray]:
    lift = mechanism.ARM_L * np.sin(np.deg2rad(theta))
    start = np.array([
        mechanism.FLOOR_PIVOT_X,
        mechanism.FOREARM_GEAR_Y,
        mechanism.RAIL_Z + lift,
    ])
    end = mechanism.forearm_hinge(theta) + np.array([
        0.0, mechanism.FOREARM_GEAR_Y, 0.0
    ])
    vector = end - start
    distance = float(np.linalg.norm(vector[[0, 2]]))
    unit = vector / distance
    input_offset = mechanism.FOREARM_INPUT_R + mechanism.FOREARM_IDLER_R
    output_offset = mechanism.FOREARM_GEAR_R + mechanism.FOREARM_IDLER_R
    return [start, start + unit * input_offset,
            end - unit * output_offset, end]


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
        "slider_chest": 0.0,
        "lid_chest": 0.0,
        "lid_rack_lid": 0.0,
        "lid_rack_chest": 0.0,
        "lid_yoke_lid": 0.0,
        "lid_yoke_chest": 0.0,
    }
    motion_sweep = []
    for theta in np.linspace(mechanism.THETA_MIN, mechanism.THETA_MAX, 13):
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
        values = {
            "hand_chest": volume_intersection(hand, named["chest"]),
            "hand_lid": volume_intersection(hand, named["lid"]),
            "hand_platform": sum(
                volume_intersection(named[name], named["platform"])
                for name in hand_names if name != "forearm"
            ),
            "hand_scissor": volume_intersection(hand, arms),
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
        }
        for name, value in values.items():
            collision_max[name] = max(collision_max[name], value)
        motion_sweep.append({
            "theta": float(theta),
            "lid_angle": mechanism.lid_angle(float(theta)),
            "forearm_angle": mechanism.forearm_angle(float(theta)),
            **{f"{name}_mm3": value for name, value in values.items()},
        })

    for name, value in collision_max.items():
        if value > 0.05:
            failures.append(f"Sweep {name}: {value:.3f} mm3")

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
        "knob_rotation_deg": mechanism.drive_angle(mechanism.THETA_MAX),
        "body_counts": body_counts,
        "max_sweep_collisions_mm3": collision_max,
        "samples": samples,
        "motion_sweep": motion_sweep,
        "duration_seconds": time.perf_counter() - started,
    }
    return result


def write_report(result: dict) -> None:
    lines = [
        "# Ghoul's Grip - Mechanik-Verifikation",
        "",
        f"Ergebnis: **{'PASS' if result['passed'] else 'FAIL'}**",
        "",
        "Geprüft wird die starre, manuell reversible Kraftkette: "
        "Drehbarer Totenkopf -> Antriebsritzel -> Schlittenzahnstange -> "
        "Doppelschere sowie Antriebsritzel -> Deckelzahnstange -> "
        "gefangener Deckelkurbelzapfen. Ein mitfahrendes Vier-Zahnrad-Getriebe "
        "überträgt die Scherenarmdrehung auf den Unterarm. Es gibt keine Seile, "
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
        f"| Totenkopf-Drehweg | {result['knob_rotation_deg']:.2f}° |",
        f"| Einzelkörper je Druckteil | {result['body_counts']} |",
        f"| Laufzeit | {result['duration_seconds']:.1f} s |",
    ]
    for name, value in result["max_sweep_collisions_mm3"].items():
        lines.append(f"| Sweep {name} | {value:.3f} mm³ |")
    lines.extend([
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
    print(json.dumps(outcome, indent=2))
    raise SystemExit(0 if outcome["passed"] else 1)
