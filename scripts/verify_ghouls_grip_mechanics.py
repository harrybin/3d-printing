"""Deterministic kinematic and collision checks for the Ghoul's Grip."""

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
import skeleton_hand

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "ghouls-grip-mechanik-verifikation.md"

THETA_MIN = mechanism.THETA_MIN
THETA_MAX = mechanism.THETA_MAX
INNER_LO = np.array([-97.0, -57.0, 3.0])
INNER_HI = np.array([97.0, 57.0, 86.0])
OUTER_LO = np.array([-100.0, -60.0, 0.0])
OUTER_HI = np.array([100.0, 60.0, 86.0])


def progress(message: str, started: float) -> None:
    elapsed = time.perf_counter() - started
    print(f"[verify +{elapsed:7.1f}s] {message}", file=sys.stderr, flush=True)


def volume_intersection(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    overlap = np.minimum(a.bounds[1], b.bounds[1]) - np.maximum(
        a.bounds[0], b.bounds[0])
    if np.any(overlap <= 0.0):
        return 0.0
    hit = trimesh.boolean.intersection([a, b], engine="manifold")
    return 0.0 if hit is None else abs(float(hit.volume))


def check() -> dict:
    started = time.perf_counter()
    failures: list[str] = []
    rows = []
    progress("Pruefe analytische Scherenkinematik (31 Stellungen)", started)
    fixed_posts = [mechanism.box((12.0, 6.0, 14.0),
                                 (mechanism.FLOOR_PIVOT_X,
                                  sy * mechanism.SCISSOR_Y, 10.0))
                   for sy in (-1.0, 1.0)]
    slider = mechanism.build_slider()
    max_post_overlap = 0.0
    max_endpoint_error = 0.0
    slot_min, slot_max = -26.0, 42.0
    min_slot_margin = 999.0

    for theta in np.linspace(THETA_MIN, THETA_MAX, 31):
        rad = np.deg2rad(theta)
        moving_x = mechanism.FLOOR_PIVOT_X + mechanism.ARM_L * np.cos(rad)
        lift = mechanism.ARM_L * np.sin(rad)
        top_fixed = np.array([mechanism.FLOOR_PIVOT_X, 8.0 + lift])
        top_sliding = np.array([moving_x, 8.0 + lift])
        platform_origin_x = (
            mechanism.FLOOR_PIVOT_X - mechanism.PLATFORM_PIN_X
        )
        slot_local = top_sliding[0] - platform_origin_x
        min_slot_margin = min(min_slot_margin,
                              slot_local - slot_min, slot_max - slot_local)

        # Both 72 mm links must close exactly between their analytical pivots.
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

    band_lengths = [
        abs((mechanism.slider_x(theta) + 8.0) - (-76.0))
        for theta in (THETA_MIN, THETA_MAX)
    ]
    if band_lengths[1] >= band_lengths[0]:
        failures.append("Antriebsgummis entspannen nicht in Hubrichtung")

    latch_alignment = abs(
        mechanism.RETRACTED_SLIDER_X
        - mechanism.slider_x(THETA_MIN)
    )
    if latch_alignment > 0.01:
        failures.append(f"Rastklinke versetzt: {latch_alignment:.3f} mm")

    platform_xy = mechanism.build_platform().extents[:2]
    progress("Pruefe zusammenhaengende Einzelteile", started)
    part_builders = {
        "platform": mechanism.build_platform,
        "forearm": mechanism.build_forearm,
        "latch": mechanism.build_latch,
        "latch_bracket": mechanism.build_latch_bracket,
        "crank_spool": mechanism.build_crank_spool,
        "crank_key": mechanism.build_crank_key,
        "band_anchor": mechanism.build_band_anchor,
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
    if np.any(platform_xy > np.array([100.0, 100.0])):
        failures.append(
            f"Hubjoch nicht kompakt: {platform_xy[0]:.1f} x "
            f"{platform_xy[1]:.1f} mm"
        )

    sweep_metrics = []
    last_lid_angle = 1.0
    max_latch_overlap = 0.0
    max_hand_chest = 0.0
    max_hand_lid = 0.0
    max_hand_platform = 0.0
    max_hand_arm = 0.0
    max_slider_chest = 0.0
    max_latch_chest = 0.0
    max_bracket_chest = 0.0
    max_latch_bracket = 0.0
    max_trigger_latch = 0.0
    max_band_arm = 0.0
    max_cord_platform = 0.0
    minimum_hidden_mechanism_margin = 999.0
    crank_external_depth = 0.0
    sweep_angles = np.linspace(THETA_MIN, THETA_MAX, 13)
    progress("Starte booleschen Baugruppen-Sweep (13 Stellungen)", started)
    for index, theta in enumerate(sweep_angles, start=1):
        progress(
            f"Baugruppen-Sweep {index}/{len(sweep_angles)} "
            f"bei {theta:.1f} Grad",
            started,
        )
        items = assembly.build_scene_at(float(theta))
        named = {name: mesh for name, mesh, _colour in items}
        hand_names = [
            name for name in named
            if name == "forearm" or name.startswith("hand-")
        ]
        rigid_hand_names = [
            name for name in hand_names if name != "forearm"
        ]
        hand = trimesh.util.concatenate([named[name] for name in hand_names])
        arms = trimesh.util.concatenate([
            mesh for name, mesh in named.items() if name.startswith("arm-")
        ])
        hand_chest = volume_intersection(hand, named["chest"])
        hand_lid = volume_intersection(hand, named["lid"])
        hand_platform = sum(
            volume_intersection(named[name], named["platform"])
            for name in rigid_hand_names
        )
        hand_arm = volume_intersection(hand, arms)
        latch_overlap = volume_intersection(
            named["slider"], named["latch"]
        )
        slider_chest = volume_intersection(named["slider"], named["chest"])
        latch_chest = volume_intersection(named["latch"], named["chest"])
        bracket_chest = volume_intersection(
            named["latch-bracket"], named["chest"]
        )
        latch_bracket = volume_intersection(
            named["latch"], named["latch-bracket"]
        )
        trigger_latch = volume_intersection(
            named["trigger"], named["latch"]
        )
        drive_bands = [mesh for name, mesh in named.items()
                       if name.startswith("drive-band-")]
        control_cords = [mesh for name, mesh in named.items()
                         if name.startswith("forearm-control-cord")]
        band_arm = max(volume_intersection(mesh, arms)
                       for mesh in drive_bands)
        # Contact with the printed guide/post is intentional; only the free
        # cord span beyond that 10 mm routing envelope is forbidden to touch.
        guide_clearance = trimesh.creation.icosphere(subdivisions=2, radius=10.0)
        guide_clearance.apply_translation(mechanism.forearm_cord_guide(float(theta)))
        free_cords = [trimesh.boolean.difference(
            [mesh, guide_clearance], engine="manifold"
        ) for mesh in control_cords]
        cord_platform = max(
            volume_intersection(mesh, named["platform"])
            for mesh in free_cords if mesh is not None
        )
        angle = assembly.lid_angle(float(theta))
        if angle > last_lid_angle + 0.01:
            failures.append(
                f"Deckel schließt im Hub bei {theta:.1f} Grad wieder"
            )
        last_lid_angle = angle
        max_hand_chest = max(max_hand_chest, hand_chest)
        max_hand_lid = max(max_hand_lid, hand_lid)
        max_hand_platform = max(max_hand_platform, hand_platform)
        max_hand_arm = max(max_hand_arm, hand_arm)
        max_latch_overlap = max(max_latch_overlap, latch_overlap)
        max_slider_chest = max(max_slider_chest, slider_chest)
        max_latch_chest = max(max_latch_chest, latch_chest)
        max_bracket_chest = max(max_bracket_chest, bracket_chest)
        max_latch_bracket = max(max_latch_bracket, latch_bracket)
        max_trigger_latch = max(max_trigger_latch, trigger_latch)
        max_band_arm = max(max_band_arm, band_arm)
        max_cord_platform = max(max_cord_platform, cord_platform)
        hidden_names = [
            name for name in named
            if (
                name in {
                    "slider", "latch", "latch-bracket", "band-anchor",
                    "latch-return-band", "reset-cord",
                }
                or name.startswith("arm-")
                or name.startswith("drive-band-")
            )
        ]
        for name in hidden_names:
            bounds = named[name].bounds
            margin = float(np.min(np.r_[
                bounds[0] - OUTER_LO,
                OUTER_HI - bounds[1],
            ]))
            minimum_hidden_mechanism_margin = min(
                minimum_hidden_mechanism_margin, margin
            )
        crank_external_depth = max(
            crank_external_depth,
            float(max(
                0.0,
                named["crank-key"].bounds[1][0] - OUTER_HI[0],
            )),
        )
        sweep_metrics.append({
            "theta": float(theta),
            "lid_angle": angle,
            "forearm_angle": mechanism.forearm_angle(float(theta)),
            "hand_chest_mm3": hand_chest,
            "hand_lid_mm3": hand_lid,
            "hand_platform_mm3": hand_platform,
            "hand_arm_mm3": hand_arm,
            "latch_slider_mm3": latch_overlap,
            "slider_chest_mm3": slider_chest,
            "latch_chest_mm3": latch_chest,
            "bracket_chest_mm3": bracket_chest,
            "latch_bracket_mm3": latch_bracket,
            "trigger_latch_mm3": trigger_latch,
            "drive_band_arm_mm3": band_arm,
            "control_cord_platform_mm3": cord_platform,
        })

    for label, value in (
        ("Hand/Gehäuse", max_hand_chest),
        ("Hand/Deckel", max_hand_lid),
        ("Hand/Hubjoch", max_hand_platform),
        ("Hand/Scherenarme", max_hand_arm),
        ("Klinke/Schlitten nach Freigabe", max_latch_overlap),
        ("Schlitten/Gehäuse", max_slider_chest),
        ("Klinke/Gehäuse", max_latch_chest),
        ("Klinkenhalter/Gehäuse", max_bracket_chest),
        ("Klinke/Klinkenführung", max_latch_bracket),
        ("Totenkopf-Stößel/Klinke in Ruhe", max_trigger_latch),
        ("Antriebsgummi/Scherenarme", max_band_arm),
        ("Steuerseil/Hubjoch", max_cord_platform),
    ):
        if value > 0.05:
            failures.append(f"{label}-Schnitt im Sweep: {value:.3f} mm3")

    if minimum_hidden_mechanism_margin < -0.01:
        failures.append(
            "Verdeckte Mechanik verlässt das Gehäuse um "
            f"{-minimum_hidden_mechanism_margin:.3f} mm"
        )
    if crank_external_depth > 10.0:
        failures.append(
            f"Aufziehschlüssel steht {crank_external_depth:.3f} mm hervor"
        )

    latch_capture_margin = 5.0 - 2.0 - latch_alignment
    if latch_capture_margin < 1.0:
        failures.append(
            f"Rastklinke greift nicht positiv: {latch_capture_margin:.3f} mm"
        )

    if assembly.lid_angle(THETA_MIN) != 0.0:
        failures.append("Deckel ist in Raststellung nicht geschlossen")
    if assembly.lid_angle(THETA_MAX) > -80.0:
        failures.append("Deckel öffnet weniger als 80 Grad")
    if abs(mechanism.forearm_angle(THETA_MIN)
           - mechanism.STOW_ANGLE) > 0.01:
        failures.append("Unterarm erreicht die Stauposition nicht")
    if abs(mechanism.forearm_angle(THETA_MAX)) > 0.01:
        failures.append("Unterarm richtet sich nicht vollständig auf")

    pose_metrics = {}
    progress("Pruefe eingefahrene und ausgefahrene Endstellung", started)
    for pose in ("retracted", "deployed"):
        progress(f"Endstellung: {pose}", started)
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
        pose_metrics[pose] = {
            "hand_bounds": np.round(bounds, 3).tolist(),
            "hand_chest_overlap_mm3": chest_overlap,
            "hand_platform_overlap_mm3": rigid_hand_overlap,
            "forearm_hinge_contact_mm3": platform_contacts["forearm"],
        }
        if chest_overlap > 0.05:
            failures.append(f"{pose}: Hand schneidet Gehäuse um {chest_overlap:.2f} mm3")
        if rigid_hand_overlap > 0.05:
            failures.append(f"{pose}: Hand schneidet Hubjoch um {rigid_hand_overlap:.2f} mm3")
        if pose == "retracted":
            low_margin = bounds[0] - INNER_LO
            high_margin = INNER_HI - bounds[1]
            if np.min(np.r_[low_margin, high_margin]) < -0.01:
                failures.append("Eingefahrene Hand liegt außerhalb des Innenraums")
            pose_metrics[pose]["cavity_margin_mm"] = float(
                np.min(np.r_[low_margin, high_margin]))
            pose_metrics[pose]["lid_clearance_mm"] = float(
                86.0 - bounds[1][2]
            )

    # The phalanges are distinct anatomical shells. They may be connected by
    # the explicit PLA flexure collar, but the source bone volumes themselves
    # must never occupy the same space, nor may a socket intersect the palm.
    progress("Lade anatomische Fingerknochen", started)
    anatomical = skeleton_hand.load_skeleton()
    max_adjacent_bone_overlap = 0.0
    max_any_bone_overlap = 0.0
    anatomy_poses = (
        ("flat", skeleton_hand.FLAT_POSE),
        ("grip", skeleton_hand.GRIP_POSE),
    )
    for pose_name, pose in anatomy_poses:
        progress(f"Pruefe Knochenueberlappungen: {pose_name}", started)
        posed_bones = []
        for ray in skeleton_hand.RAYS:
            posed = skeleton_hand.pose_ray(anatomical, ray, pose[ray])
            posed_bones.extend(posed.bones)
            for first, second in zip(posed.bones[:-1], posed.bones[1:]):
                max_adjacent_bone_overlap = max(
                    max_adjacent_bone_overlap,
                    volume_intersection(first, second),
                )
        for index, first in enumerate(posed_bones):
            for second in posed_bones[index + 1:]:
                max_any_bone_overlap = max(
                    max_any_bone_overlap,
                    volume_intersection(first, second),
                )
    deployed_named = {
        name: mesh for name, mesh, _colour
        in assembly.build_scene("deployed")
    }
    max_finger_palm_overlap = max(
        volume_intersection(
            deployed_named["hand-palm"],
            deployed_named[f"hand-finger-{ray}"],
        )
        for ray in skeleton_hand.RAYS
    )
    if max_adjacent_bone_overlap > 0.01:
        failures.append(
            f"Fingerknochen überlappen: {max_adjacent_bone_overlap:.3f} mm3"
        )
    if max_any_bone_overlap > 0.01:
        failures.append(
            f"Fingerknochen schneiden sich poseübergreifend: "
            f"{max_any_bone_overlap:.3f} mm3"
        )
    if max_finger_palm_overlap > 0.01:
        failures.append(
            f"Fingersockel schneiden Handfläche: "
            f"{max_finger_palm_overlap:.3f} mm3"
        )

    result = {
        "passed": not failures,
        "failures": failures,
        "max_pivot_error_mm": max_endpoint_error,
        "minimum_slot_margin_mm": min_slot_margin,
        "max_slider_fixed_post_overlap_mm3": max_post_overlap,
        "drive_band_lengths_mm": band_lengths,
        "latch_alignment_mm": latch_alignment,
        "platform_xy_mm": np.round(platform_xy, 3).tolist(),
        "body_counts": body_counts,
        "latch_capture_margin_mm": latch_capture_margin,
        "minimum_hidden_mechanism_margin_mm": minimum_hidden_mechanism_margin,
        "crank_external_depth_mm": crank_external_depth,
        "max_adjacent_bone_overlap_mm3": max_adjacent_bone_overlap,
        "max_any_bone_overlap_mm3": max_any_bone_overlap,
        "max_finger_palm_overlap_mm3": max_finger_palm_overlap,
        "max_sweep_collisions_mm3": {
            "hand_chest": max_hand_chest,
            "hand_lid": max_hand_lid,
            "hand_platform": max_hand_platform,
            "hand_scissor": max_hand_arm,
            "latch_slider": max_latch_overlap,
            "slider_chest": max_slider_chest,
            "latch_chest": max_latch_chest,
            "bracket_chest": max_bracket_chest,
            "latch_bracket": max_latch_bracket,
            "trigger_latch": max_trigger_latch,
            "drive_band_scissor": max_band_arm,
            "control_cord_platform": max_cord_platform,
        },
        "poses": pose_metrics,
        "samples": rows,
        "motion_sweep": sweep_metrics,
        "duration_seconds": time.perf_counter() - started,
    }
    progress(
        f"Abgeschlossen: {'PASS' if result['passed'] else 'FAIL'}",
        started,
    )
    return result


def write_report(result: dict) -> None:
    rows = result["samples"]
    lines = [
        "# Ghoul's Grip - Mechanik-Verifikation",
        "",
        f"Ergebnis: **{'PASS' if result['passed'] else 'FAIL'}**",
        "",
        "Die Prüfung rekonstruiert die kompakte 72-mm-Scherengeometrie in 31 "
        "Stellungen. Dreizehn vollständige Baugruppenstellungen prüfen die "
        "gesamte Bewegungskette: Klinke, Schlitten, Schere, verzögerte "
        "Seilsteuerung des Unterarms und federgeöffneten Deckel.",
        "",
        "| Nachweis | Ergebnis |",
        "| --- | ---: |",
        f"| Max. Pivot-Schließfehler | {result['max_pivot_error_mm']:.6f} mm |",
        f"| Kleinster Kulissenrand | {result['minimum_slot_margin_mm']:.3f} mm |",
        f"| Schlitten/Festpivot-Schnitt | {result['max_slider_fixed_post_overlap_mm3']:.3f} mm³ |",
        f"| Rastklinken-Versatz | {result['latch_alignment_mm']:.3f} mm |",
        f"| Positive Rastüberdeckung | {result['latch_capture_margin_mm']:.3f} mm |",
        f"| Kleinster Gehäuserand verdeckter Mechanik | {result['minimum_hidden_mechanism_margin_mm']:.3f} mm |",
        f"| Überstand des flachen Aufziehschlüssels | {result['crank_external_depth_mm']:.3f} mm |",
        f"| Getrennte Körper je Bauteil | {result['body_counts']} |",
        f"| Hubjoch XY | {result['platform_xy_mm'][0]:.1f} × {result['platform_xy_mm'][1]:.1f} mm |",
        f"| Antriebsgummi gespannt/ausgefahren | {result['drive_band_lengths_mm'][0]:.1f} / {result['drive_band_lengths_mm'][1]:.1f} mm |",
        f"| Benachbarte Fingerknochen-Schnittmenge | {result['max_adjacent_bone_overlap_mm3']:.3f} mm³ |",
        f"| Beliebige Fingerknochen-Schnittmenge (flach/gegriffen) | {result['max_any_bone_overlap_mm3']:.3f} mm³ |",
        f"| Fingersockel/Handfläche-Schnittmenge | {result['max_finger_palm_overlap_mm3']:.3f} mm³ |",
        f"| Laufzeit der Verifikation | {result['duration_seconds']:.1f} s |",
    ]
    for pose, values in result["poses"].items():
        lines.extend([
            f"| {pose}: Hand/Gehäuse-Schnitt | {values['hand_chest_overlap_mm3']:.3f} mm³ |",
            f"| {pose}: Hand/Hubjoch-Schnitt | {values['hand_platform_overlap_mm3']:.3f} mm³ |",
        ])
    for name, value in result["max_sweep_collisions_mm3"].items():
        lines.append(f"| Sweep {name} | {value:.3f} mm³ |")
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
    lines.extend(["", "## Gekoppelte Bewegung", "",
                  "| Scherenwinkel | Deckel | Unterarm |",
                  "| ---: | ---: | ---: |"])
    for sample in result["motion_sweep"]:
        lines.append(
            f"| {sample['theta']:.0f}° | {sample['lid_angle']:.1f}° | "
            f"{sample['forearm_angle']:.1f}° |"
        )
    if result["failures"]:
        lines.extend(["", "## Fehler", ""] +
                     [f"- {item}" for item in result["failures"]])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    outcome = check()
    write_report(outcome)
    print(json.dumps(outcome, indent=2))
    raise SystemExit(0 if outcome["passed"] else 1)
