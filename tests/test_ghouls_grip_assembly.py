"""Assembly-interface regressions for the Ghoul's Grip."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mechanism  # noqa: E402
from ghouls_grip import PRINT_QUANTITIES  # noqa: E402
from mesh_kit import cylinder, intersection  # noqa: E402
from skeleton_hand import (  # noqa: E402
    WRIST_D,
    WRIST_PIN_FROM_MOUNT,
    WRIST_SOCKET,
    WRIST_SOCKET_LEAD_IN,
    build_palm,
    load_skeleton,
    palm_to_forearm_transform,
    wrist_frame,
)


class GhoulAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skeleton = load_skeleton()
        cls.palm = build_palm(cls.skeleton)
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

    def test_printed_pin_inventory_matches_scissor_joint_contract(self) -> None:
        self.assertEqual(PRINT_QUANTITIES["pivot-pin-3"], 10)
        self.assertNotIn("pivot-pin-4", PRINT_QUANTITIES)
        arm = mechanism.build_scissor_arm()
        former_false_joint = cylinder(
            1.0,
            mechanism.ARM_T + 1.0,
            (mechanism.ARM_L / 2.0 - 8.0, 0.0, mechanism.ARM_T / 2.0),
        )
        overlap = intersection([arm, former_false_joint])
        self.assertIsNotNone(overlap)
        self.assertGreater(abs(float(overlap.volume)), 5.0)


if __name__ == "__main__":
    unittest.main()
