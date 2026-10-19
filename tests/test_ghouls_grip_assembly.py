"""Assembly-interface regressions for the Ghoul's Grip."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mechanism  # noqa: E402
from ghouls_grip import PRINT_HAND_POSE, PRINT_QUANTITIES  # noqa: E402
from mesh_kit import cylinder, intersection, sphere  # noqa: E402
from candy_hand import build_hand, build_dish, mount_datums  # noqa: E402
from skeleton_hand import (  # noqa: E402
    FLAT_POSE,
    GRIP_POSE,
    PEG_D,
    RAYS,
    SOCKET_CLEAR,
    WRIST_D,
    WRIST_PIN_FROM_MOUNT,
    WRIST_SOCKET,
    WRIST_SOCKET_LEAD_IN,
    build_finger,
    build_palm,
    load_skeleton,
    palm_to_forearm_transform,
    peg_direction,
    pose_ray,
    wrist_frame,
)


class GhoulAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skeleton = load_skeleton()
        cls.hand = build_hand(cls.skeleton)
        cls.palm = cls.hand["hand-palm"]
        cls.mount, cls.axis = wrist_frame(cls.skeleton)

    def _probe_volume(self, distance: float) -> float:
        probe = cylinder(
            (WRIST_D - 1.0) / 2.0,
            0.6,
            self.mount + self.axis * distance,
            self.axis,
        )
        overlap = intersection([self.palm, probe])
        return 0.0 if overlap is None else abs(float(overlap.volume))

    def test_palm_socket_has_open_mouth_and_blind_floor(self) -> None:
        self.assertLess(
            self._probe_volume(
                WRIST_SOCKET + WRIST_SOCKET_LEAD_IN + 0.5
            ),
            0.01,
        )
        self.assertGreater(self._probe_volume(-2.0), 20.0)

    def test_palm_cross_pin_matches_forearm_cross_pin(self) -> None:
        transform = palm_to_forearm_transform(
            self.skeleton,
            mechanism.FOREARM_LENGTH + 9.0,
            mechanism.HAND_PALM_ROLL,
        )
        palm_pin = self.mount + self.axis * WRIST_PIN_FROM_MOUNT
        installed = (transform @ np.r_[palm_pin, 1.0])[:3]
        self.assertTrue(np.allclose(
            installed,
            (0.0, 0.0, mechanism.FOREARM_LENGTH + 9.0),
            atol=1e-6,
        ))

    def test_printed_finger_sockets_align_with_palm_pegs(self) -> None:
        self.assertEqual(PRINT_HAND_POSE, GRIP_POSE)
        self.assertAlmostEqual(SOCKET_CLEAR, 0.4)
        self.assertAlmostEqual(PEG_D + SOCKET_CLEAR, 4.4)
        for ray in RAYS:
            peg_axis = peg_direction(self.skeleton, ray)
            finger = pose_ray(self.skeleton, ray, PRINT_HAND_POSE[ray])
            flat = pose_ray(self.skeleton, ray, FLAT_POSE[ray])
            self.assertTrue(np.allclose(
                finger.base_direction, peg_axis, atol=1e-6), ray)
            self.assertGreater(
                float(np.linalg.norm(flat.base_direction - peg_axis)),
                0.1,
                ray,
            )

    def test_finger_insertion_sweep_clears_palm(self) -> None:
        for ray in RAYS:
            axis = peg_direction(self.skeleton, ray)
            finger = self.hand[f"hand-finger-{ray}"]
            for remaining in (12.0, 8.0, 4.0, 0.0):
                candidate = finger.copy()
                candidate.apply_translation(axis * remaining)
                overlap = intersection([self.palm, candidate])
                volume = (
                    0.0 if overlap is None else abs(float(overlap.volume))
                )
                self.assertLessEqual(
                    volume,
                    0.5,
                    f"{ray} MCP insertion collides at {remaining:g} mm "
                    f"from the seated position: {volume:.3f} mm^3",
                )

    def test_finger_knuckles_are_solid_not_relief_gaps(self) -> None:
        for ray in RAYS:
            posed = pose_ray(self.skeleton, ray, PRINT_HAND_POSE[ray])
            finger = self.hand[f"hand-finger-{ray}"]
            for index, joint in enumerate(posed.joints[1:-1], 1):
                probe = sphere(1.2, joint)
                filled = intersection([finger, probe]).volume / probe.volume
                self.assertGreater(
                    filled, 0.98, f"{ray} joint {index} still has a relief gap")

    def test_thumb_opposes_the_other_fingers(self) -> None:
        posed = pose_ray(self.skeleton, "thumb", PRINT_HAND_POSE["thumb"])
        self.assertLess(posed.base_direction[0], -0.35)
        self.assertLess(posed.joints[-1][0], posed.base[0] - 10.0)

    def test_dish_locators_are_blind_and_have_a_solid_roof(self) -> None:
        dish = build_dish(self.skeleton)
        palm_in_dish = self.palm.copy()
        from candy_hand import dish_frame, SOCKET_DEPTH
        palm_in_dish.apply_transform(np.linalg.inv(dish_frame(self.skeleton)))
        for root, _seat in mount_datums(self.skeleton):
            x, y, z_rim = root
            bore = cylinder(1.0, 0.5, [x, y, z_rim - 1.0])
            floor = cylinder(1.0, 0.5, [x, y, z_rim - SOCKET_DEPTH - 1.0])
            peg = cylinder(1.0, 0.5, [x, y, z_rim - 1.5])
            roof = cylinder(1.0, 0.5, [x, y, 1.0])
            self.assertLess(abs(intersection([palm_in_dish, bore]).volume), 0.01)
            self.assertGreater(
                intersection([palm_in_dish, floor]).volume / floor.volume, 0.99)
            self.assertGreater(
                intersection([dish, peg]).volume / peg.volume, 0.99)
            self.assertGreater(
                intersection([dish, roof]).volume / roof.volume, 0.99)

    def test_printed_pin_inventory_matches_scissor_joint_contract(self) -> None:
        # 10 scissor snap pins + 3 idler pins + 1 lid-follower pin.
        counts = {variant: PRINT_QUANTITIES.get(f"pivot-pin-{variant}", 1)
                  for variant in mechanism.PIN_GRIPS}
        self.assertEqual(counts, mechanism.PIN_QUANTITIES)
        self.assertEqual(sum(counts.values()), 14)
        self.assertNotIn("pivot-pin-3", PRINT_QUANTITIES)
        arm = mechanism.build_scissor_arm()
        # x +-28 now carries the scissor-drive gear key hole; its boss ring
        # must stay solid (no stray joint hole cut through the arm).
        former_false_joint = cylinder(
            1.0,
            mechanism.ARM_T + 1.0,
            (mechanism.ARM_L / 2.0 - 11.0, 0.0, mechanism.ARM_T / 2.0),
        )
        overlap = intersection([arm, former_false_joint])
        self.assertIsNotNone(overlap)
        self.assertGreater(abs(float(overlap.volume)), 5.0)


if __name__ == "__main__":
    unittest.main()
