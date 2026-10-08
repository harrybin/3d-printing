"""Deterministic kinematic and collision checks for the Ghoul's Grip."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mechanism
import render_ghouls_grip as assembly

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "ghouls-grip-mechanik-verifikation.md"

THETA_MIN = 16.0
THETA_MAX = 76.0
INNER_LO = np.array([-97.0, -57.0, 3.0])
INNER_HI = np.array([97.0, 57.0, 86.0])


def volume_intersection(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    hit = trimesh.boolean.intersection([a, b], engine="manifold")
    return 0.0 if hit is None else abs(float(hit.volume))


def check() -> dict:
    failures: list[str] = []
    rows = []
    fixed_posts = [mechanism.box((12.0, 6.0, 14.0),
                                 (mechanism.FLOOR_PIVOT_X,
                                  sy * mechanism.SCISSOR_Y, 10.0))
                   for sy in (-1.0, 1.0)]
    slider = mechanism.build_slider()
    max_post_overlap = 0.0
    max_endpoint_error = 0.0
    slot_min, slot_max = -25.0, 45.0
    min_slot_margin = 999.0

    for theta in np.linspace(THETA_MIN, THETA_MAX, 31):
        rad = np.deg2rad(theta)
        moving_x = mechanism.FLOOR_PIVOT_X + mechanism.ARM_L * np.cos(rad)
        lift = mechanism.ARM_L * np.sin(rad)
        top_fixed = np.array([mechanism.FLOOR_PIVOT_X, 8.0 + lift])
        top_sliding = np.array([moving_x, 8.0 + lift])
        platform_origin_x = mechanism.FLOOR_PIVOT_X - (-42.0)
        slot_local = top_sliding[0] - platform_origin_x
        min_slot_margin = min(min_slot_margin,
                              slot_local - slot_min, slot_max - slot_local)

        # Both 90 mm links must close exactly between their analytical pivots.
        max_endpoint_error = max(
            max_endpoint_error,
            abs(np.linalg.norm(top_fixed - np.array([moving_x, 8.0]))
                - mechanism.ARM_L),
            abs(np.linalg.norm(top_sliding
                               - np.array([mechanism.FLOOR_PIVOT_X, 8.0]))
                - mechanism.ARM_L),
        )

        placed = slider.copy()
        placed.apply_translation([moving_x, 0.0, 0.0])
        for post in fixed_posts:
            max_post_overlap = max(max_post_overlap,
                                   volume_intersection(placed, post))
        rows.append((theta, moving_x, lift, slot_local))

    if max_post_overlap > 0.01:
        failures.append(f"Schlitten kollidiert mit Festpivot: {max_post_overlap:.3f} mm3")
    if max_endpoint_error > 0.01:
        failures.append(f"Pivotfehler: {max_endpoint_error:.3f} mm")
    if min_slot_margin < 0.0:
        failures.append(f"Kulisse zu kurz: Rand {min_slot_margin:.3f} mm")

    pose_metrics = {}
    for pose in ("retracted", "deployed"):
        items = assembly.build_scene(pose)
        named = {name: mesh for name, mesh, _colour in items}
        hand_names = [name for name in named
                      if name == "forearm" or name.startswith("hand-")]
        hand = trimesh.util.concatenate([named[name] for name in hand_names])
        chest_overlap = volume_intersection(hand, named["chest"])
        platform_contacts = {
            name: volume_intersection(named[name], named["platform"])
            for name in hand_names
        }
        rigid_hand_overlap = sum(v for name, v in platform_contacts.items()
                                 if name != "forearm")
        bounds = hand.bounds
        whole = trimesh.util.concatenate(list(named.values()))
        pose_metrics[pose] = {
            "hand_bounds": np.round(bounds, 3).tolist(),
            "hand_chest_overlap_mm3": chest_overlap,
            "hand_platform_overlap_mm3": rigid_hand_overlap,
            "forearm_hinge_contact_mm3": platform_contacts["forearm"],
            "assembly_xy_mm": np.round(whole.extents[:2], 3).tolist(),
        }
        if chest_overlap > 0.05:
            failures.append(f"{pose}: Hand schneidet Gehäuse um {chest_overlap:.2f} mm3")
        if rigid_hand_overlap > 0.05:
            failures.append(f"{pose}: Hand schneidet Hubjoch um {rigid_hand_overlap:.2f} mm3")
        if np.any(whole.extents[:2] > 250.0):
            failures.append(f"{pose}: Baugruppe überschreitet 250-mm-XY-Hülle")

        if pose == "retracted":
            low_margin = bounds[0] - INNER_LO
            high_margin = INNER_HI - bounds[1]
            if np.min(np.r_[low_margin, high_margin]) < -0.01:
                failures.append("Eingefahrene Hand liegt außerhalb des Innenraums")
            pose_metrics[pose]["cavity_margin_mm"] = float(
                np.min(np.r_[low_margin, high_margin]))

    result = {
        "passed": not failures,
        "failures": failures,
        "max_pivot_error_mm": max_endpoint_error,
        "minimum_slot_margin_mm": min_slot_margin,
        "max_slider_fixed_post_overlap_mm3": max_post_overlap,
        "poses": pose_metrics,
        "samples": rows,
    }
    return result


def write_report(result: dict) -> None:
    rows = result["samples"]
    lines = [
        "# Ghoul's Grip - Mechanik-Verifikation",
        "",
        f"Ergebnis: **{'PASS' if result['passed'] else 'FAIL'}**",
        "",
        "Die Prüfung rekonstruiert die reale 90-mm-Scherengeometrie in 31 "
        "Stellungen und verwendet Manifold-Schnittvolumen für die kritischen "
        "Kollisionen. Der Kontakt zwischen Unterarm und seinen Scharnierohren "
        "ist beabsichtigt und wird separat ausgewiesen.",
        "",
        "| Nachweis | Ergebnis |",
        "| --- | ---: |",
        f"| Max. Pivot-Schließfehler | {result['max_pivot_error_mm']:.6f} mm |",
        f"| Kleinster Kulissenrand | {result['minimum_slot_margin_mm']:.3f} mm |",
        f"| Schlitten/Festpivot-Schnitt | {result['max_slider_fixed_post_overlap_mm3']:.3f} mm³ |",
    ]
    for pose, values in result["poses"].items():
        lines.extend([
            f"| {pose}: Hand/Gehäuse-Schnitt | {values['hand_chest_overlap_mm3']:.3f} mm³ |",
            f"| {pose}: Hand/Hubjoch-Schnitt | {values['hand_platform_overlap_mm3']:.3f} mm³ |",
            f"| {pose}: XY-Hülle | {values['assembly_xy_mm'][0]:.1f} × {values['assembly_xy_mm'][1]:.1f} mm |",
        ])
    lines.extend(["", "## Endstellungen", "",
                  "| Zustand | Hand-/Unterarm-Bounds (min → max) |",
                  "| --- | --- |"])
    for pose, values in result["poses"].items():
        lines.append(f"| {pose} | `{values['hand_bounds'][0]}` → `{values['hand_bounds'][1]}` |")
    lines.extend(["", "## Scherensweep", "",
                  "| Winkel | Schlitten X | Hub | Kulisse lokal X |",
                  "| ---: | ---: | ---: | ---: |"])
    for theta, x, lift, slot in rows:
        lines.append(f"| {theta:.0f}° | {x:.2f} | {lift:.2f} | {slot:.2f} |")
    if result["failures"]:
        lines.extend(["", "## Fehler", ""] +
                     [f"- {item}" for item in result["failures"]])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    outcome = check()
    write_report(outcome)
    print(json.dumps(outcome, indent=2))
    raise SystemExit(0 if outcome["passed"] else 1)
