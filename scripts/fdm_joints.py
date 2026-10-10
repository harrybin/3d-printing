"""Parametric, glue-free FDM joint primitives.

The helpers return ``trimesh.Trimesh`` solids and cutters built from the
repository's manifold-backed primitives. Dimensions are millimetres. They are
deliberately simple building blocks: callers own hardware-specific dimensions,
load calculations, insertion sweeps, and final fit coupons.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Sequence

import numpy as np
import trimesh

from mesh_kit import box, clean, cylinder, difference, union

# Fit starting points for a calibrated 0.4 mm-nozzle FDM process.
CLEARANCE_CLOSE_PER_SIDE = 0.15
CLEARANCE_SLIDING_PER_SIDE = 0.25
CLEARANCE_SERVICE_PER_SIDE = 0.35
CLEARANCE_FILAMENT_HOLE_DIAMETER = 0.15

# Load-policy constants used by downstream design scripts and reviews.
STATIC_SAFETY_FACTOR_MIN = 2.0
SHOCK_SAFETY_FACTOR_MIN = 3.0
FATIGUE_STRESS_FRACTION_MAX = 0.35
CREEP_PRELOAD_FRACTION_MAX = 0.20
CRITICAL_PRINTED_PIN_DIAMETER_MIN = 5.0

FILAMENT_NOMINAL_DIAMETER = 1.75


@dataclass(frozen=True)
class DProfile:
    """Nominal D-profile dimensions."""

    diameter: float
    flat_depth: float

    @property
    def radius(self) -> float:
        return self.diameter / 2.0

    @property
    def flat_x(self) -> float:
        """X coordinate of the flat, measured from the profile centre."""
        return self.radius - self.flat_depth

    def validate(self) -> None:
        if self.diameter <= 0.0:
            raise ValueError("diameter must be positive")
        if not 0.0 < self.flat_depth < self.radius:
            raise ValueError("flat_depth must be between zero and the radius")


def _orient(mesh: trimesh.Trimesh, axis: Sequence[float],
            center: Sequence[float]) -> trimesh.Trimesh:
    result = mesh.copy()
    axis_vector = np.asarray(axis, dtype=float)
    if np.linalg.norm(axis_vector) == 0.0:
        raise ValueError("axis must be non-zero")
    axis_vector /= np.linalg.norm(axis_vector)
    if not np.allclose(axis_vector, (0.0, 0.0, 1.0)):
        result.apply_transform(
            trimesh.geometry.align_vectors((0.0, 0.0, 1.0), axis_vector)
        )
    result.apply_translation(np.asarray(center, dtype=float))
    return clean(result)


def _convex_prism(
    outline: Sequence[Sequence[float]], length: float
) -> trimesh.Trimesh:
    """Extrude a convex XY outline without relying on optional Shapely."""
    points = np.asarray(outline, dtype=float)
    z_values = (-length / 2.0, length / 2.0)
    cloud = np.vstack([
        np.column_stack([points, np.full(len(points), z)])
        for z in z_values
    ])
    return clean(trimesh.convex.convex_hull(cloud))


def d_profile(
    diameter: float,
    length: float,
    flat_depth: float,
    *,
    clearance: float = 0.0,
    axis: Sequence[float] = (0.0, 0.0, 1.0),
    center: Sequence[float] = (0.0, 0.0, 0.0),
    sections: int = 96,
) -> trimesh.Trimesh:
    """Create a D-shaft or D-bore cutter.

    Positive ``clearance`` expands the round diameter and moves the flat
    outward by the same per-side amount, making a mating bore cutter.
    """
    profile = DProfile(diameter, flat_depth)
    profile.validate()
    if length <= 0.0 or clearance < 0.0:
        raise ValueError("length must be positive and clearance non-negative")

    effective_diameter = diameter + 2.0 * clearance
    effective_flat_x = profile.flat_x + clearance
    body = cylinder(effective_diameter / 2.0, length, sections=sections)

    # Remove the +X circular cap. The cutter starts exactly at the flat plane.
    reach = effective_diameter * 2.0
    cap = box(
        (reach, reach, length + 2.0),
        (effective_flat_x + reach / 2.0, 0.0, 0.0),
    )
    return _orient(difference(body, [cap]), axis, center)


def d_shaft(
    diameter: float,
    length: float,
    flat_depth: float,
    **kwargs,
) -> trimesh.Trimesh:
    """Create a nominal D-shaft solid."""
    return d_profile(diameter, length, flat_depth, clearance=0.0, **kwargs)


def d_bore_cutter(
    diameter: float,
    length: float,
    flat_depth: float,
    *,
    clearance: float = CLEARANCE_CLOSE_PER_SIDE,
    **kwargs,
) -> trimesh.Trimesh:
    """Create an enlarged D-profile cutter for a removable mating bore."""
    return d_profile(
        diameter, length, flat_depth, clearance=clearance, **kwargs
    )


def keyed_shaft_coupling(
    shaft_diameter: float,
    flat_depth: float,
    engagement_length: float,
    outer_diameter: float,
    *,
    clearance: float = CLEARANCE_CLOSE_PER_SIDE,
    wall_extension: float = 0.0,
) -> trimesh.Trimesh:
    """Create a cylindrical coupling with a through D-bore.

    ``wall_extension`` adds closed material beyond the engagement zone for a
    caller-provided cross-pin, screw, or other axial retainer.
    """
    if outer_diameter <= shaft_diameter + 2.0 * clearance:
        raise ValueError("outer_diameter must leave positive wall around bore")
    if engagement_length <= 0.0 or wall_extension < 0.0:
        raise ValueError("invalid coupling length")
    total_length = engagement_length + wall_extension
    body = cylinder(outer_diameter / 2.0, total_length)
    bore = d_bore_cutter(
        shaft_diameter,
        total_length + 2.0,
        flat_depth,
        clearance=clearance,
    )
    return clean(difference(body, [bore]))


def cross_pin_hole(
    host_axis_diameter: float,
    *,
    pin_diameter: float = FILAMENT_NOMINAL_DIAMETER,
    diameter_clearance: float = CLEARANCE_FILAMENT_HOLE_DIAMETER,
    axis: Sequence[float] = (1.0, 0.0, 0.0),
    center: Sequence[float] = (0.0, 0.0, 0.0),
    extra_length: float = 2.0,
) -> trimesh.Trimesh:
    """Create a through-hole cutter for a cross-pin or 1.75 mm filament pin."""
    if min(host_axis_diameter, pin_diameter, extra_length) <= 0.0:
        raise ValueError("diameters and extra_length must be positive")
    return cylinder(
        (pin_diameter + diameter_clearance) / 2.0,
        host_axis_diameter + extra_length,
        center=center,
        axis=axis,
    )


def captive_hex_nut_trap(
    across_flats: float,
    nut_thickness: float,
    *,
    clearance: float = CLEARANCE_CLOSE_PER_SIDE,
    depth_clearance: float = 0.25,
    entry_length: float = 0.0,
) -> trimesh.Trimesh:
    """Create a captive hex-nut pocket cutter.

    With ``entry_length > 0`` the cutter includes a side-loading insertion
    channel along +X. The caller must add a removable stop or mating part that
    closes this path after assembly.
    """
    if min(across_flats, nut_thickness) <= 0.0:
        raise ValueError("nut dimensions must be positive")
    if min(clearance, depth_clearance, entry_length) < 0.0:
        raise ValueError("clearances and entry_length must be non-negative")

    effective_af = across_flats + 2.0 * clearance
    depth = nut_thickness + depth_clearance
    circumradius = effective_af / sqrt(3.0)
    pocket = trimesh.creation.cylinder(
        radius=circumradius, height=depth, sections=6
    )
    if entry_length == 0.0:
        return clean(pocket)

    channel = box(
        (entry_length + circumradius, effective_af, depth),
        ((entry_length + circumradius) / 2.0, 0.0, 0.0),
    )
    return clean(union([pocket, channel]))


def dovetail_tongue(
    base_width: float,
    crown_width: float,
    height: float,
    length: float,
) -> trimesh.Trimesh:
    """Create a straight male dovetail, extruded along +Z."""
    if min(base_width, crown_width, height, length) <= 0.0:
        raise ValueError("dovetail dimensions must be positive")
    if crown_width <= base_width:
        raise ValueError("crown_width must exceed base_width")
    outline = (
        (-base_width / 2.0, -height / 2.0),
        (base_width / 2.0, -height / 2.0),
        (crown_width / 2.0, height / 2.0),
        (-crown_width / 2.0, height / 2.0),
    )
    return _convex_prism(outline, length)


def dovetail_groove_cutter(
    base_width: float,
    crown_width: float,
    height: float,
    length: float,
    *,
    clearance: float = CLEARANCE_SLIDING_PER_SIDE,
    end_clearance: float = CLEARANCE_SERVICE_PER_SIDE,
) -> trimesh.Trimesh:
    """Create an enlarged female dovetail cutter for sliding assembly."""
    return dovetail_tongue(
        base_width + 2.0 * clearance,
        crown_width + 2.0 * clearance,
        height + clearance,
        length + 2.0 * end_clearance,
    )


def tongue(
    width: float,
    height: float,
    length: float,
) -> trimesh.Trimesh:
    """Create a straight rectangular tongue, extruded along +Z."""
    if min(width, height, length) <= 0.0:
        raise ValueError("tongue dimensions must be positive")
    return box((width, height, length))


def tongue_groove_cutter(
    width: float,
    height: float,
    length: float,
    *,
    clearance: float = CLEARANCE_SLIDING_PER_SIDE,
    end_clearance: float = CLEARANCE_SERVICE_PER_SIDE,
) -> trimesh.Trimesh:
    """Create an enlarged rectangular groove cutter."""
    return box((
        width + 2.0 * clearance,
        height + clearance,
        length + 2.0 * end_clearance,
    ))


def assert_single_watertight_body(mesh: trimesh.Trimesh, name: str) -> None:
    """Raise ``ValueError`` when a generated helper is not one valid solid."""
    bodies = mesh.split(only_watertight=False)
    if not mesh.is_watertight:
        raise ValueError(f"{name}: mesh is not watertight")
    if not mesh.is_winding_consistent:
        raise ValueError(f"{name}: winding is inconsistent")
    if mesh.volume <= 0.0:
        raise ValueError(f"{name}: volume is not positive")
    if len(bodies) != 1:
        raise ValueError(f"{name}: expected one body, found {len(bodies)}")


def self_check() -> None:
    """Validate representative library solids without writing model outputs."""
    examples = {
        "d-shaft": d_shaft(8.0, 20.0, 1.4),
        "d-bore": d_bore_cutter(8.0, 22.0, 1.4),
        "coupling": keyed_shaft_coupling(8.0, 1.4, 16.0, 15.0),
        "cross-pin": cross_pin_hole(10.0),
        "nut-trap": captive_hex_nut_trap(5.5, 2.4, entry_length=5.0),
        "dovetail": dovetail_tongue(8.0, 12.0, 4.0, 25.0),
        "dovetail-groove": dovetail_groove_cutter(
            8.0, 12.0, 4.0, 25.0
        ),
        "tongue": tongue(8.0, 3.0, 25.0),
        "tongue-groove": tongue_groove_cutter(8.0, 3.0, 25.0),
    }
    for name, mesh in examples.items():
        assert_single_watertight_body(mesh, name)


if __name__ == "__main__":
    self_check()
    print("fdm_joints self-check: OK")
